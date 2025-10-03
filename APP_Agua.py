# app.py
import streamlit as st
from fpdf import FPDF
from datetime import datetime
import re

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Asistente de Calidad del Agua",
    page_icon="logo_albateq-removebg-preview.png",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- Funciones de Lógica y Análisis ---
def analizar_calidad_agua(datos):
    """
    Analiza los datos del agua basándose en un árbol de decisión y devuelve una lista de diagnósticos.
    """
    diagnosticos = []
    
    # --- Análisis de ORP (con contexto de pH y Cloro) ---
    if datos["orp"] >= 650:
        diagnosticos.append({
            "tipo": "success",
            "titulo": "✅ DIAGNÓSTICO: Excelente Potencial de Desinfección (ORP)",
            "riesgos": """
                - **Desinfección Rápida y Eficaz:** Un ORP superior a +650 mV indica que el desinfectante es altamente activo y capaz de eliminar patógenos de forma casi instantánea.
                - **Agua Sanitaria:** El agua se encuentra en un estado oxidante, lo que previene el crecimiento microbiano.
                - **Importante:** Este valor es significativo solo si se acompaña de un nivel de **Cloro Libre adecuado (>1.0 mg/L)** y un **pH en el rango óptimo (6.0-7.0)**.
            """,
            "acciones": """
                1. **Mantener Parámetros:** Continuar con las buenas prácticas de dosificación y control de pH para mantener este excelente nivel de ORP.
                2. **Monitoreo Regular:** El ORP puede cambiar rápidamente. Es recomendable un monitoreo constante para asegurar que se mantenga en el rango ideal.
            """
        })
    elif 200 <= datos["orp"] < 650:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "⚠️ DIAGNÓSTICO: Desinfección Lenta o Pobre (ORP)",
            "riesgos": """
                - **Eficacia Reducida del Desinfectante:** La desinfección no es instantánea. Ciertos patógenos podrían sobrevivir.
                - **Causa Probable:** Un ORP bajo, incluso con cloro, generalmente indica un **pH demasiado alto (>7.5)** o una alta carga de contaminantes orgánicos (biofilm) que consumen el poder del desinfectante.
                - **Análisis Incompleto:** Una medida de ORP por sí sola es un análisis incompleto. Debe validarse siempre con los niveles de Cloro y pH.
            """,
            "acciones": """
                1. **Verificar y Corregir pH (Acción Prioritaria):** Asegurarse de que el pH esté en el rango ideal (6.0 - 7.0 para cloro) para maximizar la eficacia del desinfectante.
                2. **Considerar Supercloración:** Si el pH es correcto, el bajo ORP indica una alta demanda. Realizar una supercloración de choque para oxidar los contaminantes.
                3. **Revisar Filtración:** Un sistema de filtrado ineficiente puede dejar pasar contaminantes que consumen el poder del desinfectante.
            """
        })
    else: # ORP < 200 mV
        diagnosticos.append({
            "tipo": "error",
            "titulo": "🚨 DIAGNÓSTICO: Nivel Sanitario Crítico (ORP)",
            "riesgos": """
                - **Sin Capacidad de Desinfección:** El agua no puede eliminar patógenos. El riesgo de transmisión de enfermedades es extremadamente alto.
                - **Condiciones Reductoras:** El agua favorece el crecimiento de bacterias anaeróbicas, que pueden incluir especies dañinas y causar malos olores.
                - **Agua No Apta para Consumo:** Bajo ninguna circunstancia se debe consumir o usar esta agua, independientemente de la lectura de cloro.
            """,
            "acciones": """
                1. **Acción Inmediata: NO USAR EL AGUA.**
                2. **Supercloración Masiva y Urgente:** Es necesario aplicar una dosis muy alta de un oxidante fuerte (como cloro) para eliminar la carga de contaminantes y elevar el ORP a un nivel seguro.
                3. **Identificar y Eliminar la Fuente de Contaminación:** Realizar una inspección completa del sistema para encontrar la causa raíz del problema.
            """
        })

    # 1. Análisis de Microbiología
    if datos["e_coli"] > 0 or datos["coliformes_totales"] > 0:
        diagnosticos.append({
            "tipo": "error",
            "titulo": "🔴 DIAGNÓSTICO: Contaminación Microbiológica Crítica",
            "riesgos": """
                - **Riesgo Sanitario Extremo:** La presencia de E. coli o coliformes totales indica contaminación fecal.
                - **Enfermedades Graves:** Puede causar enfermedades gastrointestinales severas, infecciones y otras condiciones graves.
            """,
            "acciones": """
                1. **No Consumir el Agua:** Suspender inmediatamente el uso del agua para beber o cocinar.
                2. **Desinfección Urgente:** Aplicar un tratamiento de choque con cloro (supercloración) en la fuente de agua.
                3. **Identificar la Fuente:** Inspeccionar el sistema en busca de posibles puntos de contaminación.
            """
        })

    # 2. Análisis de Desinfección por Cloro
    if datos["cloro_libre"] < 1.0:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: Nivel de Cloro Libre Insuficiente",
            "riesgos": "- **Desinfección Ineficaz:** No se garantiza la eliminación de virus y bacterias.\n- **Riesgo de Crecimiento Microbiológico:** El agua no tiene protección residual.",
            "acciones": "1. **Aumentar Dosificación de Cloro:** Ajustar para mantener un residual de cloro libre entre 1.0 y 3.0 mg/L.\n2. **Verificar Demanda de Cloro:** Considerar un tratamiento de choque si el cloro se consume rápidamente."
        })
    elif datos["cloro_total"] > 0 and (datos["cloro_libre"] / datos["cloro_total"]) < 0.85:
        cloro_combinado = datos["cloro_total"] - datos["cloro_libre"]
        proporcion_libre = (datos["cloro_libre"] / datos["cloro_total"]) * 100
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: Alta Demanda de Cloro (Posible Biofilm)",
            "riesgos": f"- **Proporción de Cloro Libre:** {proporcion_libre:.1f}% (Ideal: > 85%).\n- **Nivel de Cloro Combinado:** {cloro_combinado:.2f} mg/L.\n- **Causa Probable:** Fuerte indicio de **biofilm** o alta materia orgánica en el agua.",
            "acciones": "1. **Supercloración de Choque:** Aplicar una dosis alta y sostenida para eliminar el biofilm.\n2. **Investigar el Sistema:** Inspeccionar depósitos y puntos muertos de la red."
        })

    # 3. Análisis de Metales
    if datos["hierro"] > 1.0:
        diagnosticos.append({
            "tipo": "error",
            "titulo": "🔴 DIAGNÓSTICO: Contaminación Severa por Hierro y Ferrobacterias",
            "riesgos": "- **Infestación por Ferrobacterias:** Caldo de cultivo ideal para bacterias que se alimentan de hierro.\n- **Formación de Biofilm (Baba):** Obstruye tuberías, bombas y filtros.\n- **Problemas Graves de Olor, Sabor y Color.**\n- **Corrosión Acelerada (MIC).**",
            "acciones": "1. **Desinfección de Choque y Limpieza (PRIORITARIO):** Supercloración masiva (20-50 mg/L) y purgado intenso.\n2. **Instalar Tratamiento de Oxidación/Filtración:** Colocar un dosificador de cloro antes de un filtro de arena verde o zeolita para remover el hierro y prevenir re-infestación.\n3. **Mantenimiento:** Realizar cloraciones y retrolavados periódicos."
        })
    elif datos["hierro"] > 0.3 or datos["manganeso"] > 0.05:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: Riesgo por Metales",
            "riesgos": "- **Problemas Estéticos:** Color, sabor metálico y manchas.\n- **Acumulación en Tuberías:** Favorece el crecimiento de biofilm.",
            "acciones": "1. **Sistema de Oxidación/Filtración:** Usar cloro o aire para oxidar los metales antes de un filtro de arena verde."
        })
        
    # 4. Análisis de Parámetros Físico-Químicos
    if datos["turbidez"] > 1.0:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: Turbidez Elevada",
            "riesgos": "- **Protección de Patógenos:** Las partículas protegen a los microorganismos del cloro.\n- **Ineficiencia de Desinfección.**",
            "acciones": "1. **Filtro de Sedimentos o Multimedia:** Instalar un sistema de filtración para eliminar partículas."
        })
        
    if not (6.0 <= datos["ph"] <= 7.0):
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: pH Fuera de Rango Óptimo para Desinfección",
            "riesgos": "- **Baja Eficacia del Cloro:** Un pH > 7.5 reduce drásticamente el poder desinfectante.\n- **Corrosión o Incrustaciones:** pH < 6.5 es corrosivo; pH > 8.5 causa incrustaciones.",
            "acciones": "1. **Ajuste de pH:** Utilizar un sistema de inyección de químicos para corregir el pH antes de la desinfección."
        })

    # 5. Análisis de Sales y Minerales
    if datos["dureza_total"] > 180:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNÓSTICO: Agua Muy Dura",
            "riesgos": "- **Incrustaciones Severas:** Acumulación de sarro en tuberías y equipos.\n- **Bajo Rendimiento de Jabones.**",
            "acciones": "1. **Instalar un Ablandador de Agua:** Un sistema de intercambio iónico es la solución más efectiva."
        })
        
    if datos["sdt"] > 1500 or datos["sulfatos"] > 250:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "🟡 DIAGNóstico: Niveles Elevados de Sales Disueltas",
            "riesgos": "- **Sabor Salino o Amargo.**\n- **Efecto Laxante.**",
            "acciones": "1. **Ósmosis Inversa (RO):** Es el método más efectivo para reducir significativamente los SDT y sulfatos."
        })
        
    return diagnosticos

