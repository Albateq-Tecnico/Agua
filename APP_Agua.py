# app.py
import streamlit as st
from fpdf import FPDF
from datetime import datetime
import re

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
    
    # Verificación de Límite Máximo de Cloro (Máxima Prioridad)
    if datos["cloro_libre"] > 5.0:
        diagnosticos.append({
            "tipo": "error",
            "titulo": "🚨 DIAGNÓSTICO: Nivel de Cloro Excesivo y Peligroso",
            "riesgos": """
                - **Toxicidad para las Aves:** Este nivel de cloro es tóxico y causará rechazo del agua. **NO DEBE SER CONSUMIDA.**
                - **Corrosión Acelerada de Equipos:** La solución es extremadamente corrosiva y dañará rápidamente tuberías, bebederos y bombas.
            """,
            "acciones": """
                1. **SUSPENDER LA DOSIFICACIÓN INMEDIATAMENTE.**
                2. **Purgar el Sistema:** Vaciar las tuberías y rellenar con agua fresca hasta que los niveles vuelvan a un rango seguro (1-3 mg/L).
                3. **Revisar el Dosificador:** Verificar que el equipo de dosificación de cloro no esté fallando.
            """
        })
        return diagnosticos

    # Análisis de ORP
    if datos["cloro_libre"] <= 0:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "⚠️ DIAGNÓSTICO: Lectura de ORP no Confiable",
            "riesgos": "- **Sin Desinfectante Activo:** La lectura de ORP no es un indicador válido de desinfección si no hay un residual de cloro libre.\n- **Falsa Seguridad:** Un valor de ORP alto sin cloro puede dar una falsa sensación de seguridad.",
            "acciones": "1. **Establecer un Residual de Cloro:** La prioridad es dosificar cloro hasta alcanzar un nivel de Cloro Libre de al menos 1.0 mg/L.\n2. **Volver a Medir ORP:** Con un residual de cloro estable, la medida de ORP será confiable."
        })
    elif datos["orp"] > 850:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "⚠️ DIAGNÓSTICO: Potencial Oxidativo Excesivo (ORP Muy Alto)",
            "riesgos": "- **Riesgo Alto de Corrosión:** El agua es químicamente agresiva y acelera la degradación de tuberías, empaques y bebederos.\n- **Posible Error de Medición:** Valores tan altos pueden ser causados por una sonda de ORP mal calibrada.",
            "acciones": "1. **VERIFICAR EL SENSOR DE ORP:** Limpiar y recalibrar la sonda.\n2. **Revisar Dosificación:** Si la lectura es correcta, considere reducir la dosificación del oxidante."
        })
    elif datos["orp"] >= 650:
        diagnosticos.append({
            "tipo": "success",
            "titulo": "✅ DIAGNÓSTICO: Excelente Potencial de Desinfección (ORP)",
            "riesgos": "- **Desinfección Rápida y Eficaz:** El desinfectante es altamente activo.\n- **Importante:** Este valor es significativo solo con **Cloro Libre adecuado (1.0-4.0 mg/L)** y un **pH óptimo (6.0-7.0)**.",
            "acciones": "1. **Mantener Parámetros:** Continuar con las buenas prácticas de dosificación y control de pH."
        })
    elif 200 <= datos["orp"] < 650:
        diagnosticos.append({
            "tipo": "warning",
            "titulo": "⚠️ DIAGNÓSTICO: Desinfección Lenta o Pobre (ORP)",
            "riesgos": "- **Eficacia Reducida del Desinfectante:** La desinfección no es instantánea.\n- **Causa Probable:** pH demasiado alto (>7.5) o alta carga de contaminantes.",
            "acciones": "1. **Verificar y Corregir pH (Acción Prioritaria).**\n2. **Considerar Supercloración** si el pH es correcto."
        })
    else: # ORP < 200 mV
        diagnosticos.append({
            "tipo": "error",
            "titulo": "🚨 DIAGNÓSTICO: Nivel Sanitario Crítico (ORP)",
            "riesgos": "- **Sin Capacidad de Desinfección:** Riesgo extremadamente alto de enfermedades.\n- **Condiciones Reductoras:** Favorece el crecimiento de bacterias anaeróbicas.",
            "acciones": "1. **Acción Inmediata: NO USAR EL AGUA.**\n2. **Supercloración Masiva y Urgente.**"
        })

    # Análisis de Nitratos y Nitritos
    if datos["nitratos"] > 10 or datos["nitritos"] > 1:
        diagnosticos.append({
            "tipo": "error",
            "titulo": "🚨 DIAGNÓSTICO: Contaminación por Nitratos/Nitritos",
            "riesgos": "- **Riesgo de Metahemoglobinemia:** Limita la capacidad de la sangre para transportar oxígeno.\n- **Indicador de Contaminación:** Sugiere contaminación por fertilizantes o desechos animales.",
            "acciones": "1. **Buscar una Fuente de Agua Alternativa INMEDIATAMENTE.**\n2. **Identificar la Fuente de Contaminación.**\n3. **Tratamiento a Largo Plazo:** Considerar **Ósmosis Inversa (RO)**."
        })

    # El resto de la lógica sigue sin cambios...
    if datos["e_coli"] > 0 or datos["coliformes_totales"] > 0:
        diagnosticos.append({"tipo": "error", "titulo": "🔴 DIAGNÓSTICO: Contaminación Microbiológica Crítica", "riesgos": "- **Riesgo Sanitario Extremo:** Indica contaminación fecal.", "acciones": "1. **No Consumir el Agua.**\n2. **Desinfección Urgente.**"})
    if datos["cloro_libre"] < 1.0 and datos["cloro_libre"] > 0:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Nivel de Cloro Libre Insuficiente", "riesgos": "- **Desinfección Ineficaz.**", "acciones": "1. **Aumentar Dosificación de Cloro.**"})
    elif datos["cloro_total"] > 0 and (datos["cloro_libre"] / datos["cloro_total"]) < 0.85:
        cloro_combinado = datos["cloro_total"] - datos["cloro_libre"]; proporcion_libre = (datos["cloro_libre"] / datos["cloro_total"]) * 100
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Alta Demanda de Cloro (Posible Biofilm)", "riesgos": f"- **Proporción de Cloro Libre:** {proporcion_libre:.1f}% (Ideal: > 85%).\n- **Causa Probable:** Fuerte indicio de **biofilm**.", "acciones": "1. **Supercloración de Choque.**"})
    if datos["hierro"] > 1.0:
        diagnosticos.append({"tipo": "error", "titulo": "🔴 DIAGNÓSTICO: Contaminación Severa por Hierro y Ferrobacterias", "riesgos": "- **Infestación por Ferrobacterias.**\n- **Formación de Biofilm (Baba).**\n- **Corrosión Acelerada (MIC).**", "acciones": "1. **Desinfección de Choque y Limpieza (PRIORITARIO).**\n2. **Instalar Tratamiento de Oxidación/Filtración.**"})
    elif datos["hierro"] > 0.3 or datos["manganeso"] > 0.05:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Riesgo por Metales", "riesgos": "- **Problemas Estéticos.**\n- **Acumulación en Tuberías.**", "acciones": "1. **Sistema de Oxidación/Filtración.**"})
    if datos["color_aparente"] > 15:
        riesgo_color = "- **Rechazo por parte de los animales.**\n"
        if datos["turbidez"] > 1.0 or datos["hierro"] > 0.3:
            riesgo_color += "- **Causa Probable:** Sólidos suspendidos (arcilla, hierro oxidado)."
            accion_color = "1. **Filtración Física:** Utilizar un filtro de sedimentos o multimedia."
        else:
            riesgo_color += "- **Causa Probable:** Materia orgánica disuelta (taninos)."
            accion_color = "1. **Filtración con Carbón Activado.**\n2. **Oxidación Química.**"
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Color Elevado", "riesgos": riesgo_color, "acciones": accion_color})
    if datos["turbidez"] > 1.0:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Turbidez Elevada", "riesgos": "- **Protección de Patógenos.**", "acciones": "1. **Filtro de Sedimentos o Multimedia.**"})
    if not (6.0 <= datos["ph"] <= 7.0):
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: pH Fuera de Rango Óptimo para Desinfección", "riesgos": "- **Baja Eficacia del Cloro.**\n- **Corrosión o Incrustaciones.**", "acciones": "1. **Ajuste de pH.**"})
    if datos["dureza_total"] > 180:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Agua Muy Dura", "riesgos": "- **Incrustaciones Severas.**\n- **Bajo Rendimiento de Jabones.**", "acciones": "1. **Instalar un Ablandador de Agua.**"})
    if datos["sdt"] > 1500 or datos["sulfatos"] > 250:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNóstico: Niveles Elevados de Sales Disueltas", "riesgos": "- **Sabor Salino o Amargo.**\n- **Efecto Laxante.**", "acciones": "1. **Ósmosis Inversa (RO).**"})
    return diagnosticos

