# Volantes hiper-segmentados por barrio — Bogotá

**Objetivo:** cruzar (a) resultados electorales por barrio —dónde perdió Cepeda y dónde se retrocedió frente a la victoria de Petro en 2022— con (b) el uso de suelo de cada barrio, para imprimir volantes personalizados que lleven el nombre del barrio y los puntos del programa de gobierno más relevantes según su uso de suelo predominante.

**Veredicto de factibilidad:** factible. La capa de uso de suelo está resuelta (datos abiertos). El trabajo real es conseguir y geolocalizar los resultados por puesto de 2026 y 2022. Si esos dos archivos están descargables —y lo están—, el resto es ensamblaje.

---

## El marco de partida

El tweet de @RicardoRuiz_ (2 jun 2026) plantea la hipótesis: en 2022 Petro ganó Bogotá con ~48%; en 2026 Cepeda sacó ~41% (casi 7 puntos menos). La izquierda conservó el sur pero perdió la "franja media" de la ciudad. Es un marco a nivel ciudad — este proyecto lo baja a nivel barrio para poder accionar.

---

## Las tres capas de datos

### 1. Resultados electorales (la parte con trabajo)

No existe un desglose oficial "por barrio". Lo más fino que publica la Registraduría es el **puesto de votación** (y la mesa). El camino es: descargar por puesto → geolocalizar cada puesto → asignarlo a un barrio/UPZ.

Fuentes confirmadas como descargables:

- **Observatorio Electoral de la Registraduría** — archivos planos (CSV) con resultados por departamento, municipio, zona, puesto, mesa y candidato. Es la fuente primaria oficial. https://observatorio.registraduria.gov.co/
- **Histórico de resultados** de la Registraduría. https://estadisticaselectorales.registraduria.gov.co/
- **CEDAE / Datasketch** — CSV ya limpios de presidenciales por puesto (1ª y 2ª vuelta). https://cedae.datasketch.co/
- **MOE** — base definitiva del escrutinio a nivel de puesto (2022). https://moe.org.co/
- **Datos Abiertos Bogotá — grupo "resultados-electorales"** — posible atajo: datasets que pueden venir ya referenciados a la geografía de Bogotá. https://datosabiertos.bogota.gov.co/group/resultados-electorales

Notas de calendario y limpieza:
- 2026 primera vuelta (los ~41% de Cepeda): consultable vía preconteo/E-14 y archivo plano. El escrutinio definitivo puede tardar días en consolidarse tras la elección.
- 2022 está completo y definitivo.
- Los puestos pueden abrir, cerrar o mudarse entre elecciones; el empalme 2022↔2026 se hace por código de puesto y, donde falle, por dirección. Es la parte tediosa pero mecánica.

### 2. Uso de suelo (la parte fácil — ya resuelta)

Descargable gratis como shapefile/GeoJSON:

- **IDECA — Infraestructura de Datos Espaciales de Bogotá.** https://www.ideca.gov.co/
- **Manzana. Bogotá D.C.** (catastral, con localidad, UPZ, código de manzana). https://datosabiertos.bogota.gov.co/dataset/manzana
- **Clasificación del suelo — POT Bogotá D.C.** (urbano, rural, expansión). https://datosabiertos.bogota.gov.co/dataset/clasificacion-del-suelo-bogota-d-c
- **Mapas Bogotá** para visualizar/descargar capas.

Para "uso de suelo" en el sentido funcional (residencial, comercial, dotacional, industrial), la fuente más rica es el **POT** y la base catastral por manzana/UPZ. Conviene decidir temprano la resolución: manzana (muy fino) vs. UPZ (más manejable para volantes).

### 3. Geografía de barrios (la malla común que une todo)

- Polígonos de **barrio catastral** y **UPZ** de IDECA. Son las piezas sobre las que se hace el point-in-polygon de los puestos y la agregación del uso de suelo.

---

## El pipeline, paso a paso

1. **Descargar** resultados por puesto de 2026 (1ª vuelta) y 2022 (1ª vuelta, para comparar contra Petro), filtrando Bogotá D.C.
2. **Geocodificar** cada puesto. Si Datos Abiertos Bogotá ya trae los puestos con coordenadas, este paso casi desaparece; si no, se geocodifican las direcciones de la resolución de puestos de la Registraduría.
3. **Join espacial** puesto → barrio/UPZ (point-in-polygon con los polígonos de IDECA).
4. **Agregar** votos por barrio: % Cepeda 2026, % Petro 2022, y el **delta** (retroceso). Marcar barrios donde Cepeda perdió y/o donde cayó más vs. 2022.
5. **Calcular uso de suelo predominante** por barrio (desde POT / catastro): residencial, comercial, dotacional, industrial, mixto.
6. **Cruzar** ambas capas en una sola tabla maestra: una fila por barrio con [nombre, %Cepeda26, %Petro22, delta, uso predominante, mensaje del programa asignado].
7. **Generar volantes** por merge desde esa tabla maestra (ver prototipo).

