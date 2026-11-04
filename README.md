# Capi Aventuras 🦫

Pipeline gratuito para crear borradores semanales de videos verticales 1080×1920 para niños brasileños de 3–6 años que aprenden español con Capi. **Nunca publica en YouTube ni TikTok**: deja un Release para revisión y subida manual.

## Uso desde Android
Abre **Releases**, entra al último `capi-epNNN` y descarga el MP4. Revisa voz, palabras y subtítulos; luego súbelo manualmente a Shorts/TikTok. También puedes ejecutar el flujo desde **Actions → Crear video semanal → Run workflow**.

## Añadir episodios
Crea `episodes/queue/ep009.json` siguiendo cualquiera de los ocho ejemplos. Cada episodio tiene cuatro palabras; cada objeto de `escenas` incluye `pose`, `texto_pt` y una palabra con `es` y `pt`. El viernes a las 15:00 UTC se procesa el siguiente episodio. Con dos o menos pendientes se abre una incidencia.

Se generan seis poses de Capi, seis fondos y `preview/capi_poses.png`. Voces: edge-tts (pt-BR-FranciscaNeural y es-MX-DaliaNeural) con respaldo Piper cuando el modelo configurado esté disponible. No requiere claves, pagos ni secretos personales. Actions usa su token temporal integrado.

La carpeta `assets/musica` queda vacía: solo añadir música original o con licencia comercial comprobable. Código e ilustraciones son originales; no se usan personajes, marcas ni canciones protegidas.
