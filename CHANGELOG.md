# Changelog

Todos los cambios importantes de este proyecto se documentan en este archivo.
El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y
el versionado [Semantic Versioning](https://semver.org/lang/es/).

## [Unreleased]

## [2.0.0] - 2026-10-26

Primera versión pública.

### Agregado

- CLI `separador-expedientes` y API importable desde Python.
- Detección automática por bookmarks planos y anidados.
- Agrupación por fecha y hora, por día o por bookmark.
- Detección por texto para PDFs sin bookmarks.
- Mapas manuales en JSON y CSV, con validación de solapamientos y páginas sin
  asignar.
- Generación de mapas borrador para editar.
- Índice en CSV (UTF-8 con BOM, compatible con Excel) y JSON.
- Verificación de los PDFs generados.
- Backends `pypdf` y `PyMuPDF`, con detección automática.
- Ejemplos 100 % ficticios y scripts para regenerarlos.
- Suite de tests con cobertura de detección, mapas, división, CLI y backends.
- Integración continua en Linux y Windows.
- Paquete instalable, wheel, sdist y entry point de consola.
- Documentación bilingüe (español e inglés), demo animado y social preview.

### Cambiado

- El nombre del programa en la ayuda y en los mensajes se obtiene del entry
  point, para que funcione igual como script y como paquete instalado.
- La limpieza de títulos quita sufijos de adjuntos y nombres de profesionales
  sin romper títulos legítimos.

### Corregido

- Manejo de bookmarks con niveles mixtos y de índices con un nodo raíz.
- Normalización de fechas y horas para agrupar correctamente.
- Nombres de archivo duplicados y caracteres inválidos en Windows.

### Seguridad

- El repositorio no contiene expedientes reales. Todos los PDFs versionados son
  sintéticos y llevan la leyenda `EJEMPLO FICTICIO - SIN DATOS REALES`.
- El procesamiento es local: la herramienta no sube archivos a ningún servidor.
