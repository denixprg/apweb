# Backend (FastAPI)

API REST con autenticación por tokens, roles (admin), items, ratings y stats.

## Requisitos (Windows)
- Windows 10/11
- Python 3.10+
- Postgres para producción (en local puedes usar SQLite por defecto)

## Variables de entorno
- `DATABASE_URL`
  - Local (SQLite): `sqlite:///./app.db`
  - Postgres: `postgresql://USER:PASSWORD@HOST:PORT/DBNAME`
- `SECRET_KEY` (obligatoria en producción)
- `CORS_ORIGINS` (separadas por coma, por ejemplo `http://localhost`)
- Las credenciales bootstrap se generan automáticamente en startup (ver abajo).

## Ejecutar en local (Windows)
1. Ir a la carpeta del backend:
   ```powershell
   cd backend
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
4. Migraciones:
   ```powershell
   $env:DATABASE_URL="sqlite:///./app.db"
   alembic -c alembic.ini upgrade head
   ```
5. Bootstrap de perfiles iniciales (automático en startup):
   - p1 / p1pass
   - p2 / p2pass
   - p3 / p3pass (admin)
   - p4 / p4pass
   Cambia estas credenciales en producción.
6. Arrancar API:
   ```powershell
   $env:SECRET_KEY="dev-secret-change-me"
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

## Dev con SQLite
```powershell
$env:DATABASE_URL="sqlite:///./test.db"
$env:SECRET_KEY="dev-secret"
alembic upgrade head
uvicorn app.main:app --reload
```

## Endpoints principales
- `POST /auth/register` (invite_code, username, password)
- `POST /auth/login` (username, password)
- `GET /me`
- `GET /items`
- `POST /items`
- `DELETE /items/{id}` (admin)
- `PATCH /items/{id}` (admin)
- `POST /items/{id}/ratings`
- `GET /items/summary?range=7|30|all`
- `GET /stats/ranking?range=7|30|all`
- `GET /items/{id}/stats?range=7|30|all`
- `POST /admin/invites` (admin)
- `GET /admin/users` (admin)
- `POST /admin/users/{id}/block` (admin)
- `POST /admin/users/{id}/unblock` (admin)

## Notas de seguridad
- Passwords con PBKDF2 (passlib).
- Tokens JWT con expiración.
- Rate limit básico en endpoints de auth (memoria en proceso).
- No se imprimen datos sensibles en logs.

## Probar borrado de items (manual)
1. Iniciar sesión en la app con perfil admin (p3).
2. Ir a Items y tocar el icono de basura.
3. Confirmar borrado y verificar que el item desaparece.