# --- Clase para Generación de PDF (sin cambios) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Reporte de Calidad del Agua', 0, 1, 'C')
        self.set_font('Arial', '', 8)
        self.cell(0, 10, f'Fecha de Emision: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        body_cleaned = body.encode('latin-1', 'replace').decode('latin-1')
        self.multi_cell(0, 5, body_cleaned)
        self.ln()

    def add_diagnostic_section(self, tipo, titulo, riesgos, acciones):
        if tipo == "error":
            self.set_text_color(220, 50, 50)
        elif tipo == "warning":
            self.set_text_color(255, 193, 7)
        elif tipo == "success":
            self.set_text_color(40, 167, 69)
        else:
            self.set_text_color(0, 0, 0)

        titulo_pdf = re.sub(r'[^\w\s\.:\-%()]', '', titulo)
        self.set_font('Arial', 'B', 11)
        self.multi_cell(0, 5, titulo_pdf)
        self.set_text_color(0, 0, 0)
        self.ln(2)
        riesgos_pdf = riesgos.encode('latin-1', 'replace').decode('latin-1')
        acciones_pdf = acciones.encode('latin-1', 'replace').decode('latin-1')
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "Riesgos Potenciales:")
        self.ln()
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, riesgos_pdf)
        self.ln(2)
        self.set_font('Arial', 'B', 10)
        self.cell(0, 5, "Plan de Accion Recomendado:")
        self.ln()
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 5, acciones_pdf)
        self.ln(5)

