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

# --- Funciones de Lógica y Análisis (sin cambios) ---
def analizar_calidad_agua(datos):
    diagnosticos = []
    
    # Verificación de Límite Máximo de Cloro
    if datos.get("cloro_libre", 0) > 5.0:
        diagnosticos.append({"tipo": "error", "titulo": "🚨 DIAGNÓSTICO: Nivel de Cloro Excesivo y Peligroso", "riesgos": "- **Toxicidad para las Aves.**\n- **Corrosión Acelerada de Equipos.**", "acciones": "1. **SUSPENDER LA DOSIFICACIÓN INMEDIATAMENTE.**\n2. **Purgar el Sistema.**\n3. **Revisar el Dosificador.**"})
        return diagnosticos

    # Análisis de ORP si el dato está disponible
    if "orp" in datos:
        if datos.get("cloro_libre", 0) <= 0:
            diagnosticos.append({"tipo": "warning", "titulo": "⚠️ DIAGNÓSTICO: Lectura de ORP no Confiable", "riesgos": "- **Sin Desinfectante Activo:** La lectura de ORP no es válida sin un residual de cloro libre.", "acciones": "1. **Establecer un Residual de Cloro.**\n2. **Volver a Medir ORP.**"})
        elif datos["orp"] > 850:
            diagnosticos.append({"tipo": "warning", "titulo": "⚠️ DIAGNÓSTICO: Potencial Oxidativo Excesivo (ORP Muy Alto)", "riesgos": "- **Riesgo Alto de Corrosión.**\n- **Posible Error de Medición.**", "acciones": "1. **VERIFICAR EL SENSOR DE ORP.**\n2. **Revisar Dosificación.**"})
        elif datos["orp"] >= 650:
            diagnosticos.append({"tipo": "success", "titulo": "✅ DIAGNÓSTICO: Excelente Potencial de Desinfección (ORP)", "riesgos": "- **Desinfección Rápida y Eficaz.**\n- **Importante:** Válido solo con Cloro y pH en rangos óptimos.", "acciones": "1. **Mantener Parámetros.**"})
        elif 200 <= datos["orp"] < 650:
            diagnosticos.append({"tipo": "warning", "titulo": "⚠️ DIAGNÓSTICO: Desinfección Lenta o Pobre (ORP)", "riesgos": "- **Eficacia Reducida del Desinfectante.**\n- **Causa Probable:** pH demasiado alto o alta carga de contaminantes.", "acciones": "1. **Verificar y Corregir pH.**\n2. **Considerar Supercloración.**"})
        else: # ORP < 200 mV
            diagnosticos.append({"tipo": "error", "titulo": "🚨 DIAGNÓSTICO: Nivel Sanitario Crítico (ORP)", "riesgos": "- **Sin Capacidad de Desinfección.**", "acciones": "1. **Acción Inmediata: NO USAR EL AGUA.**\n2. **Supercloración Masiva.**"})

    # Análisis de Nitratos y Nitritos si los datos están disponibles
    if datos.get("nitratos", 0) > 10 or datos.get("nitritos", 0) > 1:
        diagnosticos.append({"tipo": "error", "titulo": "🚨 DIAGNÓSTICO: Contaminación por Nitratos/Nitritos", "riesgos": "- **Riesgo de Metahemoglobinemia.**\n- **Indicador de Contaminación por fertilizantes o desechos.**", "acciones": "1. **Buscar Fuente de Agua Alternativa.**\n2. **Identificar la Fuente de Contaminación.**\n3. **Tratamiento a Largo Plazo (RO).**"})

    # El resto de la lógica comprueba si la clave existe antes de analizar
    if datos.get("e_coli", 0) > 0 or datos.get("coliformes_totales", 0) > 0:
        diagnosticos.append({"tipo": "error", "titulo": "🔴 DIAGNÓSTICO: Contaminación Microbiológica Crítica", "riesgos": "- **Riesgo Sanitario Extremo.**", "acciones": "1. **No Consumir el Agua.**\n2. **Desinfección Urgente.**"})
    
    cloro_libre = datos.get("cloro_libre")
    cloro_total = datos.get("cloro_total")
    if cloro_libre is not None and cloro_total is not None:
        if cloro_libre < 1.0 and cloro_libre > 0:
            diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Nivel de Cloro Libre Insuficiente", "riesgos": "- **Desinfección Ineficaz.**", "acciones": "1. **Aumentar Dosificación de Cloro.**"})
        elif cloro_total > 0 and (cloro_libre / cloro_total) < 0.85:
            diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Alta Demanda de Cloro (Posible Biofilm)", "riesgos": "- **Fuerte indicio de biofilm.**", "acciones": "1. **Supercloración de Choque.**"})

    if datos.get("hierro", 0) > 1.0:
        diagnosticos.append({"tipo": "error", "titulo": "🔴 DIAGNÓSTICO: Contaminación Severa por Hierro y Ferrobacterias", "riesgos": "- **Infestación por Ferrobacterias y Biofilm.**\n- **Corrosión Acelerada.**", "acciones": "1. **Desinfección de Choque y Limpieza.**\n2. **Instalar Tratamiento de Oxidación/Filtración.**"})
    elif datos.get("hierro", 0) > 0.3 or datos.get("manganeso", 0) > 0.05:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Riesgo por Metales", "riesgos": "- **Problemas Estéticos y acumulación.**", "acciones": "1. **Sistema de Oxidación/Filtración.**"})
    
    if datos.get("color_aparente", 0) > 15:
        riesgo_color = "- **Rechazo por parte de los animales.**\n"
        if datos.get("turbidez", 0) > 1.0 or datos.get("hierro", 0) > 0.3:
            riesgo_color += "- **Causa Probable:** Sólidos suspendidos."
            accion_color = "1. **Filtración Física (sedimentos o multimedia).**"
        else:
            riesgo_color += "- **Causa Probable:** Materia orgánica disuelta (taninos)."
            accion_color = "1. **Filtración con Carbón Activado.**"
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Color Elevado", "riesgos": riesgo_color, "acciones": accion_color})

    if datos.get("turbidez", 0) > 1.0:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Turbidez Elevada", "riesgos": "- **Protección de Patógenos.**", "acciones": "1. **Filtro de Sedimentos o Multimedia.**"})
    
    if "ph" in datos and not (6.0 <= datos["ph"] <= 7.0):
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: pH Fuera de Rango Óptimo para Desinfección", "riesgos": "- **Baja Eficacia del Cloro.**", "acciones": "1. **Ajuste de pH.**"})

    if datos.get("dureza_total", 0) > 180:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNÓSTICO: Agua Muy Dura", "riesgos": "- **Incrustaciones Severas.**", "acciones": "1. **Instalar un Ablandador de Agua.**"})

    if datos.get("sdt", 0) > 1500 or datos.get("sulfatos", 0) > 250:
        diagnosticos.append({"tipo": "warning", "titulo": "🟡 DIAGNóstico: Niveles Elevados de Sales Disueltas", "riesgos": "- **Sabor Salino o Amargo.**", "acciones": "1. **Ósmosis Inversa (RO).**"})
        
    return diagnosticos

