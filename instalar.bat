@echo off
echo Creando entorno virtual...
python -m venv .venv

echo Instalando dependencias...
.venv\Scripts\pip install -r requirements.txt

echo.
echo Listo. Para activar el entorno ejecuta:
echo   .venv\Scripts\activate
pause