# --- Clases y Funciones de PDF (Sin cambios) ---
class PDF(FPDF):
    def header(self): self.set_font('Arial', 'B', 12); self.cell(0, 10, 'Reporte de Calidad del Agua', 0, 1, 'C'); self.set_font('Arial', '', 8); self.cell(0, 10, f'Fecha de Emision: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C'); self.ln(10)
    def footer(self): self.set_y(-15); self.set_font('Arial', 'I', 8); self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')
    def chapter_title(self, title): self.set_font('Arial', 'B', 12); self.cell(0, 10, title, 0, 1, 'L'); self.ln(4)
    def chapter_body(self, body): self.set_font('Arial', '', 10); body_cleaned = body.encode('latin-1', 'replace').decode('latin-1'); self.multi_cell(0, 5, body_cleaned); self.ln()
    def add_diagnostic_section(self, tipo, titulo, riesgos, acciones):
        if tipo == "error": self.set_text_color(220, 50, 50)
        elif tipo == "warning": self.set_text_color(255, 193, 7)
        elif tipo == "success": self.set_text_color(40, 167, 69)
        else: self.set_text_color(0, 0, 0)
        titulo_pdf = re.sub(r'[^\w\s\.:\-%()]', '', titulo)
        self.set_font('Arial', 'B', 11); self.multi_cell(0, 5, titulo_pdf); self.set_text_color(0, 0, 0); self.ln(2)
        riesgos_pdf = riesgos.encode('latin-1', 'replace').decode('latin-1'); acciones_pdf = acciones.encode('latin-1', 'replace').decode('latin-1')
        self.set_font('Arial', 'B', 10); self.cell(0, 5, "Riesgos Potenciales:"); self.ln(); self.set_font('Arial', '', 10); self.multi_cell(0, 5, riesgos_pdf); self.ln(2)
        self.set_font('Arial', 'B', 10); self.cell(0, 5, "Plan de Accion Recomendado:"); self.ln(); self.set_font('Arial', '', 10); self.multi_cell(0, 5, acciones_pdf); self.ln(5)