# --- Clases y Funciones de PDF (sin cambios) ---
class PDF(FPDF):
    def header(self):
        try: self.image('log_agua_alb.png', 10, 8, 33)
        except FileNotFoundError: pass 
        self.set_font('Arial', 'B', 15); self.cell(80); self.cell(30, 10, 'Reporte de Calidad del Agua', 0, 0, 'C'); self.set_font('Arial', '', 8); self.ln(5); self.cell(80); self.cell(30, 10, f'Fecha de Emision: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C'); self.ln(20)
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
    pdf.ln(10); pdf.set_font('Arial', 'I', 8); pdf.set_text_color(128, 128, 128)
    disclaimer_text = ("Nota de Responsabilidad: Esta es una herramienta de apoyo para uso en granja. " "La utilización de los resultados es de su exclusiva responsabilidad. No sustituye la asesoría profesional " "y Albateq S.A. no se hace responsable por las decisiones tomadas con base en la información aquí presentada.\n\n" "Desarrollado por la Dirección Técnica de Albateq | dtecnico@albateq.com")
    disclaimer_cleaned = disclaimer_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 4, disclaimer_cleaned, align='C')
    return bytes(pdf.output())

# --- Interfaz de Usuario (Streamlit) ---
try:
    st.image("log_PEQ.png", width=100)
