"""Confere se tudo está pronto neste PC. Rode quando algo não funcionar.

Uso: python instalacao/diagnostico.py [--sem-fatiar]
Sai com código 1 se algum item obrigatório falhar.
"""
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rede  # noqa: E402
from facilitador import config, fatiar, moonraker, perfis  # noqa: E402

falhas = []


def item(nome, ok, detalhe="", obrigatorio=True):
    marca = "OK   " if ok else ("FALHA" if obrigatorio else "aviso")
    print(f"[{marca}] {nome}" + (f" - {detalhe}" if detalhe else ""))
    if not ok and obrigatorio:
        falhas.append(nome)
    return ok


def cubo_stl(caminho, lado=20.0):
    v = [(0, 0, 0), (lado, 0, 0), (lado, lado, 0), (0, lado, 0),
         (0, 0, lado), (lado, 0, lado), (lado, lado, lado), (0, lado, lado)]
    f = [(0, 2, 1), (0, 3, 2), (4, 5, 6), (4, 6, 7), (0, 1, 5), (0, 5, 4),
         (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7)]
    with open(caminho, "wb") as o:
        o.write(b"\0" * 80 + struct.pack("<I", len(f)))
        for t in f:
            o.write(struct.pack("<3f", 0, 0, 0))
            for i in t:
                o.write(struct.pack("<3f", *v[i]))
            o.write(b"\0\0")


def main():
    print(f"Repo: {RAIZ}\n")
    item("Python 3.10+", sys.version_info >= (3, 10), sys.version.split()[0])
    git = shutil.which("git")
    item("Git instalado", bool(git), git or "instale Git for Windows")
    if git:
        r = subprocess.run([git, "-C", str(RAIZ), "status", "-sb"], capture_output=True, text=True)
        primeira = (r.stdout.splitlines() or ["?"])[0]
        item("Repo git sem conflito", r.returncode == 0 and "behind" not in primeira, primeira, obrigatorio=False)
    item("Claude Code", bool(shutil.which("claude")), "opcional", obrigatorio=False)
    item("Tailscale", bool(shutil.which("tailscale")), "opcional (passo 4)", obrigatorio=False)

    item("config.local.json", config.ARQ_LOCAL.exists(), "rode: python instalacao/configurar.py")
    cfg = config.carregar()
    item("OrcaSlicer", Path(cfg["orca_exe"]).exists(), cfg["orca_exe"])
    item("Perfis de sistema do Orca", Path(cfg["orca_profiles"], "Creality").is_dir(), cfg["orca_profiles"])

    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "validar_perfis.py")], capture_output=True, text=True)
    item("Perfis do repo consistentes", r.returncode == 0, (r.stdout.strip().splitlines() or [""])[-1])

    if "--sem-fatiar" not in sys.argv and Path(cfg["orca_exe"]).exists():
        with tempfile.TemporaryDirectory() as tmp:
            cubo_stl(Path(tmp) / "cubo.stl")
            for q in perfis.qualidades():
                for fid in perfis.filamentos():
                    try:
                        info = fatiar.fatiar(Path(tmp) / "cubo.stl", Path(tmp) / f"{q}_{fid}", fid, q, False, cfg)
                        item(f"Fatiar cubo {fid}/{q}", True, f"{info['tempo_txt']}, {info['peso_g']} g")
                    except Exception as e:
                        item(f"Fatiar cubo {fid}/{q}", False, str(e)[:200])

    url = cfg["moonraker_url"]
    info, erro = rede.info_moonraker(url, cfg.get("moonraker_api_key", ""))
    if item("Impressora responde (Moonraker)", bool(info), url + (f" - {erro}" if erro else "")):
        item("Klipper pronto", info.get("klippy_state") == "ready", info.get("klippy_state", "?"))
        try:
            st = moonraker.status(cfg)
            item("Status da impressora", True, f"{st['estado']}, bico {st['bico']}°C, mesa {st['mesa']}°C")
        except moonraker.ErroMoonraker as e:
            item("Status da impressora", False, str(e))
    else:
        ip = url.split("//")[-1].split(":")[0]
        if rede.porta_aberta(ip, rede.PORTA_FLUIDD) or rede.porta_aberta(ip, 80):
            print("        a impressora existe no IP, mas o Moonraker não responde: confira root + Helper Script (GUIA.md)")
        else:
            print("        nada nesse IP: rode  python instalacao/rede.py  para procurar")

    print("\n" + ("TUDO CERTO" if not falhas else f"{len(falhas)} problema(s): " + "; ".join(falhas)))
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
