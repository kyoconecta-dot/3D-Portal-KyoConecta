"""Facilitador local: arrasta STL -> fatia com perfil do repo -> envia ao Moonraker.

Uso: python -m facilitador.app   (abre em http://localhost:8000)
Só biblioteca padrão do Python; escuta apenas em 127.0.0.1.
"""
import csv
import json
import re
import sys
import threading
import traceback
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

if __package__ in (None, ""):  # permite "python facilitador/app.py"
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "facilitador"

from facilitador import config, fatiar, moonraker, perfis  # noqa: E402

PASTA = Path(__file__).resolve().parent
TRABALHOS = PASTA / "trabalhos"  # local, fora do git
HISTORICO = TRABALHOS / "historico.csv"
EXTENSOES = {".stl", ".3mf", ".obj", ".step", ".stp"}
MAX_BYTES = 200 * 1024 * 1024
TRAVA_FATIAR = threading.Lock()  # um fatiamento por vez
CFG = config.carregar()


def nome_seguro(txt):
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", txt).strip("._")
    return base[:60] or "peca"


def registrar(trab, acao):
    novo = not HISTORICO.exists()
    with open(HISTORICO, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        if novo:
            w.writerow(["data", "peca", "filamento", "qualidade", "suporte", "peso_g", "tempo_min", "custo_total", "acao"])
        w.writerow([datetime.now().isoformat(timespec="seconds"), trab["peca"], trab["filamento"], trab["qualidade"],
                    int(trab["suporte"]), trab["peso_g"], trab["tempo_min"], trab["custo"]["total"], acao])


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))

    def _json(self, obj, codigo=200):
        corpo = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def _erro(self, msg, codigo=400):
        self._json({"erro": msg}, codigo)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/":
            corpo = (PASTA / "pagina.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        elif url.path == "/api/opcoes":
            fil = [{"id": k, "rotulo": f"{v['material']} {v['marca']} {v['cor']}".strip(), "obs": v["obs_pei"],
                    "status": v["status"]} for k, v in perfis.filamentos().items()]
            qual = [{"id": k, "rotulo": f"{k} ({v['altura_camada_mm']} mm)", "obs": v["descricao"]}
                    for k, v in perfis.qualidades().items()]
            self._json({"filamentos": fil, "qualidades": qual,
                        "orca_ok": Path(CFG["orca_exe"]).exists(), "moonraker": CFG["moonraker_url"]})
        elif url.path == "/api/impressora":
            try:
                self._json(moonraker.status(CFG))
            except moonraker.ErroMoonraker as e:
                self._erro(str(e), 502)
        else:
            self._erro("não encontrado", 404)

    def do_POST(self):
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        try:
            if url.path == "/api/fatiar":
                self._fatiar(q)
            elif url.path == "/api/enviar":
                self._enviar(q)
            else:
                self._erro("não encontrado", 404)
        except moonraker.ErroMoonraker as e:
            self._erro(str(e), 502)
        except Exception as e:  # erro inesperado: mostra na tela e no terminal
            traceback.print_exc()
            self._erro(str(e), 500)

    def _fatiar(self, q):
        nome = q.get("nome", "")
        ext = Path(nome).suffix.lower()
        if ext not in EXTENSOES:
            return self._erro(f"formato não suportado: {ext or '?'} (use STL, 3MF, OBJ ou STEP)")
        if q.get("filamento") not in perfis.filamentos() or q.get("qualidade") not in perfis.qualidades():
            return self._erro("filamento ou qualidade inválidos")
        tam = int(self.headers.get("Content-Length", 0))
        if not 0 < tam <= MAX_BYTES:
            return self._erro("arquivo vazio ou maior que 200 MB")
        dados = self.rfile.read(tam)

        peca = nome_seguro(Path(nome).stem)
        trab_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + peca
        pasta = TRABALHOS / trab_id
        pasta.mkdir(parents=True)
        modelo = pasta / f"{peca}{ext}"
        modelo.write_bytes(dados)
        suporte = q.get("suporte") == "1"
        with TRAVA_FATIAR:
            info = fatiar.fatiar(modelo, pasta, q["filamento"], q["qualidade"], suporte, CFG)
        trab = {"id": trab_id, "peca": peca, "filamento": q["filamento"], "qualidade": q["qualidade"],
                "suporte": suporte, **info}
        (pasta / "trabalho.json").write_text(json.dumps(trab, ensure_ascii=False, indent=1), encoding="utf-8")
        registrar(trab, "fatiado")
        self._json({k: v for k, v in trab.items() if k != "gcode"})

    def _enviar(self, q):
        trab_id = q.get("id", "")
        arq = TRABALHOS / trab_id / "trabalho.json"
        if not re.fullmatch(r"[\w.-]+", trab_id) or not arq.exists():
            return self._erro("trabalho não encontrado")
        trab = json.loads(arq.read_text(encoding="utf-8"))
        imprimir = q.get("imprimir") == "1"
        if imprimir:
            st = moonraker.status(CFG)
            if st["estado"] in ("printing", "paused"):
                return self._erro(f"impressora ocupada ({st['estado']}: {st['arquivo']}); envie sem imprimir", 409)
        nome_remoto = f"{trab['peca']}_{trab['filamento']}_{trab['qualidade']}.gcode"
        # passo 3 do roadmap: assinar o G-code aqui, antes do envio
        moonraker.enviar(CFG, trab["gcode"], nome_remoto, imprimir)
        registrar(trab, "impressao_iniciada" if imprimir else "enviado")
        self._json({"ok": True, "arquivo": nome_remoto, "imprimindo": imprimir})


def main():
    TRABALHOS.mkdir(exist_ok=True)
    porta = int(CFG["porta"])
    srv = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    url = f"http://localhost:{porta}"
    print(f"Facilitador em {url}  (Ctrl+C para sair)")
    if not Path(CFG["orca_exe"]).exists():
        print(f"AVISO: OrcaSlicer não encontrado em {CFG['orca_exe']} - ajuste config.local.json")
    if "--sem-navegador" not in sys.argv:
        threading.Timer(1.0, webbrowser.open, [url]).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
