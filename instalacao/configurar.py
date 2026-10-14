"""Configura o facilitador neste PC: acha o OrcaSlicer e a impressora, grava config.local.json.

Uso: python instalacao/configurar.py   (pode rodar de novo a qualquer momento)
"""
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import rede  # noqa: E402
from facilitador import config  # noqa: E402


def achar_orca():
    candidatos = []
    for var in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            candidatos += [Path(base) / "OrcaSlicer" / "orca-slicer.exe",
                           Path(base) / "Programs" / "OrcaSlicer" / "orca-slicer.exe"]
    for c in candidatos:
        if c.exists():
            return str(c)
    for var in ("ProgramFiles", "LOCALAPPDATA"):  # instalação em pasta com versão no nome
        base = os.environ.get(var)
        if base:
            for c in Path(base).glob("Orca*/orca-slicer.exe"):
                return str(c)
    return ""


def perguntar(texto, padrao=""):
    r = input(f"{texto}" + (f" [{padrao}]" if padrao != "" else "") + ": ").strip()
    return r or padrao


def main():
    atual = json.loads(config.ARQ_LOCAL.read_text(encoding="utf-8")) if config.ARQ_LOCAL.exists() else {}
    cfg = {**config.PADRAO, **atual}

    print("\n== OrcaSlicer ==")
    orca = atual.get("orca_exe") if atual.get("orca_exe") and Path(atual["orca_exe"]).exists() else achar_orca()
    orca = perguntar("Caminho do orca-slicer.exe", orca or config.PADRAO["orca_exe"])
    if not Path(orca).exists():
        print("  AVISO: arquivo não existe; o facilitador não vai fatiar até corrigir.")

    print("\n== Impressora ==")
    url = atual.get("moonraker_url", "")
    if url and rede.info_moonraker(url, atual.get("moonraker_api_key", ""))[0]:
        print(f"  impressora atual responde em {url}")
    else:
        print(f"  procurando na rede ({rede.ip_local()}/24)...")
        achados = rede.procurar()
        if len(achados) == 1:
            url = f"http://{achados[0]}:{rede.PORTA_MOONRAKER}"
            print(f"  encontrada: {achados[0]}")
        elif achados:
            for i, ip in enumerate(achados, 1):
                print(f"  {i}) {ip}")
            url = f"http://{achados[int(perguntar('Qual delas', '1')) - 1]}:{rede.PORTA_MOONRAKER}"
        else:
            print("  nada encontrado. Veja o IP na tela da impressora (Configurações > Rede).")
            url = f"http://{perguntar('IP da impressora')}:{rede.PORTA_MOONRAKER}"
    chave = perguntar("Chave de API do Moonraker (Enter = sem chave por enquanto)", atual.get("moonraker_api_key", ""))
    info, erro = rede.info_moonraker(url, chave)
    print(f"  {'OK' if info else 'FALHOU'}: " + (f"Moonraker {info.get('moonraker_version')}, klippy {info.get('klippy_state')}" if info else erro))

    print("\n== Custos (Enter mantém) ==")
    precos = dict(cfg["preco_kg"])
    for mat in precos:
        precos[mat] = float(perguntar(f"R$/kg {mat}", precos[mat]))
    kwh = float(perguntar("R$/kWh", cfg["kwh"]))
    watts = float(perguntar("Consumo médio da impressora (W)", cfg["watts"]))

    novo = {**atual, "orca_exe": orca, "moonraker_url": url, "moonraker_api_key": chave,
            "preco_kg": precos, "kwh": kwh, "watts": watts}
    config.ARQ_LOCAL.write_text(json.dumps(novo, indent=4, ensure_ascii=False), encoding="utf-8")
    print(f"\nGravado em {config.ARQ_LOCAL} (fica só neste PC, fora do git).")


if __name__ == "__main__":
    main()
