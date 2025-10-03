# app.py
import streamlit as st
from fpdf import FPDF
from datetime import datetime

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Asistente de Calidad del Agua",
    page_icon="💧",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Funciones de Lógica y Análisis ---

def analizar_calidad_agua(datos):
    """
    Analiza los datos del agua basándose en un árbol de decisión y devuelve una lista de diagnósticos.
    """
    diagnosticos = []
    
    # 1. Análisis de Microbiología (Prioridad Crítica)
    if datos["e_coli"] > 0 or datos["coliformes_totales"] > 0:
        diagnosticos.append({
            "tipo": "error",
            "titulo": "🔴 DIAGNÓSTICO: Contaminación Microbiológica Crítica",
            "riesgos": """
                - **Riesgo Sanitario Extremo:** La presencia de E. coli o coliformes totales indica contaminación fecal.
                - **Enfermedades Graves:** Puede causar enfermedades gastrointestinales severas, infecciones y otras condiciones graves.
                - **No Apta para Consumo:** El agua no debe ser consumida ni utilizada para cocinar o higiene personal bajo ninguna circunstancia.
            """,
            "acciones": """
                1. **No Consumir el Agua:** Suspender inmediatamente el uso del agua para beber o cocinar.
                2. **Hervir el Agua:** Si es absolutamente necesario usarla, hervir el agua durante al menos 5 minutos antes de cualquier uso.
                3. **Desinfección Urgente:** Aplicar un tratamiento de choque con cloro (supercloración) en la fuente de agua (pozo, tanque).
                4. **Identificar la Fuente:** Inspeccionar el sistema en busca de posibles puntos de contaminación (fisuras, cercanía a fosas sépticas).
                5. **Repetir Análisis:** Realizar un nuevo análisis microbiológico después del tratamiento para confirmar la eliminación de bacterias.
            """
        })

    # 2. Análisis de Metales
    if datos["hierro"] > 0.3 or datos["manganeso"] > 0.05:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: Riesgo por Metales",
            "riesgos": """
                - **Problemas Estéticos:** Puede causar coloración (rojiza/marrón), sabor metálico y manchas en ropa y sanitarios.
                - **Acumulación en Tuberías:** El hierro y manganeso pueden acumularse, reduciendo la presión del agua y favoreciendo el crecimiento de bacterias.
                - **Posibles Efectos en la Salud:** Aunque los límites son principalmente estéticos, altas concentraciones de manganeso a largo plazo pueden tener efectos neurológicos.
            """,
            "acciones": """
                1. **Instalar Filtro de Sedimentos:** Para partículas más grandes de óxido de hierro.
                2. **Sistema de Oxidación/Filtración:** Utilizar un sistema que oxida los metales (con cloro o aire) para que puedan ser filtrados fácilmente. Un filtro de arena verde (greensand) es muy efectivo.
                3. **Ablandador de Agua con Intercambio Iónico:** Algunos ablandadores también pueden reducir niveles moderados de hierro y manganeso.
            """
        })
        
    # 3. Análisis de Parámetros Físico-Químicos
    if datos["turbidez"] > 1.0:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: Turbidez Elevada",
            "riesgos": """
                - **Protección de Patógenos:** Las partículas suspendidas pueden proteger a microorganismos de los desinfectantes como el cloro.
                - **Ineficiencia de Desinfección:** La turbidez reduce la efectividad de la desinfección UV y química.
                - **Aspecto Desagradable:** El agua se ve turbia y poco atractiva para el consumo.
            """,
            "acciones": """
                1. **Filtro de Sedimentos o Multimedia:** Instalar un sistema de filtración en el punto de entrada para eliminar las partículas suspendidas.
                2. **Coagulación/Floculación:** Para turbidez muy alta, se pueden necesitar procesos químicos antes de la filtración.
                3. **Revisar la Fuente:** Identificar si la turbidez se debe a arrastre de sedimentos en la fuente (pozo, río).
            """
        })
        
    if not (6.0 <= datos["ph"] <= 7.0):
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: pH Fuera de Rango Óptimo para Desinfección",
            "riesgos": """
                - **Baja Eficacia del Cloro:** Si el pH es superior a 7.5, la capacidad desinfectante del cloro se reduce drásticamente.
                - **Corrosión o Incrustaciones:** Un pH muy bajo (<6.5) puede ser corrosivo para las tuberías metálicas. Un pH muy alto (>8.5) puede causar incrustaciones.
            """,
            "acciones": """
                1. **Ajuste de pH:** Utilizar un sistema de inyección de químicos para ajustar el pH.
                - Para **subir el pH** (si es ácido): Usar soda ash (carbonato de sodio).
                - Para **bajar el pH** (si es alcalino): Usar ácido cítrico o vinagre (en sistemas pequeños) o un sistema de inyección de ácido.
                2. **Prioridad:** Ajustar el pH es crucial *antes* de la etapa de desinfección con cloro para asegurar su efectividad.
            """
        })

    # 4. Análisis de Sales y Minerales
    if datos["dureza_total"] > 180:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: Agua Muy Dura",
            "riesgos": """
                - **Incrustaciones Severas:** Acumulación de sarro en tuberías, calentadores de agua y electrodomésticos, reduciendo su eficiencia y vida útil.
                - **Bajo Rendimiento de Jabones:** Reduce la efectividad de jabones y detergentes, requiriendo mayor cantidad.
                - **Piel y Cabello Secos:** Puede causar resequedad en la piel y el cabello.
            """,
            "acciones": """
                1. **Instalar un Ablandador de Agua:** Un sistema de intercambio iónico es la solución más común y efectiva para eliminar la dureza.
                2. **Mantenimiento Preventivo:** Realizar descalcificaciones periódicas de electrodomésticos que usan agua caliente.
            """
        })
        
    if datos["sdt"] > 1500 or datos["sulfatos"] > 250:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNóstico: Niveles Elevados de Sales Disueltas",
            "riesgos": """
                - **Sabor Salino o Amargo:** Altas concentraciones de SDT o sulfatos afectan negativamente el sabor del agua.
                - **Efecto Laxante:** Los sulfatos por encima de 250-400 ppm pueden tener un efecto laxante, especialmente en personas no acostumbradas.
                - **Corrosión:** Altos niveles de SDT pueden acelerar la corrosión de componentes metálicos.
            """,
            "acciones": """
                1. **Ósmosis Inversa (RO):** Es el método más efectivo para reducir significativamente los SDT y sulfatos. Se puede instalar en el punto de uso (cocina) o para toda la casa.
                2. **Destilación:** Otra opción para purificar el agua, aunque menos común a nivel residencial por su costo energético.
            """
        })
        
    return diagnosticos

