// Generado por tools/demo/generar_datos.py. Datos ficticios.
window.DEMO_DATA = {
  "prompt": "C:\\casos\\expediente-demo>",
  "listar": {
    "comando": "separador-expedientes expediente.pdf --listar",
    "salida": [
      "  #  Paginas      Cant.  Categoria                                     Nombre",
      "----------------------------------------------------------------------------------------------------------------------------------",
      "  1  1-3              3  Actuaciones Procesales - Escrito de parte     DEMANDA DE ALIMENTOS",
      "  2  4-4              1  Actuaciones Procesales - Resolucion judicial  PROVIDENCIA: TENGASE POR PRESENTADO",
      "  3  5-5              1  Actuaciones Procesales - Resolucion judicial  LIBRAR OFICIO",
      "  4  6-7              2  Actuaciones Procesales - Escrito de parte     CONTESTA DEMANDA",
      "  5  8-8              1  Actuaciones Procesales - Resolucion judicial  SENTENCIA",
      "  6  9-9              1  Actuaciones Procesales - Resolucion judicial  NOTA DE SECRETARIA",
      "  7  10-10            1  Actuaciones Procesales - Oficio               OFICIO DILIGENCIADO",
      "  8  11-11            1  Actuaciones Procesales - Oficio               ACOMPANA OFICIO",
      "----------------------------------------------------------------------------------------------------------------------------------",
      "Total: 8 trámites, 11 páginas."
    ]
  },
  "dividir": {
    "comando": "separador-expedientes expediente.pdf -o \"TRAMITES SEPARADOS\"",
    "salida": [
      "[  1/8] 01_DEMANDA_DE_ALIMENTOS.pdf",
      "[  2/8] 02_PROVIDENCIA_TENGASE_POR_PRESENTADO.pdf",
      "[  3/8] 03_LIBRAR_OFICIO.pdf",
      "[  4/8] 04_CONTESTA_DEMANDA.pdf",
      "[  5/8] 05_SENTENCIA.pdf",
      "[  6/8] 06_NOTA_DE_SECRETARIA.pdf",
      "[  7/8] 07_OFICIO_DILIGENCIADO.pdf",
      "[  8/8] 08_ACOMPANA_OFICIO.pdf",
      "",
      "Listo: 8 trámites en C:\\casos\\expediente-demo\\TRAMITES SEPARADOS",
      "Índice: C:\\casos\\expediente-demo\\TRAMITES SEPARADOS\\INDICE_TRAMITES.csv"
    ]
  },
  "archivos": {
    "comando": "Get-ChildItem \"TRAMITES SEPARADOS\" -Name",
    "salida": [
      "01_DEMANDA_DE_ALIMENTOS.pdf",
      "02_PROVIDENCIA_TENGASE_POR_PRESENTADO.pdf",
      "03_LIBRAR_OFICIO.pdf",
      "04_CONTESTA_DEMANDA.pdf",
      "05_SENTENCIA.pdf",
      "06_NOTA_DE_SECRETARIA.pdf",
      "07_OFICIO_DILIGENCIADO.pdf",
      "08_ACOMPANA_OFICIO.pdf",
      "INDICE_TRAMITES.csv",
      "INDICE_TRAMITES.json"
    ]
  }
};
