# Facilitador local (PC Windows do primo)

Página no navegador (`http://localhost:8000`): arrasta o STL, escolhe filamento, qualidade e suporte, vê tempo/peso/custo e envia para a impressora (Moonraker). Fatia com o OrcaSlicer CLI usando os perfis de `perfis/`. Só biblioteca padrão do Python: nada de `pip install`.

## Instalação (uma vez)
1. Python 3.10+ (python.org, marcar "Add to PATH"), Git for Windows e OrcaSlicer 2.4.x (instalador padrão).
2. `git clone` deste repo (ex.: `C:\impressora\3D-Portal-KyoConecta`).
3. Copie `facilitador\config.exemplo.json` para `facilitador\config.local.json` e preencha:
   - `orca_exe`: caminho do `orca-slicer.exe`;
   - `moonraker_url`: IP da impressora na rede, porta 7125;
   - `moonraker_api_key`: chave do Moonraker (Fluidd → Configurações → Autorização). Fica só neste PC;
   - `preco_kg`, `kwh`, `watts`: custos reais.
4. Crie um atalho na área de trabalho para `facilitador\iniciar.bat` (faz `git pull` e abre a página).

## Uso
Arrastar arquivo → Filamento → Qualidade → (suporte se tiver parte no ar) → **Calcular** → **Enviar e imprimir** (ou **Só enviar**: o arquivo fica na impressora para iniciar pelo Fluidd/tela).

- Uma peça/placa por vez; o Orca posiciona no centro da mesa (não gira a peça).
- Bloqueia "imprimir" se a impressora já estiver imprimindo ou pausada.
- Trabalhos ficam em `facilitador\trabalhos\` (modelo, perfis achatados, G-code, `orca.log`) e o histórico local em `facilitador\trabalhos\historico.csv`. Nada disso vai para o git.

## Arquivos
- `app.py` servidor HTTP (escuta só em 127.0.0.1) e API: `/api/opcoes`, `/api/impressora`, `/api/fatiar`, `/api/enviar`.
- `perfis.py` lê `perfis/*.csv` e achata os perfis do Orca (ver `perfis/orca/README.md`).
- `fatiar.py` chama o CLI e lê tempo/peso do G-code; calcula o custo.
- `moonraker.py` status e upload (`/server/files/upload`, com `print=true` para iniciar).
- `pagina.html` interface.

## Testado
Orca 2.4.2 (Linux, mesmo CLI do Windows): 3 filamentos × 3 qualidades fatiando com os valores certos no G-code; envio contra um Moonraker simulado (chave de API, upload, `print=true`, bloqueio quando ocupado). Falta testar na impressora real e no Windows.
