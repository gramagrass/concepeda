# Handoff de desarrollo — Volantes hiperlocales por barrio (Cepeda 2026, 2ª vuelta)

> Documento para que otro agente/dev retome y construya el producto. Autocontenido: incluye objetivo, arquitectura, fuentes de datos con URLs, pipeline ETL, esquemas de archivos, especificación del frontend, generación de PDF, reglas editoriales y criterios de aceptación.

## 0. Contexto y urgencia
Campaña de Iván Cepeda para la **segunda vuelta presidencial 2026** contra Abelardo de la Espriella (ultraderecha, ganó la 1ª vuelta). Meta: ~1.000.000 de votos adicionales en **menos de 3 semanas**. El producto es una herramienta de campaña hiperlocal: la gente entra a una página, ve su barrio en el mapa, y descarga un volante personalizado para imprimir y repartir / usar como guion al tocar puertas.

Implicación de tiempo: priorizar lo que despacha volantes esta semana. No perseguir perfección de datos en las 7 ciudades antes de lanzar Bogotá.

## 1. Objetivo del producto (esta entrega)
**Una sola página** que contiene:
1. **Arriba: mapa de Bogotá** (coroplético por barrio). Al pasar el mouse (hover) sobre un barrio, un tooltip muestra: nombre del barrio, UPZ, % Cepeda 2026, retroceso vs. Petro 2022 (delta en puntos), uso de suelo predominante.
2. **Al hacer clic en un barrio: se genera el volante debajo del mapa**, personalizado para ese barrio (nombre + 3 ejes según uso de suelo + logro del gobierno + contraste con De la Espriella), con botón de descarga en PDF.

Es la evolución del mockup actual (`sitio-mockup.html`), que ya tiene buscador por nombre + render del volante; falta reemplazar/añadir el **mapa** como entrada principal y conectar datos reales.

## 2. ¿Es viable? Sí
- Mapa coroplético con hover + clic: estándar con D3-geo o Leaflet/MapLibre, 100% cliente.
- Polígonos de barrio de Bogotá: datos abiertos (IDECA). 
- Puestos de votación **ya geolocalizados** (IDECA) → el cruce electoral→barrio no requiere geocodificar direcciones.
- Generación del volante: ya implementada en el mockup; se reusa la función de render.
- Todo puede servirse como **sitio estático** (sin backend), o con un build-step para pre-generar PDFs.

## 3. Estado actual — archivos que ya existen (en esta carpeta)
- `sitio-mockup.html` — mockup funcional: buscador de barrio + toggles (contraste / guion largo) + render del volante grande + descarga (simulada). Lee `contenido.json` vía fetch con copia de respaldo embebida. **Reusar su CSS y su función `render()`.**
- `contenido.json` — **fuente única de contenido** (mensajes Cepeda, logros del gobierno, contrastes con De la Espriella, mapeo uso de suelo→ejes). El sitio lo lee en tiempo real. Ver esquema en §7.
- `banco-mensajes-programa.md` — destilación de los ejes del programa de Cepeda (origen del contenido).
- `hoja-de-ruta.md` — plan general del proyecto y verificación de datos.
- Datos de origen (subidos por el usuario, fuera de esta carpeta): `programa-gobierno-2026-2030.pdf` (Cepeda, 433 pp) y `PROPUESTAS-DEL-TIGRE.pdf` (De la Espriella, 13 propuestas). Son la fuente de los textos; ya están destilados en `contenido.json`.

Faltan (a construir): `barrios.geojson` (datos reales), el mapa, el pipeline ETL, y la generación de PDF.

## 4. Fuentes de datos (con URLs)

### 4.1 Resultados electorales por puesto (capa con trabajo)
No hay desglose oficial por barrio; el nivel más fino es **puesto de votación / mesa**. Descargar y luego cruzar a barrio.
- Observatorio Electoral – Registraduría (archivos planos CSV por depto/municipio/zona/puesto/mesa/candidato): https://observatorio.registraduria.gov.co/
- Resultados 2026 (presidencia): https://wapp.registraduria.gov.co/electoral/2026/presidente-de-la-republica/index.html y https://www.resultados.registraduria.gov.co/
- Histórico de resultados: https://estadisticaselectorales.registraduria.gov.co/
- CEDAE / Datasketch (CSV ya limpios por puesto, 1ª y 2ª vuelta): https://cedae.datasketch.co/datos-democracia/resultados-electorales/explora-los-datos/
- MOE (base definitiva del escrutinio a nivel de puesto, 2022): https://moe.org.co/

