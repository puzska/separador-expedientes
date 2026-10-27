# Guía del mapa manual

El mapa manual sirve para decirle a la herramienta exactamente qué páginas
forman cada trámite. Es la opción más segura cuando:

- el PDF está escaneado y no tiene texto extraíble;
- los bookmarks no representan la separación procesal que necesitás;
- el juzgado tiene un criterio propio para agrupar actuaciones;
- querés revisar y corregir la detección antes de generar los PDFs.

## Flujo recomendado

1. Generá un mapa borrador:

```bat
separador-expedientes "expediente.pdf" --generar-mapa "mapa_borrador.json"
```

2. Revisá y editá el JSON o el CSV.
3. Validá y generá la salida:

```bat
separador-expedientes "expediente.pdf" -o "TRAMITES SEPARADOS" --mapa "mapa_borrador.json"
```

4. Verificá que cada PDF tenga las páginas esperadas:

```bat
separador-expedientes "expediente.pdf" -o "TRAMITES SEPARADOS" --mapa "mapa_borrador.json" --verificar
```

## Formato JSON mínimo

```json
[
  {
    "archivo": "01_Demanda.pdf",
    "nombre": "Demanda",
    "categoria": "Actuaciones Procesales - Escrito de parte",
    "paginas": "1-3"
  },
  {
    "archivo": "02_Providencia.pdf",
    "nombre": "Providencia: téngase por presentado",
    "categoria": "Actuaciones Procesales - Resolución judicial",
    "paginas": "4-4"
  }
]
```

## Formato CSV mínimo

```csv
archivo,nombre,categoria,paginas
01_Demanda.pdf,Demanda,Actuaciones Procesales - Escrito de parte,1-3
02_Providencia.pdf,Providencia,Actuaciones Procesales - Resolución judicial,4-4
```

El CSV acepta coma, punto y coma, tabulación o `|` como separador. La
herramienta detecta el separador automáticamente. Si el archivo tiene BOM
(por ejemplo, exportado desde Excel), también se lee.

## Campos

| Campo | Obligatorio | Descripción |
|---|---|---|
| `archivo` | No | Nombre del PDF de salida. Si falta, se genera a partir de `nombre`. |
| `nombre` | Sí, si no hay `archivo` | Título visible del trámite. |
| `categoria` | No | Texto libre para el índice. |
| `paginas` | Una de las formas de rango | Rango inclusivo, por ejemplo `"1-3"`, `"1 a 3"`, `"1 hasta 3"` o `[1, 3]`. |
| `pagina_inicio` | Alternativa | Primera página, 1-based. |
| `pagina_fin` | Alternativa | Última página, inclusiva. |
| `cant` | Alternativa | Cantidad de páginas. Se calcula en orden desde la página 1 si no hay rango. |
| `fecha` | No | Fecha informativa para el índice. |
| `hora` | No | Hora informativa para el índice. |

Las páginas son **1-based e inclusivas**. `"1-3"` incluye las páginas 1, 2 y 3.

## Rangos y páginas sin asignar

Por defecto, la herramienta valida que:

- no haya páginas repetidas entre trámites;
- no haya páginas sin asignar;
- los rangos estén dentro del total de páginas del PDF.

Si querés permitir huecos, usá `--permitir-huecos`. Esto es útil cuando el PDF
tiene separadores, carátulas o páginas en blanco que no querés incluir.

## Nombres de archivo

- Se quitan caracteres inválidos para Windows.
- Se evitan nombres duplicados.
- Se puede anteponer un prefijo con `--prefijo "0000123_"`.
- Si un archivo ya existe, la herramienta falla salvo que uses
  `--sobrescribir`.

## Ejemplo incluido

El repositorio trae un mapa sintético:

```bat
separador-expedientes "ejemplos/expediente_sintetico.pdf" -o "salida" --mapa "ejemplos/mapa_sintetico.json"
```

El PDF y el mapa son ficticios. No contienen datos de personas ni de causas
reales.

## Consejos para escaneos

- Si el escaneo no tiene texto, no intentes adivinar por texto: usá un mapa.
- Numerá las páginas del PDF antes de armar el mapa para evitar confusiones.
- Revisá el índice CSV generado contra el expediente en papel o en el visor.
- Si el PDF tiene una carátula o un separador, decidi explícitamente si va en
  un trámite, en el primero o en ninguno.
