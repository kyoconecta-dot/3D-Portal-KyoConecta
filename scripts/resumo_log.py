"""Resumo do histórico: python scripts/resumo_log.py"""
import csv
from collections import Counter
from pathlib import Path

linhas = list(csv.DictReader(open(Path(__file__).parent.parent / "log/impressoes.csv", encoding="utf-8")))
print(f"Impressões: {len(linhas)}")
print(f"Filamento total: {sum(float(l['peso_g'] or 0) for l in linhas):.0f} g")
print(f"Horas: {sum(float(l['tempo_min'] or 0) for l in linhas) / 60:.1f} h")
for r, n in Counter(l["resultado"] for l in linhas).items():
    print(f"  {r}: {n}")
