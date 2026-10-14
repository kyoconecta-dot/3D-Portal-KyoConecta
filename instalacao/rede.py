"""Descoberta da impressora (Moonraker) na rede local. Só biblioteca padrão."""
import ipaddress
import json
import socket
import urllib.request
from concurrent.futures import ThreadPoolExecutor

PORTA_MOONRAKER = 7125
PORTA_FLUIDD = 4408


def ip_local():
    """IP deste PC na rede (sem enviar nada: o connect UDP só escolhe a interface)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def porta_aberta(ip, porta, timeout=0.4):
    try:
        with socket.create_connection((str(ip), porta), timeout=timeout):
            return True
    except OSError:
        return False


def info_moonraker(url, api_key="", timeout=3):
    """GET /server/info. Devolve (dict|None, erro|None)."""
    h = {"X-Api-Key": api_key} if api_key else {}
    try:
        req = urllib.request.Request(url.rstrip("/") + "/server/info", headers=h)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())["result"], None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}" + (" (precisa de chave de API)" if e.code in (401, 403) else "")
    except Exception as e:  # rede: qualquer falha vira mensagem
        return None, str(e)


def procurar(rede=None, porta=PORTA_MOONRAKER):
    """Varre a /24 do PC (ou `rede`) atrás da porta do Moonraker. Devolve lista de IPs."""
    rede = ipaddress.ip_network(rede or f"{ip_local()}/24", strict=False)
    hosts = list(rede.hosts())
    with ThreadPoolExecutor(max_workers=64) as ex:
        abertos = ex.map(lambda ip: (ip, porta_aberta(ip, porta)), hosts)
        return [str(ip) for ip, ok in abertos if ok]


if __name__ == "__main__":
    print(f"Este PC: {ip_local()} - procurando Moonraker (porta {PORTA_MOONRAKER})...")
    achados = procurar()
    for ip in achados:
        info, erro = info_moonraker(f"http://{ip}:{PORTA_MOONRAKER}")
        print(f"  {ip}: " + (f"Moonraker {info.get('moonraker_version', '?')}, klippy {info.get('klippy_state')}" if info else erro))
    if not achados:
        print("  nenhuma impressora encontrada (ligada? mesma rede? Moonraker instalado?)")