def generar_pdf(datos_entrada, resultados):
    pdf = PDF()
    pdf.add_page()
    pdf.chapter_title("1. Parametros Ingresados por el Usuario")
    body = ""
    for key, value in datos_entrada.items():
        formatted_key = key.replace("_", " ").title()
        body += f"- {formatted_key}: {value}\n"
    pdf.chapter_body(body)
    pdf.chapter_title("2. Diagnosticos y Recomendaciones")
    if not resultados:
        pdf.set_text_color(40, 167, 69)
        pdf.set_font('Arial', 'B', 12)
        mensaje_exito = "¡Excelente! La calidad de tu agua cumple con los parametros analizados."
        pdf.multi_cell(0, 5, mensaje_exito)
        pdf.set_text_color(0, 0, 0)
    else:
        for diag in resultados:
            pdf.add_diagnostic_section(diag["tipo"], diag["titulo"], diag["riesgos"], diag["acciones"])
    return bytes(pdf.output())

# --- Interfaz de Usuario (Streamlit) ---
try:
    st.image("log_PEQ.png", width=100)
except FileNotFoundError:
    st.warning("No se encontró el archivo 'log_PEQ.png'. Por favor, asegúrese de que esté en el directorio del repositorio.")

st.title("Asistente de Calidad del Agua")
st.markdown("Introduce los resultados de tu análisis de agua para recibir un diagnóstico instantáneo y un plan de acción.")