Qué bajar: presidencial **1ª vuelta 2026** (los ~41% de Cepeda; este es el dato base del retroceso) y presidencial **1ª vuelta 2022** (Petro), filtrando Bogotá D.C. Para el contraste de "retroceso" se compara el % de la izquierda en ambos comicios al mismo nivel de puesto. (Decidir con el usuario si se compara 1ª vuelta 2026 vs 1ª vuelta 2022, que es lo que cita el tweet de origen.)

### 4.2 Geografía y uso de suelo de Bogotá (capa fácil)
- IDECA – Infraestructura de Datos Espaciales de Bogotá: https://www.ideca.gov.co/ y portal: https://datosabiertos.bogota.gov.co/
- **Puesto de Votación. Bogotá D.C.** (PUNTOS ya geolocalizados; SHP/GeoJSON/GPKG/KMZ; act. 2025-11-11) — grupo: https://datosabiertos.bogota.gov.co/group/resultados-electorales
- Polígonos de **barrio / sector catastral** y **UPZ**: en IDECA / Datos Abiertos Bogotá (datasets "Sector Catastral", "UPZ", "Manzana"): https://datosabiertos.bogota.gov.co/dataset/manzana
- **Clasificación / uso de suelo (POT)**: https://datosabiertos.bogota.gov.co/dataset/clasificacion-del-suelo-bogota-d-c (para uso funcional residencial/comercial/dotacional/industrial, usar las capas de tratamientos/usos del POT y/o la vocación de cada UPZ).

### 4.3 Respaldo nacional (para escalar a otras ciudades)
- DANE – Geoportal y Marco Geoestadístico Nacional (MGN): manzana, sector urbano y **estrato** para todo el país: https://geoportal.dane.gov.co/ · MGN municipio: https://www.icde.gov.co/datos-y-recursos/marco-geoestadistico-nacional-municipio
- GeoMedellín (OpenData): https://www.medellin.gov.co/geomedellin · IDESC Cali: https://idesc.cali.gov.co/

## 5. Pipeline de datos (ETL) — produce `barrios.geojson`
Recomendado: Python con `geopandas` + `pandas`. Pasos:
1. **Descargar** resultados por puesto: 2026-1ª y 2022-1ª, Bogotá (CSV de Observatorio o CEDAE).
2. **Descargar** capa de puestos geolocalizados (IDECA) y polígonos de barrio + UPZ + uso de suelo.
3. **Unir** resultados ↔ puntos de puesto por **código de puesto** (fallback: nombre+dirección normalizados). Empalmar 2022↔2026 por código de puesto; los puestos que cambiaron se reconcilian manualmente o por cercanía.
4. **Point-in-polygon**: asignar cada puesto a su **UPZ** (unidad de agregación robusta) y a su **barrio** (etiqueta).
5. **Agregar** por UPZ: total válidos, votos Cepeda 2026, votos Petro 2022 → `pct_cepeda26`, `pct_petro22`, `delta = pct_cepeda26 - pct_petro22`.
6. **Uso de suelo predominante** por UPZ/barrio (desde POT): clasificar en {Residencial, Comercial, Dotacional, Industrial, Mixto}.
7. **Construir `barrios.geojson`**: un feature por barrio (polígono), heredando del UPZ las métricas electorales y de uso de suelo (hasta tener dato barrial directo). Simplificar geometría (p.ej. `mapshaper -simplify 8%`) y/o convertir a **TopoJSON** para peso liviano.
8. (Opcional) exportar `master.csv` para revisión.

Nota metodológica (incluir como descargo en el sitio): el resultado de un puesto refleja **dónde vota** la gente, no exactamente dónde vive ni el uso de suelo de su vivienda. Es un proxy válido para segmentar, no inferencia individual.

## 6. Esquema de `barrios.geojson` (properties por feature)
```json
{
  "type": "Feature",
  "geometry": { "type": "Polygon", "coordinates": [ ... ] },
  "properties": {
    "barrio": "Quiroga",
    "upz": "Quiroga",
    "localidad": "Rafael Uribe Uribe",
    "uso_suelo": "Residencial",          // uno de: Residencial|Comercial|Dotacional|Industrial|Mixto
    "pct_cepeda26": 44.0,
    "pct_petro22": 52.0,
    "delta": -8.0,                        // negativo = retroceso
    "votos_validos_26": 12450             // opcional, para ponderar prioridad
  }
}
```

