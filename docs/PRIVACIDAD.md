# Privacidad y datos

## Procesamiento local

`separador-expedientes` trabaja con archivos locales. No tiene telemetría, no
hace llamadas de red y no sube expedientes a ningún servidor.

El flujo es:

1. lee el PDF desde tu disco;
2. detecta o carga un mapa de páginas;
3. escribe los PDFs y el índice en la carpeta de salida.

No hay cuentas, licencias ni servicios en la nube.

## Qué contiene este repositorio

- Cuatro PDFs de ejemplo en `ejemplos/`.
- Mapas de ejemplo en JSON y CSV.
- Tests que usan esos PDFs y otros fixtures generados en memoria.

Todos los PDFs versionados son sintéticos. Cada página incluye la leyenda
`EJEMPLO FICTICIO - SIN DATOS REALES`. Los nombres, fechas, causas y textos son
inventados.

## Protecciones del repositorio

- `.gitignore` bloquea todos los `*.pdf` salvo `ejemplos/*.pdf` y
  `tests/**/*.pdf`.
- También bloquea carpetas de salida, índices generados y mapas borrador.
- `.gitattributes` marca PDFs e imágenes como binarios.
- La integración continua no recibe expedientes reales.
- El demo usa solo el PDF sintético.

El `.gitignore` es una red de seguridad, no una garantía. Revisá siempre
`git status` antes de commitear.

## Recomendaciones para usar la herramienta

- Trabajá en una carpeta dedicada y cifrada si el equipo lo permite.
- No copies expedientes reales dentro del repositorio.
- No pegues texto de expedientes en issues, pull requests ni discusiones.
- Si necesitás compartir un error, describí la estructura del PDF o armá un
  ejemplo sintético.
- Borrá las carpetas de salida temporales cuando termines.
- Revisá los índices CSV/JSON antes de compartirlos: contienen nombres de
  trámites y fechas.
- Si usás un mapa manual, también puede contener datos del caso.

## Si encontrás datos reales en el repositorio

Reportalo como problema de seguridad:

https://github.com/puzska/separador-expedientes/security/advisories/new

No lo publiques en un issue. El objetivo es retirar el archivo y, si corresponde,
limpiar el historial antes de que se propague.

## Dependencias

La herramienta no envía datos por sí misma, pero las dependencias que instales
(`pypdf`, `PyMuPDF`, `Pillow` para el demo) tienen sus propias políticas. Revisá
sus licencias y sus notas de seguridad si trabajás en un entorno regulado.

## Alcance

Esta política cubre el repositorio y la herramienta. No cubre los servicios de
GitHub, PyPI ni el sistema operativo donde se ejecuta.
