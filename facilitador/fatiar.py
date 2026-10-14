"""Fatia um STL/3MF com o OrcaSlicer CLI e lê tempo/peso do G-code."""
import re
import shutil
import subprocess
from pathlib import Path

from . import perfis

SUPORTE = {"enable_support": "1", "support_type": "tree(auto)", "support_on_build_plate_only": "1"}


def _tempo_min(txt):
    """'1d 2h 3m 4s' -> minutos."""
    mult = {"d": 1440, "h": 60, "m": 1, "s": 1 / 60}
    return round(sum(int(n) * mult[u] for n, u in re.findall(r"(\d+)([dhms])", txt)), 1)


def ler_cabecalho(gcode):
    """Extrai tempo e filamento dos comentários que o Orca grava no G-code."""
    info = {}
    with open(gcode, encoding="utf-8", errors="replace") as f:
        for linha in f:
            if not linha.startswith(";"):
                continue
            m = re.match(r"; (.+?) = (.*)", linha.strip())
            if not m:
                continue
            chave, valor = m.groups()
            if chave == "estimated printing time (normal mode)":
                info["tempo_min"] = _tempo_min(valor)
                info["tempo_txt"] = valor
            elif chave == "total filament used [g]":
                info["peso_g"] = float(valor)
            elif chave == "filament used [mm]":
                info["filamento_mm"] = float(valor.split(",")[0])
    if "tempo_min" not in info or "peso_g" not in info:
        raise RuntimeError("G-code sem estimativa de tempo/peso")
    return info


def custo(peso_g, tempo_min, material, cfg):
    preco = cfg["preco_kg"].get(material, max(cfg["preco_kg"].values()))
    fil = round(peso_g / 1000 * preco, 2)
    energia = round(cfg["watts"] / 1000 * tempo_min / 60 * cfg["kwh"], 2)
    return {"filamento": fil, "energia": energia, "total": round(fil + energia, 2)}  # soma bate com a tela


def fatiar(modelo, pasta, filamento_id, qualidade_id, suporte, cfg):
    """Fatia `modelo` dentro de `pasta` e devolve dict com gcode, tempo, peso e custo."""
    pasta = Path(pasta)
    saida = pasta / "saida"
    shutil.rmtree(saida, ignore_errors=True)
    saida.mkdir(parents=True)
    arq = perfis.gravar_achatados(pasta / "perfis", cfg["orca_profiles"], filamento_id, qualidade_id,
                                  SUPORTE if suporte else None)
    cmd = [cfg["orca_exe"],
           "--datadir", str(pasta / "orca_datadir"),  # isola do Orca que o primo usa na interface
           "--load-settings", f"{arq['machine']};{arq['process']}",
           "--load-filaments", str(arq["filament"]),
           "--arrange", "1", "--slice", "0",
           "--outputdir", str(saida), str(modelo)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=cfg["timeout_fatiar_s"])
    (pasta / "orca.log").write_text(r.stdout + r.stderr, encoding="utf-8")
    gcodes = sorted(saida.glob("*.gcode"))
    if r.returncode != 0 or not gcodes:
        detalhe = (r.stdout + r.stderr).strip().splitlines()[-3:]
        raise RuntimeError(f"OrcaSlicer falhou (código {r.returncode}): " + " | ".join(detalhe))
    if len(gcodes) > 1:
        raise RuntimeError("arquivo gerou mais de uma placa; envie uma peça/placa por vez")
    info = ler_cabecalho(gcodes[0])
    material = perfis.filamentos()[filamento_id]["material"]
    info.update(gcode=str(gcodes[0]), custo=custo(info["peso_g"], info["tempo_min"], material, cfg))
    return info
