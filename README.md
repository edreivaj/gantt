# Aplicación de Planificación y Pagos de Obra

Esta aplicación web replica la funcionalidad del Excel "Plantilla planificación y pagos.xlsm" y permite generar diagramas de Gantt y tablas de planificación en formato JPG.

## Características

- ✅ Formulario web para introducir datos del proyecto
- ✅ Cálculo automático de fechas y montos según la lógica del Excel
- ✅ Generación de diagrama de Gantt visual
- ✅ Generación de tabla de planificación y pagos
- ✅ Exportación de ambos elementos como imágenes JPG
- ✅ Interfaz moderna y responsiva con Bootstrap

## Requisitos

- Python 3.11+
- Bibliotecas Python (instaladas automáticamente):
  - Flask
  - Flask-CORS
  - matplotlib
  - pandas
  - numpy
  - openpyxl
  - pillow

## Instalación

1. Clonar o descargar el repositorio

2. Instalar las dependencias:
```bash
pip install flask flask-cors matplotlib pandas numpy openpyxl pillow
```

## Uso

1. Ejecutar la aplicación:
```bash
cd app
python app.py
```

2. Abrir el navegador en `http://localhost:5000`

3. Introducir los datos del proyecto:
   - Total presupuesto PREMIUM s/IVA
   - Total servicios y arquitectura PREMIUM s/IVA
   - Fecha de presentación ITP
   - Nombre del cliente
   - Dirección de la construcción

4. Hacer clic en "Generar Planificación"

5. Descargar los JPGs del Gantt y la tabla

## Estructura del Proyecto

```
gantt/
├── app/
│   ├── app.py              # Aplicación Flask principal
│   ├── templates/
│   │   └── index.html      # Interfaz HTML
│   └── static/             # Archivos estáticos (si los hay)
├── Plantilla planificación y pagos.xlsm  # Excel original
├── analyze_excel.py        # Scripts de análisis
├── detailed_analysis.py
├── check_charts.py
└── README.md
```

## Funcionalidad

### Cálculos Realizados

La aplicación calcula automáticamente:

1. **Actividades del proyecto** con sus fechas de inicio y fin
2. **Distribución de pagos**:
   - Contratación de proyecto (servicios arquitectura)
   - Preparación de obra (10% del presupuesto)
   - Inicio de obra (20% del presupuesto)
   - Certificaciones de obra (70% del presupuesto)
3. **Pagos al ayuntamiento** (licencia de obra ≈ 3% del presupuesto)
4. **Presupuesto pendiente** después de cada pago
5. **IVA (21%)** sobre cada concepto

### Actividades Generadas

1. Presentación ITP
2. Contratación proyecto (15 días)
3. Redacción del Proyecto básico (28 días)
4. Obtención licencia (90 días)
5. Pago preparación obra (7 días)
6. Redacción proyecto ejecutivo (56 días)
7. Pago licencia de obra (7 días)
8. Pago inicio obra (15 días)
9. Inicio obra (15 días)
10. Certificaciones de obra (180 días)

### Diagrama de Gantt

El diagrama de Gantt incluye:
- Barras de tiempo para cada actividad
- Código de colores por tipo de actividad:
  - 🔵 Azul: Administrativo
  - 🟢 Verde: Proyecto/Redacción
  - 🟠 Naranja: Pagos
  - 🔴 Rojo: Obra
- Etiquetas con montos de pago
- Escala temporal mensual

### Tabla de Planificación

La tabla incluye:
- N° de orden
- Actividad
- Fecha inicio
- Días de duración
- Fecha final
- Base imponible
- IVA
- Total
- Presupuesto pendiente de pago
- Pagos al ayuntamiento

## Notas

- Las cifras se calculan en base a la gama PREMIUM del presupuesto
- Los plazos son tiempos medios estimados
- El porcentaje para licencia de obras es aproximado (3%)
- Las certificaciones se abonan progresivamente durante la obra

## Autor

Desarrollado con Claude Code basándose en el Excel "Plantilla planificación y pagos.xlsm"
