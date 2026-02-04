# Mobile (Kivy/KivyMD)

App móvil mínima con login/registro, listado de items y pantalla de puntuación.

## Requisitos (Windows)
- Windows 10/11
- Python 3.10+

## Variables de entorno
- `API_URL` (por defecto `http://127.0.0.1:8000`)

## Ejecutar en local (Windows)
1. Ir a la carpeta mobile:
   ```powershell
   cd mobile
   ```
2. Crear y activar entorno virtual:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Instalar dependencias:
   ```powershell
   pip install -r requirements.txt
   ```
4. Ejecutar app:
   ```powershell
   python main.py
   ```

## Notas
- Modo nombres: mantener pulsado el botón para ver nombres (requiere PIN local).
- Al perder foco o pausar la app se bloquea el modo nombres y exige PIN.
- Si hay errores de red o credenciales inválidas, se muestran en pantalla.