Herramientas sugeridas: Python con `geopandas` (join espacial), `pandas` (agregación), y para geocodificar las direcciones de puestos un geocoder local sobre la malla vial de IDECA o un servicio de geocoding. Todo reproducible en un par de scripts.

---

## Salvedad metodológica (importante, para no sobre-interpretar)

El resultado de un puesto refleja **dónde vota** la gente, no exactamente dónde vive ni el uso de suelo de su vivienda. Un puesto en zona comercial o dotacional (un colegio, una plaza) puede recibir votantes de un área residencial vecina. Para **segmentar y priorizar barrios** funciona muy bien como proxy; no es inferencia causal a nivel individual. Conviene tenerlo presente al redactar conclusiones.

---

## Diseño de los volantes

Cada volante es la misma plantilla con campos que se rellenan por barrio:

- **{{BARRIO}}** — nombre del barrio (encabezado, hace el volante "tuyo").
- **{{USO_SUELO}}** — uso predominante, define el enfoque del mensaje.
- **3 puntos del programa** mapeados al uso de suelo (ver tabla de mapeo abajo).

Mapeo uso de suelo → enfoque del mensaje (la metodología; los textos exactos salen del programa oficial de Cepeda):

| Uso de suelo predominante | Ejes del programa a destacar |
|---|---|
| Residencial | Vivienda, servicios públicos, seguridad de barrio, espacio público y cuidado |
| Comercial | Economía popular, seguridad para el comercio, formalización, crédito |
| Industrial / logístico | Empleo, reconversión productiva, transporte de carga, ambiente |
| Dotacional (educación/salud) | Educación pública, salud, primera infancia, cultura |
| Mixto | Combinación de los dos usos más presentes |

> Nota: el prototipo trae **textos de ejemplo entre corchetes**. Los puntos reales deben tomarse del **programa de gobierno oficial de Iván Cepeda** para no atribuirle propuestas que no son suyas. Reemplazar los corchetes por las propuestas oficiales es el último paso antes de imprimir.

---

## Producción / impresión

- La tabla maestra (un barrio por fila) alimenta un **merge**: HTML+CSS para impresión (lo más flexible y vistoso), o mail-merge de Word/InDesign.
- Tamaño media carta para volante de mano; PDF por barrio o un PDF consolidado con todos.

---

## Actualización — verificación de datos (confirmado)

- **Los puestos de votación SÍ están publicados como capa geolocalizada.** Datos Abiertos Bogotá / IDECA tiene el dataset *"Puesto de Votación. Bogotá D.C."* (puntos, en SHP/GeoJSON/GPKG/KMZ, actualizado nov-2025). Esto **casi elimina la geocodificación**: solo hay que unir los resultados de la Registraduría a esta capa por código/nombre de puesto y hacer el point-in-polygon a barrio/UPZ.
- El paso 2 del pipeline (geocodificar) se reduce a un **join por clave** + verificación de los puestos que no empaten.
- **Banco de mensajes del programa: hecho** (ver `banco-mensajes-programa.md`). El programa es más visión nacional que checklist municipal; los ejes de ciudad ya están traducidos a lenguaje de volante y mapeados a uso de suelo.

## Nueva visión: sitio web de descarga por barrio

En vez de imprimir centralizado, la gente entra a un sitio, elige su barrio y descarga su volante personalizado para imprimirlo y hacer campaña hiperlocal. Implicaciones:

- **Generación previa (recomendado):** pre-renderizar un PDF por barrio desde la tabla maestra y servirlos estáticos. Más simple, más rápido, sin backend pesado. Un sitio estático (buscador de barrio + descarga) basta.
- **Datos que alimentan el sitio:** la tabla maestra (un barrio por fila: nombre, %Cepeda26, %Petro22, delta, uso de suelo, ejes asignados) + los PDF generados.
- **UX mínima:** caja de búsqueda/autocompletar por nombre de barrio o mapa clicable; botón de descarga; quizá un "imprime y reparte" con instrucciones.
- **Hosting:** sitio estático (los PDF pesan poco si son vectoriales/HTML→PDF).

## Qué falta para arrancar la construcción

1. ~~Confirmar si los puestos vienen geolocalizados~~ → **confirmado, sí.**
2. ~~Conseguir el programa de gobierno~~ → **hecho, banco de mensajes listo.**
3. Decidir resolución: **barrio catastral vs. UPZ** (afecta cuántos volantes se generan).
4. Definir cobertura: ¿todos los barrios, o solo los de retroceso y los perdidos?
5. Decidir si el sitio sirve PDF pre-generados (recomendado) o genera al vuelo.
6. Validar tono y si se incluyen cifras/metas.