def generar_pdf(datos_entrada, resultados):
    pdf = PDF(); pdf.add_page(); pdf.chapter_title("1. Parametros Ingresados por el Usuario")
    body = ""; 
    for key, value in datos_entrada.items(): body += f"- {key.replace('_', ' ').title()}: {value}\n"
    pdf.chapter_body(body)
    pdf.chapter_title("2. Diagnosticos y Recomendaciones")
    if not resultados:
        pdf.set_text_color(40, 167, 69); pdf.set_font('Arial', 'B', 12); mensaje_exito = "¡Excelente! La calidad de tu agua cumple con los parametros analizados."
        pdf.multi_cell(0, 5, mensaje_exito); pdf.set_text_color(0, 0, 0)
    else:
        for diag in resultados: pdf.add_diagnostic_section(diag["tipo"], diag["titulo"], diag["riesgos"], diag["acciones"])
    return bytes(pdf.output())

# --- Interfaz de Usuario (Streamlit) ---
try:
    st.image("log_PEQ.png", width=100)
except FileNotFoundError: st.warning("No se encontró 'log_PEQ.png'.")
st.title("Asistente de Calidad del Agua")
st.markdown("Introduce los resultados de tu análisis de agua para recibir un diagnóstico instantáneo y un plan de acción.")

