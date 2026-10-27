# Seguridad

## Versiones soportadas

| Versión | Soporte |
|---|---|
| 2.x | Sí |
| 1.x | No |

## Cómo reportar una vulnerabilidad

No abras un issue público para problemas de seguridad.

Usá el reporte privado de GitHub:

https://github.com/puzska/separador-expedientes/security/advisories/new

Si no podés usar esa vía, escribí a `francopuszkarsky@gmail.com` con el asunto
`SEGURIDAD separador-expedientes`.

Incluí, si es posible:

- versión del paquete y de Python;
- sistema operativo;
- backend (`pypdf` o `PyMuPDF`);
- pasos mínimos para reproducir;
- impacto esperado;
- un PDF sintético o una descripción de la estructura, nunca un expediente
  real.

## Qué está en alcance

- Ejecución de comandos o escritura arbitraria de archivos a partir de un PDF
  malicioso.
- Path traversal en nombres de archivo, mapas o carpetas de salida.
- Agotamiento de memoria o CPU con PDFs manipulados.
- Vulnerabilidades en dependencias que afecten al paquete.
- Exposición de datos locales por logs, índices o archivos temporales.

## Qué no está en alcance

- La exactitud de la detección automática: es una heurística, no una decisión
  judicial.
- PDFs protegidos con contraseña o dañados que no se puedan abrir.
- Problemas que requieran acceso físico a la máquina o una cuenta ya
  comprometida.
- Ataques de ingeniería social.

## Compromiso de respuesta

- Acuse de recibo: dentro de 7 días.
- Evaluación inicial: dentro de 14 días.
- Corrección o mitigación: según la gravedad, con un objetivo de 30 días para
  problemas críticos.

## Privacidad

La herramienta procesa archivos locales y no envía datos a ningún servidor. El
repositorio no contiene expedientes reales: todos los PDFs versionados son
sintéticos. Si encontrás un archivo con datos reales en el repositorio o en un
release, reportalo como vulnerabilidad para retirarlo.
