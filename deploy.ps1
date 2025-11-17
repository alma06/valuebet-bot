# ==============================================================================
# SCRIPT RÁPIDO PARA SUBIR A GITHUB Y DESPLEGAR EN RENDER
# ==============================================================================

Write-Host "`n=== PASO 1: VERIFICAR GIT ===" -ForegroundColor Cyan

# Verificar si Git está instalado
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git no está instalado" -ForegroundColor Red
    Write-Host "Instalar con: winget install --id Git.Git" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Git instalado" -ForegroundColor Green

# ==============================================================================

Write-Host "`n=== PASO 2: CONFIGURAR GIT (si es primera vez) ===" -ForegroundColor Cyan

$userName = git config user.name
$userEmail = git config user.email

if (!$userName) {
    $userName = Read-Host "Tu nombre para Git"
    git config --global user.name "$userName"
}

if (!$userEmail) {
    $userEmail = Read-Host "Tu email para Git"
    git config --global user.email "$userEmail"
}

Write-Host "✅ Usuario: $userName <$userEmail>" -ForegroundColor Green

# ==============================================================================

Write-Host "`n=== PASO 3: INICIALIZAR REPOSITORIO ===" -ForegroundColor Cyan

Set-Location C:\BotValueBets

if (Test-Path .git) {
    Write-Host "⚠️  Repositorio ya existe" -ForegroundColor Yellow
} else {
    git init
    Write-Host "✅ Repositorio inicializado" -ForegroundColor Green
}

# ==============================================================================

Write-Host "`n=== PASO 4: AGREGAR ARCHIVOS ===" -ForegroundColor Cyan

git add .
git status --short

Write-Host "✅ Archivos agregados" -ForegroundColor Green

# ==============================================================================

Write-Host "`n=== PASO 5: HACER COMMIT ===" -ForegroundColor Cyan

git commit -m "Initial commit - Value Bets Bot with Supabase"

Write-Host "✅ Commit realizado" -ForegroundColor Green

# ==============================================================================

Write-Host "`n=== PASO 6: CONECTAR CON GITHUB ===" -ForegroundColor Cyan
Write-Host "`n⚠️  IMPORTANTE:" -ForegroundColor Yellow
Write-Host "1. Ve a https://github.com/new" -ForegroundColor White
Write-Host "2. Crea un repositorio llamado 'valuebet-bot' (o el que quieras)" -ForegroundColor White
Write-Host "3. Márcalo como PRIVADO (recomendado)" -ForegroundColor White
Write-Host "4. NO agregues README, .gitignore ni LICENSE" -ForegroundColor White
Write-Host "5. Click 'Create repository'`n" -ForegroundColor White

$repoUrl = Read-Host "Pega la URL del repositorio (ej: https://github.com/usuario/repo.git)"

if ($repoUrl) {
    git remote add origin $repoUrl
    Write-Host "✅ Repositorio remoto agregado" -ForegroundColor Green
} else {
    Write-Host "❌ URL inválida" -ForegroundColor Red
    exit 1
}

# ==============================================================================

Write-Host "`n=== PASO 7: SUBIR CÓDIGO A GITHUB ===" -ForegroundColor Cyan

git branch -M main
git push -u origin main

Write-Host "✅ Código subido a GitHub!" -ForegroundColor Green

# ==============================================================================

Write-Host "`n=== PASO 8: DESPLEGAR EN RENDER ===" -ForegroundColor Cyan
Write-Host "`nAhora ve a Render:" -ForegroundColor Yellow
Write-Host "1. https://render.com" -ForegroundColor White
Write-Host "2. Sign up with GitHub" -ForegroundColor White
Write-Host "3. New + → Web Service" -ForegroundColor White
Write-Host "4. Conecta tu repo 'valuebet-bot'" -ForegroundColor White
Write-Host "5. Configura:" -ForegroundColor White
Write-Host "   - Build: pip install -r requirements.txt" -ForegroundColor Gray
Write-Host "   - Start: python main.py" -ForegroundColor Gray
Write-Host "   - Plan: Free" -ForegroundColor Gray
Write-Host "6. Agrega variables de entorno (ver DEPLOY_RENDER.md)" -ForegroundColor White
Write-Host "7. Create Web Service" -ForegroundColor White

Write-Host "`n✅ LISTO! Sigue las instrucciones en DEPLOY_RENDER.md`n" -ForegroundColor Green

# ==============================================================================

Write-Host "📝 Archivos importantes creados:" -ForegroundColor Cyan
Write-Host "   - README.md (descripción del proyecto)" -ForegroundColor Gray
Write-Host "   - requirements.txt (dependencias)" -ForegroundColor Gray
Write-Host "   - Procfile (comando de inicio)" -ForegroundColor Gray
Write-Host "   - runtime.txt (versión Python)" -ForegroundColor Gray
Write-Host "   - .gitignore (archivos a ignorar)" -ForegroundColor Gray
Write-Host "   - DEPLOY_RENDER.md (guía completa)" -ForegroundColor Gray

Write-Host "`n🎯 Próximos pasos:" -ForegroundColor Yellow
Write-Host "   1. Verifica que el código esté en GitHub" -ForegroundColor White
Write-Host "   2. Despliega en Render" -ForegroundColor White
Write-Host "   3. Configura UptimeRobot para mantenerlo 24/7" -ForegroundColor White
Write-Host "   4. ¡Disfruta tu bot corriendo en la nube!`n" -ForegroundColor White