with st.sidebar:
    # --- IMAGEN DEL LOGO EN LA PARTE SUPERIOR DE LA BARRA LATERAL ---
    try:
        st.image("log_agua_alb.png", width=200) # Ajusta el width si es necesario
    except FileNotFoundError:
        st.warning("No se encontró 'log_agua_alb.png'. Asegúrate de que la imagen esté en el directorio correcto.")
    
    st.header("Parámetros del Agua")
    
    # --- NUEVO ORDEN DE ENTRADA ---
    st.subheader("1. Desinfección")
    ph = st.number_input("pH", 0.0, 14.0, 7.2, 0.1, help="Rango ideal para desinfección con cloro: 6.0 - 7.0")
    cloro_libre = st.number_input("Cloro Libre (mg/L)", 0.0, 500.0, 1.5, 0.1, help="Rango ideal para bebida: 1.0 - 4.0 mg/L")
    cloro_total = st.number_input("Cloro Total (mg/L)", 0.0, 500.0, 1.6, 0.1, help="Debe ser igual o mayor que el Cloro Libre")
    
    st.divider()
    st.subheader("2. Contaminantes Químicos")
    nitratos = st.number_input("Nitratos (NO₃⁻) en ppm", min_value=0.0, value=5.0, step=1.0, help="Límite máximo: 10 ppm")
    nitritos = st.number_input("Nitritos (NO₂⁻) en ppm", min_value=0.0, value=0.0, step=0.1, help="Límite máximo: 1 ppm")
    
    st.divider()
    st.subheader("3. Parámetros Físicos y Estéticos")
    hierro = st.number_input("Hierro (Fe) en mg/L", 0.0, value=0.1, step=0.1, help="Límite estético: < 0.3 mg/L")
    manganeso = st.number_input("Manganeso (Mn) en mg/L", 0.0, value=0.02, step=0.01, help="Límite estético: < 0.05 mg/L")
    turbidez = st.number_input("Turbidez en NTU", 0.0, 0.5, 0.5, help="Límite para desinfección eficaz: < 1 NTU")
    color_aparente = st.number_input("Color Aparente (U. Pt-Co)", min_value=0, value=10, step=5, help="Límite estético: 15 U. Pt-Co")
    
    st.divider()
    st.subheader("4. Parámetros Generales")
    dureza_total = st.number_input("Dureza Total (CaCO₃) en mg/L", 0, 120, 10, help="Agua muy dura: > 180 mg/L")
    sdt = st.number_input("Sólidos Disueltos Totales (SDT) en ppm", 0, 300, 50, help="Límite recomendado: < 1000 ppm")
    sulfatos = st.number_input("Sulfatos (SO₄²⁻) en ppm", 0, 50, 10, help="Límite recomendado: < 250 ppm")
    
    st.divider()
    st.subheader("5. Microbiología")
    e_coli = st.number_input("E. coli (UFC/100mL)", min_value=0, value=0, step=1, help="Debe ser 0 para agua potable")
    coliformes_totales = st.number_input("Coliformes Totales (UFC/100mL)", min_value=0, value=0, step=1, help="Debe ser 0 para agua potable")
    
    st.divider()
    st.subheader("6. Potencial de Desinfección")
    orp = st.number_input("ORP (Potencial de Óxido-Reducción) en mV", -500, 1200, 650, 10, help="Ideal: > +650 mV (con cloro). Alerta Corrosión: > +850 mV.")
    
    st.divider()
    analizar_btn = st.button("Analizar Calidad del Agua", type="primary", use_container_width=True)

# --- Lógica de Visualización de Resultados ---
if analizar_btn:
    if cloro_total < cloro_libre: st.error("Error: El Cloro Total no puede ser menor que el Cloro Libre.")
    else:
        datos_usuario = {
            "orp": orp, "cloro_libre": cloro_libre, "cloro_total": cloro_total, "ph": ph, 
            "nitratos": nitratos, "nitritos": nitritos, "hierro": hierro, "manganeso": manganeso, 
            "turbidez": turbidez, "color_aparente": color_aparente, "dureza_total": dureza_total, 
            "sdt": sdt, "sulfatos": sulfatos, "e_coli": e_coli, "coliformes_totales": coliformes_totales
        }
        diagnosticos = analizar_calidad_agua(datos_usuario)
        st.session_state['diagnosticos'] = diagnosticos
        st.session_state['datos_usuario'] = datos_usuario

if 'diagnosticos' in st.session_state:
    diagnosticos = st.session_state['diagnosticos']
    st.header("Resultados del Análisis")
    if not diagnosticos: st.success("✅ ¡Excelente! La calidad de tu agua cumple con los parámetros analizados.")
    else:
        order = {"error": 0, "warning": 1, "success": 2}
        diagnosticos.sort(key=lambda x: order.get(x['tipo'], 99))
        for diag in diagnosticos:
            with st.expander(f"**{diag['titulo']}**", expanded=True):
                if diag['tipo'] == 'error': st.error(f"**DIAGNÓSTICO:** {diag['titulo']}")
                elif diag['tipo'] == 'warning': st.warning(f"**DIAGNÓSTICO:** {diag['titulo']}")
                elif diag['tipo'] == 'success': st.success(f"**DIAGNÓSTICO:** {diag['titulo']}")
                st.subheader("Riesgos Potenciales"); st.markdown(diag['riesgos'], unsafe_allow_html=True)
                st.subheader("Plan de Acción Recomendado"); st.markdown(diag['acciones'], unsafe_allow_html=True)
    if st.session_state.get('datos_usuario'):
        pdf_bytes = generar_pdf(st.session_state['datos_usuario'], diagnosticos)
        st.download_button("📄 Descargar Reporte en PDF", pdf_bytes, f"reporte_calidad_agua_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
    st.divider()
    st.info("""**Nota de Responsabilidad:** Esta es una herramienta de apoyo para uso en granja. La utilización de los resultados es de su exclusiva responsabilidad. No sustituye la asesoría profesional y Albateq S.A. no se hace responsable por las decisiones tomadas con base en la información aquí presentada.""")
    st.markdown("<div style='text-align: center; font-size: small;'>Desarrollado por la Dirección Técnica de Albateq | dtecnico@albateq.com</div>", unsafe_allow_html=True)
