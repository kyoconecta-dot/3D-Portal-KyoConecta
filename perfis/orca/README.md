# Perfis OrcaSlicer — Ender 3 V3 KE (bico 0.4)

Fonte da verdade dos perfis usados pelo facilitador (OrcaSlicer CLI). Valores atuais são **base conservadora — ajustar após teste**.

## Pastas
| Pasta | Tipo Orca | Herda de (perfil de sistema Creality) |
|---|---|---|
| `machine/` | Impressora | `Creality Ender-3 V3 KE 0.4 nozzle` |
| `filament/` | Filamento | `Generic PLA/PETG/TPU @Creality Ender-3V3-all` |
| `process/` | Processo | `0.24mm Draft` / `0.20mm Standard` / `0.12mm Fine @Creality Ender3V3KE` |

Os arquivos guardam só o que difere do sistema (`"from": "User"` + `"inherits"`). Nomes de perfil sem espaço: `name` = nome do arquivo.

## Tabelas
- `../filamentos.csv` — catálogo fio → perfil (temperaturas, ventoinha, retração, obs. PEI).
- `../qualidades.csv` — rapida / normal / fina → perfil de processo.
- Após qualquer mudança: `python scripts/validar_perfis.py` (tabela e JSON precisam bater).

## Exportar do OrcaSlicer (Windows)
1. Ajuste e **salve** o preset no Orca (ícone de disquete) com nome no padrão `KYO_<MATERIAL>_<marca>_V3KE` (filamento) ou `KYO_<qualidade>_<camada>_V3KE` (processo).
2. Copie o JSON da pasta de usuário:
   `%APPDATA%\OrcaSlicer\user\default\filament\` (também `process\` e `machine\`).
   Atalho no Orca: *Ajuda → Mostrar pasta de configuração*.
3. Cole em `perfis/orca/<tipo>/` deste repo (ignore o `.info` ao lado).
4. Atualize a linha correspondente em `filamentos.csv` / `qualidades.csv`, troque `status` para `testado` e rode o validador.
5. Commit + push. O PC do primo recebe no próximo `git pull`.

Alternativa: *Arquivo → Exportar → Exportar pacote de presets* gera um `.zip`; extraia os JSON nas pastas acima.

## Importar no Orca (PC do primo, uso manual)
*Arquivo → Importar → Importar configurações* e selecione os JSON. O facilitador não depende disso: passa os arquivos direto ao CLI.

## Como o facilitador usa estes perfis
O CLI do Orca 2.4.2 resolve `inherits` de processo/filamento, mas não do perfil de máquina de usuário (G-code sai sem `G92 E0` e o fatiamento falha). Por isso `facilitador/perfis.py` "achata" cada perfil (resolve a cadeia contra `resources/profiles` do Orca instalado) antes de chamar o CLI. Nomes de sistema seguem a 2.4.2 (`Creality Generic PLA @Ender-3V3-all`); o achatador aceita também o nome novo do `main` (`Generic PLA @Creality Ender-3V3-all`).
