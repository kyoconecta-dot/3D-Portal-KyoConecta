# 3D-Portal KyoConecta — Central de comando da impressora 3D

Contexto fixo para toda sessão do Claude Code neste repositório.

## Equipamento
- Impressora: Creality Ender 3 V3 KE (Klipper / Creality OS, bico 0.4 mm, volume 220x220x240 mm)
- Mesa: PEI
- Slicer: OrcaSlicer
- Filamentos em uso: PLA, PETG, TPU (detalhar marcas/temperaturas em `perfis/`)

## Regras de trabalho
1. Antes de imprimir, validar o 3MF (skill validate-3mf ou `scripts/`).
2. Toda impressão relevante entra em `log/impressoes.csv`.
3. Todo defeito resolvido vira um arquivo em `problemas/` (sintoma, causa, ajuste no OrcaSlicer, resultado).
4. Análises e cálculos: preferir scripts Python em `scripts/` a análise manual.
5. Uso principal pelo celular (S22): respostas curtas e objetivas.

## Estrutura
- `perfis/` — perfis exportados do OrcaSlicer (impressora, filamento, processo)
- `modelos/` — STL/3MF organizados por projeto ou cliente
- `problemas/` — base de conhecimento de falhas e correções
- `scripts/` — utilitários (custo, resumo do log, validação)
- `log/impressoes.csv` — histórico de impressões
