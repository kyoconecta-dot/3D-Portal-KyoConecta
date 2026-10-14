"""Confere consistência entre perfis/filamentos.csv, perfis/qualidades.csv e perfis/orca/.

Uso: python scripts/validar_perfis.py   (sai com código 1 se houver erro)
"""
import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "perfis"
ORCA = RAIZ / "orca"
IMPRESSORA = "Creality Ender-3 V3 KE 0.4 nozzle"

# coluna do CSV -> chave no JSON do OrcaSlicer (valor fica em lista de strings)
CAMPOS_FILAMENTO = {
    "material": "filament_type",
    "temp_bico": "nozzle_temperature",
    "temp_bico_camada1": "nozzle_temperature_initial_layer",
    "temp_mesa": "hot_plate_temp",
    "vel_max_volumetrica_mm3s": "filament_max_volumetric_speed",
    "ventoinha_min_pct": "fan_min_speed",
    "ventoinha_max_pct": "fan_max_speed",
    "retracao_mm": "filament_retraction_length",
    "retracao_vel_mms": "filament_retraction_speed",
    "perfil_sistema_base": "inherits",
}
CAMPOS_QUALIDADE = {"altura_camada_mm": "layer_height", "perfil_sistema_base": "inherits"}
QUALIDADES_OBRIGATORIAS = {"rapida", "normal", "fina"}
LIMITES = {"temp_bico": (180, 300), "temp_mesa": (0, 100), "altura_camada_mm": (0.08, 0.32)}

erros, avisos = [], []


def valor(v):
    v = v[0] if isinstance(v, list) and v else v
    try:
        return float(str(v).rstrip("%"))
    except ValueError:
        return str(v).strip()


def ler_json(rel, tipo):
    p = ORCA / rel
    if not p.exists():
        erros.append(f"{rel}: arquivo não existe")
        return None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        erros.append(f"{rel}: JSON inválido ({e})")
        return None
    if d.get("type") != tipo:
        erros.append(f"{rel}: type={d.get('type')!r}, esperado {tipo!r}")
    if d.get("name") != p.stem:
        erros.append(f"{rel}: name={d.get('name')!r} difere do nome do arquivo")
    if not d.get("inherits"):
        avisos.append(f"{rel}: sem 'inherits' (perfil completo, ok se exportado assim)")
    cp = d.get("compatible_printers")
    if cp and IMPRESSORA not in cp:
        erros.append(f"{rel}: compatible_printers não inclui {IMPRESSORA}")
    return d


def conferir_tabela(arq, tipo, campos):
    referenciados = set()
    with open(RAIZ / arq, encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))
    ids = [l["id"] for l in linhas]
    for dup in {i for i in ids if ids.count(i) > 1}:
        erros.append(f"{arq}: id duplicado {dup}")
    for l in linhas:
        for col, (lo, hi) in LIMITES.items():
            if col in l and not lo <= float(l[col]) <= hi:
                erros.append(f"{arq} [{l['id']}]: {col}={l[col]} fora de {lo}-{hi}")
        rel = l["perfil_orca"]
        referenciados.add((ORCA / rel).resolve())
        d = ler_json(rel, tipo)
        if not d:
            continue
        for col, chave in campos.items():
            if chave not in d:
                avisos.append(f"{arq} [{l['id']}]: {chave} não definido no JSON (herdado)")
            elif valor(d[chave]) != valor(l[col]):
                erros.append(f"{arq} [{l['id']}]: {col}={l[col]} mas JSON {chave}={valor(d[chave])}")
    return ids, referenciados


ids_f, ref_f = conferir_tabela("filamentos.csv", "filament", CAMPOS_FILAMENTO)
ids_q, ref_q = conferir_tabela("qualidades.csv", "process", CAMPOS_QUALIDADE)
for q in QUALIDADES_OBRIGATORIAS - set(ids_q):
    erros.append(f"qualidades.csv: falta qualidade {q}")

for pasta, ref in (("filament", ref_f), ("process", ref_q)):
    for p in sorted((ORCA / pasta).glob("*.json")):
        if p.resolve() not in ref:
            avisos.append(f"{pasta}/{p.name}: não referenciado na tabela")
for p in sorted((ORCA / "machine").glob("*.json")):
    d = ler_json(f"machine/{p.name}", "machine")
    if d and d.get("inherits") != IMPRESSORA:
        avisos.append(f"machine/{p.name}: inherits={d.get('inherits')!r}")

for a in avisos:
    print("AVISO:", a)
for e in erros:
    print("ERRO: ", e)
print(f"{len(ids_f)} filamentos, {len(ids_q)} qualidades | {len(erros)} erro(s), {len(avisos)} aviso(s)")
sys.exit(1 if erros else 0)