with st.sidebar:
    st.header("Parámetros del Agua")
    
    orp = st.number_input("ORP (Potencial de Óxido-Reducción) en mV", min_value=-500, max_value=1000, value=650, step=10, help="Ideal para desinfección: > +650 mV")
    cloro_libre = st.number_input("Cloro Libre (mg/L)", min_value=0.0, value=1.5, step=0.1, help="Rango ideal: 1.0 - 3.0 mg/L")
    cloro_total = st.number_input("Cloro Total (mg/L)", min_value=0.0, value=1.6, step=0.1, help="Debe ser igual o mayor que el Cloro Libre")
    ph = st.number_input("pH", min_value=0.0, max_value=14.0, value=7.2, step=0.1, help="Rango ideal para desinfección: 6.0 - 7.0")
    hierro = st.number_input("Hierro (Fe) en mg/L", min_value=0.0, value=0.1, step=0.1, help="Valor típico: < 0.3 mg/L")
    manganeso = st.number_input("Manganeso (Mn) en mg/L", min_value=0.0, value=0.02, step=0.01, help="Valor típico: < 0.05 mg/L")
    turbidez = st.number_input("Turbidez en NTU", min_value=0.0, value=0.5, step=0.5, help="Valor típico: < 1 NTU")
    dureza_total = st.number_input("Dureza Total (CaCO₃) en mg/L", min_value=0, value=120, step=10, help="Agua muy dura: > 180 mg/L")
    e_coli = st.number_input("E. coli (UFC/100mL)", min_value=0, value=0, step=1, help="Debe ser 0 para agua potable")
    coliformes_totales = st.number_input("Coliformes Totales (UFC/100mL)", min_value=0, value=0, step=1, help="Debe ser 0 para agua potable")
    sdt = st.number_input("Sólidos Disueltos Totales (SDT) en ppm", min_value=0, value=300, step=50, help="Problemas digestivos: > 1500 ppm")
    sulfatos = st.number_input("Sulfatos (SO₄²⁻) en ppm", min_value=0, value=50, step=10, help="Límite recomendado: < 250 ppm")

    analizar_btn = st.button("Analizar Calidad del Agua", type="primary", use_container_width=True)

# --- Lógica de Visualización de Resultados ---
if analizar_btn:
    if cloro_total < cloro_libre:
        st.error("Error: El Cloro Total no puede ser menor que el Cloro Libre. Por favor, corrija los valores.")
    else:
        datos_usuario = {
            "orp": orp, "cloro_libre": cloro_libre, "cloro_total": cloro_total,
            "ph": ph, "hierro": hierro, "manganeso": manganeso,
            "turbidez": turbidez, "dureza_total": dureza_total, "e_coli": e_coli,
            "coliformes_totales": coliformes_totales, "sdt": sdt, "sulfatos": sulfatos
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
        order = {"error": 0, "warning": 1, "success": 2}
        diagnosticos.sort(key=lambda x: order.get(x['tipo'], 99))
        
        for diag in diagnosticos:
            with st.expander(f"**{diag['titulo']}**", expanded=True):
                if diag['tipo'] == 'error':
                    st.error(f"**DIAGNÓSTICO:** {diag['titulo']}")
                elif diag['tipo'] == 'warning':
                    st.warning(f"**DIAGNÓSTICO:** {diag['titulo']}")
                elif diag['tipo'] == 'success':
                    st.success(f"**DIAGNÓSTICO:** {diag['titulo']}")
                
                st.subheader("Riesgos Potenciales")
                st.markdown(diag['riesgos'])
                st.subheader("Plan de Acción Recomendado")
                st.markdown(diag['acciones'])
    
    if st.session_state.get('datos_usuario'):
        pdf_bytes = generar_pdf(st.session_state['datos_usuario'], diagnosticos)
        st.download_button(
            label="📄 Descargar Reporte en PDF",
            data=pdf_bytes,
            file_name=f"reporte_calidad_agua_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
    
    st.divider()

    # --- NUEVO: Nota de Responsabilidad ---
    st.info("""
    **Nota de Responsabilidad:** Esta es una herramienta de apoyo para uso en granja. 
    La utilización de los resultados es de su exclusiva responsabilidad. No sustituye la asesoría profesional 
    y Albateq S.A. no se hace responsable por las decisiones tomadas con base en la información aquí presentada.
    """)
    st.markdown("<div style='text-align: center;'>Desarrollado por la Dirección Técnica de Albateq | dtecnico@albateq.com</div>", unsafe_allow_html=True)
