param(
    [Parameter(Mandatory=$true)]
    [string]$ServerIp,
    [string]$codePath = "/z/docker/jay_words",
    [string]$ServerPath = "/vol1/1000/download/docker/jay_words"
)

$SshUser = if ($env:SSH_USER) { $env:SSH_USER } else { "admin" }
$SshPort = if ($env:SSH_PORT) { $env:SSH_PORT } else { 22 }
$DstDir = "Z:\docker\jay_words"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SrcDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== Deploy jay-words to ${ServerIp}:${codePath} ==="

# 1. backup old version (mapped dir = server dir)
if (Test-Path $DstDir) {
    Write-Host "Backup old version to ${DstDir}_backup_$Timestamp ..."
    Rename-Item -Path $DstDir -NewName "jay_words_backup_$Timestamp"
}

# 2. copy code to mapped dir
Write-Host "Copy code to $DstDir ..."
if (-not (Test-Path "Z:\docker")) {
    New-Item -ItemType Directory -Path "Z:\docker" -Force | Out-Null
}
Copy-Item -Path $SrcDir -Destination "Z:\docker" -Recurse -Force

# cleanup unneeded files
foreach ($p in @("$DstDir\.git", "$DstDir\frontend\node_modules")) {
    if (Test-Path $p) { Remove-Item -Path $p -Recurse -Force -ErrorAction SilentlyContinue }
}
Get-ChildItem -Path $DstDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $DstDir -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue

# 3. SSH to server to run docker commands
Write-Host "Connect to server ${ServerIp} ..."

# build remote command array
$remoteLines = @(
    "cd $ServerPath",
    "echo '=== Current containers ==='",
    "docker ps --filter 'name=jay-words' 2>/dev/null || echo '  (none)'",
    "if [ ! -f .env ]; then",
    "  echo 'DB_HOST=127.0.0.1' > .env",
    "  echo 'DB_PORT=3306' >> .env",
    "  echo 'DB_USER=jay' >> .env",
    "  echo 'DB_PASSWORD=your_password_here' >> .env",
    "  echo 'DB_NAME=jay_words' >> .env",
    "  echo 'Please edit ${ServerPath}/.env, then re-run deploy'",
    "  exit 1",
    "fi",
    "echo '=== Stopping old containers ==='",
    "docker compose down --remove-orphans; exit_code=`$?",
    "echo \"  docker compose down exit code: `$exit_code\"",
    "echo '=== Building and starting ==='",
    "docker compose up -d --build"
)
$remoteCmd = $remoteLines -join "`n"

$remoteCmd | ssh -p $SshPort "${SshUser}@${ServerIp}" "bash -s"

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== Deploy complete ==="
    Write-Host "Visit http://${ServerIp}:18001"
} else {
    Write-Host "Deploy failed, check server connection and config"
}
