"""Catálogo (CSV do repo) e achatamento de perfis OrcaSlicer.

Os perfis do repo guardam só as diferenças ("inherits" + chaves alteradas).
O CLI do Orca 2.4 não resolve a herança do perfil de máquina de usuário (o
G-code sai sem "G92 E0" e o fatiamento falha), então aqui a cadeia é resolvida
contra os perfis de sistema do Orca instalado e o CLI recebe JSON completo.
"""
import csv
import json
import re
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PERFIS = REPO / "perfis"
ORCA = PERFIS / "orca"
PASTA = {"machine": "machine", "filament": "filament", "process": "process"}
# metadados de preset que não devem ir para o perfil achatado
# "inherits" fica (sem ele o CLI não sabe o nome de sistema e recusa a combinação
# máquina x processo), mas todas as chaves vêm resolvidas.
METADADOS = {"instantiation", "setting_id", "renamed_from", "description"}


def ler_csv(nome):
    with open(PERFIS / nome, encoding="utf-8") as f:
        return {l["id"]: l for l in csv.DictReader(f)}


def filamentos():
    return ler_csv("filamentos.csv")


def qualidades():
    return ler_csv("qualidades.csv")


def maquina():
    arqs = sorted((ORCA / "machine").glob("*.json"))
    if len(arqs) != 1:
        raise RuntimeError(f"esperado 1 perfil em perfis/orca/machine, achei {len(arqs)}")
    return arqs[0]


VENDOR = "Creality"
BIBLIOTECA = "OrcaFilamentLibrary"  # base comum de filamentos em versões novas do Orca


@lru_cache(maxsize=None)
def _indice_sistema(dir_profiles, vendor):
    """(tipo, name) -> caminho dos perfis de sistema de um fabricante.

    Indexa pelo campo "name" (o nome do arquivo nem sempre bate) e só dentro do
    fabricante: nomes como fdm_filament_pla se repetem entre fabricantes.
    """
    idx = {}
    for p in sorted((Path(dir_profiles) / vendor).rglob("*.json")):
        tipo = next((t for t in PASTA if t in p.relative_to(Path(dir_profiles) / vendor).parts), None)
        if tipo is None:
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        nomes = [d.get("name")] + [n for n in d.get("renamed_from", "").split(";")]
        for nome in filter(None, nomes):
            idx.setdefault((tipo, nome.strip()), p)
    return idx


def _apelidos(nome):
    """Nomes equivalentes entre versões do Orca.

    2.4.x: "Creality Generic PLA @Ender-3V3-all"; main: "Generic PLA @Creality Ender-3V3-all".
    """
    yield nome
    m = re.fullmatch(r"Creality Generic (.+) @(.+)", nome)
    if m:
        yield f"Generic {m[1]} @Creality {m[2]}"
    m = re.fullmatch(r"Generic (.+) @Creality (.+)", nome)
    if m:
        yield f"Creality Generic {m[1]} @{m[2]}"


def _achar_sistema(dir_profiles, tipo, nome):
    for vendor in (VENDOR, BIBLIOTECA):
        for apelido in _apelidos(nome):
            p = _indice_sistema(str(dir_profiles), vendor).get((tipo, apelido))
            if p:
                return p
    return None


def _carregar(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def achatar(path, tipo, dir_profiles):
    """Devolve o perfil completo: cadeia de herança mesclada, filho sobrescreve pai."""
    cadeia = [_carregar(path)]
    vistos = set()
    while cadeia[-1].get("inherits"):
        nome = cadeia[-1]["inherits"]
        if nome in vistos:
            raise RuntimeError(f"herança circular em {nome}")
        vistos.add(nome)
        p = _achar_sistema(dir_profiles, tipo, nome)
        if p is None:
            raise RuntimeError(f"perfil de sistema '{nome}' ({tipo}) não encontrado em {dir_profiles}")
        cadeia.append(_carregar(p))
    final = {}
    for d in reversed(cadeia):
        final.update(d)
    for k in METADADOS:
        final.pop(k, None)
    final["from"] = "User"
    final["name"] = cadeia[0]["name"]
    final["inherits"] = cadeia[0].get("inherits", "")
    return final


def gravar_achatados(destino, dir_profiles, filamento_id, qualidade_id, ajustes_processo=None):
    """Grava machine/process/filament achatados em `destino` e devolve os caminhos.

    `ajustes_processo`: chaves que sobrescrevem o processo (ex.: suporte ligado).
    """
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    fil = filamentos()[filamento_id]
    qual = qualidades()[qualidade_id]
    saida = {}
    for tipo, origem in (("machine", maquina()),
                         ("process", ORCA / qual["perfil_orca"]),
                         ("filament", ORCA / fil["perfil_orca"])):
        d = achatar(origem, tipo, dir_profiles)
        if tipo == "process" and ajustes_processo:
            d.update(ajustes_processo)
        p = destino / f"{tipo}.json"
        p.write_text(json.dumps(d, indent=1, ensure_ascii=False), encoding="utf-8")
        saida[tipo] = p
    return saida
