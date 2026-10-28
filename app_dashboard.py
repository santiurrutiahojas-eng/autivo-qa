#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard ejecutivo de auditoría QA automotriz con selección de proveedor de IA.
Diseño Corporativo Oficial Autivo (ai based solutions).
100% Homogéneo con el Portal Oficial de Autivo (Login y Dashboard Interior).
"""

import os
import json
import base64
import html
import io
import re
import tempfile
import zipfile
import pandas as pd
import streamlit as st
import altair as alt
import importlib

import procesar_pdf
importlib.reload(procesar_pdf)
from procesar_pdf import (
    procesar_pipeline,
    cargar_api_key_guardada,
    CONFIG
)

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Autivo - AI Agent Dashboard",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# LOGOS OFICIALES AUTIVO
# ==============================================================================
def obtener_logo_html(tipo: str = "negro", ancho: int = 220) -> str:
    """Devuelve el logo oficial en HTML con fallback a Base64 o SVG corporativo."""
    # 1. Archivos locales directos
    archivo_map = {
        "negro": "logo_autivo.png",
        "blanco": "logo_autivo_blanco.png",
        "icono": "logo_icono.png"
    }
    archivo = archivo_map.get(tipo, "logo_autivo.png")
    if os.path.exists(archivo):
        try:
            with open(archivo, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
                if tipo == "icono":
                    return f'<img src="data:image/png;base64,{b64}" style="width:26px; height:26px; object-fit:contain;" alt="Autivo Icon" />'
                return f'<img src="data:image/png;base64,{b64}" style="max-width:{ancho}px; width:100%; height:auto;" alt="Autivo" />'
        except Exception:
            pass

    # 2. Datos Base64 integrados en logos_data.py
    try:
        from logos_data import LOGO_BLACK_B64, LOGO_WHITE_B64, LOGO_ICON_B64
        if tipo == "icono" and LOGO_ICON_B64:
            return f'<img src="data:image/png;base64,{LOGO_ICON_B64}" style="width:26px; height:26px; object-fit:contain;" alt="Autivo Icon" />'
        b64 = LOGO_BLACK_B64 if tipo == "negro" else LOGO_WHITE_B64
        if b64:
            return f'<img src="data:image/png;base64,{b64}" style="max-width:{ancho}px; width:100%; height:auto;" alt="Autivo" />'
    except Exception:
        pass

    # 3. Fallback tipográfico corporativo
    if tipo == "icono":
        return '<span style="display:inline-flex; align-items:center; justify-content:center; width:26px; height:26px; border-radius:50%; background:#10B981; color:#FFFFFF; font-weight:800; font-size:14px;">@</span>'
    
    color = "#0F172A" if tipo == "negro" else "#FFFFFF"
    sub_color = "#64748B" if tipo == "negro" else "#94A3B8"
    return f"""<div style="font-family:'Plus Jakarta Sans', sans-serif; text-align:center;"><span style="font-size:1.6rem; font-weight:800; color:{color}; letter-spacing:-0.5px;">autivo</span><div style="font-size:0.75rem; font-weight:600; color:{sub_color}; letter-spacing:1px; text-transform:lowercase; margin-top:-4px;">ai based solutions</div></div>"""

# ==============================================================================
# PALETAS DE COLOR CORPORATIVAS (MARCAS AUTOMOTRICES Y CAUSAS DE FALLA)
# ==============================================================================
COLORES_MARCAS = {
    "Hyundai": "#002C6C",     # Azul marino Hyundai
    "Jac": "#DC2626",         # Rojo JAC
    "JAC": "#DC2626",
    "Jeep": "#15803D",        # Verde bosque Jeep
    "Opel": "#F59E0B",        # Amarillo / Ámbar Opel
    "Peugeot": "#2563EB",     # Azul eléctrico Peugeot
    "Citroën": "#991B1B",     # Granate Citroën
    "Fiat": "#EF4444",        # Rojo Fiat
    "RAM": "#475569",         # Carbón RAM
    "Geely": "#06B6D4",       # Celeste Geely
    "Lippi": "#7C3AED",       # Morado Lippi
    "Omni": "#4F46E5",        # Índigo Omni
    "Todas": "#1A62E8"
}

COLORES_FALLAS = {
    "Bucle de Validación": "#EF4444",
    "Falla Técnica del Bot": "#DC2626",
    "Alucinación o Error de Catálogo": "#F59E0B",
    "Frustración del Cliente": "#EC4899",
    "Lead Incompleto": "#8B5CF6",
    "Abandono por Falla del Bot": "#F97316",
    "Error de API Gemini": "#64748B",
    "Error de API OpenAI": "#64748B",
    "Otro": "#3B82F6"
}


# ==============================================================================
# ESTILOS CSS GLOBALES (HOMOGÉNEOS CON EL PORTAL AUTIVO)
# ==============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Fondo principal del dashboard */
    .stApp {
        background-color: #F8FAFC !important;
    }

    /* Reducir padding superior de Streamlit */
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
        max-width: 100% !important;
    }

    /* Ocultar barra de Streamlit innecesaria */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* ========================================== */
    /* BARRA LATERAL OSCURA OFICIAL AUTIVO (#0C1017) */
    /* ========================================== */
    section[data-testid="stSidebar"] {
        background-color: #0C1017 !important;
        border-right: 1px solid #1E293B !important;
    }

    /* Textos dentro del sidebar */
    section[data-testid="stSidebar"] * {
        color: #94A3B8;
    }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] strong {
        color: #FFFFFF !important;
    }

    /* Radio buttons como enlaces de menú del Sidebar */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 6px !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: transparent !important;
        border-radius: 8px !important;
        padding: 9px 14px !important;
        margin-bottom: 2px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
        border: 1px solid transparent !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        background-color: #1A2233 !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"],
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background-color: #1A2233 !important;
        color: #FFFFFF !important;
        border-left: 3px solid #1A62E8 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label span {
        color: #CBD5E1 !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }

    /* Botones en Sidebar */
    section[data-testid="stSidebar"] button {
        background-color: #161F30 !important;
        color: #CBD5E1 !important;
        border: 1px solid #28354A !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background-color: #202D45 !important;
        color: #FFFFFF !important;
        border-color: #384C6B !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #1A62E8 !important;
        color: #FFFFFF !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(26, 98, 232, 0.3) !important;
    }
    section[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #1551C2 !important;
    }

    /* Divisores en sidebar */
    section[data-testid="stSidebar"] hr {
        border-color: #1E293B !important;
        margin: 16px 0 !important;
    }

    /* ========================================== */
    /* TARJETAS KPI OFICIALES AUTIVO (#FFFFFF)    */
    /* ========================================== */
    .autivo-kpi-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        transition: all 0.2s ease-in-out;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .autivo-kpi-card:hover {
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
        border-color: #CBD5E1;
    }
    .autivo-kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .autivo-kpi-title {
        font-size: 0.82rem;
        font-weight: 500;
        color: #64748B;
        letter-spacing: -0.1px;
    }
    .autivo-kpi-icon {
        color: #94A3B8;
        display: flex;
        align-items: center;
    }
    .autivo-kpi-value {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1;
        letter-spacing: -0.5px;
        margin-bottom: 4px;
    }
    .autivo-kpi-footer {
        font-size: 0.78rem;
        color: #94A3B8;
        font-weight: 500;
    }

    /* ========================================== */
    /* TARJETA CONTENEDORA GENERAL                */
    /* ========================================== */
    .autivo-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 22px 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        margin-bottom: 20px;
    }
    .autivo-card-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0 0 16px 0;
        letter-spacing: -0.3px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* ========================================== */
    /* BARRAS DE PROGRESO DE TOP THEMES           */
    /* ========================================== */
    .theme-item {
        margin-bottom: 14px;
    }
    .theme-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
        margin-bottom: 6px;
    }
    .theme-label {
        font-weight: 600;
        color: #1E293B;
    }
    .theme-count {
        font-weight: 500;
        color: #64748B;
        font-size: 0.82rem;
    }
    .theme-bar-track {
        background-color: #F1F5F9;
        height: 6px;
        border-radius: 4px;
        overflow: hidden;
        width: 100%;
    }
    .theme-bar-fill {
        background-color: #1A62E8;
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }

    /* ========================================== */
    /* PILLS DE ACCIÓN Y RANGOS (ACTION BAR)      */
    /* ========================================== */
    .action-pill {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 7px 14px;
        font-size: 0.82rem;
        font-weight: 600;
        color: #334155;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }

    /* Estilos del Login Oficial */
    .stTextInput input {
        background-color: #EBF2FA !important;
        border: 1px solid #D2E1F0 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
        font-size: 0.95rem !important;
        padding: 10px 14px !important;
    }
    .stTextInput input:focus {
        border-color: #1A62E8 !important;
        box-shadow: 0 0 0 2px rgba(26, 98, 232, 0.2) !important;
    }
    .stTextInput label {
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #334155 !important;
        margin-bottom: 4px !important;
    }

    /* Botón Oficial Autivo Azul */
    div[data-testid="stFormSubmitButton"] button {
        background-color: #1A62E8 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 12px 20px !important;
        box-shadow: 0 4px 14px rgba(26, 98, 232, 0.25) !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1551C2 !important;
        box-shadow: 0 6px 18px rgba(26, 98, 232, 0.35) !important;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# SISTEMA DE AUTENTICACIÓN / PANTALLA DE LOGIN IDÉNTICA A LA OFICIAL
# ==============================================================================
def verificar_credenciales(email: str, password: str) -> bool:
    # Credenciales autorizadas por defecto para evitar bloqueos si secrets no está configurado
    emails_validos = [
        "santiagourrutiahojas@gmail.com",
        "saurrutia@alumnos.uai.cl"
    ]
    pass_valida = "Santiago2608#"

    # Cargar desde Streamlit Secrets si están definidos
    try:
        if hasattr(st, "secrets"):
            if "LOGIN_EMAIL" in st.secrets:
                emails_validos.append(str(st.secrets["LOGIN_EMAIL"]).strip().lower())
            if "LOGIN_EMAILS" in st.secrets:
                emails_validos.extend(e.strip().lower() for e in str(st.secrets["LOGIN_EMAILS"]).split(",") if e.strip())
            if "LOGIN_PASSWORD" in st.secrets:
                pass_valida = str(st.secrets["LOGIN_PASSWORD"]).strip()
    except Exception:
        pass

    # Cargar desde variables de entorno si están definidas
    if os.environ.get("LOGIN_EMAIL"):
        emails_validos.append(os.environ["LOGIN_EMAIL"].strip().lower())
    if os.environ.get("LOGIN_PASSWORD"):
        pass_valida = os.environ["LOGIN_PASSWORD"].strip()

    email_clean = email.strip().lower()
    return email_clean in [e.lower() for e in emails_validos] and password.strip() == pass_valida


if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

# ------------------------------------------------------------------------------
# PANTALLA DE INGRESO (LOGIN SCREEN - IDÉNTICA A LA OFICIAL DE AUTIVO)
# ------------------------------------------------------------------------------
if not st.session_state["autenticado"]:
    col_izq, col_centro, col_der = st.columns([1, 1.25, 1])
    with col_centro:
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
        # Logo Superior Fuera de la Tarjeta
        logo_html = obtener_logo_html(tipo="negro", ancho=250)
        st.markdown(f"""
        <div style="text-align: center; margin-bottom: 28px;">
            {logo_html}
        </div>
        """, unsafe_allow_html=True)

        # Tarjeta Blanca de Login
        st.markdown("""
        <div style="background: #FFFFFF; border-radius: 14px; padding: 32px 30px; box-shadow: 0 10px 30px rgba(0, 40, 100, 0.08); border: 1px solid #E6EEF8;">
            <h2 style="text-align: center; color: #0F172A; font-weight: 700; margin: 0 0 24px 0; font-size: 1.5rem;">
                Login
            </h2>
        """, unsafe_allow_html=True)

        with st.form("form_login"):
            correo_ingresado = st.text_input("Username", value="santiagourrutiahojas@gmail.com", placeholder="usuario@correo.com")
            clave_ingresada = st.text_input("Password", type="password", placeholder="••••••••")
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            btn_ingresar = st.form_submit_button("LOGIN", use_container_width=True)

            if btn_ingresar:
                if verificar_credenciales(correo_ingresado, clave_ingresada):
                    st.session_state["autenticado"] = True
                    st.session_state["usuario_actual"] = correo_ingresado.strip()
                    st.success("✓ Acceso concedido.")
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas. Verifique su usuario y contraseña.")

        st.markdown("</div>", unsafe_allow_html=True)

        # Footer Oficial
        st.markdown("""
        <div style="text-align: center; margin-top: 30px; color: #94A3B8; font-size: 0.82rem;">
            © 2026 Autivo. All rights reserved.
        </div>
        """, unsafe_allow_html=True)

    st.stop()


# ==============================================================================
# CARGA DE DATOS AUDITADOS
# ==============================================================================
def cargar_datos() -> pd.DataFrame:
    if os.path.exists(CONFIG["REPORTE_JSON"]):
        try:
            with open(CONFIG["REPORTE_JSON"], "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    for item in data:
                        # Asegurar clasificación real de intención / tema (Top Themes)
                        if not item.get("tema_conversacion"):
                            texto_busqueda = f"{item.get('vehiculo_cotizado','')} {item.get('observacion','')} {' '.join(item.get('errores',[]))}".lower()
                            if any(w in texto_busqueda for w in ["financ", "crédit", "credit", "cuota", "pie", "banco", "tasa", "simulac"]):
                                item["tema_conversacion"] = "Financing Questions"
                            elif any(w in texto_busqueda for w in ["especific", "ficha", "motor", "hp", "consumo", "versión", "version", "equip"]):
                                item["tema_conversacion"] = "Technical Specifications Questions"
                            elif any(w in texto_busqueda for w in ["contact", "asesor", "ejecutiv", "humano", "llamad", "sucursal"]):
                                item["tema_conversacion"] = "Contact Request"
                            elif any(w in texto_busqueda for w in ["retoma", "usado", "renov", "parte de pago", "tasac"]):
                                item["tema_conversacion"] = "Vehicle Exchange or Renewal"
                            elif any(w in texto_busqueda for w in ["cotiz", "precio", "valor", "costo", "descuento", "bono"]):
                                item["tema_conversacion"] = "Price Requests"
                            else:
                                item["tema_conversacion"] = "General Inquiry"

                        # Asegurar conteo dinámico de turnos de diálogo
                        try:
                            val_int = int(item.get("interacciones", 0))
                        except Exception:
                            val_int = 0
                        if val_int < 0:
                            val_int = 0
                        item["interacciones"] = val_int

                        # Asegurar detección de solicitud de ejecutivo humano
                        if "solicito_humano" not in item:
                            texto_humano = f"{item.get('observacion','')} {' '.join(item.get('errores',[]))}".lower()
                            item["solicito_humano"] = any(w in texto_humano for w in ["humano", "asesor", "ejecutivo", "persona", "vendedor", "contactar"]) or item.get("tema_conversacion") == "Contact Request"

                        # Un resumen ausente no se rellena con mensajes inventados.
                        if not isinstance(item.get("dialogo_resumen"), list):
                            item["dialogo_resumen"] = []

                        # Verificación estricta de Falta de Respuesta del Bot (Silencio)
                        d_res = item.get("dialogo_resumen", [])
                        mensajes_b = [d for d in d_res if isinstance(d, dict) and d.get("emisor", "").lower() in ["bot", "asistente", "agente", "ia"]]
                        mensajes_c = [d for d in d_res if isinstance(d, dict) and d.get("emisor", "").lower() in ["cliente", "usuario", "user"]]
                        texto_diag = f"{item.get('observacion', '')} {' '.join(item.get('errores', []))}".lower()

                        if (len(mensajes_c) > 0 and len(mensajes_b) == 0) or any(f in texto_diag for f in ["no responde", "no respondió", "sin respuesta", "0 respuestas"]):
                            item["estado"] = "Rechazado"
                            item["categoria_falla"] = "Falla Técnica del Bot"

                    return pd.DataFrame(data)
        except Exception:
            pass
    return pd.DataFrame()

df_global = cargar_datos()

# ------------------------------------------------------------------------------
# MODAL DE INFORME EJECUTIVO ONE-PAGER (NATIVO STREAMLIT DIALOG)
# ------------------------------------------------------------------------------
@st.dialog("📄 Informe Ejecutivo de Auditoría QA - Autivo", width="large")
def mostrar_informe_ejecutivo(df_filtrado: pd.DataFrame, marca_nombre: str = "Multimarca"):
    """Genera un briefing ejecutivo formal imprimible para Directorio y Gerencia."""
    total_c = len(df_filtrado)
    aprob_c = len(df_filtrado[df_filtrado["estado"] == "Aprobado"])
    rech_c = len(df_filtrado[df_filtrado["estado"] == "Rechazado"])
    revision_c = len(df_filtrado[df_filtrado["estado"] == "Revisión"])
    evaluadas_c = aprob_c + rech_c
    pct_ok = round((aprob_c / evaluadas_c * 100), 1) if evaluadas_c > 0 else 0.0
    leads_riesgo = rech_c
    salud_badge = "SIN EVALUACIONES" if evaluadas_c == 0 else ("🟢 ÓPTIMA (>85%)" if pct_ok >= 85 else ("🟡 EN OBSERVACIÓN (70-84%)" if pct_ok >= 70 else "🔴 ALERTA CRÍTICA (<70%)"))
    
    st.markdown(f"""
    <div style="font-family:'Plus Jakarta Sans', sans-serif; color:#0F172A; border-bottom:2px solid #1A62E8; padding-bottom:12px; margin-bottom:18px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:1.6rem; font-weight:800; color:#0F172A; letter-spacing:-0.5px;">autivo</span>
                <span style="font-size:0.8rem; color:#64748B; margin-left:8px; font-weight:600;">ai based solutions</span>
            </div>
            <div style="text-align:right; font-size:0.82rem; color:#64748B;">
                <b>Fecha de Emisión:</b> {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}<br/>
                <b>Auditor Senior:</b> Motor de evaluación IA
            </div>
        </div>
        <h2 style="font-size:1.3rem; font-weight:700; color:#1E293B; margin:14px 0 2px 0;">
            Reporte Ejecutivo de Rendimiento Comercial de Agentes IA — {marca_nombre}
        </h2>
        <div style="font-size:0.85rem; color:#64748B;">
            Monitoreo y Control de Calidad en Canales WhatsApp y Web Concesionarios
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 4 Métricas Clave
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Conversaciones", total_c)
    with m2:
        st.metric("Efectividad Comercial", f"{pct_ok}%" if evaluadas_c else "—", help="Aprobadas ÷ evaluaciones válidas. Se excluyen los casos en revisión técnica.")
    with m3:
        st.metric("Pendientes de revisión", revision_c)
    with m4:
        st.metric("Leads rechazados", leads_riesgo)

    st.markdown("<hr style='margin:16px 0; border-color:#E2E8F0;'/>", unsafe_allow_html=True)

    # Diagnóstico y Conclusiones
    st.markdown("### 📋 Conclusiones Ejecutivas y Plan de Acción")
    if evaluadas_c == 0:
        st.info("No hay evaluaciones válidas para calcular la efectividad. Revisa los casos marcados como Revisión.")
    elif pct_ok >= 85:
        st.success(f"**Operación Saludable ({pct_ok}% Aprobación):** Los asistentes virtuales de {marca_nombre} presentan un desempeño óptimo, completando flujos de cotización y capturando datos de prospectos de manera fluida. Se recomienda mantener pauta publicitaria activa.")
    elif pct_ok >= 70:
        st.warning(f"**Operación en Observación ({pct_ok}% Aprobación):** Se registran deserciones en modelos puntuales debido a dudas sobre financiamiento o bucles de catálogo. Se sugiere calibrar menús interactivos antes de incrementar volumen de campañas.")
    else:
        st.error(f"**Alerta Crítica ({pct_ok}% Aprobación):** Alto volumen de prospectos no convertidos ({leads_riesgo} clientes). Las fallas se concentran en bucles repetitivos y deficiencias en derivación humana. Se requiere intervención técnica prioritaria.")

    # Desglose por Marcas
    st.markdown("### 🚗 Rendimiento Comparativo por Marca")
    if not df_filtrado.empty and "marca" in df_filtrado.columns:
        resumen_rep = []
        for m, grp in df_filtrado.groupby("marca"):
            c_tot = len(grp)
            c_ok = len(grp[grp["estado"] == "Aprobado"])
            c_rech = len(grp[grp["estado"] == "Rechazado"])
            c_revision = len(grp[grp["estado"] == "Revisión"])
            c_evaluadas = c_ok + c_rech
            c_hum = len(grp[grp["solicito_humano"] == True]) if "solicito_humano" in grp.columns else 0
            p_ok = (c_ok / c_evaluadas * 100) if c_evaluadas > 0 else 0
            p_hum = (c_hum / c_tot * 100) if c_tot > 0 else 0
            resumen_rep.append({
                "Marca": f"Bot {m}",
                "Chats Auditados": c_tot,
                "Aprobados": c_ok,
                "Rechazados": c_rech,
                "Por revisar": c_revision,
                "Efectividad (% OK)": f"{p_ok:.1f}%" if c_evaluadas else "—",
                "Solicitud Ejecutivo Humano": f"{p_hum:.0f}%"
            })
        st.dataframe(pd.DataFrame(resumen_rep), use_container_width=True, hide_index=True)

    st.markdown("""
    <div style="font-size:0.75rem; color:#94A3B8; text-align:center; margin-top:20px;">
        © 2026 Autivo (ai based solutions). Documento Confidencial para Uso Interno de Gerencia.
    </div>
    """, unsafe_allow_html=True)
    st.caption("💡 Para guardar en PDF o imprimir este informe, presiona Ctrl + P en tu navegador.")


