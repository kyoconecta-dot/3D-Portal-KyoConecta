# Kit de instalação — PC do primo (Windows)

Objetivo: no fim, a área de trabalho tem o atalho **Impressora 3D**. Ele abre a página onde se arrasta o STL, vê tempo, peso e custo, e manda imprimir. Leva uns 30 minutos.

## 0. Antes de sair de casa
- [ ] Impressora com **root** e **Moonraker + Fluidd** já funcionando (hoje: Moonraker na porta 7125, câmera na 8080). Se for reinstalar: tela da impressora → Configurações → root; depois `ssh root@<ip>` e Creality Helper Script (`/usr/data/helper-script`) → instalar Moonraker + Nginx + Fluidd.
- [ ] Anote a chave de API do Moonraker, se já usa `force_logins` (via SSH: `curl -s http://127.0.0.1:7125/access/api_key`).
- [ ] Login do GitHub não é necessário: o repo é público. Se ficar privado, leve um token de leitura (veja o item 6).

## 1. Impressora na rede do primo
1. Na tela da impressora: Configurações → Rede → Wi-Fi do primo.
2. No roteador do primo: **reservar o IP** da impressora (DHCP fixo pelo MAC). Assim o endereço não muda depois de religar.
3. No PC do primo, confira no navegador: `http://<ip-da-impressora>:4408` (Fluidd) deve abrir.

## 2. Rodar o instalador
Abra o **PowerShell** (menu Iniciar → "PowerShell") e cole:

```powershell
irm https://raw.githubusercontent.com/kyoconecta-dot/3D-Portal-KyoConecta/main/instalacao/instalar.ps1 | iex
```

Ele faz, em ordem (pode rodar de novo, o que já existe é pulado):
1. Instala pelo winget: Git, Python 3.12, OrcaSlicer e, se você quiser, Tailscale.
2. Pergunta se instala o **Claude Code**.
3. Baixa o repo em `%USERPROFILE%\KyoConecta3D\3D-Portal-KyoConecta`.
4. Roda o **configurador**: acha o OrcaSlicer, **procura a impressora na rede sozinho**, testa a conexão, pede a chave de API (Enter se ainda não tem) e os custos (R$/kg, R$/kWh, watts).
5. Cria o atalho **Impressora 3D** na área de trabalho.
6. Agenda `git pull` a cada hora (tarefa `KyoConecta3D-atualizar`): perfis e correções chegam sozinhos.
7. Roda o **diagnóstico**: fatia um cubo em todas as combinações e consulta a impressora. Precisa terminar em `TUDO CERTO`.

Se o winget pedir permissão de administrador, aceite. Se o Python "não aparecer", feche e abra o PowerShell e cole o comando de novo.

## 3. Abrir o OrcaSlicer uma vez
Abra o OrcaSlicer pelo menu Iniciar, escolha **Creality Ender-3 V3 KE 0.4** no assistente e feche. O facilitador não depende disso, mas o primo pode precisar do Orca para olhar uma peça.

## 4. Teste real (com você presente)
1. Clique duas vezes no atalho **Impressora 3D**. A página abre em `http://localhost:8000`.
2. O topo deve mostrar "Impressora: parada · bico X °C · mesa Y °C".
3. Arraste uma peça pequena e conhecida, use PETG normal → **Calcular** → confira tempo e peso contra o seu Orca.
4. **Enviar e imprimir** → acompanhe pelo Fluidd ou pela câmera.
5. Repita com suporte ligado.

## 5. Claude Code no PC do primo (opcional)
- Abra o PowerShell na pasta do repo: `cd $env:USERPROFILE\KyoConecta3D\3D-Portal-KyoConecta` e rode `claude`. Faça login com a **sua** conta (custo zero: usa a sua assinatura).
- O `CLAUDE.md` do repo já explica para o Claude como diagnosticar (seção "No PC do primo").
- Para você operar de longe pelo Claude: `claude remote-control` nesse PC.

## 6. Se o repo virar privado
Crie no GitHub um *fine-grained token* só leitura (Contents: Read) só para este repo. No primeiro `git pull`, o Git pede usuário e senha: use o seu usuário e cole o token como senha. O Windows guarda o token.

## Problemas comuns
| Sintoma | O que fazer |
|---|---|
| Página diz "impressora inacessível" | `python instalacao\rede.py` acha o IP novo → rode `python instalacao\configurar.py` |
| "recusou a chave de API" | Pegue a chave de novo (item 0) → `configurar.py` |
| "OrcaSlicer não encontrado" | `configurar.py` e informe o caminho do `orca-slicer.exe` |
| Fatiar falha | Veja `facilitador\trabalhos\<trabalho>\orca.log`; rode `python instalacao\diagnostico.py` |
| Qualquer outra coisa | `python instalacao\diagnostico.py` e mande o resultado para o dono (foto da tela serve) |

Comandos (sempre dentro da pasta do repo): `python instalacao\diagnostico.py`, `python instalacao\configurar.py`, `python instalacao\rede.py`.
