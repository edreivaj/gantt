#!/usr/bin/env python3
"""
Aplicación Flask para generar planificación de obra y diagrama de Gantt
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
import io
import os

app = Flask(__name__)
CORS(app)

# Configuración para matplotlib en español
plt.rcParams['font.family'] = 'DejaVu Sans'

class PlanificacionObra:
    def __init__(self, presupuesto_total, servicios_arquitectura, fecha_itp, nombre_cliente, direccion):
        self.presupuesto_total = float(presupuesto_total)
        self.servicios_arquitectura = float(servicios_arquitectura)
        self.fecha_itp = datetime.strptime(fecha_itp, '%Y-%m-%d')
        self.nombre_cliente = nombre_cliente
        self.direccion = direccion
        self.actividades = []
        self.calcular_actividades()

    def calcular_actividades(self):
        """Calcula todas las actividades y sus fechas basándose en la lógica del Excel"""

        # IVA 21%
        IVA_RATE = 0.21

        # Cálculo de porcentajes según el Excel
        # Del presupuesto total:
        # - 10% preparación obra
        # - 20% inicio obra
        # - 70% certificaciones (resto)

        prep_obra_base = self.presupuesto_total * 0.10
        inicio_obra_base = self.presupuesto_total * 0.20
        certificaciones_base = self.presupuesto_total * 0.70

        # Total con IVA
        total_presupuesto_iva = self.presupuesto_total * (1 + IVA_RATE)
        servicios_iva = self.servicios_arquitectura * (1 + IVA_RATE)
        prep_obra_iva = prep_obra_base * (1 + IVA_RATE)
        inicio_obra_iva = inicio_obra_base * (1 + IVA_RATE)
        certificaciones_iva = certificaciones_base * (1 + IVA_RATE)

        # Licencia de obra (aproximadamente 3% del presupuesto total)
        licencia_obra = self.presupuesto_total * 0.03

        fecha_actual = self.fecha_itp

        # Lista de actividades con sus duraciones
        actividades_config = [
            {
                'nombre': 'Presentación ITP',
                'dias': 0,
                'base': 0,
                'pagos_ayto': 0
            },
            {
                'nombre': 'Contratación proyecto',
                'dias': 15,
                'base': self.servicios_arquitectura,
                'pagos_ayto': 0
            },
            {
                'nombre': 'Redacción del Proyecto básico y presentación al ayuntamiento',
                'dias': 28,
                'base': 0,
                'pagos_ayto': 0
            },
            {
                'nombre': 'Obtención licencia',
                'dias': 90,
                'base': 0,
                'pagos_ayto': 0
            },
            {
                'nombre': 'Pago preparación obra',
                'dias': 7,
                'base': prep_obra_base,
                'pagos_ayto': 0
            },
            {
                'nombre': 'Redacción proyecto ejecutivo, visado y presentación ayuntamiento',
                'dias': 56,
                'base': 0,
                'pagos_ayto': 0
            },
            {
                'nombre': 'Pago licencia de obra (Ajuntamiento)',
                'dias': 7,
                'base': 0,
                'pagos_ayto': licencia_obra
            },
            {
                'nombre': 'Pago inicio obra',
                'dias': 15,
                'base': inicio_obra_base,
                'pagos_ayto': 0
            },
            {
                'nombre': 'Inicio obra',
                'dias': 15,
                'base': 0,
                'pagos_ayto': 0
            },
            {
                'nombre': 'Certificaciones de obra ( con la ultima la obra queda pagada)',
                'dias': 180,
                'base': certificaciones_base,
                'pagos_ayto': 0
            }
        ]

        # Calcular presupuesto pendiente acumulado
        presupuesto_pendiente = total_presupuesto_iva + servicios_iva

        for i, config in enumerate(actividades_config):
            fecha_inicio = fecha_actual
            fecha_final = fecha_inicio + timedelta(days=config['dias'])

            base = config['base']
            iva = base * IVA_RATE if base > 0 else 0
            total = base + iva
            pagos_ayto = config['pagos_ayto']

            # Actualizar presupuesto pendiente
            if total > 0:
                presupuesto_pendiente -= total

            actividad = {
                'n_orden': i + 1,
                'actividad': config['nombre'],
                'inicio': fecha_inicio,
                'dias': config['dias'],
                'final': fecha_final,
                'base': base,
                'iva': iva,
                'total': total,
                'ppto_pendiente': presupuesto_pendiente if total > 0 else presupuesto_pendiente,
                'pagos_ayto': pagos_ayto
            }

            self.actividades.append(actividad)

            # La siguiente actividad comienza donde termina esta
            # Excepto algunas que empiezan en paralelo
            if config['nombre'] == 'Obtención licencia':
                # "Pago preparación obra" comienza con "Obtención licencia"
                fecha_actual = fecha_inicio
            elif config['nombre'] == 'Pago preparación obra':
                # "Redacción proyecto ejecutivo" comienza cuando termina "Pago preparación obra"
                fecha_actual = fecha_final
            elif config['nombre'] == 'Redacción proyecto ejecutivo, visado y presentación ayuntamiento':
                # Volver a la fecha de obtención de licencia para las siguientes
                fecha_actual = self.actividades[3]['final']  # Final de "Obtención licencia"
            else:
                fecha_actual = fecha_final

    def generar_tabla_html(self):
        """Genera la tabla de planificación en HTML"""
        df = pd.DataFrame([
            {
                'N°': a['n_orden'],
                'Actividad': a['actividad'],
                'Inicio': a['inicio'].strftime('%d/%m/%Y'),
                'Días': a['dias'],
                'Final': a['final'].strftime('%d/%m/%Y'),
                'Base (€)': f"{a['base']:,.2f}",
                'IVA (€)': f"{a['iva']:,.2f}",
                'Total (€)': f"{a['total']:,.2f}",
                'Ppto. pendiente (€)': f"{a['ppto_pendiente']:,.2f}",
                'Pagos Ayto. (€)': f"{a['pagos_ayto']:,.2f}" if a['pagos_ayto'] > 0 else ""
            }
            for a in self.actividades
        ])
        return df

    def generar_gantt(self):
        """Genera el diagrama de Gantt y devuelve la imagen"""
        fig, ax = plt.subplots(figsize=(18, 10))

        # Colores para diferentes tipos de actividades
        colors = {
            'administrativo': '#4472C4',  # Azul
            'proyecto': '#70AD47',  # Verde
            'pago': '#FFC000',  # Naranja
            'obra': '#C00000'  # Rojo
        }

        # Clasificar actividades
        def get_color(nombre):
            if 'pago' in nombre.lower() or 'licencia' in nombre.lower():
                return colors['pago']
            elif 'redacción' in nombre.lower() or 'proyecto' in nombre.lower():
                return colors['proyecto']
            elif 'obra' in nombre.lower() or 'certificaciones' in nombre.lower():
                return colors['obra']
            else:
                return colors['administrativo']

        # Dibujar barras del Gantt usando barh (horizontal bar)
        y_pos = np.arange(len(self.actividades))

        for i, actividad in enumerate(self.actividades):
            fecha_inicio = actividad['inicio']
            fecha_final = actividad['final']
            dias = actividad['dias']

            color = get_color(actividad['actividad'])

            # Dibujar barra horizontal
            if dias > 0:
                ax.barh(i, dias, left=mdates.date2num(fecha_inicio),
                       height=0.6, color=color, edgecolor='black', linewidth=0.5)

                # Añadir etiqueta con el total si hay pago
                if actividad['total'] > 0:
                    mid_point = mdates.date2num(fecha_inicio) + dias/2
                    ax.text(mid_point, i,
                           f"{actividad['total']:,.0f}€",
                           ha='center', va='center',
                           fontsize=7, fontweight='bold', color='white')

                # Añadir etiqueta con pagos al ayuntamiento
                if actividad['pagos_ayto'] > 0:
                    mid_point = mdates.date2num(fecha_inicio) + dias/2
                    ax.text(mid_point, i,
                           f"{actividad['pagos_ayto']:,.0f}€",
                           ha='center', va='center',
                           fontsize=7, fontweight='bold', color='white')
            else:
                # Para actividades sin duración, mostrar un marcador
                ax.plot(mdates.date2num(fecha_inicio), i, marker='D',
                       markersize=8, color=color, markeredgecolor='black')

        # Configurar ejes
        ax.set_yticks(y_pos)
        ax.set_yticklabels([a['actividad'] for a in self.actividades], fontsize=8)
        ax.set_ylim(-0.5, len(self.actividades) - 0.5)

        # Formato de fechas en eje X
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_minor_locator(mdates.WeekdayLocator())

        # Rotar etiquetas del eje X
        for label in ax.get_xticklabels():
            label.set_rotation(45)
            label.set_ha('right')

        # Invertir eje Y para que la primera actividad esté arriba
        ax.invert_yaxis()

        # Título y etiquetas
        ax.set_xlabel('Fecha', fontsize=12, fontweight='bold')
        ax.set_title('GANTT DE PLANIFICACION Y PAGOS',
                    fontsize=16, fontweight='bold', pad=20)

        # Grid
        ax.grid(True, axis='x', alpha=0.3, linestyle='--')

        # Ajustar márgenes
        plt.subplots_adjust(left=0.25, right=0.95, top=0.95, bottom=0.15)

        # Guardar en buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='jpg', dpi=200, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return buf

    def generar_tabla_imagen(self):
        """Genera la tabla de planificación como imagen JPG"""
        df = self.generar_tabla_html()

        # Crear figura
        fig, ax = plt.subplots(figsize=(20, 12))
        ax.axis('tight')
        ax.axis('off')

        # Crear tabla
        table = ax.table(cellText=df.values,
                        colLabels=df.columns,
                        cellLoc='center',
                        loc='center',
                        colWidths=[0.05, 0.35, 0.08, 0.05, 0.08, 0.08, 0.08, 0.08, 0.1, 0.1])

        # Estilo de la tabla
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2)

        # Estilo de encabezados
        for i in range(len(df.columns)):
            cell = table[(0, i)]
            cell.set_facecolor('#4472C4')
            cell.set_text_props(weight='bold', color='white')

        # Alternar colores de filas
        for i in range(1, len(df) + 1):
            for j in range(len(df.columns)):
                cell = table[(i, j)]
                if i % 2 == 0:
                    cell.set_facecolor('#E7E6E6')
                else:
                    cell.set_facecolor('white')

        # Título
        plt.title('TABLA DE PLANIFICACION Y PAGOS',
                 fontsize=18, fontweight='bold', pad=20)

        # Guardar en buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='jpg', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close()

        return buf


@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/calcular', methods=['POST'])
def calcular():
    """Procesa los datos y genera la planificación"""
    try:
        datos = request.json

        planificacion = PlanificacionObra(
            presupuesto_total=datos['presupuesto_total'],
            servicios_arquitectura=datos['servicios_arquitectura'],
            fecha_itp=datos['fecha_itp'],
            nombre_cliente=datos['nombre_cliente'],
            direccion=datos['direccion']
        )

        # Generar tabla HTML
        df = planificacion.generar_tabla_html()
        tabla_html = df.to_html(classes='table table-striped', index=False)

        return jsonify({
            'success': True,
            'tabla_html': tabla_html,
            'actividades': [
                {
                    'n_orden': a['n_orden'],
                    'actividad': a['actividad'],
                    'inicio': a['inicio'].strftime('%Y-%m-%d'),
                    'dias': a['dias'],
                    'final': a['final'].strftime('%Y-%m-%d'),
                    'base': a['base'],
                    'iva': a['iva'],
                    'total': a['total'],
                    'ppto_pendiente': a['ppto_pendiente'],
                    'pagos_ayto': a['pagos_ayto']
                }
                for a in planificacion.actividades
            ]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/generar_gantt', methods=['POST'])
def generar_gantt():
    """Genera y descarga el diagrama de Gantt como JPG"""
    try:
        datos = request.json

        planificacion = PlanificacionObra(
            presupuesto_total=datos['presupuesto_total'],
            servicios_arquitectura=datos['servicios_arquitectura'],
            fecha_itp=datos['fecha_itp'],
            nombre_cliente=datos['nombre_cliente'],
            direccion=datos['direccion']
        )

        # Generar Gantt
        buf = planificacion.generar_gantt()

        return send_file(
            buf,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='gantt_planificacion.jpg'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/generar_tabla', methods=['POST'])
def generar_tabla():
    """Genera y descarga la tabla de planificación como JPG"""
    try:
        datos = request.json

        planificacion = PlanificacionObra(
            presupuesto_total=datos['presupuesto_total'],
            servicios_arquitectura=datos['servicios_arquitectura'],
            fecha_itp=datos['fecha_itp'],
            nombre_cliente=datos['nombre_cliente'],
            direccion=datos['direccion']
        )

        # Generar tabla como imagen
        buf = planificacion.generar_tabla_imagen()

        return send_file(
            buf,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='tabla_planificacion.jpg'
        )

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