except FileNotFoundError: st.warning("No se encontró 'log_PEQ.png'.")
st.title("Asistente de Calidad del Agua")
st.markdown("Introduce los resultados de tu análisis de agua para recibir un diagnóstico instantáneo y un plan de acción.")

with st.sidebar:
    # --- LOGO AÑADIDO DE NUEVO ---
    try:
        st.image("log_agua_alb.png", use_container_width=True)
    except FileNotFoundError:
        st.warning("No se encontró 'log_agua_alb.png'.")
    
    st.divider()

    # --- Calculadora de Capacidad en la Barra Lateral ---
    if st.toggle("Activar Calculadora de Capacidad"):
        with st.form("capacity_form"):
            st.markdown("#### Calculadora de Consumo")
            col1, col2 = st.columns(2)
            with col1:
                num_galpones = st.number_input("Nº de galpones", min_value=1, value=4, step=1)
                consumo_ave_dia = st.number_input("Consumo (L/ave/día)", min_value=0.0, value=0.25, step=0.01, format="%.2f")
            with col2:
                aves_por_galpon = st.number_input("Aves por galpón", min_value=1, value=10000, step=100)
                horas_planta = st.number_input("Horas de planta/día", min_value=1, max_value=24, value=8, step=1)
            submitted = st.form_submit_button("Calcular")
            
            if submitted:
                total_aves = num_galpones * aves_por_galpon
                consumo_total_diario = total_aves * consumo_ave_dia
                capacidad_planta_hora = consumo_total_diario / horas_planta
                st.markdown("---")
                st.metric("Consumo Total Diario", f"{consumo_total_diario:,.0f} L/día")
                st.metric("Capacidad de Planta Requerida", f"{capacidad_planta_hora:,.0f} L/hora")
    
    st.divider()

    st.header("Análisis de Calidad del Agua")
    modo_analisis = st.radio("Modo de Análisis", ["Rápido (pH y Cloro)", "Completo (Todos los parámetros)"], horizontal=True, label_visibility="collapsed")
    datos_usuario = {}
    st.subheader("1. Desinfección")
    datos_usuario["ph"] = st.number_input("pH", 0.0, 14.0, 7.2, 0.1, help="Rango ideal para desinfección con cloro: 6.0 - 7.0")
    datos_usuario["cloro_libre"] = st.number_input("Cloro Libre (mg/L)", 0.0, 500.0, 1.5, 0.1, help="Rango ideal para bebida: 1.0 - 4.0 mg/L")
    datos_usuario["cloro_total"] = st.number_input("Cloro Total (mg/L)", 0.0, 500.0, 1.6, 0.1, help="Debe ser igual o mayor que el Cloro Libre")

    if modo_analisis == "Completo (Todos los parámetros)":
        st.divider()
        st.subheader("2. Contaminantes Químicos")
        datos_usuario["nitratos"] = st.number_input("Nitratos (NO₃⁻) en ppm", min_value=0.0, value=5.0, step=1.0, help="Límite máximo: 10 ppm")
        datos_usuario["nitritos"] = st.number_input("Nitritos (NO₂⁻) en ppm", min_value=0.0, value=0.0, step=0.1, help="Límite máximo: 1 ppm")
        st.divider()
        st.subheader("3. Parámetros Físicos y Estéticos")
        datos_usuario["hierro"] = st.number_input("Hierro (Fe) en mg/L", 0.0, value=0.1, step=0.1, help="Límite estético: < 0.3 mg/L")
        datos_usuario["manganeso"] = st.number_input("Manganeso (Mn) en mg/L", 0.0, value=0.02, step=0.01, help="Límite estético: < 0.05 mg/L")
        datos_usuario["turbidez"] = st.number_input("Turbidez en NTU", 0.0, 0.5, 0.5, help="Límite para desinfección eficaz: < 1 NTU")
        datos_usuario["color_aparente"] = st.number_input("Color Aparente (U. Pt-Co)", min_value=0, value=10, step=5, help="Límite estético: 15 U. Pt-Co")
        st.divider()
        st.subheader("4. Parámetros Generales")
        datos_usuario["dureza_total"] = st.number_input("Dureza Total (CaCO₃) en mg/L", 0, 120, 10, help="Agua muy dura: > 180 mg/L")
        datos_usuario["sdt"] = st.number_input("Sólidos Disueltos Totales (SDT) en ppm", 0, 300, 50, help="Límite recomendado: < 1000 ppm")
        datos_usuario["sulfatos"] = st.number_input("Sulfatos (SO₄²⁻) en ppm", 0, 50, 10, help="Límite recomendado: < 250 ppm")
        st.divider()
        st.subheader("5. Microbiología")
        datos_usuario["e_coli"] = st.number_input("E. coli (UFC/100mL)", min_value=0, value=0, step=1, help="Debe ser 0 para agua potable")
        datos_usuario["coliformes_totales"] = st.number_input("Coliformes Totales (UFC/100mL)", min_value=0, value=0, step=1, help="Debe ser 0 para agua potable")
        st.divider()
        st.subheader("6. Potencial de Desinfección")
        datos_usuario["orp"] = st.number_input("ORP (Potencial de Óxido-Reducción) en mV", -500, 1200, 650, 10, help="Ideal: > +650 mV (con cloro). Alerta Corrosión: > +850 mV.")
    
    st.divider()
    analizar_btn = st.button("Analizar Calidad del Agua", type="primary", use_container_width=True)

