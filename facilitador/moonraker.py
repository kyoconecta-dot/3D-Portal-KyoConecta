"""Cliente mínimo do Moonraker (só biblioteca padrão)."""
import json
import urllib.error
import urllib.request
import uuid
from pathlib import Path


class ErroMoonraker(RuntimeError):
    pass


def _req(cfg, caminho, dados=None, cabecalhos=None, timeout=15):
    url = cfg["moonraker_url"].rstrip("/") + caminho
    h = dict(cabecalhos or {})
    if cfg.get("moonraker_api_key"):
        h["X-Api-Key"] = cfg["moonraker_api_key"]
    req = urllib.request.Request(url, data=dados, headers=h, method="POST" if dados is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        corpo = e.read().decode("utf-8", "replace")[:300]
        if e.code in (401, 403):
            raise ErroMoonraker("impressora recusou a chave de API (confira moonraker_api_key)") from e
        raise ErroMoonraker(f"HTTP {e.code}: {corpo}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ErroMoonraker(f"impressora inacessível em {cfg['moonraker_url']} ({e})") from e


def status(cfg):
    """Estado resumido: klippy, impressão atual, temperaturas."""
    r = _req(cfg, "/printer/objects/query?print_stats&extruder&heater_bed&virtual_sdcard")["result"]["status"]
    ps = r.get("print_stats", {})
    return {
        "estado": ps.get("state", "?"),
        "arquivo": ps.get("filename", ""),
        "progresso": round(100 * r.get("virtual_sdcard", {}).get("progress", 0), 1),
        "bico": round(r.get("extruder", {}).get("temperature", 0)),
        "mesa": round(r.get("heater_bed", {}).get("temperature", 0)),
    }


def enviar(cfg, gcode, nome_remoto, imprimir=False):
    """Envia o G-code (POST /server/files/upload). Com imprimir=True já inicia."""
    fronteira = uuid.uuid4().hex
    partes = []

    def campo(nome, valor):
        partes.append(f'--{fronteira}\r\nContent-Disposition: form-data; name="{nome}"\r\n\r\n{valor}\r\n'.encode())

    campo("root", "gcodes")
    if imprimir:
        campo("print", "true")
    partes.append((f'--{fronteira}\r\nContent-Disposition: form-data; name="file"; filename="{nome_remoto}"\r\n'
                   "Content-Type: application/octet-stream\r\n\r\n").encode())
    partes.append(Path(gcode).read_bytes())
    partes.append(f"\r\n--{fronteira}--\r\n".encode())
    return _req(cfg, "/server/files/upload", b"".join(partes),
                {"Content-Type": f"multipart/form-data; boundary={fronteira}"}, timeout=120)
