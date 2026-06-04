# Bogotá con Cepeda — Tu barrio, tu volante

Herramienta hiperlocal de campaña: mapa de Bogotá barrio por barrio (1.177 barrios catastrales, IDECA) que genera volantes personalizados en hoja carta según el perfil de cada barrio (estrato real + uso de suelo), con contenido oficial de la Caja de herramientas y los logros del gobierno.

## Archivos

- `index.html` — el sitio completo (mapa Mapbox + generador de volantes + pin descargable).
- `fichas.json` — las 96 fichas oficiales + mapas de selección (`estrato_fichas`, `uso_fichas`, `relevancia_estrato`) y contrastes. **Editar esto cambia los volantes sin tocar código.**
- `logros.json` — base de logros para "Lo que ya logramos", etiquetados por tema. Solo logros propositivos.
- `barrios.geojson` — capa de barrios con estrato (real, IDECA) y datos electorales **reales por puesto de votación**: **escrutinio definitivo** mesa a mesa de la 1ª vuelta 2026 (Registraduría, validado contra los totales oficiales: Cepeda 1.705.455 = 41,70%, ADLE 1.543.282 = 37,74% de válidos), cruzado con los puestos geolocalizados (IDECA) y asignado a cada barrio catastral. Retroceso (`d`) = Cepeda 2026 real − Petro 2022 real (escrutinio mesa a mesa), por puesto. Campo `src: "2026"` = dato observado. Se regenera con `etl/build_barrios_electoral.py`.
- `etl/build_barrios_electoral.py` — pipeline reproducible que genera los datos electorales de `barrios.geojson` (y la copia embebida `BGEO` de `index.html`). Comando usado: `python3 etl/build_barrios_electoral.py --mmv2026 registraduria/ESCRUTINIOS_MMV_4_MMV_9999.csv --mmv2022-2v etl/data/MMV_NACIONAL_PRESIDENTE_2022_2v.csv`. Acepta el archivo de divulgación de la Registraduría (ancho fijo, `PRE_MMV_*.txt`) o formato MMV CSV; sin `--mmv2026` cae al modo estimación (swing por localidad). Insumos en `etl/data/` (descomprimir el zip del MMV 2022 antes de correr); los archivos de datos crudos están en `.gitignore`. Requiere `shapely` y `numpy`. Acepta tres formatos de archivo 2026: escrutinio (`ESCRUTINIOS_MMV_*.csv`), divulgación de preconteo (`PRE_MMV_*.txt`) o MMV con encabezados — detecta el formato solo.
- Con `--mmv2022-2v etl/data/MMV_NACIONAL_PRESIDENTE_2022_2v.csv` añade por barrio `p2` (% Petro 2ª vuelta 2022, real) y `g22` (puntos que creció Petro entre 1ª y 2ª vuelta 2022, real): el mapa del voto persuadible de cara a la 2ª vuelta del 21 de junio. Rango actual: +5 a +22 pts, mediana +11,5.
- `bogota-localidades.geojson` — contornos de localidades.
- `images/ivnaaida.webp` — foto de campaña usada en header y pin.
- `contenido.json`, `banco-mensajes-programa.md`, `hoja-de-ruta.md`, `HANDOFF-DESARROLLO.md` — documentación y material de origen.

## Cómo actualizar contenido

**Editor visual:** abrir `editor.html` (en GitHub Pages: `…/editor.html`). Lista las 96 propuestas y los 34 logros, con buscador; clic en una tarjeta para editar los textos, y **Guardar** descarga el .json corregido — subirlo a GitHub y queda publicado. Valida en vivo las reglas editoriales (nunca «el programa de» Abelardo; contrastes nombran a De la Espriella al inicio e incluyen la contrapropuesta «Cepeda…»).

Alternativa: editar `fichas.json` o `logros.json` directamente en GitHub (botón ✏️) y hacer commit: el sitio los lee en vivo, así que el cambio queda publicado al instante en GitHub Pages. (`index.html` lleva además una copia embebida de respaldo: regenerarla solo es necesario si se quiere que funcione offline con el contenido nuevo.)

## Datos pendientes

- Demografía DANE por manzana para targeting por identidad (adulto mayor, jóvenes, mujeres, etnia).

## Créditos

por: [grama.co](https://grama.co) | [@gramagrass_](https://x.com/gramagrass_)
Datos: IDECA · Catastro Bogotá, Registraduría Nacional, Mapbox/OSM. Contenido: campaña Iván Cepeda + Aída Quilcué.