# --- Lógica de Visualización de Resultados ---
if analizar_btn:
    if datos_usuario["cloro_total"] < datos_usuario["cloro_libre"]:
        st.error("Error: El Cloro Total no puede ser menor que el Cloro Libre.")
    else:
        diagnosticos = analizar_calidad_agua(datos_usuario)
        st.session_state['diagnosticos'] = diagnosticos
        st.session_state['datos_usuario'] = datos_usuario
        st.session_state['modo_analisis_ejecutado'] = modo_analisis

if 'diagnosticos' in st.session_state:
    st.header("Resultados del Análisis de Calidad")
    diagnosticos = st.session_state['diagnosticos']
    datos_actuales = st.session_state['datos_usuario']
    if not diagnosticos:
        st.success("✅ ¡Excelente! La calidad de tu agua cumple con los parámetros analizados.")
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
    
    if st.session_state.get('modo_analisis_ejecutado') == "Rápido (pH y Cloro)":
        parametros_todos = ["nitratos", "nitritos", "hierro", "manganeso", "turbidez", "color_aparente", "dureza_total", "sdt", "sulfatos", "e_coli", "coliformes_totales", "orp"]
        parametros_faltantes = [p.replace("_", " ").title() for p in parametros_todos if p not in datos_actuales]
        if parametros_faltantes:
            st.info(f"**Para un análisis más completo**, te recomendamos medir también: **{', '.join(parametros_faltantes)}**.")

    pdf_bytes = generar_pdf(datos_actuales, diagnosticos)
    st.download_button("📄 Descargar Reporte en PDF", pdf_bytes, f"reporte_calidad_agua_{datetime.now().strftime('%Y%m%d')}.pdf", "application/pdf")
    st.divider()
    st.info("""**Nota de Responsabilidad:** Esta es una herramienta de apoyo para uso en granja...""")
    st.markdown("<div style='text-align: center; font-size: small;'>Desarrollado por la Dirección Técnica...</div>", unsafe_allow_html=True)