# --- Clase para Generación de PDF ---

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte de Calidad del Agua', 0, 1, 'C')
        self.set_font('Arial', '', 8)
        self.cell(0, 10, f'Fecha de Emisión: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, body)
        self.ln()

    def add_diagnostic_section(self, tipo, titulo, riesgos, acciones):
        if tipo == "error":
            self.set_text_color(220, 50, 50)  # Rojo
        elif tipo == "warning":
            self.set_text_color(255, 193, 7) # Ámbar
        else:
            self.set_text_color(40, 167, 69) # Verde

        self.set_font('Arial', 'B', 11)
        self.multi_cell(0, 5, titulo)
        self.set_text_color(0, 0, 0) # Reset color
        self.ln(2)

        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "Riesgos Potenciales:")
        self.ln()
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, riesgos)
        self.ln(2)

        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "Plan de Acción Recomendado:")
        self.ln()
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, acciones)
        self.ln(5)


def generar_pdf(datos_entrada, resultados):
    pdf = PDF()
    pdf.add_page()

    # Sección de datos de entrada
    pdf.chapter_title("1. Parámetros Ingresados por el Usuario")
    body = ""
    for key, value in datos_entrada.items():
        # Formatear el nombre para visualización
        formatted_key = key.replace("_", " ").title()
        body += f"- {formatted_key}: {value}\n"
    pdf.chapter_body(body)

    # Sección de diagnósticos
    pdf.chapter_title("2. Diagnósticos y Recomendaciones")
    if not resultados:
        pdf.set_text_color(40, 167, 69) # Verde
        pdf.set_font('Arial', 'B', 12)
        pdf.multi_cell(0, 5, "¡Excelente! La calidad de tu agua cumple con los parámetros analizados.")
        pdf.set_text_color(0, 0, 0)
    else:
        for diag in resultados:
            pdf.add_diagnostic_section(diag["tipo"], diag["titulo"], diag["riesgos"], diag["acciones"])
            
    # Guarda el PDF en memoria
    return pdf.output(dest='S').encode('latin1')


