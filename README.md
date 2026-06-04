# Bogotá con Cepeda — Tu barrio, tu volante

Herramienta hiperlocal de campaña: mapa de Bogotá barrio por barrio (1.177 barrios catastrales, IDECA) que genera volantes personalizados en hoja carta según el perfil de cada barrio (estrato real + uso de suelo), con contenido oficial de la Caja de herramientas y los logros del gobierno.

## Archivos

- `index.html` — el sitio completo (mapa Mapbox + generador de volantes + pin descargable).
- `fichas.json` — las 96 fichas oficiales + mapas de selección (`estrato_fichas`, `uso_fichas`, `relevancia_estrato`) y contrastes. **Editar esto cambia los volantes sin tocar código.**
- `logros.json` — base de logros para "Lo que ya logramos", etiquetados por tema. Solo logros propositivos.
- `barrios.geojson` — capa de barrios con estrato (real, IDECA) y datos electorales (ilustrativos hasta el cruce con Registraduría).
- `bogota-localidades.geojson` — contornos de localidades.
- `images/ivnaaida.webp` — foto de campaña usada en header y pin.
- `contenido.json`, `banco-mensajes-programa.md`, `hoja-de-ruta.md`, `HANDOFF-DESARROLLO.md` — documentación y material de origen.

## Cómo actualizar contenido

Editar `fichas.json` o `logros.json` directamente en GitHub (botón ✏️) y hacer commit: el sitio los lee en vivo, así que el cambio queda publicado al instante en GitHub Pages. (`index.html` lleva además una copia embebida de respaldo: regenerarla solo es necesario si se quiere que funcione offline con el contenido nuevo.)

## Datos pendientes

- Cruce electoral real preconteo→barrio (Registraduría). Hoy los números son ilustrativos, calibrados a los agregados reales de Bogotá.
- Demografía DANE por manzana para targeting por identidad (adulto mayor, jóvenes, mujeres, etnia).

## Créditos

por: [grama.co](https://grama.co) | [@gramagrass_](https://instagram.com/gramagrass_)
Datos: IDECA · Catastro Bogotá, Registraduría Nacional, Mapbox/OSM. Contenido: campaña Iván Cepeda + Aída Quilcué.
