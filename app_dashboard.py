#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard Ejecutivo de Auditoría QA Automotriz con IA (Google Gemini 3.6 Flash)
Diseño Corporativo Oficial Autivo (ai based solutions).
"""

import os
import json
import base64
import zipfile
import pandas as pd
import streamlit as st
import importlib

import procesar_pdf
importlib.reload(procesar_pdf)
from procesar_pdf import (
    procesar_pipeline,
    cargar_api_key_guardada,
    CONFIG
)

# ==============================================================================
# GESTOR DE LOGOS OFICIALES AUTIVO
# ==============================================================================
def obtener_logo_html(tipo: str = "negro", ancho: int = 200) -> str:
    """Devuelve el código HTML del logo de Autivo en alta resolución."""
    # 1. Cargar archivo local de imagen si está en el repositorio
    archivo = "logo_autivo.png" if tipo == "negro" else "logo_autivo_blanco.png"
    if os.path.exists(archivo):
        try:
            with open(archivo, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                return f'<img src="data:image/png;base64,{b64}" style="max-width:{ancho}px; width:100%; height:auto;" alt="Autivo" />'
        except Exception:
            pass

    # 2. Cargar desde módulo auxiliar si existe
    try:
        from logos_data import LOGO_BLACK_B64, LOGO_WHITE_B64
        b64 = LOGO_BLACK_B64 if tipo == "negro" else LOGO_WHITE_B64
        if b64:
            return f'<img src="data:image/png;base64,{b64}" style="max-width:{ancho}px; width:100%; height:auto;" alt="Autivo" />'
    except Exception:
        pass

    # 3. Fallback tipográfico corporativo
    color = "#0F172A" if tipo == "negro" else "#FFFFFF"
    sub_color = "#64748B" if tipo == "negro" else "#94A3B8"
    return f'''
    <div style="font-family:'Plus Jakarta Sans', sans-serif; text-align:center;">
        <span style="font-size:1.6rem; font-weight:800; color:{color}; letter-spacing:-0.5px;">autivo</span>
        <div style="font-size:0.75rem; font-weight:600; color:{sub_color}; letter-spacing:1px; text-transform:lowercase; margin-top:-4px;">ai based solutions</div>
    </div>
    '''

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Autivo QA - Portal Ejecutivo",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS ejecutivos y profesionales de nivel Enterprise
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #F8FAFC;
    }

    /* Banner Superior Ejecutivo */
    .hero-banner {
        background: linear-gradient(135deg, #09121F 0%, #152A4A 100%);
        border-radius: 16px;
        padding: 28px 34px;
        margin-bottom: 24px;
        color: white;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.15);
        border-left: 6px solid #3B82F6;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 20px;
    }
    .hero-badge {
        background: rgba(59, 130, 246, 0.22);
        color: #93C5FD;
        padding: 5px 14px;
        border-radius: 30px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 8px;
        border: 1px solid rgba(147, 197, 253, 0.3);
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #FFFFFF;
        margin: 0 0 6px 0;
        letter-spacing: -0.5px;
    }
    .hero-desc {
        font-size: 0.95rem;
        color: #CBD5E1;
        margin: 0;
        font-weight: 400;
    }

    /* Tarjetas Métricas Ejecutivas */
    .kpi-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 22px 20px;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
        border: 1px solid #E2E8F0;
        transition: all 0.25s ease-in-out;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px -4px rgba(0, 0, 0, 0.09);
    }
    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }
    .kpi-lbl {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .kpi-icon {
        font-size: 1.3rem;
        padding: 8px;
        border-radius: 10px;
        background: #F1F5F9;
    }
    .kpi-val {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
        margin-bottom: 6px;
    }
    .kpi-sub {
        font-size: 0.82rem;
        color: #94A3B8;
        font-weight: 500;
    }

    .kpi-accent-blue { border-top: 4px solid #3B82F6; }
    .kpi-accent-green { border-top: 4px solid #10B981; }
    .kpi-accent-red { border-top: 4px solid #EF4444; }
    .kpi-accent-purple { border-top: 4px solid #8B5CF6; }

    /* Badges de Estado */
    .badge-ok {
        background-color: #DCFCE7;
        color: #15803D;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-block;
        font-size: 0.82rem;
        border: 1px solid #BBF7D0;
    }
    .badge-fail {
        background-color: #FEE2E2;
        color: #B91C1C;
        font-weight: 700;
        padding: 5px 12px;
        border-radius: 20px;
        display: inline-block;
        font-size: 0.82rem;
        border: 1px solid #FECACA;
    }

    /* Tarjeta de Login */
    .login-box {
        background: #FFFFFF;
        border-radius: 20px;
        padding: 40px 36px;
        box-shadow: 0 20px 40px -15px rgba(15, 23, 42, 0.12);
        border: 1px solid #E2E8F0;
        text-align: center;
        margin-top: 40px;
    }

    /* Ficha Técnica */
    .audit-spec-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }
    .audit-spec-row {
        display: flex;
        justify-content: space-between;
        padding: 10px 0;
        border-bottom: 1px solid #F1F5F9;
        font-size: 0.9rem;
    }
    .audit-spec-lbl {
        color: #64748B;
        font-weight: 600;
    }
    .audit-spec-val {
        color: #0F172A;
        font-weight: 700;
    }

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SISTEMA DE AUTENTICACIÓN / PANTALLA DE LOGIN
# ==============================================================================
def verificar_credenciales(email: str, password: str) -> bool:
    email_valido = "santiagourrutiahojas@gmail.com"
    pass_valida = "Santiago2608#"

    try:
        if hasattr(st, "secrets"):
            email_valido = str(st.secrets.get("LOGIN_EMAIL", email_valido)).strip()
            pass_valida = str(st.secrets.get("LOGIN_PASSWORD", pass_valida)).strip()
    except Exception:
        pass

    return email.strip().lower() == email_valido.lower() and password.strip() == pass_valida

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    col_izq, col_centro, col_der = st.columns([1, 1.3, 1])
    with col_centro:
        logo_login_html = obtener_logo_html(tipo="negro", ancho=230)
        st.markdown(f"""
        <div class="login-box">
            <div style="margin-bottom: 22px;">
                {logo_login_html}
            </div>
            <span class="hero-badge" style="background:#EFF6FF; color:#2563EB; border:1px solid #BFDBFE;">
                PORTAL CORPORATIVO QA
            </span>
            <p style="color:#64748B; font-size:0.9rem; margin-top:8px; margin-bottom:28px;">
                Control de Calidad y Auditoría de Ventas con Inteligencia Artificial
            </p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            correo_ingresado = st.text_input("Correo corporativo:", placeholder="usuario@correo.com")
            clave_ingresada = st.text_input("Contraseña de acceso:", type="password", placeholder="••••••••")
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            btn_ingresar = st.form_submit_button("Ingresar al Portal Seguro", type="primary", use_container_width=True)

            if btn_ingresar:
                if verificar_credenciales(correo_ingresado, clave_ingresada):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_actual"] = correo_ingresado.strip()
                    st.success("✓ Credenciales verificadas. Accediendo al sistema...")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique su correo y contraseña.")
        
        st.markdown("<p style='text-align:center; color:#94A3B8; font-size:0.8rem; margin-top:20px;'>🔒 Conexión cifrada SSL/TLS para ejecutivos autorizados de Autivo.</p>", unsafe_allow_html=True)

    st.stop()

