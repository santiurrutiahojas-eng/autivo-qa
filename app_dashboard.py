#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard de Auditoría QA Automotriz con IA (Google Gemini 3.6 Flash)
Auditoría inteligente multimarca y multicanal (WhatsApp y Web).
"""

import os
import json
import zipfile
import pandas as pd
import streamlit as st
import importlib

import procesar_pdf
importlib.reload(procesar_pdf)
from procesar_pdf import (
    procesar_pipeline,
    cargar_api_key_guardada,
    guardar_api_key,
    CONFIG
)

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ==============================================================================
st.set_page_config(
    page_title="Autivo QA - Auditoría Inteligente de Ventas",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS profesionales
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1B365D 0%, #2A5298 100%);
        color: white;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .metric-num {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 4px 0;
    }
    .metric-text {
        font-size: 0.9rem;
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-ok {
        background-color: #D4EDDA;
        color: #155724;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }
    .badge-fail {
        background-color: #F8D7DA;
        color: #721C24;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# BARRA LATERAL (CONFIGURACIÓN Y ACCIONES)
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/car--v1.png", width=64)
    st.title("Autivo QA")
    st.caption("Auditoría Autónoma de Bots con Gemini 3.6 Flash")
    st.markdown("---")
    
    # 1. API Key de Gemini
    st.subheader("🔑 Google Gemini API")
    key_guardada = cargar_api_key_guardada()
    gemini_key = st.text_input(
        "Gemini API Key:",
        value=key_guardada,
        type="password",
        help="Clave gratuita de Google AI Studio (https://aistudio.google.com)"
    )
    if gemini_key and gemini_key != key_guardada:
        guardar_api_key(gemini_key)
        st.success("✓ Clave guardada correctamente.")

    st.markdown("---")
    
    # 2. Carga de Archivos
    st.subheader("📄 Subir Conversaciones (PDF)")
    archivos_subidos = st.file_uploader(
        "Arrastra uno o varios PDFs aquí:",
        type=["pdf", "txt", "zip"],
        accept_multiple_files=True,
        help="Puedes subir el PDF de cualquier marca (Peugeot, Opel, Hyundai, Citroën, Fiat, etc.)"
    )

    btn_evaluar = st.button("🚀 Iniciar Auditoría QA", type="primary", use_container_width=True)

    st.markdown("---")
    
    # 3. Descargar Excel
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
    # 4. Reinicio de Historial
    with st.expander("⚙️ Empezar Nueva Marca / Reiniciar"):
        st.caption("Borra las evaluaciones actuales para evaluar una marca nueva de cero:")
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
        st.error("⚠️ Por favor ingresa tu API Key de Gemini en la barra lateral para continuar.")
    else:
        carpeta_destino = CONFIG["CARPETA_PDFS"]
        os.makedirs(carpeta_destino, exist_ok=True)
        rutas_a_evaluar = []

        # Si el usuario subió archivos en este momento, evaluar exclusivamente esos archivos
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

        # Barra de progreso
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
# ENCABEZADO Y KPIS DEL DASHBOARD
# ==============================================================================
st.title("🚗 Auditoría Inteligente de Calidad (QA) Automotriz")
st.markdown("Evaluación autónoma con IA para **Peugeot, Opel, Citroën, Fiat, Hyundai, JAC, Jeep, RAM y más**.")

if df.empty:
    st.info("👋 **Aún no hay conversaciones auditadas.** Sube un archivo PDF o una transcripción en la barra lateral izquierda y presiona **'🚀 Iniciar Auditoría QA'** para comenzar.")
else:
    # Métricas principales
    total = len(df)
    aprobados = len(df[df["estado"] == "Aprobado"])
    rechazados = len(df[df["estado"] == "Rechazado"])
    tasa_exito = (aprobados / total * 100) if total > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-text">Total Evaluados</div>
            <div class="metric-num">{total}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
            <div class="metric-text">Aprobados (Éxito)</div>
            <div class="metric-num">{aprobados}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);">
            <div class="metric-text">Rechazados (Fallas)</div>
            <div class="metric-num">{rechazados}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%);">
            <div class="metric-text">Tasa de Aprobación</div>
            <div class="metric-num">{tasa_exito:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ==============================================================================
    # GRÁFICOS DINÁMICOS
    # ==============================================================================
    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        st.subheader("📊 Distribución por Marca Detectada")
        if "marca" in df.columns:
            marca_counts = df["marca"].value_counts()
            st.bar_chart(marca_counts, color="#1B365D")

    with col_chart2:
        st.subheader("⚠️ Motivos de Falla / Categoría")
        if "categoria_falla" in df.columns:
            fallas = df[df["estado"] == "Rechazado"]["categoria_falla"].value_counts()
            if not fallas.empty:
                st.bar_chart(fallas, color="#F45C43")
            else:
                st.success("🎉 No se registraron fallas en el lote evaluado.")

    st.markdown("---")

    # ==============================================================================
    # TABLA DETALLADA CON FILTROS
    # ==============================================================================
    st.subheader("📋 Detalle de Evaluaciones QA")
    
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
    # INSPECTOR DE CONVERSACIÓN
    # ==============================================================================
    st.markdown("---")
    st.subheader("🔍 Inspector de Conversación y Dictamen del Juez")
    
    archivos_disponibles = df_filtrado["archivo"].tolist() if "archivo" in df_filtrado.columns else []
    if archivos_disponibles:
        archivo_sel = st.selectbox("Selecciona un chat para ver el desglose completo:", archivos_disponibles)
        fila = df[df["archivo"] == archivo_sel].iloc[0]

        card_col1, card_col2 = st.columns([1, 2])
        with card_col1:
            st.markdown(f"**Archivo:** `{fila.get('archivo', '')}`")
            st.markdown(f"**Marca detectada:** `{fila.get('marca', '')}`")
            st.markdown(f"**Vehículo:** `{fila.get('vehiculo_cotizado', '')}`")
            st.markdown(f"**Canal:** `{fila.get('canal', '')}` | **País:** `{fila.get('pais', '')}`")
            estado = fila.get("estado", "")
            if estado == "Aprobado":
                st.markdown("**Dictamen:** <span class='badge-ok'>APROBADO</span>", unsafe_allow_html=True)
            else:
                st.markdown("**Dictamen:** <span class='badge-fail'>RECHAZADO</span>", unsafe_allow_html=True)
                st.markdown(f"**Causa principal:** `{fila.get('categoria_falla', 'Ninguna')}`")

        with card_col2:
            st.markdown("**Observación del Juez Senior:**")
            st.info(fila.get("observacion", "Sin observaciones adicionales."))

            errores = fila.get("errores", [])
            if errores:
                st.markdown("**Fallas específicas detectadas:**")
                for err in errores:
                    st.error(f"• {err}")
            else:
                st.success("✓ Flujo comercial completado sin errores técnicos ni de negocio.")
