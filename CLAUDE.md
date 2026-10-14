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
4. Mudou perfil ou tabela → rodar `python scripts/validar_perfis.py`.
5. Análises e cálculos: preferir scripts Python em `scripts/` a análise manual.
6. Uso principal pelo celular (S22): respostas curtas e objetivas.

## Estrutura
- `perfis/filamentos.csv` — catálogo fio → perfil Orca (temperaturas, ventoinha, retração, obs. PEI)
- `perfis/qualidades.csv` — rapida/normal/fina → perfil de processo
- `perfis/orca/{machine,filament,process}/` — perfis OrcaSlicer (JSON de usuário herdando do sistema Creality V3 KE); ver README
- `facilitador/` — app local do PC do primo (STL → OrcaSlicer CLI → Moonraker); ver README
- `fila/` — (futuro) trabalhos aguardando impressão
- `modelos/` — STL/3MF organizados por projeto ou cliente
- `problemas/` — base de conhecimento de falhas e correções
- `scripts/` — utilitários (custo, resumo do log, `validar_perfis.py`)
- `log/impressoes.csv` — histórico de impressões

## Arquitetura (decidida)
Contexto: a impressora fica com o primo (amador, PC Windows); o dono do repo (experiente) terceiriza produção e opera remoto. Custo zero: só impressora, PC do primo, GitHub free, Tailscale free, assinatura Claude do dono, OrcaSlicer CLI.

- **GitHub = fonte da verdade**: perfis curados, tabela fio→perfil, `fila/`, `log/`, código, verificador. **Nunca** chaves/tokens no repo.
- **PC do primo (ponte)**: `git pull` automático; facilitador local (app Python no navegador, `localhost:8000`); OrcaSlicer CLI; Tailscale; opcional `claude remote-control`.
- **Facilitador**: primo arrasta STL → escolhe filamento/qualidade/suporte → app fatia com perfil do repo → mostra tempo/peso/custo → assina e envia ao Moonraker. Sem IA no app (sem custo de API nem uso da conta do dono).
- **Impressora**: Moonraker com `force_logins` + API key; Fluidd; verificador de assinatura HMAC (cancela impressão sem assinatura válida; chave por pessoa). Creality Cloud desativado para a regra valer.

## Roadmap
1. [x] Perfis base + tabela de filamentos/qualidades + validador (valores base, ajustar após teste)
2. [x] Facilitador local: OrcaSlicer CLI + envio ao Moonraker (testado com Orca 2.4.2 e Moonraker simulado; falta teste real no Windows/impressora)
3. [ ] Assinatura HMAC + token Moonraker
4. [ ] Tailscale (acesso remoto)
5. [ ] Skill Claude para o dono
6. [ ] Orçamentos: gerar orçamento para cliente a partir do fatiamento (reaproveita `facilitador/fatiar.py`: tempo, peso, custo de filamento e energia), somando margem, mão de obra, acabamento e frete; saída em PDF para o cliente. Escopo e regras de preço a definir.

Pendente: teste real do facilitador no Windows + impressora; sincronizar `facilitador/trabalhos/historico.csv` com `log/impressoes.csv`; regra de assinatura das peças do primo (sugestão: chave por pessoa); custos reais (R$/kg, R$/kWh, watts) em `scripts/custo.py`; importar histórico de chats antigos; exportar perfis reais do OrcaSlicer.