## 7. `contenido.json` — esquema y reglas de render
Estructura (ya poblada):
- `_meta`: descripción, tono, versión, leyenda de usos.
- `logros_gobierno[]`: `{id, titular, guion, dato, fuente_dato}` — logros para "continuar con Cepeda" (salario mínimo, salario vital, Colombia Mayor).
- `temas[]`: por tema:
  - `id`, `titulo`, `icono` (Tabler), `uso_suelo[]` (en qué usos aplica).
  - `cepeda`: `{titular, guion, puntos[]}` — `guion` es el texto largo para volante/guion puerta a puerta.
  - `gobierno`: id de un logro a enganchar (o `null`).
  - `contraste`: `{abelardo_dice, en_una_linea, fuente}`.
    - `abelardo_dice` = descripción **neutral y auditable** de la posición de De la Espriella (NO se muestra en el volante; es para revisión/fact-check).
    - `en_una_linea` = línea **confrontativa** que SÍ se muestra en el volante.
- `uso_suelo_map`: `{ uso → [ids de temas ]}` — define qué ejes entran según el uso de suelo del barrio.

**Reglas de render del volante (replicar exactamente):**
1. Tomar los primeros 3 temas de `uso_suelo_map[uso_suelo_del_barrio]`.
2. Por cada tema: mostrar `cepeda.titular` + `cepeda.guion` (o primera frase si "guion corto").
3. Si algún tema tiene `gobierno`, mostrar una caja "Lo que ya logramos" con ese logro (titular + dato).
4. Si el contraste está activo: mostrar `contraste.en_una_linea`. **Empieza directo con "De la Espriella…"** (sin etiqueta "vs De la Espriella"). **La contrapropuesta de Cepeda va en negrita** (regex actual: envolver en `<strong>` desde `(?:Para )?Cepeda[ ,].*$`, color azul tinta).
5. **Nunca** escribir "en el programa de" / "el programa de" / "su programa de" Abelardo o De la Espriella. Ya está saneado; mantener la regla al editar contenido.
6. Encabezado del volante: `CEPEDA · El poder de la verdad`. Cierre: `En segunda vuelta, vota Cepeda.`

## 8. Frontend — la página única
**Stack recomendado:** vanilla JS + **D3-geo** (coroplético sin tiles, liviano y offline) cargando `barrios.topojson`. Alternativa válida: **MapLibre GL** o **Leaflet** + GeoJSON si se quiere mapa base/zoom fluido. Para ~1.200 barrios, simplificar geometría y usar TopoJSON.

Layout (reusar tokens y `render()` del mockup):
- Sección mapa (arriba): SVG D3 con proyección ajustada al bounding box de Bogotá. Color de cada barrio por `delta` (escala divergente: rojo = retroceso fuerte → neutro → verde = se mantuvo/creció). Leyenda.
- **Hover**: tooltip flotante con `barrio`, `upz`, `pct_cepeda26 %`, `delta` (etiquetado "retroceso de X pts vs Petro 2022"), `uso_suelo`.
- **Clic**: setear barrio actual y llamar `render(barrio)` que pinta el volante en la sección de abajo (misma función del mockup, alimentada por `contenido.json` + properties del barrio).
- Conservar buscador por nombre como alternativa al mapa (accesibilidad / móvil).
- Toggles existentes: contraste on/off, guion largo/corto.

Color del coroplético (divergente, alineado a la paleta de campaña): usar rampa roja→crema→verde sobre `delta` con dominio aprox. [-16, +2].

## 9. Generación de PDF
Dos opciones (recomendado combinar):
- **Build-time (recomendado para fidelidad de impresión):** script Node con **Puppeteer** que renderiza el volante de cada barrio (HTML→PDF, media carta 139.7×215.9 mm, márgenes 0) y guarda `pdf/{barrio}.pdf`. El botón "Descargar" sirve el estático. Reproducible: re-correr cuando cambie `contenido.json` o los datos.
- **Cliente (fallback / inmediato):** `window.print()` con `@media print` (ya hay base) o `html2pdf.js`. Menos fiel pero sin build.

Definir tamaño final con el usuario: el volante "se imprime grande" — confirmar si media carta, carta completa o tabloide. El CSS actual usa media carta; escalar tipografía si se va a A3/tabloide.

