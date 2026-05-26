@echo off
title MV Energia Solar
cd /d "%~dp0"

echo ============================================
echo       MV Energia Solar - Iniciando...
echo ============================================
echo.

REM Verifica se Python esta instalado
python --version > nul 2>&1
if errorlevel 1 (
    echo ERRO: Python nao encontrado.
    echo Instale o Python 3.11 ou superior em https://www.python.org
    echo Marque a opcao "Add Python to PATH" durante a instalacao.
    pause
    exit /b 1
)

REM Cria o ambiente virtual se nao existir
if not exist ".venv\Scripts\activate.bat" (
    echo [1/5] Configurando ambiente pela primeira vez...
    python -m venv .venv
)

REM Ativa o ambiente virtual
call .venv\Scripts\activate.bat

REM Instala dependencias (silencioso apos a primeira vez)
echo [2/5] Verificando dependencias...
pip install -r requirements.txt -q --disable-pip-version-check

REM Aplica migracoes de banco pendentes
echo [3/5] Atualizando banco de dados...
alembic upgrade head

REM Backup automatico do banco
echo [4/5] Criando backup...
python backup.py

REM Inicia a API em segundo plano (apenas localhost - clientes nao precisam acessar a API diretamente)
echo [5/5] Iniciando sistema...
start "SolarAPI" /min cmd /k "cd /d "%~dp0" && call .venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port 8000"

REM Aguarda a API subir
timeout /t 4 /nobreak > nul

REM Descobre o IP local da maquina
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set _IP=%%a
    goto :ip_ok
)
:ip_ok
set LOCAL_IP=%_IP: =%

echo.
echo ============================================
echo   SISTEMA INICIADO COM SUCESSO
echo ============================================
echo.
echo   Nesta maquina:    http://localhost:8501
echo   Outras maquinas:  http://%LOCAL_IP%:8501
echo.
echo   Compartilhe o endereco acima com a equipe.
echo   Eles abrem no navegador - sem instalar nada.
echo ============================================
echo.

REM Libera o firewall automaticamente para a porta 8501 (Streamlit)
netsh advfirewall firewall show rule name="MV Solar Streamlit" > nul 2>&1
if errorlevel 1 (
    echo Liberando porta 8501 no firewall do Windows...
    netsh advfirewall firewall add rule name="MV Solar Streamlit" dir=in action=allow protocol=TCP localport=8501 > nul 2>&1
)

REM Inicia o Streamlit ouvindo em todas as interfaces (0.0.0.0)
streamlit run streamlit_app\app.py ^
    --server.port 8501 ^
    --server.address 0.0.0.0 ^
    --server.headless true ^
    --browser.gatherUsageStats false

REM Ao fechar o Streamlit, encerra a API tambem
echo.
echo Encerrando MV Energia Solar...
taskkill /fi "WINDOWTITLE eq SolarAPI" /f > nul 2>&1
echo Encerrado. Pode fechar esta janela.
timeout /t 2 /nobreak > nul
