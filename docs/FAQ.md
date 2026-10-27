# Preguntas frecuentes

## ¿Sirve para PDFs escaneados?

Sí, si le pasás un mapa manual. La detección automática por texto necesita texto
extraíble. Para escaneos sin OCR, generá un mapa borrador, revisalo y usá
`--mapa`.

## ¿La herramienta sube el expediente a algún servidor?

No. Todo el procesamiento es local. No hay telemetría ni llamadas de red.

## ¿Cómo detecta los trámites?

Primero intenta con los bookmarks del PDF. Elige el nivel más representativo y
agrupa según `--agrupar`. Si no hay bookmarks suficientes, prueba con el texto:
numeración que reinicia, encabezados, fechas y títulos conocidos. Si tampoco
encuentra nada, necesita un mapa manual.

## ¿Qué diferencia hay entre `fecha`, `dia` y `marcador`?

- `fecha`: un trámite por envío, usando fecha y hora. Es el modo por defecto y
  el más seguro cuando el sistema exporta un bookmark por envío.
- `dia`: fusiona todas las actuaciones de la misma fecha.
- `marcador`: respeta cada bookmark, aunque compartan fecha y hora.

## ¿Puedo usar mi propia separación?

Sí. Generá un mapa borrador, editalo y ejecutá con `--mapa`. El mapa tiene
prioridad sobre la detección automática. Ver [la guía del mapa](MAPA.md).

## ¿Qué pasa si hay páginas sin asignar?

Por defecto, la herramienta falla para que no se pierdan páginas. Si querés
permitir huecos, usá `--permitir-huecos`.

## ¿Puedo procesar varios expedientes?

Sí. Podés ejecutar el comando en un bucle y usar `--prefijo` para distinguir los
archivos. El procesamiento por lotes integrado está en la hoja de ruta.

## ¿Funciona en Windows, Linux y macOS?

Sí. La integración continua corre en Linux y Windows. En macOS debería funcionar
igual, aunque no está en la matriz de CI.

## ¿Qué backend conviene?

`pypdf` es el recomendado y el más portable. `PyMuPDF` suele ser más rápido y
tolera mejor algunos PDFs, pero tiene una licencia distinta. Si están los dos
instalados, se usa `pypdf`; podés forzar uno con `--backend`.

## ¿Por qué el CSV tiene BOM?

Para que Excel en Windows abra los acentos correctamente. El JSON no tiene BOM.

## ¿Puedo cambiar las categorías?

Sí, desde el mapa manual. La categoría automática es orientativa y se basa en
palabras clave.

## ¿Cómo reporto un error?

Usá la plantilla de issue e incluí sistema operativo, versión de Python, backend,
comando y salida del error. No adjuntes expedientes reales. Ver
[CONTRIBUTING.md](../CONTRIBUTING.md).

## ¿Cómo contribuyo?

Leé [CONTRIBUTING.md](../CONTRIBUTING.md) y el
[Código de conducta](../CODE_OF_CONDUCT.md). Los cambios de comportamiento
necesitan tests.

## ¿Dónde están los datos de ejemplo?

En `ejemplos/`. Son PDFs sintéticos, con nombres y textos inventados, y cada
página lleva la leyenda `EJEMPLO FICTICIO - SIN DATOS REALES`. Se regeneran con
`python scripts/generar_ejemplo.py`.