# --- Interfaz de Usuario (Streamlit) ---

st.title("💧 Asistente de Calidad del Agua")
st.markdown("Introduce los resultados de tu análisis de agua para recibir un diagnóstico instantáneo y un plan de acción.")

with st.sidebar:
    st.header("Parámetros del Agua")
    
    # --- Widgets de Entrada ---
    hierro = st.number_input("Hierro (Fe) en mg/L", min_value=0.0, value=0.1, step=0.1, help="Valor típico: < 0.3 mg/L")
    manganeso = st.number_input("Manganeso (Mn) en mg/L", min_value=0.0, value=0.02, step=0.01, help="Valor típico: < 0.05 mg/L")
    turbidez = st.number_input("Turbidez en NTU", min_value=0.0, value=0.5, step=0.5, help="Valor típico: < 1 NTU")
    dureza_total = st.number_input("Dureza Total (CaCO₃) en mg/L", min_value=0, value=120, step=10, help="Agua muy dura: > 180 mg/L")
    ph = st.number_input("pH", min_value=0.0, max_value=14.0, value=7.2, step=0.1, help="Rango ideal para desinfección: 6.0 - 7.0")
    e_coli = st.number_input("E. coli (UFC/100mL)", min_value=0, value=0, step=1, help="Debe ser 0 para agua potable")
    coliformes_totales = st.number_input("Coliformes Totales (UFC/100mL)", min_value=0, value=0, step=1, help="Debe ser 0 para agua potable")
    sdt = st.number_input("Sólidos Disueltos Totales (SDT) en ppm", min_value=0, value=300, step=50, help="Problemas digestivos: > 1500 ppm")
    sulfatos = st.number_input("Sulfatos (SO₄²⁻) en ppm", min_value=0, value=50, step=10, help="Límite recomendado: < 250 ppm")

    analizar_btn = st.button("Analizar Calidad del Agua", type="primary", use_container_width=True)


# --- Lógica de Visualización de Resultados ---

if analizar_btn:
    datos_usuario = {
        "hierro": hierro,
        "manganeso": manganeso,
        "turbidez": turbidez,
        "dureza_total": dureza_total,
        "ph": ph,
        "e_coli": e_coli,
        "coliformes_totales": coliformes_totales,
        "sdt": sdt,
        "sulfatos": sulfatos
    }
    
    diagnosticos = analizar_calidad_agua(datos_usuario)
    st.session_state['diagnosticos'] = diagnosticos
    st.session_state['datos_usuario'] = datos_usuario

if 'diagnosticos' in st.session_state:
    diagnosticos = st.session_state['diagnosticos']
    
    st.header("Resultados del Análisis")

    if not diagnosticos:
        st.success("✅ ¡Excelente! La calidad de tu agua cumple con los parámetros analizados.")
    else:
        for i, diag in enumerate(diagnosticos):
            with st.expander(f"**{diag['titulo']}**", expanded=True):
                if diag['tipo'] == 'error':
                    st.error(f"**DIAGNÓSTICO:** {diag['titulo']}")
                elif diag['tipo'] == 'warning':
                    st.warning(f"**DIAGNÓSTICO:** {diag['titulo']}")
                
                st.subheader("Riesgos Potenciales")
                st.markdown(diag['riesgos'])
                
                st.subheader("Plan de Acción Recomendado")
                st.markdown(diag['acciones'])
    
    # Botón de descarga de PDF
    pdf_bytes = generar_pdf(st.session_state['datos_usuario'], diagnosticos)
    st.download_button(
        label="📄 Descargar Reporte en PDF",
        data=pdf_bytes,
        file_name=f"reporte_calidad_agua_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/octet-stream"
    )