# ==============================================================================
# USUARIO AUTENTICADO: CARGAR API KEY INVISIBLE EN SEGUNDO PLANO
# ==============================================================================
gemini_key = cargar_api_key_guardada()

# ==============================================================================
# BARRA LATERAL (PANEL DE CONTROL CORPORATIVO)
# ==============================================================================
with st.sidebar:
    logo_sidebar_html = obtener_logo_html(tipo="negro", ancho=175)
    st.markdown(f"""
    <div style="margin-bottom: 18px; padding-bottom: 12px; border-bottom: 1px solid #E2E8F0; text-align:center;">
        {logo_sidebar_html}
    </div>
    """, unsafe_allow_html=True)

    usuario_sesion = st.session_state.get("usuario_actual", "santiagourrutiahojas@gmail.com")
    st.markdown(f"""
    <div style="background:#F1F5F9; padding:10px 14px; border-radius:10px; margin-bottom:12px; font-size:0.85rem; border:1px solid #E2E8F0;">
        <div style="color:#64748B; font-size:0.75rem; font-weight:700;">SESIÓN ACTIVA</div>
        <div style="color:#0F172A; font-weight:600; word-break:break-all;">{usuario_sesion}</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    if gemini_key:
        st.markdown("""
        <div style="background:#ECFDF5; border:1px solid #A7F3D0; padding:8px 12px; border-radius:8px; display:flex; align-items:center; gap:8px;">
            <div style="width:8px; height:8px; background:#10B981; border-radius:50%;"></div>
            <div style="color:#065F46; font-size:0.82rem; font-weight:600;">Motor Gemini 3.6 Flash: En línea</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Clave API no detectada en Secrets.")

    st.markdown("---")
    
    st.markdown("<div style='font-size:0.9rem; font-weight:700; color:#0F172A; margin-bottom:6px;'>📄 Cargar Conversaciones (PDF)</div>", unsafe_allow_html=True)
    archivos_subidos = st.file_uploader(
        "Arrastra uno o varios PDFs aquí:",
        type=["pdf", "txt", "zip"],
        accept_multiple_files=True,
        help="Sube documentos de cualquier marca (Peugeot, Opel, Citroën, Hyundai, etc.)"
    )

    btn_evaluar = st.button("🚀 Iniciar Auditoría QA", type="primary", use_container_width=True)

    st.markdown("---")
    
    if os.path.exists(CONFIG["REPORTE_EXCEL"]):
        try:
            with open(CONFIG["REPORTE_EXCEL"], "rb") as f:
                st.download_button(
                    label="📥 Descargar Reporte Excel",
                    data=f,
                    file_name="reporte_qa_autivo.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        except Exception:
            pass

    st.markdown("---")
    
    with st.expander("⚙️ Gestión de Sesión / Reinicio"):
        st.caption("Borra las evaluaciones actuales para auditar una nueva marca de cero:")
        if st.button("🗑️ Borrar Historial y Empezar de Cero", use_container_width=True):
            if os.path.exists(CONFIG["REPORTE_JSON"]):
                with open(CONFIG["REPORTE_JSON"], "w", encoding="utf-8") as f:
                    f.write("[]")
            if os.path.exists(CONFIG["REPORTE_EXCEL"]):
                try:
                    os.remove(CONFIG["REPORTE_EXCEL"])
                except Exception:
                    pass
            st.success("Historial reiniciado exitosamente.")
            st.rerun()

# ==============================================================================
# EJECUCIÓN DE EVALUACIÓN AL PULSAR BOTÓN
# ==============================================================================
if btn_evaluar:
    if not gemini_key:
        st.error("⚠️ No se encontró la API Key de Gemini configurada en Secrets.")
    else:
        carpeta_destino = CONFIG["CARPETA_PDFS"]
        os.makedirs(carpeta_destino, exist_ok=True)
        rutas_a_evaluar = []

        if archivos_subidos:
            for archivo in archivos_subidos:
                nombre = archivo.name
                if nombre.lower().endswith(".zip"):
                    try:
                        archivo.seek(0)
                        with zipfile.ZipFile(archivo, 'r') as zf:
                            for m in zf.namelist():
                                if m.lower().endswith(('.pdf', '.txt')) and not '__macosx' in m.lower():
                                    nb = os.path.basename(m)
                                    if nb:
                                        p_out = os.path.join(carpeta_destino, nb)
                                        with open(p_out, "wb") as f_out:
                                            f_out.write(zf.read(m))
                                        rutas_a_evaluar.append(p_out)
                    except Exception as e:
                        st.sidebar.error(f"Error descomprimiendo ZIP: {e}")
                else:
                    archivo.seek(0)
                    ruta_guardada = os.path.join(carpeta_destino, nombre)
                    with open(ruta_guardada, "wb") as f_out:
                        f_out.write(archivo.getbuffer())
                    rutas_a_evaluar.append(ruta_guardada)

        st.info("⚡ Conectando con Google Gemini 3.6 Flash para auditar conversaciones...")
        progress_bar = st.progress(0)
        status_text = st.empty()

        def callback_ui(actual, total, evaluacion):
            p = actual / max(total, 1)
            progress_bar.progress(p)
            marca = evaluacion.get('marca', 'No Identificada')
            modelo = evaluacion.get('vehiculo_cotizado', 'Vehículo')
            estado = evaluacion.get('estado', '')
            status_text.markdown(f"**[{actual}/{total}]** Evaluado: `{evaluacion.get('archivo')}` — **{marca} {modelo}** ({estado})")

        ok, msg = procesar_pipeline(
            api_key=gemini_key,
            archivos_especificos=rutas_a_evaluar if rutas_a_evaluar else None,
            callback_progreso=callback_ui
        )

        if ok:
            st.success(f"🎉 {msg}")
            st.balloons()
            st.rerun()
        else:
            st.error(f"Aviso: {msg}")

# ==============================================================================
# CARGA DE DATOS PARA VISUALIZACIÓN
# ==============================================================================
def cargar_datos():
    if os.path.exists(CONFIG["REPORTE_JSON"]):
        try:
            with open(CONFIG["REPORTE_JSON"], "r", encoding="utf-8") as f:
                data = json.load(f)
                return pd.DataFrame(data)
        except Exception:
            pass
    return pd.DataFrame()

df = cargar_datos()

# ==============================================================================
# ENCABEZADO EJECUTIVO DEL DASHBOARD CON BRANDING AUTIVO
# ==============================================================================
logo_hero_html = obtener_logo_html(tipo="blanco", ancho=210)
st.markdown(f"""
<div class="hero-banner">
    <div>
        <span class="hero-badge">PLATAFORMA CORPORATIVA QA</span>
        <h1 class="hero-title">Auditoría y Calidad de Ventas Automotrices</h1>
        <p class="hero-desc">
            Diagnóstico comercial de embudos omnicanal con IA multimodal para 
            <b>Peugeot, Opel, Citroën, Fiat, Hyundai, JAC, Jeep, RAM y más</b>.
        </p>
    </div>
    <div>
        {logo_hero_html}
    </div>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.info("👋 **Aún no hay conversaciones auditadas.** Sube un archivo PDF o transcripción en la barra lateral izquierda y presiona **'🚀 Iniciar Auditoría QA'** para comenzar.")
else:
    total = len(df)
    aprobados = len(df[df["estado"] == "Aprobado"])
    rechazados = len(df[df["estado"] == "Rechazado"])
    tasa_exito = (aprobados / total * 100) if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-blue">
            <div class="kpi-header">
                <span class="kpi-lbl">TOTAL AUDITORÍAS</span>
                <span class="kpi-icon">📈</span>
            </div>
            <div class="kpi-val">{total}</div>
            <div class="kpi-sub">Chats analizados por IA</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-green">
            <div class="kpi-header">
                <span class="kpi-lbl">COTIZACIONES EXITOSAS</span>
                <span class="kpi-icon">🎯</span>
            </div>
            <div class="kpi-val" style="color:#059669;">{aprobados}</div>
            <div class="kpi-sub">Embudo de venta completado</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-red">
            <div class="kpi-header">
                <span class="kpi-lbl">FALLAS DEL ASISTENTE</span>
                <span class="kpi-icon">⚠️</span>
            </div>
            <div class="kpi-val" style="color:#DC2626;">{rechazados}</div>
            <div class="kpi-sub">Requiere ajuste técnico</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card kpi-accent-purple">
            <div class="kpi-header">
                <span class="kpi-lbl">TASA DE CALIDAD</span>
                <span class="kpi-icon">🏆</span>
            </div>
            <div class="kpi-val" style="color:#2563EB;">{tasa_exito:.1f}%</div>
            <div class="kpi-sub">Índice global de efectividad</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # GRÁFICOS DINÁMICOS
    # ==============================================================================
    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        st.markdown("""
        <div style="background:#FFFFFF; padding:20px 22px; border-radius:14px; border:1px solid #E2E8F0; box-shadow:0 2px 10px rgba(0,0,0,0.03);">
            <div style="font-weight:700; font-size:1.05rem; color:#0F172A; margin-bottom:4px;">📊 Distribución por Marca Detectada</div>
            <div style="font-size:0.8rem; color:#64748B; margin-bottom:12px;">Identificación automática realizada por Gemini 3.6 Flash</div>
        </div>
        """, unsafe_allow_html=True)
        if "marca" in df.columns:
            marca_counts = df["marca"].value_counts()
            st.bar_chart(marca_counts, color="#152A4A")

    with col_chart2:
        st.markdown("""
        <div style="background:#FFFFFF; padding:20px 22px; border-radius:14px; border:1px solid #E2E8F0; box-shadow:0 2px 10px rgba(0,0,0,0.03);">
            <div style="font-weight:700; font-size:1.05rem; color:#0F172A; margin-bottom:4px;">⚠️ Causas Principales de Falla</div>
            <div style="font-size:0.8rem; color:#64748B; margin-bottom:12px;">Categorización objetiva de fallas comerciales reales</div>
        </div>
        """, unsafe_allow_html=True)
        if "categoria_falla" in df.columns:
            fallas = df[df["estado"] == "Rechazado"]["categoria_falla"].value_counts()
            if not fallas.empty:
                st.bar_chart(fallas, color="#EF4444")
            else:
                st.success("🎉 No se registraron fallas en las conversaciones evaluadas.")

    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

    # ==============================================================================
    # TABLA DETALLADA CON FILTROS
    # ==============================================================================
    st.markdown("""
    <div style="background:#FFFFFF; padding:20px 22px; border-radius:14px; border:1px solid #E2E8F0; margin-bottom:16px;">
        <div style="font-weight:700; font-size:1.15rem; color:#0F172A; margin-bottom:4px;">📋 Registro General de Auditorías</div>
        <div style="font-size:0.85rem; color:#64748B;">Filtra y explora las evaluaciones detalladas por marca, estado o tipo de falla.</div>
    </div>
    """, unsafe_allow_html=True)
    
    filtro_col1, filtro_col2, filtro_col3 = st.columns(3)
    with filtro_col1:
        marcas_disponibles = ["Todas"] + sorted(list(df["marca"].dropna().unique()))
        sel_marca = st.selectbox("Filtrar por Marca:", marcas_disponibles)
    with filtro_col2:
        estados_disponibles = ["Todos", "Aprobado", "Rechazado"]
        sel_estado = st.selectbox("Filtrar por Estado:", estados_disponibles)
    with filtro_col3:
        cats_disponibles = ["Todas"] + sorted(list(df["categoria_falla"].dropna().unique()))
        sel_cat = st.selectbox("Filtrar por Categoría:", cats_disponibles)

    df_filtrado = df.copy()
    if sel_marca != "Todas":
        df_filtrado = df_filtrado[df_filtrado["marca"] == sel_marca]
    if sel_estado != "Todos":
        df_filtrado = df_filtrado[df_filtrado["estado"] == sel_estado]
    if sel_cat != "Todas":
        df_filtrado = df_filtrado[df_filtrado["categoria_falla"] == sel_cat]

    columnas_mostrar = [c for c in ["archivo", "marca", "vehiculo_cotizado", "estado", "categoria_falla", "observacion", "fecha_evaluacion"] if c in df_filtrado.columns]
    st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True)

    # ==============================================================================
    # INSPECTOR DE CONVERSACIÓN / FICHA TÉCNICA
    # ==============================================================================
    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#FFFFFF; padding:20px 22px; border-radius:14px; border:1px solid #E2E8F0; margin-bottom:16px;">
        <div style="font-weight:700; font-size:1.15rem; color:#0F172A; margin-bottom:4px;">🔍 Inspector Técnico y Diagnóstico del Juez</div>
        <div style="font-size:0.85rem; color:#64748B;">Selecciona cualquier conversación para ver el desglose comercial completo y los errores específicos detectados.</div>
    </div>
    """, unsafe_allow_html=True)
    
    archivos_disponibles = df_filtrado["archivo"].tolist() if "archivo" in df_filtrado.columns else []
    if archivos_disponibles:
        archivo_sel = st.selectbox("Selecciona una conversación para inspeccionar:", archivos_disponibles)
        fila = df[df["archivo"] == archivo_sel].iloc[0]

        card_col1, card_col2 = st.columns([1, 1.8])
        with card_col1:
            st.markdown(f"""
            <div class="audit-spec-card">
                <div style="font-weight:700; font-size:1rem; color:#0F172A; margin-bottom:12px; border-bottom:2px solid #E2E8F0; padding-bottom:8px;">
                    📄 Ficha de Conversación
                </div>
                <div class="audit-spec-row">
                    <span class="audit-spec-lbl">Archivo:</span>
                    <span class="audit-spec-val" style="font-family:monospace; font-size:0.8rem;">{fila.get('archivo', '')}</span>
                </div>
                <div class="audit-spec-row">
                    <span class="audit-spec-lbl">Marca Detectada:</span>
                    <span class="audit-spec-val" style="color:#2563EB;">{fila.get('marca', '')}</span>
                </div>
                <div class="audit-spec-row">
                    <span class="audit-spec-lbl">Vehículo:</span>
                    <span class="audit-spec-val">{fila.get('vehiculo_cotizado', '')}</span>
                </div>
                <div class="audit-spec-row">
                    <span class="audit-spec-lbl">Canal / País:</span>
                    <span class="audit-spec-val">{fila.get('canal', 'WhatsApp')} | {fila.get('pais', 'Chile')}</span>
                </div>
                <div class="audit-spec-row">
                    <span class="audit-spec-lbl">Dictamen Final:</span>
                    <span>{"<span class='badge-ok'>APROBADO</span>" if fila.get("estado") == "Aprobado" else "<span class='badge-fail'>RECHAZADO</span>"}</span>
                </div>
                <div class="audit-spec-row" style="border-bottom:none;">
                    <span class="audit-spec-lbl">Causa Principal:</span>
                    <span class="audit-spec-val" style="color:#DC2626;">{fila.get('categoria_falla', 'Ninguna')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with card_col2:
            st.markdown(f"""
            <div class="audit-spec-card">
                <div style="font-weight:700; font-size:1rem; color:#0F172A; margin-bottom:12px; border-bottom:2px solid #E2E8F0; padding-bottom:8px;">
                    ⚖️ Diagnóstico Ejecutivo de la IA
                </div>
                <p style="font-size:0.95rem; color:#334155; line-height:1.6; background:#F8FAFC; padding:14px 18px; border-radius:10px; border-left:4px solid #3B82F6; margin-bottom:16px;">
                    "{fila.get('observacion', 'Sin observaciones adicionales.')}"
                </p>
            </div>
            """, unsafe_allow_html=True)

            errores = fila.get("errores", [])
            if errores:
                st.markdown("<div style='font-size:0.88rem; font-weight:700; color:#0F172A; margin-top:14px; margin-bottom:6px;'>🚨 Fallas Críticas Identificadas:</div>", unsafe_allow_html=True)
                for err in errores:
                    st.error(f"• {err}")
            else:
                st.success("✓ Flujo comercial completado exitosamente sin fallas del asistente.")