# ==============================================================================
# BARRA LATERAL OSCURA OFICIAL AUTIVO (#0C1017)
# ==============================================================================
with st.sidebar:
    # Encabezado del Sidebar: Icono blanco de Autivo + texto
    icono_sidebar_html = obtener_logo_html(tipo="icono", ancho=28)
    st.markdown(f"""
    <div style="display:flex; align-items:center; justify-content:space-between; padding:12px 6px 16px 6px; border-bottom:1px solid #1E293B; margin-bottom:16px;">
        <div style="display:flex; align-items:center; gap:10px;">
            {icono_sidebar_html}
            <span style="font-family:'Plus Jakarta Sans', sans-serif; font-size:1.35rem; font-weight:700; color:#FFFFFF; letter-spacing:-0.4px;">Autivo</span>
        </div>
        <div style="color:#64748B; font-size:0.85rem; cursor:pointer;" title="Plataforma QA">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="9" y1="3" x2="9" y2="21"></line></svg>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Navegación del Sidebar (Idéntica a la vista corporativa)
    opciones_nav = [
        "🏠 Home",
        "💬 Recurrent Themes",
        "📄 Transcriptions",
        "🚀 Subir / Auditar PDFs"
    ]
    seccion_seleccionada = st.radio(
        "Navegación",
        opciones_nav,
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    st.markdown("#### Motor de evaluación")
    proveedor_etiqueta = st.selectbox("Proveedor de IA", ["Google Gemini", "OpenAI"], index=0, key="proveedor_ia_ui")
    proveedor_ia = "gemini" if proveedor_etiqueta == "Google Gemini" else "openai"
    if proveedor_ia == "openai":
        modelo_default = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        try:
            modelo_default = str(st.secrets.get("OPENAI_MODEL", modelo_default))
        except Exception:
            pass
        modelo_ia = st.text_input("Modelo", value=modelo_default, key="modelo_openai_ui", help="Modelo disponible para la Responses API; por defecto gpt-4o-mini.")
    else:
        modelo_default = os.environ.get("GEMINI_MODEL", CONFIG["MODELOS_GEMINI"][0])
        try:
            modelo_default = str(st.secrets.get("GEMINI_MODEL", modelo_default))
        except Exception:
            pass
        modelo_ia = st.text_input("Modelo", value=modelo_default, key="modelo_gemini_ui")
    try:
        concurrencia_default = max(1, min(10, int(os.environ.get("QA_CONCURRENCY", "4"))))
    except (TypeError, ValueError):
        concurrencia_default = 4
    concurrencia_ia = st.slider("Conversaciones simultáneas", min_value=1, max_value=10, value=concurrencia_default, help="Ajusta este valor según los límites de tu cuenta y el volumen del lote.")
    api_key = cargar_api_key_guardada(proveedor_ia)

    # Estado de la IA seleccionada
    if api_key:
        st.markdown("""
        <div style="background:#0F231D; border:1px solid #164E3D; padding:8px 12px; border-radius:8px; display:flex; align-items:center; gap:8px;">
            <div style="width:7px; height:7px; background:#10B981; border-radius:50%; box-shadow: 0 0 8px #10B981;"></div>
            <div style="color:#6EE7B7; font-size:0.78rem; font-weight:600;">""" + proveedor_etiqueta + """ · conexión lista</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#2C1618; border:1px solid #571C20; padding:8px 12px; border-radius:8px; display:flex; align-items:center; gap:8px;">
            <div style="width:7px; height:7px; background:#EF4444; border-radius:50%;"></div>
            <div style="color:#FCA5A5; font-size:0.78rem; font-weight:600;">""" + proveedor_etiqueta + """ · falta configurar clave</div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🔑 Clave de API", expanded=not bool(api_key)):
        st.caption("La clave se conserva solo en esta sesión. Para uso permanente, configúrala en Streamlit Secrets.")
        clave_ingresada_sidebar = st.text_input(
            f"API Key {proveedor_etiqueta}",
            value=st.session_state.get(f"{proveedor_ia}_api_key", ""),
            type="password",
            placeholder="Pega la clave de API aquí...",
            label_visibility="collapsed"
        )
        if st.button("🔌 Conectar Clave", use_container_width=True):
            if clave_ingresada_sidebar.strip():
                st.session_state[f"{proveedor_ia}_api_key"] = clave_ingresada_sidebar.strip()
                st.success("Clave disponible durante esta sesión.")
                st.rerun()

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)

    # Pie del Sidebar (Organization view & Logout idéntico a la captura)
    usuario_sesion = st.session_state.get("usuario_actual", "Usuario autorizado")
    st.markdown(f"""
    <div style="padding: 0 4px; margin-bottom: 12px;">
        <div style="display:flex; align-items:center; gap:8px; color:#94A3B8; font-size:0.82rem; margin-bottom:6px;">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21h18M3 7v14M21 7v14M6 11h2M6 15h2M10 11h2M10 15h2M14 11h2M14 15h2M18 11h2M18 15h2M9 3h6v4H9z"></path></svg>
            <span style="font-weight:600; color:#CBD5E1;">Organization view</span>
        </div>
        <div style="color:#64748B; font-size:0.75rem; word-break:break-all; padding-left:23px;">{usuario_sesion}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state["autenticado"] = False
        st.rerun()

    with st.expander("⚙️ Gestión de Datos"):
        st.caption("Reiniciar historial de auditorías para evaluar de cero:")
        if st.button("🗑️ Borrar Historial", use_container_width=True):
            if os.path.exists(CONFIG["REPORTE_JSON"]):
                with open(CONFIG["REPORTE_JSON"], "w", encoding="utf-8") as f:
                    f.write("[]")
            if os.path.exists(CONFIG["REPORTE_EXCEL"]):
                try:
                    os.remove(CONFIG["REPORTE_EXCEL"])
                except Exception:
                    pass
            st.success("Historial reiniciado.")
            st.rerun()


# ==============================================================================
# PROCESAMIENTO DE ARCHIVOS (LOTES CON OPENAI O GEMINI)
# ==============================================================================
if seccion_seleccionada == "🚀 Subir / Auditar PDFs":
    st.markdown("""
    <div class="autivo-card">
        <h2 style="font-size:1.4rem; font-weight:700; color:#0F172A; margin:0 0 6px 0;">
            🚀 Cargar Nuevas Conversaciones para Auditoría
        </h2>
        <p style="font-size:0.88rem; color:#64748B; margin:0;">
            Sube varias conversaciones TXT o PDF, o un ZIP exportado desde Autivo. Puedes procesar hasta 2.000 conversaciones por lote.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_up1, col_up2 = st.columns([1.5, 2.5])
    with col_up1:
        opciones_marca_carga = ["🤖 Detección Automática por IA"] + CONFIG["MARCAS_REFERENCIA"]
        marca_seleccionada_carga = st.selectbox(
            "🏢 Asignar Marca a las conversaciones:",
            opciones_marca_carga,
            index=0,
            help="Selecciona la marca automotriz de las transcripciones (ej: Hyundai, JAC, Jeep, etc.) si los PDFs no incluyen el logo o nombre en el texto."
        )
    with col_up2:
        st.markdown(f"""
        <div style="background:#F1F5F9; border-radius:8px; padding:10px 14px; font-size:0.83rem; color:#475569; margin-top:22px; border-left:3px solid #1A62E8;">
            💡 <b>Tip de Integración:</b> En transcripciones de Autivo donde el bot nunca respondió, el texto del PDF omite el nombre de la marca. Seleccionar aquí <b>{marca_seleccionada_carga}</b> garantiza su correcta categorización.
        </div>
        """, unsafe_allow_html=True)

    archivos_subidos = st.file_uploader(
        "Arrastra uno o varios archivos o ZIP aquí:",
        type=["pdf", "txt", "zip"],
        accept_multiple_files=True,
        help="Hasta 50 MB por archivo. Cada ZIP puede contener PDF y TXT en subcarpetas."
    )

    btn_evaluar = st.button(f"🚀 Evaluar lote con {proveedor_etiqueta}", type="primary", use_container_width=True)
    if archivos_subidos:
        st.caption(f"{len(archivos_subidos)} archivo(s) cargado(s). Los ZIP se expandirán antes de evaluar.")

    if btn_evaluar:
        if not api_key:
            st.error(f"No hay una clave de API configurada para {proveedor_etiqueta}. Agrégala en Secrets o en el panel lateral.")
        elif not archivos_subidos:
            st.warning("Primero selecciona una o más conversaciones.")
        else:
            max_lote = 2000
            rutas_a_evaluar = []
            avisos_lote = []
            contador_archivo = [0]
            bytes_zip = 0
            with tempfile.TemporaryDirectory(prefix="autivo_qa_batch_") as carpeta_temporal:
                def guardar_temporal(nombre, contenido):
                    contador_archivo[0] += 1
                    nombre_seguro = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(nombre)) or "conversacion"
                    extension = os.path.splitext(nombre_seguro)[1].lower()
                    if extension not in (".pdf", ".txt"):
                        return
                    destino = os.path.join(carpeta_temporal, f"{contador_archivo[0]:05d}_{nombre_seguro}")
                    with open(destino, "wb") as archivo_destino:
                        archivo_destino.write(contenido)
                    rutas_a_evaluar.append(destino)

                for archivo in archivos_subidos:
                    contenido = archivo.getvalue()
                    if len(contenido) > 50 * 1024 * 1024:
                        avisos_lote.append(f"{archivo.name}: supera 50 MB y se omitió.")
                        continue
                    if archivo.name.lower().endswith(".zip"):
                        try:
                            with zipfile.ZipFile(io.BytesIO(contenido), "r") as zf:
                                miembros = [m for m in zf.infolist() if not m.is_dir() and m.filename.lower().endswith((".pdf", ".txt")) and "__macosx" not in m.filename.lower()]
                                for miembro in miembros:
                                    if len(rutas_a_evaluar) >= max_lote:
                                        avisos_lote.append(f"Se alcanzó el máximo de {max_lote:,} conversaciones; el resto se omitió.")
                                        break
                                    if miembro.file_size > 25 * 1024 * 1024:
                                        avisos_lote.append(f"{os.path.basename(miembro.filename)}: supera 25 MB y se omitió.")
                                        continue
                                    bytes_zip += miembro.file_size
                                    if bytes_zip > 500 * 1024 * 1024:
                                        avisos_lote.append("El lote ZIP superó 500 MB descomprimidos; se omitió el resto.")
                                        break
                                    guardar_temporal(miembro.filename, zf.read(miembro))
                        except (zipfile.BadZipFile, OSError):
                            avisos_lote.append(f"{archivo.name}: ZIP inválido o dañado.")
                    else:
                        if len(rutas_a_evaluar) >= max_lote:
                            avisos_lote.append(f"Se alcanzó el máximo de {max_lote:,} conversaciones; el resto se omitió.")
                            break
                        guardar_temporal(archivo.name, contenido)

                if avisos_lote:
                    for aviso in avisos_lote[:10]:
                        st.warning(aviso)
                    if len(avisos_lote) > 10:
                        st.caption(f"{len(avisos_lote) - 10} avisos adicionales.")
                if not rutas_a_evaluar:
                    st.error("No encontramos ningún PDF o TXT válido en la carga.")
                else:
                    st.info(f"Evaluando {len(rutas_a_evaluar):,} conversaciones con {proveedor_etiqueta} ({modelo_ia}) · {concurrencia_ia} simultáneas.")
                    progress_bar = st.progress(0, text="Iniciando lote…")
                    status_text = st.empty()

                    def callback_ui(actual, total, evaluacion):
                        progress_bar.progress(actual / max(total, 1), text=f"Evaluando: {actual:,} de {total:,}")
                        status_text.markdown(f"**[{actual:,}/{total:,}]** `{evaluacion.get('archivo')}` — **{evaluacion.get('marca', 'No identificada')} · {evaluacion.get('estado', 'Revisión')}**")

                    marca_param = None if marca_seleccionada_carga == "🤖 Detección Automática por IA" else marca_seleccionada_carga
                    ok, msg = procesar_pipeline(
                        api_key=api_key,
                        archivos_especificos=rutas_a_evaluar,
                        callback_progreso=callback_ui,
                        marca_asignada=marca_param,
                        proveedor=proveedor_ia,
                        modelo=modelo_ia.strip(),
                        concurrencia=concurrencia_ia,
                    )
                    if ok:
                        st.success(f"Lote finalizado. {msg}")
                        st.rerun()
                    else:
                        st.error(msg)

    st.stop()