## 10. Estilo / tokens
- Colores: `--tinta:#0f2a43` (azul), `--acento:#e4572e` (coral), `--acento2:#f3a712` (ámbar), `--bg:#f4f1ea`, texto `#1c2733`.
- Tipografía actual: Helvetica/Arial; sustituir por la tipografía oficial de campaña cuando esté.
- Placeholders a reemplazar en el volante: `[Logo campaña]` y `[Línea legal · tarjetón]` (número del tarjetón, aviso legal de propaganda electoral).
- Iconos: Tabler (outline) — los ids ya están en `contenido.json` (`icono`).

## 11. Reglas editoriales y éticas (obligatorias)
- Los contrastes deben permanecer **anclados a las propuestas reales** de cada candidato (`fuente` y `abelardo_dice` permiten auditarlo). No inventar datos ni cifras.
- **Nunca** decir "en el programa de" Abelardo/De la Espriella (regla del usuario).
- Mostrar el descargo del proxy (voto en puesto ≠ residencia) y, mientras los datos sean placeholder, el banner "datos ilustrativos".
- Cumplir normas de propaganda electoral (incluir tarjetón / responsable / no usar recursos prohibidos).

## 12. Escalamiento nacional (después de Bogotá)
El **contenido es nacional** (se reusa tal cual). Solo cambia la capa geográfica:
- Nivel completo (barrio + uso de suelo): **Bogotá, Medellín (GeoMedellín), Cali (IDESC)**.
- Nivel bueno: **Barranquilla, Bucaramanga** (IDEs metropolitanas).
- Con respaldo DANE (manzana + **estrato** + comuna): **Cúcuta, Tunja, Yopal**.
La capa electoral de la Registraduría es nacional; el **estrato del DANE** es un proxy de segmentación universal donde falte el uso de suelo municipal. Recomendación dado el plazo: lanzar Bogotá/Medellín/Cali con segmentación fina; el resto por estrato/comuna.

## 13. Decisiones abiertas (confirmar con el usuario David)
- ¿Comparar 1ª vuelta 2026 vs 1ª vuelta 2022 (lo del tweet) o vs 2ª vuelta 2022? Define el "retroceso".
- Resolución del mapa: barrio catastral (~1.200) vs UPZ (~112). Acordado: **agregar en UPZ, etiquetar/colorear barrio**.
- Tamaño físico del volante (media carta / carta / tabloide).
- ¿Mostrar al votante el dato de "retroceso", o dejarlo solo como herramienta interna y que el volante sea puramente propositivo?
- Tono del contraste (ya quedó confrontativo; validar caso por caso).

## 14. Criterios de aceptación (definition of done)
- [ ] `barrios.geojson` real generado por el ETL, validado (suma de votos cuadra con totales oficiales de Bogotá).
- [ ] Página única: mapa arriba con hover (tooltip con los 4 datos) + clic que genera el volante abajo.
- [ ] Volante alimentado por `contenido.json` (cambiar el JSON cambia el volante sin tocar código).
- [ ] Reglas de render respetadas (3 ejes por uso, logro, contraste sin etiqueta "vs", negrita en respuesta de Cepeda, sin "en el programa de").
- [ ] Descarga de PDF imprimible por barrio.
- [ ] Banner de "datos ilustrativos" retirado solo cuando los datos sean reales.
- [ ] Responsive (móvil: buscador como entrada principal si el mapa no cabe).

## 15. Resumen de recursos (enlaces)
Electoral: Observatorio Registraduría https://observatorio.registraduria.gov.co/ · Resultados 2026 https://wapp.registraduria.gov.co/electoral/2026/presidente-de-la-republica/index.html · Histórico https://estadisticaselectorales.registraduria.gov.co/ · CEDAE https://cedae.datasketch.co/datos-democracia/resultados-electorales/explora-los-datos/ · MOE https://moe.org.co/
Geo Bogotá: IDECA https://www.ideca.gov.co/ · Datos Abiertos https://datosabiertos.bogota.gov.co/ · Puestos/resultados (grupo) https://datosabiertos.bogota.gov.co/group/resultados-electorales · Manzana https://datosabiertos.bogota.gov.co/dataset/manzana · Clasificación del suelo POT https://datosabiertos.bogota.gov.co/dataset/clasificacion-del-suelo-bogota-d-c
Nacional: DANE Geoportal https://geoportal.dane.gov.co/ · MGN municipio https://www.icde.gov.co/datos-y-recursos/marco-geoestadistico-nacional-municipio · GeoMedellín https://www.medellin.gov.co/geomedellin · IDESC Cali https://idesc.cali.gov.co/
Libs sugeridas: D3 (d3-geo, d3-scale) · topojson · mapshaper (simplificar) · geopandas/pandas (ETL) · Puppeteer (PDF).
