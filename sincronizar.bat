@echo off
echo Sincronizando repositorio com o GitHub...
git pull origin main --rebase
git add -A
git commit -m "Atualizacao automatica de dados da plataforma"
git push origin main
pause