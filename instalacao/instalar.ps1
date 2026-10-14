# Instalador do kit KyoConecta 3D no PC Windows do primo.
# Uso (PowerShell normal, nao precisa ser administrador; o winget pede permissao quando precisar):
#   irm https://raw.githubusercontent.com/kyoconecta-dot/3D-Portal-KyoConecta/main/instalacao/instalar.ps1 | iex
# ou, com o repo ja baixado:  powershell -ExecutionPolicy Bypass -File instalacao\instalar.ps1
# Pode rodar de novo: o que ja estiver instalado e pulado.

$ErrorActionPreference = 'Stop'
$Repo  = 'https://github.com/kyoconecta-dot/3D-Portal-KyoConecta.git'
$Pasta = Join-Path $env:USERPROFILE 'KyoConecta3D'
$Dest  = Join-Path $Pasta '3D-Portal-KyoConecta'

function Passo($t) { Write-Host "`n== $t ==" -ForegroundColor Cyan }
function Ok($t)    { Write-Host "  OK  $t" -ForegroundColor Green }
function Aviso($t) { Write-Host "  !!  $t" -ForegroundColor Yellow }
function Sim($pergunta) { (Read-Host "$pergunta (s/n)") -match '^[sS]' }

function Atualizar-Path {
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
}

function Instalar-Winget($id, $nome, $comando) {
    if ($comando -and (Get-Command $comando -ErrorAction SilentlyContinue)) { Ok "$nome ja instalado"; return }
    $lista = winget list --id $id -e --accept-source-agreements 2>$null | Out-String
    if ($lista -match [regex]::Escape($id)) { Ok "$nome ja instalado"; return }
    Write-Host "  instalando $nome..."
    winget install --id $id -e --silent --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -ne 0) { Aviso "${nome}: winget retornou $LASTEXITCODE (veja acima)" } else { Ok $nome }
    Atualizar-Path
}

Passo 'Verificando winget'
if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    throw 'winget nao encontrado. Atualize o "Instalador de Aplicativo" pela Microsoft Store e rode de novo.'
}
Ok 'winget'

Passo 'Programas'
Instalar-Winget 'Git.Git'               'Git'         'git'
Instalar-Winget 'Python.Python.3.12'    'Python 3.12' $null
Instalar-Winget 'SoftFever.OrcaSlicer'  'OrcaSlicer'  $null
if (Sim 'Instalar Tailscale (acesso remoto, passo 4)?') { Instalar-Winget 'Tailscale.Tailscale' 'Tailscale' 'tailscale' }

# Python: prefere o lancador "py"; "python" pode ser o atalho falso da Microsoft Store
$PyExe = $null; $PyArgs = @()
if (Get-Command py -ErrorAction SilentlyContinue) { $PyExe = 'py'; $PyArgs = @('-3') }
elseif (Get-Command python -ErrorAction SilentlyContinue) { $PyExe = 'python' }
if (-not $PyExe) { throw 'Python nao apareceu no PATH. Feche e abra o PowerShell e rode o instalador de novo.' }
function Rodar-Py { & $PyExe @PyArgs @args }

Passo 'Claude Code'
if (Get-Command claude -ErrorAction SilentlyContinue) { Ok 'Claude Code ja instalado' }
elseif (Sim 'Instalar o Claude Code?') {
    Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
    Atualizar-Path
    Ok 'Claude Code instalado (faca login rodando "claude" dentro da pasta do repo)'
}

Passo "Repositorio em $Dest"
New-Item -ItemType Directory -Force -Path $Pasta | Out-Null
if (Test-Path (Join-Path $Dest '.git')) {
    git -C $Dest pull --ff-only
    Ok 'repo atualizado'
} else {
    git clone $Repo $Dest
    Ok 'repo baixado'
}

Passo 'Configuracao (OrcaSlicer, impressora, custos)'
Rodar-Py (Join-Path $Dest 'instalacao\configurar.py')

Passo 'Atalho na area de trabalho'
$Atalho = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Impressora 3D.lnk'
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($Atalho)
$s.TargetPath = Join-Path $Dest 'facilitador\iniciar.bat'
$s.WorkingDirectory = $Dest
$Orca = Get-ChildItem "$env:ProgramFiles\OrcaSlicer\orca-slicer.exe" -ErrorAction SilentlyContinue
if ($Orca) { $s.IconLocation = $Orca.FullName }
$s.Save()
Ok $Atalho

Passo 'Atualizacao automatica (git pull a cada hora)'
$Acao = New-ScheduledTaskAction -Execute 'git.exe' -Argument "-C `"$Dest`" pull --ff-only"
$Gatilho = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 1)
$Config = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries
Register-ScheduledTask -TaskName 'KyoConecta3D-atualizar' -Action $Acao -Trigger $Gatilho -Settings $Config -Force | Out-Null
Ok 'tarefa agendada KyoConecta3D-atualizar'

Passo 'Diagnostico'
Rodar-Py (Join-Path $Dest 'instalacao\diagnostico.py')

Write-Host "`nPronto. Use o atalho 'Impressora 3D' na area de trabalho." -ForegroundColor Green
