"""Configuração local do facilitador.

Valores padrão aqui; o que for específico da máquina (caminho do Orca, endereço
e chave do Moonraker, custos) fica em facilitador/config.local.json, que NÃO vai
para o git. Use config.exemplo.json como modelo.
"""
import json
from pathlib import Path

PASTA = Path(__file__).resolve().parent
ARQ_LOCAL = PASTA / "config.local.json"

PADRAO = {
    "porta": 8000,
    "orca_exe": r"C:\Program Files\OrcaSlicer\orca-slicer.exe",
    # vazio = <pasta do orca_exe>/resources/profiles
    "orca_profiles": "",
    "moonraker_url": "http://192.168.0.50:7125",
    "moonraker_api_key": "",
    "preco_kg": {"PLA": 100.0, "PETG": 110.0, "TPU": 150.0},
    "kwh": 0.90,
    "watts": 150.0,
    "timeout_fatiar_s": 600,
}


def carregar():
    cfg = json.loads(json.dumps(PADRAO))
    if ARQ_LOCAL.exists():
        local = json.loads(ARQ_LOCAL.read_text(encoding="utf-8"))
        for k, v in local.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    if not cfg["orca_profiles"]:
        cfg["orca_profiles"] = str(Path(cfg["orca_exe"]).parent / "resources" / "profiles")
    return cfg
