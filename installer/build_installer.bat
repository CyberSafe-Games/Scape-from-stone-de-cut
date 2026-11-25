@echo off
setlocal EnableExtensions

set "ROOT=%~dp0.."
for %%I in ("%ROOT%") do set "ROOT=%%~fI"
set "APP_VERSION=%~1"
if not defined APP_VERSION (
    for /f "usebackq delims=" %%V in ("%ROOT%\VERSION") do if not defined APP_VERSION set "APP_VERSION=%%V"
)
if not defined APP_VERSION (
    echo ERRO: nao foi possivel ler a versao do arquivo VERSION.
    exit /b 1
)
echo %APP_VERSION%| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if errorlevel 1 (
    echo ERRO: versao invalida "%APP_VERSION%". Use o formato X.Y.Z.
    exit /b 1
)

set "VENV=%ROOT%\.venv-build"
set "BUILD_PYTHON=%VENV%\Scripts\python.exe"
if exist "%BUILD_PYTHON%" goto build_environment_ready

set "PYTHON_CMD="
where py >nul 2>nul
if not errorlevel 1 (
    py -3.12 -c "import sys; raise SystemExit(0 if (3,12) <= sys.version_info[:2] < (3,14) and sys.maxsize > 2**32 else 1)" >nul 2>nul
    if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)
if not defined PYTHON_CMD (
    where python >nul 2>nul
    if not errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if (3,12) <= sys.version_info[:2] < (3,14) and sys.maxsize > 2**32 else 1)" >nul 2>nul
        if not errorlevel 1 set "PYTHON_CMD=python"
    )
)
if not defined PYTHON_CMD (
    echo ERRO: Python 3.12/3.13 de 64 bits nao encontrado. Instale Python 3.12 x64 e tente novamente.
    exit /b 1
)

set "VENV=%ROOT%\.venv-build"
if not exist "%VENV%\Scripts\python.exe" (
    %PYTHON_CMD% -m venv "%VENV%"
    if errorlevel 1 exit /b 1
)
set "BUILD_PYTHON=%VENV%\Scripts\python.exe"
:build_environment_ready
"%BUILD_PYTHON%" -c "import sys; print('Python usado no build: ' + sys.version.split()[0] + ' (' + str(sys.maxsize.bit_length()+1) + ' bits)'); raise SystemExit(0 if (3,12) <= sys.version_info[:2] < (3,14) and sys.maxsize > 2**32 else 1)"
if errorlevel 1 (
    echo ERRO: o ambiente de build precisa de Python 3.12 ou 3.13, de 64 bits, para PyInstaller 6.11.1.
    exit /b 1
)

echo Instalando dependencias do jogo e de build...
"%BUILD_PYTHON%" -m pip install -r "%ROOT%\requirements.txt" -r "%ROOT%\requirements-build.txt"
if errorlevel 1 exit /b 1

echo Gerando a pasta dist\ScapeFromStoneDeCut...
pushd "%ROOT%"
"%BUILD_PYTHON%" -m PyInstaller --noconfirm --clean scape_from_stone.spec
if errorlevel 1 (
    popd
    exit /b 1
)
popd
if not exist "%ROOT%\dist\ScapeFromStoneDeCut\ScapeFromStoneDeCut.exe" (
    echo ERRO: o executavel nao foi encontrado em dist\ScapeFromStoneDeCut.
    exit /b 1
)

set "ISCC="
for %%I in (ISCC.exe) do set "ISCC=%%~$PATH:I"
if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "%ProgramData%\chocolatey\bin\ISCC.exe" set "ISCC=%ProgramData%\chocolatey\bin\ISCC.exe"
if not defined ISCC (
    echo ERRO: Inno Setup nao encontrado. Instale-o em https://jrsoftware.org/isdl.php e execute este script novamente.
    exit /b 1
)

echo Compilando instalador versao %APP_VERSION%...
"%ISCC%" /DMyAppVersion=%APP_VERSION% "%ROOT%\installer\scape_from_stone.iss"
if errorlevel 1 exit /b 1

echo.
echo Instalador gerado: %ROOT%\ScapeFromStoneDeCut-Setup-%APP_VERSION%.exe
endlocal