# ==============================================================================
# FILTROS SUPERIORES DE MARCA (SELECTOR EN CABECERA)
# ==============================================================================
marcas_en_datos = []
if not df_global.empty and "marca" in df_global.columns:
    marcas_en_datos = sorted([m for m in df_global["marca"].dropna().unique() if m != "Error de Conexión"])

lista_marcas_selector = ["Todas las Marcas"] + (marcas_en_datos if marcas_en_datos else CONFIG["MARCAS_REFERENCIA"])


# ==============================================================================
# VISTA: 🏠 HOME (IDÉNTICA A LA CAPTURA OFICIAL AUTIVO media_1790131589109.png)
# ==============================================================================
if seccion_seleccionada == "🏠 Home":
    # --------------------------------------------------------------------------
    # 1. ENCABEZADO SUPERIOR & SELECTOR DE MARCA
    # --------------------------------------------------------------------------
    col_hdr_left, col_hdr_right = st.columns([3, 1.3])
    
    with col_hdr_right:
        marca_seleccionada = st.selectbox(
            "Filtrar Marca:",
            lista_marcas_selector,
            index=0,
            label_visibility="collapsed"
        )

    # Filtrar dataframe según marca seleccionada
    df_actual = df_global.copy()
    if not df_actual.empty and marca_seleccionada != "Todas las Marcas":
        df_actual = df_actual[df_actual["marca"] == marca_seleccionada]

    titulo_marca = f"{marca_seleccionada} Chile Whatsapp" if marca_seleccionada != "Todas las Marcas" else "Multimarca Chile Whatsapp & Web"
    
    with col_hdr_left:
        st.markdown(f"""
        <div>
            <h1 style="font-size:1.75rem; font-weight:700; color:#0F172A; margin:0 0 4px 0; letter-spacing:-0.5px;">
                AI Agent Dashboard - {titulo_marca}
            </h1>
            <p style="font-size:0.9rem; color:#64748B; margin:0;">
                Monitor your AI agent performance metrics
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 2. BARRA DE ACCIÓN: BOTÓN EXPORT & FECHA (ACTION BAR)
    # --------------------------------------------------------------------------
    col_act_left, col_act_right = st.columns([2.5, 1.5])
    with col_act_left:
        btn_c1, btn_c2 = st.columns([1, 1.4])
        with btn_c1:
            if os.path.exists(CONFIG["REPORTE_EXCEL"]):
                try:
                    with open(CONFIG["REPORTE_EXCEL"], "rb") as f_excel:
                        st.download_button(
                            label="📥 Export Excel",
                            data=f_excel,
                            file_name="reporte_qa_autivo.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                except Exception:
                    pass
            else:
                st.markdown("""
                <div class="action-pill" style="opacity:0.6; cursor:not-allowed;">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                    Export
                </div>
                """, unsafe_allow_html=True)
        with btn_c2:
            if st.button("📊 Informe Ejecutivo (One-Pager)", key="btn_open_report_hdr", use_container_width=True):
                mostrar_informe_ejecutivo(df_actual if not df_actual.empty else df_global, titulo_marca)

    with col_act_right:
        # Fechas dinámicas o representativas
        fecha_texto = "Sep 16, 2026 - Sep 18, 2026"
        if not df_actual.empty and "fecha_evaluacion" in df_actual.columns:
            fechas_validas = df_actual["fecha_evaluacion"].dropna().tolist()
            if fechas_validas:
                f_min = min(fechas_validas)[:10]
                f_max = max(fechas_validas)[:10]
                fecha_texto = f"{f_min} - {f_max}"

        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end;">
            <div class="action-pill">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#64748B" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <span>{fecha_texto}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 18px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 3. FILA DE TARJETAS KPI (METRIC CARDS) - 4 TARJETAS EJECUTIVAS
    # --------------------------------------------------------------------------
    total_convs = len(df_actual) if not df_actual.empty else 0
    aprobados = len(df_actual[df_actual["estado"] == "Aprobado"]) if not df_actual.empty else 0
    rechazados = len(df_actual[df_actual["estado"] == "Rechazado"]) if not df_actual.empty else 0
    revisiones = len(df_actual[df_actual["estado"] == "Revisión"]) if not df_actual.empty else 0
    evaluaciones_validas = aprobados + rechazados
    tasa_efectividad = (aprobados / evaluaciones_validas * 100) if evaluaciones_validas > 0 else 0.0

    # Conteo dinámico y real de interacciones / turnos de diálogo
    if not df_actual.empty and "interacciones" in df_actual.columns:
        interacciones_totales = int(df_actual["interacciones"].sum())
        promedio_interacciones = round(float(df_actual["interacciones"].mean()), 1)
    else:
        interacciones_totales = 0
        promedio_interacciones = 0.0

    interacciones_str = f"{interacciones_totales:,}".replace(",", ".")
    promedio_str = str(promedio_interacciones).replace(".", ",")

    # Los casos en revisión no cuentan como rechazo ni como lead en riesgo.
    leads_en_riesgo = rechazados

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(f"""
        <div class="autivo-kpi-card">
            <div class="autivo-kpi-header">
                <span class="autivo-kpi-title">Total Conversations</span>
                <span class="autivo-kpi-icon">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
                </span>
            </div>
            <div>
                <div class="autivo-kpi-value">{total_convs if total_convs > 0 else "0"}</div>
                <div class="autivo-kpi-footer">Conversaciones registradas</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col2:
        st.markdown(f"""
        <div class="autivo-kpi-card">
            <div class="autivo-kpi-header">
                <span class="autivo-kpi-title">Interactions</span>
                <span class="autivo-kpi-icon">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
                </span>
            </div>
            <div>
                <div class="autivo-kpi-value">{interacciones_str if total_convs > 0 else "0"}</div>
                <div class="autivo-kpi-footer">Mensajes procesados por IA</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col3:
        st.markdown(f"""
        <div class="autivo-kpi-card">
            <div class="autivo-kpi-header">
                <span class="autivo-kpi-title">Mean Interactions by User</span>
                <span class="autivo-kpi-icon">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                </span>
            </div>
            <div>
                <div class="autivo-kpi-value">{promedio_str if total_convs > 0 else "0"}</div>
                <div class="autivo-kpi-footer">Promedio de turnos de diálogo</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_col4:
        st.markdown(f"""
        <div class="autivo-kpi-card" style="border-left: 3px solid #EF4444;">
            <div class="autivo-kpi-header">
                <span class="autivo-kpi-title" style="color:#DC2626;">Leads en Riesgo de Fuga</span>
                <span class="autivo-kpi-icon" style="color:#DC2626;">
                    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                </span>
            </div>
            <div>
                <div class="autivo-kpi-value" style="color:#DC2626;">{leads_en_riesgo}</div>
                <div class="autivo-kpi-footer">{revisiones} casos requieren revisión técnica</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 3.1 SEMÁFORO DE SALUD OPERATIVA Y CALIDAD SLA (EXECUTIVE HEALTH SCORE)
    # --------------------------------------------------------------------------
    if not df_actual.empty:
        if evaluaciones_validas == 0:
            sla_tag = "⚪ SIN EVALUACIONES VÁLIDAS"
            sla_color = "#475569"
            sla_bg = "#F1F5F9"
            sla_border = "#CBD5E1"
            sla_text = f"{revisiones} casos requieren revisión antes de calcular efectividad."
        elif tasa_efectividad >= 85.0:
            sla_tag = "🟢 OPERACIÓN SALUDABLE"
            sla_color = "#15803D"
            sla_bg = "#F0FDF4"
            sla_border = "#BBF7D0"
            sla_text = f"Los agentes virtuales registran una tasa de efectividad óptima del <b>{tasa_efectividad:.1f}%</b>. Flujos de cotización fluidos y sin fricción técnica. <b>Recomendación:</b> Mantener inversión publicitaria y pauta activa."
        elif tasa_efectividad >= 70.0:
            sla_tag = "🟡 EN OBSERVACIÓN (ATENCIÓN REQUERIDA)"
            sla_color = "#B45309"
            sla_bg = "#FFFBEB"
            sla_border = "#FDE68A"
            sla_text = f"Efectividad en <b>{tasa_efectividad:.1f}%</b>. Se detectan deserciones esporádicas o dudas en financiamiento. <b>Recomendación:</b> Calibrar menús de validación y catálogo de modelos antes de escalar campañas."
        else:
            sla_tag = "🔴 ALERTA CRÍTICA (ACCIÓN PRIORITARIA)"
            sla_color = "#B91C1C"
            sla_bg = "#FEF2F2"
            sla_border = "#FECACA"
            sla_text = f"Efectividad crítica del <b>{tasa_efectividad:.1f}%</b>. <b>{rechazados} clientes</b> no completaron su cotización debido a incidencias del bot. <b>Recomendación:</b> Priorizar revisión técnica de los flujos de conversación."

        st.markdown(f"""
        <div style="background:{sla_bg}; border:1px solid {sla_border}; border-radius:10px; padding:12px 18px; margin-bottom:18px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:12px; flex:1; min-width:280px;">
                <span style="background:{sla_color}; color:#FFFFFF; font-weight:800; font-size:0.75rem; padding:4px 10px; border-radius:20px; letter-spacing:0.5px; white-space:nowrap;">
                    {sla_tag}
                </span>
                <span style="font-size:0.86rem; color:#1E293B;">
                    {sla_text}
                </span>
            </div>
            <div style="font-size:0.8rem; font-weight:700; color:{sla_color}; white-space:nowrap;">
                Meta Autivo: ≥ 80% OK
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------------------------
    # 4. GRÁFICO PRINCIPAL: CONVERSATIONS & INTERACTIONS (DINÁMICO POR MARCA)
    # --------------------------------------------------------------------------
    with st.container(border=True):
        st.markdown(
            '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">'
            '<span style="font-size:1.05rem; font-weight:700; color:#0F172A;">Conversations & Interactions - Rendimiento y Volumen por Marca</span>'
            '<span style="font-size:0.8rem; font-weight:600; color:#1A62E8; background:#EFF6FF; border:1px solid #DBEAFE; padding:4px 10px; border-radius:12px;">📊 Enlace en vivo con auditorías</span>'
            '</div>',
            unsafe_allow_html=True
        )

        df_validas = df_actual[df_actual["marca"] != "Error de Conexión"] if not df_actual.empty and "marca" in df_actual.columns else pd.DataFrame()
        
        if not df_validas.empty:
            # Calcular métricas dinámicas directamente vinculadas a los porcentajes reales de cada bot
            filas_marcas = []
            for m, grupo in df_validas.groupby("marca"):
                cnt = len(grupo)
                aprob = len(grupo[grupo["estado"] == "Aprobado"])
                rechaz = len(grupo[grupo["estado"] == "Rechazado"])
                revision = len(grupo[grupo["estado"] == "Revisión"])
                evaluadas = aprob + rechaz
                pct = (aprob / evaluadas * 100) if evaluadas > 0 else 0.0
                filas_marcas.append({
                    "Marca": f"Bot {m}",
                    "Marca_Simple": m,
                    "Efectividad (%)": round(pct, 1),
                    "Conversaciones": cnt,
                    "Evaluaciones válidas": evaluadas,
                    "Aprobadas": aprob,
                    "Rechazadas": rechaz,
                    "Por revisar": revision
                })
            
            df_chart_marcas = pd.DataFrame(filas_marcas).sort_values(by="Efectividad (%)", ascending=True)

            # Capa base
            chart_base = alt.Chart(df_chart_marcas).encode(
                x=alt.X('Marca:N', title=None, axis=alt.Axis(labelAngle=0, labelColor='#334155', labelFontWeight='bold', labelFontSize=12))
            )

            # Barras individuales por marca con su color corporativo
            chart_bars = chart_base.mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=46, opacity=0.85).encode(
                y=alt.Y('Efectividad (%):Q', title='Efectividad (% Aprobadas)', scale=alt.Scale(domain=[0, 115]), axis=alt.Axis(gridColor='#F1F5F9', labelColor='#64748B')),
                color=alt.Color('Marca_Simple:N', scale=alt.Scale(domain=list(COLORES_MARCAS.keys()), range=list(COLORES_MARCAS.values())), legend=None),
                tooltip=['Marca', 'Efectividad (%)', 'Conversaciones', 'Evaluaciones válidas', 'Aprobadas', 'Rechazadas', 'Por revisar']
            )

            # Etiqueta de porcentaje exacto sobre cada barra
            chart_text = chart_base.mark_text(dy=-10, fontSize=12, fontWeight='bold', color='#1E293B').encode(
                y=alt.Y('Efectividad (%):Q'),
                text=alt.Text('Efectividad (%):Q', format='.1f')
            )

            # Línea conectora de tendencia
            chart_line = chart_base.mark_line(color='#1A62E8', strokeWidth=3, interpolate='monotone', opacity=0.55).encode(
                y=alt.Y('Efectividad (%):Q')
            )

            # Puntos destacados de cada marca
            chart_points = chart_base.mark_circle(size=130, opacity=1).encode(
                y=alt.Y('Efectividad (%):Q'),
                color=alt.Color('Marca_Simple:N', scale=alt.Scale(domain=list(COLORES_MARCAS.keys()), range=list(COLORES_MARCAS.values())), legend=None),
                tooltip=['Marca', 'Efectividad (%)', 'Conversaciones', 'Aprobadas', 'Rechazadas']
            )

            # Línea de meta de referencia Autivo (80%)
            df_rule = pd.DataFrame({'y': [80]})
            chart_rule = alt.Chart(df_rule).mark_rule(strokeDash=[4, 4], color='#94A3B8', strokeWidth=1.5).encode(y='y:Q')
            df_rule_txt = pd.DataFrame({'y': [82], 'text': ['Meta Óptima (80%)']})
            chart_rule_text = alt.Chart(df_rule_txt).mark_text(align='left', dx=10, color='#64748B', fontSize=10, fontWeight=600).encode(y='y:Q', text='text:N')

            final_chart = (chart_bars + chart_text + chart_line + chart_points + chart_rule + chart_rule_text).properties(
                height=300
            ).configure_view(
                strokeOpacity=0
            )

            st.altair_chart(final_chart, use_container_width=True)

            # Leyenda tipo píldoras corporativas (sin indentación de markdown para renderizar HTML directo)
            legend_pills = []
            for _, row in df_chart_marcas.iterrows():
                m_nombre = row["Marca"]
                m_simple = row["Marca_Simple"]
                color = COLORES_MARCAS.get(m_simple, "#1A62E8")
                pct_val = row["Efectividad (%)"]
                cnt_val = row["Conversaciones"]
                legend_pills.append(
                    f'<span style="display:inline-flex; align-items:center; gap:6px; background:#F8FAFC; border:1px solid #E2E8F0; padding:4px 12px; border-radius:20px; font-size:0.82rem; color:#334155; margin:3px;">'
                    f'<span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:{color};"></span>'
                    f'<b>{m_nombre}</b>: {pct_val}% OK ({cnt_val} chats)'
                    f'</span>'
                )
            legend_html = "".join(legend_pills)
            st.markdown(
                f'<div style="display:flex; justify-content:center; align-items:center; flex-wrap:wrap; gap:4px; margin-top:8px; margin-bottom:4px;">{legend_html}</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("👋 Sube y audita PDFs para visualizar las curvas y efectividad por marca.")

    # --------------------------------------------------------------------------
    # 5. FILA INFERIOR DIVIDIDA: TOP THEMES & START MENU BUTTON CLICKS
    # --------------------------------------------------------------------------
    col_bottom_left, col_bottom_right = st.columns([1, 1])

    with col_bottom_left:
        st.markdown("""
        <div class="autivo-card">
            <div class="autivo-card-title">
                Top Themes
            </div>
        """, unsafe_allow_html=True)

        # Temas 100% reales calculados desde las conversaciones de los usuarios
        temas_reales = []
        if not df_actual.empty and "tema_conversacion" in df_actual.columns:
            total_chats = len(df_actual)
            conteo_temas = df_actual["tema_conversacion"].value_counts()
            for tema_nom, cant in conteo_temas.items():
                pct = round((cant / total_chats) * 100, 1)
                temas_reales.append((tema_nom, cant, pct))

        if temas_reales:
            for nombre_tema, cant, pct in temas_reales:
                ancho_barra = min(max(pct, 4), 100)
                st.markdown(f"""
                <div class="theme-item">
                    <div class="theme-header">
                        <span class="theme-label">{nombre_tema}</span>
                        <span class="theme-count">{cant} ({pct}%)</span>
                    </div>
                    <div class="theme-bar-track">
                        <div class="theme-bar-fill" style="width: {ancho_barra}%;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center; padding: 28px 12px; color:#94A3B8; font-size:0.86rem;">
                👋 Sube conversaciones en PDF para clasificar automáticamente los temas consultados por los clientes.
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_bottom_right:
        st.markdown("""
        <div class="autivo-card">
            <div class="autivo-card-title">
                Rendimiento por Marca
            </div>
        """, unsafe_allow_html=True)

        tab_clicks, tab_podio = st.tabs(["📊 Conversaciones por Marca", "🏆 Leaderboard de Marcas"])

        with tab_clicks:
            df_clicks = pd.DataFrame(columns=["Marca", "Conversaciones", "Tasa de aprobación"])

            if not df_actual.empty and "marca" in df_actual.columns:
                resumen_marcas = []
                for m, grupo in df_actual.groupby("marca"):
                    if m == "Error de Conexión":
                        continue
                    cnt = len(grupo)
                    aprob = len(grupo[grupo["estado"] == "Aprobado"])
                    rechaz = len(grupo[grupo["estado"] == "Rechazado"])
                    evaluadas = aprob + rechaz
                    pct_aprob = (aprob / evaluadas * 100) if evaluadas > 0 else 0
                    resumen_marcas.append({
                        "Marca": f"Bot {m}",
                        "Conversaciones": cnt,
                        "Tasa de aprobación": f"{pct_aprob:.0f}%" if evaluadas else "—"
                    })
                if resumen_marcas:
                    df_clicks = pd.DataFrame(resumen_marcas)
            if df_clicks.empty:
                st.info("No hay conversaciones auditadas para comparar.")
            else:
                st.dataframe(df_clicks, hide_index=True, use_container_width=True)

        with tab_podio:
            if not df_actual.empty and "marca" in df_actual.columns:
                lista_ranking = []
                for m, grp in df_actual.groupby("marca"):
                    if m == "Error de Conexión":
                        continue
                    tot = len(grp)
                    ok = len(grp[grp["estado"] == "Aprobado"])
                    rechaz = len(grp[grp["estado"] == "Rechazado"])
                    evaluadas = ok + rechaz
                    p_ok = (ok / evaluadas * 100) if evaluadas > 0 else 0
                    hum = len(grp[grp["solicito_humano"] == True]) if "solicito_humano" in grp.columns else 0
                    p_hum = (hum / tot * 100) if tot > 0 else 0
                    lista_ranking.append({
                        "marca": m,
                        "tot": tot,
                        "ok": ok,
                        "pct": p_ok,
                        "hum_pct": p_hum
                    })
                lista_ranking.sort(key=lambda x: (x["pct"], x["tot"]), reverse=True)
                medallas = ["🥇 1°", "🥈 2°", "🥉 3°", "4°", "5°", "6°", "7°", "8°"]
                for idx, item in enumerate(lista_ranking):
                    med = medallas[idx] if idx < len(medallas) else f"{idx+1}°"
                    m_color = COLORES_MARCAS.get(item["marca"], "#1A62E8")
                    color_status = "#15803D" if item["pct"] >= 80 else ("#B45309" if item["pct"] >= 60 else "#B91C1C")
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 12px; background:#F8FAFC; border-radius:8px; margin-bottom:6px; border-left:4px solid {m_color}; border:1px solid #E2E8F0;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            <span style="font-size:0.95rem; font-weight:700;">{med}</span>
                            <span style="font-weight:700; color:#1E293B; font-size:0.88rem;">Bot {item['marca']}</span>
                            <span style="font-size:0.75rem; color:#64748B;">({item['tot']} chats)</span>
                        </div>
                        <div style="text-align:right;">
                            <span style="font-weight:800; color:{color_status}; font-size:0.92rem;">{item['pct']:.0f}% OK</span>
                            <div style="font-size:0.7rem; color:#64748B;">{item['hum_pct']:.0f}% pidió asesor</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("👋 Sube conversaciones para visualizar el podio de rendimiento.")

        st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# VISTA: 💬 RECURRENT THEMES (ANÁLISIS PROFUNDO DE TEMAS Y FALLAS)
# ==============================================================================
elif seccion_seleccionada == "💬 Recurrent Themes":
    st.markdown("""
    <div class="autivo-card">
        <h2 style="font-size:1.4rem; font-weight:700; color:#0F172A; margin:0 0 6px 0;">
            💬 Recurrent Themes & Alertas de Calidad
        </h2>
        <p style="font-size:0.88rem; color:#64748B; margin:0;">
            Patrones conversacionales recurrentes y análisis diagnóstico de puntos de fricción comercial.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if df_global.empty:
        st.info("Aún no hay datos de auditoría disponibles. Ve a '🚀 Subir / Auditar PDFs' para comenzar.")
    else:
        col_th1, col_th2 = st.columns(2)
        with col_th1:
            st.markdown("""
            <div class="autivo-card">
                <div class="autivo-card-title">Distribución por Causa de Falla</div>
            """, unsafe_allow_html=True)
            if "categoria_falla" in df_global.columns:
                df_fallas_raw = df_global[(df_global["estado"] == "Rechazado") & (df_global["categoria_falla"] != "Ninguna")]
                if not df_fallas_raw.empty:
                    fallas_df = df_fallas_raw["categoria_falla"].value_counts().reset_index()
                    fallas_df.columns = ["Causa de Falla", "Cantidad"]
                    
                    chart_f = alt.Chart(fallas_df).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                        x=alt.X("Causa de Falla:N", title=None, axis=alt.Axis(labelAngle=-25, labelColor="#475569", labelFontWeight="bold")),
                        y=alt.Y("Cantidad:Q", title="Ocurrencias", axis=alt.Axis(labelColor="#475569", gridColor="#F1F5F9")),
                        color=alt.Color("Causa de Falla:N", scale=alt.Scale(domain=list(COLORES_FALLAS.keys()), range=list(COLORES_FALLAS.values())), legend=None),
                        tooltip=["Causa de Falla", "Cantidad"]
                    ).properties(height=280)
                    st.altair_chart(chart_f, use_container_width=True)
                else:
                    st.success("✓ No se registraron fallas en las conversaciones evaluadas.")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_th2:
            st.markdown("""
            <div class="autivo-card">
                <div class="autivo-card-title">Volumen de Auditoría por Marca</div>
            """, unsafe_allow_html=True)
            if "marca" in df_global.columns:
                df_marcas_raw = df_global[df_global["marca"] != "Error de Conexión"]
                if not df_marcas_raw.empty:
                    marcas_df = df_marcas_raw["marca"].value_counts().reset_index()
                    marcas_df.columns = ["Marca", "Evaluaciones"]
                    
                    chart_m = alt.Chart(marcas_df).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                        x=alt.X("Marca:N", title=None, axis=alt.Axis(labelAngle=-25, labelColor="#475569", labelFontWeight="bold")),
                        y=alt.Y("Evaluaciones:Q", title="Total Evaluadas", axis=alt.Axis(labelColor="#475569", gridColor="#F1F5F9")),
                        color=alt.Color("Marca:N", scale=alt.Scale(domain=list(COLORES_MARCAS.keys()), range=list(COLORES_MARCAS.values())), legend=None),
                        tooltip=["Marca", "Evaluaciones"]
                    ).properties(height=280)
                    st.altair_chart(chart_m, use_container_width=True)
                else:
                    st.info("Sin marcas auditadas aún.")
            st.markdown("</div>", unsafe_allow_html=True)


# ==============================================================================
# VISTA: 📄 TRANSCRIPTIONS (REGISTRO DETALLADO E INSPECTOR TÉCNICO)
# ==============================================================================
elif seccion_seleccionada == "📄 Transcriptions":
    st.markdown("""
    <div class="autivo-card">
        <h2 style="font-size:1.4rem; font-weight:700; color:#0F172A; margin:0 0 6px 0;">
            📄 Transcriptions & Auditoría Detallada
        </h2>
        <p style="font-size:0.88rem; color:#64748B; margin:0;">
            Explora las conversaciones individuales, transcripciones y el diagnóstico del motor de IA.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if df_global.empty:
        st.info("Aún no hay transcripciones auditadas. Ve a '🚀 Subir / Auditar PDFs' para subir archivos.")
    else:
        # Filtros de búsqueda
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            m_list = ["Todas"] + sorted([m for m in df_global["marca"].dropna().unique()])
            filtro_m = st.selectbox("Marca:", m_list)
        with f_col2:
            filtro_est = st.selectbox("Estado QA:", ["Todos", "Aprobado", "Rechazado", "Revisión"])
        with f_col3:
            cats = ["Todas"] + sorted([c for c in df_global["categoria_falla"].dropna().unique()])
            filtro_cat = st.selectbox("Categoría Falla:", cats)

        df_view = df_global.copy()
        if filtro_m != "Todas":
            df_view = df_view[df_view["marca"] == filtro_m]
        if filtro_est != "Todos":
            df_view = df_view[df_view["estado"] == filtro_est]
        if filtro_cat != "Todas":
            df_view = df_view[df_view["categoria_falla"] == filtro_cat]

        cols_mostrar = [c for c in ["archivo", "marca", "vehiculo_cotizado", "cliente_nombre", "estado", "categoria_falla", "fecha_evaluacion"] if c in df_view.columns]
        st.dataframe(df_view[cols_mostrar], use_container_width=True)

        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

        # Inspector Individual
        archivos_disponibles = df_view["archivo"].tolist() if "archivo" in df_view.columns else []
        if archivos_disponibles:
            st.markdown("<div class='autivo-card-title'>🔍 Inspector Técnico de Conversación</div>", unsafe_allow_html=True)
            archivo_sel = st.selectbox("Selecciona una conversación para inspeccionar a fondo:", archivos_disponibles)
            fila = df_global[df_global["archivo"] == archivo_sel].iloc[0]

            col_insp1, col_insp2 = st.columns([1, 1.8])
            with col_insp1:
                if fila.get("estado") == "Aprobado":
                    badge_html = "<span style='background:#DCFCE7; color:#15803D; font-weight:700; padding:4px 10px; border-radius:12px; font-size:0.8rem;'>APROBADO</span>"
                elif fila.get("estado") == "Rechazado":
                    badge_html = "<span style='background:#FEE2E2; color:#B91C1C; font-weight:700; padding:4px 10px; border-radius:12px; font-size:0.8rem;'>RECHAZADO</span>"
                else:
                    badge_html = "<span style='background:#FEF3C7; color:#92400E; font-weight:700; padding:4px 10px; border-radius:12px; font-size:0.8rem;'>REVISIÓN</span>"
                archivo_html = html.escape(str(fila.get("archivo", "")))
                marca_html = html.escape(str(fila.get("marca", "")))
                vehiculo_html = html.escape(str(fila.get("vehiculo_cotizado", "")))
                cliente_html = html.escape(str(fila.get("cliente_nombre", "No detectado")))
                canal_html = html.escape(str(fila.get("canal", "WhatsApp")))
                pais_html = html.escape(str(fila.get("pais", "Chile")))
                categoria_html = html.escape(str(fila.get("categoria_falla", "Ninguna")))
                st.markdown(f"""
                <div class="autivo-card" style="padding:18px 20px;">
                    <div style="font-weight:700; font-size:0.95rem; color:#0F172A; margin-bottom:12px; border-bottom:1px solid #E2E8F0; padding-bottom:8px;">
                        📄 Ficha de Conversación
                    </div>
                    <div style="font-size:0.84rem; line-height:2;">
                        <div><b style="color:#64748B;">Archivo:</b> <code style="font-size:0.75rem;">{archivo_html}</code></div>
                        <div><b style="color:#64748B;">Marca:</b> <span style="color:#1A62E8; font-weight:700;">{marca_html}</span></div>
                        <div><b style="color:#64748B;">Vehículo:</b> <b>{vehiculo_html}</b></div>
                        <div><b style="color:#64748B;">Cliente:</b> {cliente_html}</div>
                        <div><b style="color:#64748B;">Canal / País:</b> {canal_html} | {pais_html}</div>
                        <div style="margin-top:8px;"><b style="color:#64748B;">Dictamen:</b> {badge_html}</div>
                        <div style="margin-top:4px;"><b style="color:#64748B;">Causa Falla:</b> <span style="color:#DC2626; font-weight:600;">{categoria_html}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("✏️ Reasignar Marca / Ajustar Dictamen"):
                    st.caption("Modifica la marca o dictamen si el PDF no traía marca explícita:")
                    marcas_disponibles_edit = ["Hyundai", "JAC", "Jeep", "Opel", "Peugeot", "Citroën", "Fiat", "RAM", "Geely", "Lippi", "Omni", "No Identificada"]
                    marca_actual = str(fila.get("marca", "Hyundai"))
                    idx_marca = marcas_disponibles_edit.index(marca_actual) if marca_actual in marcas_disponibles_edit else 0
                    nueva_marca = st.selectbox("Marca Asignada:", marcas_disponibles_edit, index=idx_marca, key=f"sel_m_{archivo_sel}")
                    
                    estados_edit = ["Revisión", "Rechazado", "Aprobado"]
                    idx_est = estados_edit.index(fila.get("estado")) if fila.get("estado") in estados_edit else 0
                    nuevo_estado = st.selectbox("Estado QA:", estados_edit, index=idx_est, key=f"sel_est_{archivo_sel}")
                    
                    fallas_edit = ["Falla Técnica del Bot", "Bucle de Validación", "Alucinación o Error de Catálogo", "Frustración del Cliente", "Ninguna"]
                    cat_actual = str(fila.get("categoria_falla", "Falla Técnica del Bot"))
                    idx_cat = fallas_edit.index(cat_actual) if cat_actual in fallas_edit else 0
                    nueva_cat = st.selectbox("Causa de Falla:", fallas_edit, index=idx_cat, key=f"sel_cat_{archivo_sel}")
                    
                    if st.button("💾 Guardar Cambios", key=f"btn_save_{archivo_sel}", use_container_width=True):
                        try:
                            with open(CONFIG["REPORTE_JSON"], "r", encoding="utf-8") as f_json:
                                lista_actual = json.load(f_json)
                            for item in lista_actual:
                                if item.get("archivo") == archivo_sel:
                                    item["marca"] = nueva_marca
                                    item["estado"] = nuevo_estado
                                    item["categoria_falla"] = nueva_cat if nuevo_estado == "Rechazado" else ("Error de Procesamiento" if nuevo_estado == "Revisión" else "Ninguna")
                                    if nuevo_estado in ("Aprobado", "Revisión"):
                                        item["errores"] = []
                                    if nuevo_estado == "Revisión":
                                        item["motivo_revision"] = "Pendiente de revisión manual"
                                    else:
                                        item.pop("motivo_revision", None)
                            from procesar_pdf import generar_reportes
                            generar_reportes(lista_actual, CONFIG["REPORTE_EXCEL"], CONFIG["REPORTE_JSON"])
                            st.success("✓ Conversación actualizada exitosamente.")
                            st.rerun()
                        except Exception as ex_edit:
                            st.error(f"Error al guardar: {ex_edit}")

            with col_insp2:
                tab_replay, tab_diag = st.tabs(["💬 Resumen del diálogo", "⚖️ Diagnóstico Ejecutivo"])
                
                with tab_replay:
                    dialogo = fila.get("dialogo_resumen", [])
                    if isinstance(dialogo, list) and len(dialogo) > 0:
                        st.caption("Resumen sintetizado por IA; no es una transcripción literal. Consulta el archivo original para verificar el contenido.")
                        marca_chat = html.escape(str(fila.get("marca", "Autivo")))
                        m_color = COLORES_MARCAS.get(marca_chat, "#1A62E8")
                        
                        burbujas_html = []
                        for turno in dialogo:
                            emisor_raw = str(turno.get("emisor", "Asistente"))
                            emisor = html.escape(emisor_raw)
                            texto = html.escape(str(turno.get("texto", "")))
                            es_falla = turno.get("es_falla", False)
                            clase_cliente = emisor_raw.lower() in ["cliente", "usuario", "user"]

                            if clase_cliente:
                                burbujas_html.append(
                                    f'<div style="display:flex; justify-content:flex-end; margin-bottom:10px;">'
                                    f'<div style="background:#D9FDD3; color:#111B21; border-radius:8px 8px 0 8px; padding:8px 12px; max-width:78%; box-shadow:0 1px 1px rgba(0,0,0,0.06); font-size:0.87rem; line-height:1.4;">'
                                    f'<div style="font-size:0.68rem; color:#52605A; font-weight:700; margin-bottom:4px;">{emisor}</div><div>{texto}</div>'
                                    f'</div></div>'
                                )
                            else:
                                if es_falla:
                                    burbujas_html.append(
                                        f'<div style="display:flex; justify-content:flex-start; margin-bottom:10px;">'
                                        f'<div style="background:#FEF2F2; color:#991B1B; border:1.5px solid #EF4444; border-radius:8px 8px 8px 0; padding:10px 14px; max-width:82%; box-shadow:0 1px 2px rgba(239,68,68,0.15); font-size:0.87rem; line-height:1.4;">'
                                        f'<div style="display:inline-block; background:#DC2626; color:#FFFFFF; font-size:0.68rem; font-weight:800; padding:2px 8px; border-radius:10px; margin-bottom:6px; letter-spacing:0.4px;">PUNTO MARCADO POR IA</div>'
                                        f'<div style="font-size:0.68rem; color:#52605A; font-weight:700; margin-bottom:4px;">{emisor}</div><div style="font-weight:600;">{texto}</div>'
                                        f'</div></div>'
                                    )
                                else:
                                    burbujas_html.append(
                                        f'<div style="display:flex; justify-content:flex-start; margin-bottom:10px;">'
                                        f'<div style="background:#FFFFFF; color:#111B21; border-radius:8px 8px 8px 0; padding:8px 12px; max-width:78%; box-shadow:0 1px 1px rgba(0,0,0,0.06); font-size:0.87rem; line-height:1.4;">'
                                        f'<div style="font-size:0.68rem; color:#52605A; font-weight:700; margin-bottom:4px;">{emisor}</div><div>{texto}</div>'
                                        f'</div></div>'
                                    )
                        
                        chat_content = "".join(burbujas_html)
                        if fila.get("estado") == "Aprobado":
                            status_banner = '<div style="background:#DCFCE7; color:#15803D; font-weight:700; text-align:center; padding:7px 12px; border-radius:8px; font-size:0.8rem; margin-top:10px;">Evaluación aprobada según el criterio QA</div>'
                        elif fila.get("estado") == "Rechazado":
                            causa = html.escape(str(fila.get("categoria_falla", "Incidencia")))
                            status_banner = f'<div style="background:#FEE2E2; color:#B91C1C; font-weight:700; text-align:center; padding:7px 12px; border-radius:8px; font-size:0.8rem; margin-top:10px;">Falla detectada · {causa}</div>'
                        else:
                            status_banner = '<div style="background:#FEF3C7; color:#92400E; font-weight:700; text-align:center; padding:7px 12px; border-radius:8px; font-size:0.8rem; margin-top:10px;">Pendiente de revisión manual</div>'

                        st.markdown(f"""
                        <div style="background:#EFEAE2; border-radius:12px; border:1px solid #D1D7DB; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.05); max-width:620px; margin:0 auto;">
                            <div style="background:#075E54; padding:10px 14px; display:flex; align-items:center; gap:10px; color:#FFFFFF;">
                                <div style="width:34px; height:34px; border-radius:50%; background:{m_color}; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:0.9rem; color:#FFF;">
                                    {marca_chat[:2].upper()}
                                </div>
                                <div>
                                    <div style="font-weight:700; font-size:0.92rem; color:#FFFFFF;">Resumen de conversación</div>
                                    <div style="font-size:0.72rem; color:#A7F3D0;">{marca_chat}</div>
                                </div>
                            </div>
                            <div style="padding:16px 14px; min-height:260px;">
                                {chat_content}
                                {status_banner}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("No hay un resumen de diálogo disponible. El diagnóstico y la evidencia se muestran en la pestaña siguiente.")

                with tab_diag:
                    st.markdown(f"""
                    <div class="autivo-card" style="padding:18px 20px;">
                        <div style="font-weight:700; font-size:0.95rem; color:#0F172A; margin-bottom:12px; border-bottom:1px solid #E2E8F0; padding-bottom:8px;">
                            ⚖️ Diagnóstico Ejecutivo de la IA
                        </div>
                        <p style="font-size:0.9rem; color:#334155; line-height:1.6; background:#F8FAFC; padding:14px 16px; border-radius:8px; border-left:4px solid #1A62E8; margin-bottom:14px;">
                            "{html.escape(str(fila.get('observacion', 'Sin observaciones adicionales.')))}"
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    errores = fila.get("errores", [])
                    if errores:
                        st.markdown("<div style='font-size:0.85rem; font-weight:700; color:#0F172A; margin-bottom:6px;'>🚨 Fallas Críticas Identificadas:</div>", unsafe_allow_html=True)
                        for err in errores:
                            st.error(f"• {err}")
                    elif fila.get("estado") == "Aprobado":
                        st.success("Evaluación aprobada según el criterio QA, sin fallas críticas identificadas.")
                    elif fila.get("estado") == "Revisión":
                        motivo_revision = fila.get("motivo_revision", "Se requiere revisión manual.")
                        st.warning(f"Revisión pendiente: {motivo_revision}")
                    else:
                        st.info("El dictamen es rechazado, pero no se registraron errores estructurados. Revisa la observación del juez.")
