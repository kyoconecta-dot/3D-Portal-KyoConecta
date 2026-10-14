"""Custo de uma peça: python scripts/custo.py <peso_g> <tempo_min> [preco_kg] [kwh] [watts]"""
import sys

peso, tempo = float(sys.argv[1]), float(sys.argv[2])
preco_kg = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
kwh = float(sys.argv[4]) if len(sys.argv) > 4 else 0.90
watts = float(sys.argv[5]) if len(sys.argv) > 5 else 150.0

filamento = peso / 1000 * preco_kg
energia = watts / 1000 * tempo / 60 * kwh
print(f"Filamento: R$ {filamento:.2f} | Energia: R$ {energia:.2f} | Total: R$ {filamento + energia:.2f}")
