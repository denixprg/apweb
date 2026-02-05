# Web (PWA)

Frontend web sencillo (PWA) sin dependencias. Se conecta al backend en Render.

## Configuracion
- Backend URL actual: https://apweb-zhfm.onrender.com
- Para cambiarlo, edita `web/app.js` y busca `API_BASE`.

## Ejecutar en local
- Abrir `web/index.html` con un servidor estatico (por ejemplo, `python -m http.server`).

## Despliegue en Render (Static Site)
1. Crear un nuevo servicio "Static Site" en Render.
2. Conectar el repo y seleccionar la carpeta `web` como Root Directory.
3. Build Command: (vacio)
4. Publish Directory: `.` (root de /web)
5. Guardar y desplegar.

## Notas
- La app guarda el token en localStorage por perfil.
- Para limpiar sesion, refresca la pagina y elige perfil de nuevo.
