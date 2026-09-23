#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor de Auditoría QA Automotriz con IA (100% Autónomo y Dinámico)
Tecnología: Google Gemini Flash Multimodal (Gemini 3.6 Flash)
Capacidades: Lectura directa de PDFs (texto y capturas/imágenes) y TXTs.
Detección autónoma de marca, modelo, país, canal y fallas comerciales reales.
"""

import os
import re
import json
import glob
import time
import base64
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
from pypdf import PdfReader

# ==============================================================================
# CONFIGURACIÓN GENERAL
# ==============================================================================
CONFIG_FILE = ".config_qa.json"

def cargar_api_key_guardada() -> str:
    """Recupera la API Key desde Streamlit Secrets, session_state, archivo local, env o clave de respaldo."""
    # 0. Session State de Streamlit (si el usuario la ingresó en la app)
    try:
        import streamlit as st
        if hasattr(st, "session_state") and "gemini_api_key" in st.session_state:
            val = str(st.session_state["gemini_api_key"]).strip()
            if val:
                return val
    except Exception:
        pass

    # 1. Streamlit Secrets (Nube)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            val = str(st.secrets["GEMINI_API_KEY"]).strip()
            if val:
                return val
    except Exception:
        pass

    # 2. Archivo de configuración local
    candidatos = [
        CONFIG_FILE,
        os.path.join(os.path.dirname(__file__), CONFIG_FILE),
        r"C:\Users\urruh\OneDrive\Escritorio\Archivos_Autivo_QA\.config_qa.json"
    ]
    for path_cand in candidatos:
        if os.path.exists(path_cand):
            try:
                with open(path_cand, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    val = data.get("gemini_api_key", "").strip()
                    if val:
                        return val
            except Exception:
                pass

    # 3. Variable de entorno
    env_val = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_val:
        return env_val

    return ""


def guardar_api_key(api_key: str):
    """Guarda la API Key localmente para reutilizarla."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"gemini_api_key": api_key.strip()}, f, indent=2)
    except Exception as e:
        print(f"[!] No se pudo guardar la clave local: {e}")

CONFIG = {
    "MODELOS_GEMINI": [
        "gemini-3.6-flash", 
        "gemini-3.5-flash", 
        "gemini-3.7-flash", 
        "gemini-3.8-flash", 
        "gemini-3.1-flash-lite", 
        "gemini-flash-latest"
    ],
    "CARPETA_PDFS": "transcripciones_pdf",
    "REPORTE_EXCEL": "reporte_qa_autivo.xlsx",
    "REPORTE_JSON": "resultados_qa.json",
    "TIMEOUT_SEGUNDOS": 60,
    "MARCAS_REFERENCIA": [
        "Citroën", "Fiat", "Geely", "Hyundai", "JAC", 
        "Jeep", "Lippi", "Omni", "Opel", "Peugeot", "RAM"
    ]
}

# ==============================================================================
# PROMPT UNIVERSAL DEL JUEZ SENIOR QA
# ==============================================================================
PROMPT_AUDITORIA_SISTEMA = """Eres un Auditor Senior de Control de Calidad (QA) para sistemas de ventas automotrices omnicanal (WhatsApp y Web) en Chile y Perú.

Tu objetivo es auditar transcripciones reales (en documento PDF con capturas o texto) de forma 100% autónoma, objetiva y justa.

INSTRUCCIONES CLAVE:
1. DETECCIÓN AUTÓNOMA DE MARCA Y VEHÍCULO:
   - Identifica la marca automotriz que se está comercializando (por ejemplo: Peugeot, Opel, Citroën, Fiat, Hyundai, JAC, Jeep, RAM, Geely, etc.). No asumas ninguna de antemano; reconócela por los nombres de vehículos (ej: Rifter, 208, 2008, Corsa, Mokka, C3, Tucson, Creta, Compass, Rampage, T60), logotipos o mensajes del bot.
   - Identifica el modelo y versión de vehículo cotizado o consultado.

2. CRITERIOS DE EVALUACIÓN (JUSTICIA Y REALISMO):
   - 'Aprobado':
     * El bot logró completar el flujo comercial (identificó el modelo, capturó los datos del cliente y confirmó la cotización o derivación a ejecutivo).
     * REGLA DE ABANDONO DEL CLIENTE: Si el bot respondió cordialmente, formuló una pregunta válida o presentó el menú de opciones del catálogo, y la conversación simplemente se detuvo porque el cliente/usuario dejó de contestar, no hizo clic o abandonó el celular por su cuenta, ESTO NO ES ERROR DEL BOT. En tal caso, califica como 'Aprobado' con categoria_falla 'Ninguna' y observación destacando que el bot atendió correctamente hasta el abandono voluntario del usuario.
   
   - 'Rechazado': ÚNICAMENTE ante fallas reales, técnicas o comerciales imputables al BOT:
     a) 'Bucle de Validación': El bot se queda estancado repitiendo preguntas o menús sin entender respuestas válidas o texto libre del usuario.
     b) 'Falla Técnica del Bot': El bot dejó de responder en medio de una respuesta, se congeló o arrojó un error de sistema interno.
     c) 'Alucinación o Error de Catálogo': El bot ofrece modelos de otra marca no perteneciente, inventa precios o da datos erróneos de financiamiento.
     d) 'Frustración del Cliente': El cliente reclama explícitamente por la mala atención o pide hablar con un humano por incapacidad del bot de asistirlo.

3. FORMATO DE RESPUESTA:
Responde EXCLUSIVAMENTE con un JSON válido con esta estructura:
{
  "marca": "Nombre de la marca identificada",
  "pais": "Chile | Perú | Desconocido",
  "canal": "WhatsApp | Web | Desconocido",
  "estado": "Aprobado | Rechazado",
  "categoria_falla": "Ninguna | Bucle de Validación | Falla Técnica del Bot | Alucinación o Error de Catálogo | Frustración del Cliente",
  "cliente_nombre": "Nombre del cliente si aparece o 'No detectado'",
  "vehiculo_cotizado": "Modelo identificado o 'No detectado'",
  "errores": ["descripción clara del fallo si hubo alguno"],
  "observacion": "Explicación profesional y precisa (1 o 2 oraciones) de lo sucedido."
}"""

# ==============================================================================
# LLAMADAS A GOOGLE GEMINI (REST v1beta CON REINTENTO Y EXPONENTIAL BACKOFF)
# ==============================================================================
def llamar_gemini_api(partes: List[Dict[str, Any]], api_key: str, max_reintentos_por_modelo: int = 3) -> str:
    """Envía la solicitud a Google Gemini vía REST oficial v1beta con reintentos y tolerancia a fallos."""
    ultimo_error = ""
    for modelo in CONFIG["MODELOS_GEMINI"]:
        for intento in range(max_reintentos_por_modelo):
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={api_key.strip()}"
            headers = {
                "Content-Type": "application/json"
            }
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": partes
                }],
                "generationConfig": {
                    "temperature": 0.1
                }
            }

            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=CONFIG["TIMEOUT_SEGUNDOS"]) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8"))
                        candidatos = data.get("candidates", [])
                        if candidatos:
                            partes_resp = candidatos[0].get("content", {}).get("parts", [])
                            textos = [p.get("text", "") for p in partes_resp if "text" in p]
                            return "\n".join(textos)
            except urllib.error.HTTPError as e:
                cuerpo = e.read().decode("utf-8", errors="ignore")
                ultimo_error = f"HTTP {e.code}: {cuerpo}"
                if e.code == 429:
                    # Límite por minuto alcanzado temporalmente: pausar y reintentar con backoff exponencial
                    espera = 4 * (intento + 1)
                    print(f"  [!] Cuota temporal alcanzada (HTTP 429) en {modelo}. Pausando {espera}s antes de reintentar (intento {intento+1}/{max_reintentos_por_modelo})...")
                    time.sleep(espera)
                    continue
                elif e.code in [404, 503]:
                    # Modelo no disponible o sobrecargado, pasar al siguiente modelo
                    break
                else:
                    break
            except Exception as e:
                ultimo_error = str(e)
                time.sleep(2 * (intento + 1))
                continue

    raise RuntimeError(ultimo_error or "No se pudo comunicar con Google Gemini.")

# ==============================================================================
# PROCESAMIENTO Y PREPARACIÓN DE ARCHIVOS (PDF Y TXT)
# ==============================================================================
def extraer_texto_pdf(ruta_pdf: str) -> str:
    """Extrae texto si el PDF tiene capa de texto seleccionable."""
    try:
        reader = PdfReader(ruta_pdf)
        texto = []
        for p in reader.pages:
            t = p.extract_text() or ""
            if t.strip():
                texto.append(t.strip())
        return "\n".join(texto)
    except Exception:
        return ""

def preparar_partes_para_gemini(ruta_archivo: str) -> List[Dict[str, Any]]:
    """
    Prepara el payload multimodal o textual para Gemini.
    Si es PDF, usa visión directa en base64 para interpretar capturas de pantalla
    y textos perfectamente.
    """
    ext = os.path.splitext(ruta_archivo)[1].lower()
    
    if ext == ".pdf":
        texto_capa = extraer_texto_pdf(ruta_archivo)
        # Si el PDF tiene abundante texto digital (> 200 palabras), enviamos texto directo
        if len(texto_capa.split()) > 200:
            prompt_texto = f"{PROMPT_AUDITORIA_SISTEMA}\n\n--- TRANSCRIPCIÓN DEL CHAT ---\n{texto_capa[:35000]}\n--- FIN TRANSCRIPCIÓN ---"
            return [{"text": prompt_texto}]
        else:
            # Es un PDF con capturas/imágenes o formato visual: enviar como documento visual multimodal
            with open(ruta_archivo, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
            return [
                {"inlineData": {"mimeType": "application/pdf", "data": pdf_b64}},
                {"text": f"{PROMPT_AUDITORIA_SISTEMA}\n\nAudita este documento de chat y responde con el JSON requerido."}
            ]
            
    elif ext == ".txt":
        try:
            with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read()
        except Exception:
            contenido = ""
        prompt_texto = f"{PROMPT_AUDITORIA_SISTEMA}\n\n--- TRANSCRIPCIÓN DEL CHAT ---\n{contenido[:35000]}\n--- FIN TRANSCRIPCIÓN ---"
        return [{"text": prompt_texto}]

    return []

# ==============================================================================
# PARSER ROBUSTO DE JSON
# ==============================================================================
def parsear_respuesta_json(raw_text: str, nombre_archivo: str = "") -> Dict[str, Any]:
    """Limpia y normaliza la respuesta generada por Gemini asegurando JSON válido."""
    default_res = {
        "marca": "Desconocida",
        "pais": "Chile",
        "canal": "WhatsApp",
        "estado": "Rechazado",
        "categoria_falla": "Error de Procesamiento",
        "cliente_nombre": "No detectado",
        "vehiculo_cotizado": "No detectado",
        "errores": ["No se pudo interpretar la respuesta del modelo"],
        "observacion": "La IA devolvió una respuesta no estructurada."
    }

    if not raw_text or not raw_text.strip():
        return default_res

    texto = raw_text.strip()
    texto = re.sub(r"^```(?:json)?\s*", "", texto, flags=re.IGNORECASE)
    texto = re.sub(r"\s*```$", "", texto).strip()

    data = None
    # Intento 1: Carga directa
    try:
        data = json.loads(texto)
    except Exception:
        pass

    # Intento 2: Buscar bloque JSON con regex
    if not data:
        m = re.search(r"(\{[\s\S]*\})", texto)
        if m:
            try:
                data = json.loads(m.group(1).strip())
            except Exception:
                pass

    if not data or not isinstance(data, dict):
        return default_res

    # Normalizar campos
    estado_raw = str(data.get("estado", "")).strip().lower()
    estado = "Aprobado" if "aprob" in estado_raw else "Rechazado"

    marca = str(data.get("marca", "")).strip().title()
    if not marca or marca.lower() in ["desconocida", "none", "null", ""]:
        marca = "No Identificada"

    vehiculo = str(data.get("vehiculo_cotizado", "") or data.get("modelo", "")).strip() or "No detectado"
    cliente = str(data.get("cliente_nombre", "")).strip() or "No detectado"
    pais = str(data.get("pais", "Chile")).strip().title()
    canal = str(data.get("canal", "WhatsApp")).strip().title()
    categoria_falla = str(data.get("categoria_falla", "Ninguna")).strip() if estado == "Rechazado" else "Ninguna"

    errores_raw = data.get("errores", [])
    if isinstance(errores_raw, list):
        errores = [str(e).strip() for e in errores_raw if str(e).strip()]
    elif isinstance(errores_raw, str) and errores_raw.strip():
        errores = [errores_raw.strip()]
    else:
        errores = []

    if estado == "Aprobado":
        errores = []
        categoria_falla = "Ninguna"

    obs = str(data.get("observacion", "")).strip() or "Auditoría completada."

    return {
        "marca": marca,
        "pais": pais,
        "canal": canal,
        "estado": estado,
        "categoria_falla": categoria_falla,
        "cliente_nombre": cliente,
        "vehiculo_cotizado": vehiculo,
        "errores": errores,
        "observacion": obs
    }

# ==============================================================================
# AUDITORÍA DE UN ARCHIVO INDIVIDUAL
# ==============================================================================
def evaluar_archivo(ruta_archivo: str, api_key: str) -> Dict[str, Any]:
    """Evalúa un archivo de transcripción (PDF o TXT) con Gemini 3.6 Flash."""
    nombre = os.path.basename(ruta_archivo)
    partes = preparar_partes_para_gemini(ruta_archivo)
    
    if not partes:
        return {
            "archivo": nombre,
            "marca": "No Identificada",
            "pais": "Chile",
            "canal": "WhatsApp",
            "estado": "Rechazado",
            "categoria_falla": "Archivo Ilegible",
            "cliente_nombre": "No detectado",
            "vehiculo_cotizado": "No detectado",
            "errores": ["No se pudo extraer contenido del archivo"],
            "observacion": "El archivo está vacío o tiene un formato no compatible.",
            "fecha_evaluacion": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    try:
        raw_output = llamar_gemini_api(partes, api_key=api_key)
        res = parsear_respuesta_json(raw_output, nombre_archivo=nombre)
        res["archivo"] = nombre
        res["fecha_evaluacion"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        return res
    except Exception as e:
        err_msg = str(e)
        return {
            "archivo": nombre,
            "marca": "Error de Conexión",
            "pais": "Chile",
            "canal": "WhatsApp",
            "estado": "Rechazado",
            "categoria_falla": "Error de API Gemini",
            "cliente_nombre": "No detectado",
            "vehiculo_cotizado": "No detectado",
            "errores": [f"Error de llamada a la IA: {err_msg[:120]}"],
            "observacion": f"Falla de comunicación con Gemini: {err_msg[:120]}",
            "fecha_evaluacion": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

# ==============================================================================
# GENERACIÓN DE REPORTES (EXCEL PROFESIONAL Y JSON)
# ==============================================================================
def generar_reportes(resultados: List[Dict[str, Any]], ruta_excel: str, ruta_json: str):
    """Genera el JSON para el Dashboard y el Excel con formato ejecutivo corporativo."""
    if not resultados:
        return

    # 1. Guardar JSON
    try:
        with open(ruta_json, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[!] Error guardando JSON: {e}")

    # 2. Guardar Excel con formato
    filas = []
    for r in resultados:
        filas.append({
            "Archivo": r.get("archivo", ""),
            "Marca": r.get("marca", "No Identificada"),
            "Vehículo": r.get("vehiculo_cotizado", "No detectado"),
            "Estado": r.get("estado", "Rechazado"),
            "Categoría de Falla": r.get("categoria_falla", "Ninguna"),
            "Cliente": r.get("cliente_nombre", "No detectado"),
            "Canal": r.get("canal", "WhatsApp"),
            "País": r.get("pais", "Chile"),
            "N° Errores": len(r.get("errores", [])),
            "Errores Detectados": " | ".join(r.get("errores", [])) if r.get("errores") else "Ninguno",
            "Observación del Juez": r.get("observacion", ""),
            "Fecha": r.get("fecha_evaluacion", datetime.now().strftime("%Y-%m-%d %H:%M"))
        })

    df_detalle = pd.DataFrame(filas)
    total = len(df_detalle)
    aprobados = len(df_detalle[df_detalle["Estado"] == "Aprobado"])
    rechazados = len(df_detalle[df_detalle["Estado"] == "Rechazado"])
    tasa = (aprobados / total * 100) if total > 0 else 0

    try:
        with pd.ExcelWriter(ruta_excel, engine="openpyxl") as writer:
            df_detalle.to_excel(writer, sheet_name="Auditoría QA", index=False)
            
            # Resumen Ejecutivo
            df_resumen = pd.DataFrame([
                {"Métrica": "Total de Chats Evaluados", "Valor": total},
                {"Métrica": "Cotizaciones Aprobadas", "Valor": aprobados},
                {"Métrica": "Cotizaciones Rechazadas", "Valor": rechazados},
                {"Métrica": "Tasa de Aprobación (%)", "Valor": f"{tasa:.1f}%"}
            ])
            df_resumen.to_excel(writer, sheet_name="Resumen", index=False)

            if "Marca" in df_detalle.columns:
                desglose = df_detalle.groupby("Marca")["Estado"].value_counts().unstack(fill_value=0).reset_index()
                desglose.to_excel(writer, sheet_name="Resumen", index=False, startrow=7)

            # Estilos OpenpyXL
            wb = writer.book
            ws = wb["Auditoría QA"]
            from openpyxl.styles import PatternFill, Font, Alignment

            verde = PatternFill(start_color="D4EDDA", end_color="D4EDDA", fill_type="solid")
            rojo = PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid")
            azul = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
            font_blanca = Font(color="FFFFFF", bold=True)

            for cell in ws[1]:
                cell.fill = azul
                cell.font = font_blanca
                cell.alignment = Alignment(horizontal="center")

            for col in ws.columns:
                max_l = max(len(str(c.value or "")) for c in col)
                ws.column_dimensions[col[0].column_letter].width = min(max(max_l + 3, 12), 45)

            for row in ws.iter_rows(min_row=2, min_col=1, max_col=len(df_detalle.columns)):
                estado_cell = row[3] # Columna Estado
                if estado_cell.value == "Aprobado":
                    estado_cell.fill = verde
                elif estado_cell.value == "Rechazado":
                    estado_cell.fill = rojo

        print(f"[+] Reporte Excel generado: {ruta_excel}")
    except Exception as e:
        print(f"[!] Error al exportar Excel: {e}")

# ==============================================================================
# PIPELINE PRINCIPAL DE EVALUACIÓN
# ==============================================================================
def procesar_pipeline(
    api_key: Optional[str] = None, 
    archivos_especificos: Optional[List[str]] = None,
    limite_archivos: Optional[int] = None, 
    callback_progreso = None
) -> Tuple[bool, str]:
    """
    Ejecuta el pipeline de auditoría. Si se le entregan 'archivos_especificos',
    evalúa únicamente esos archivos. De lo contrario, busca en la carpeta de PDFs.
    """
    key_a_usar = api_key or CONFIG.get("GEMINI_API_KEY") or cargar_api_key_guardada()
    if not key_a_usar:
        return False, "Falta ingresar la API Key de Google Gemini."

    guardar_api_key(key_a_usar)

    # Determinar qué archivos evaluar
    if archivos_especificos:
        archivos_a_procesar = [a for a in archivos_especificos if os.path.exists(a)]
    else:
        carpeta = CONFIG["CARPETA_PDFS"]
        os.makedirs(carpeta, exist_ok=True)
        archivos_a_procesar = sorted(
            glob.glob(os.path.join(carpeta, "*.pdf")) + 
            glob.glob(os.path.join(carpeta, "*.txt"))
        )

    if not archivos_a_procesar:
        return False, "No se encontraron archivos PDF o TXT para evaluar."

    # Cargar historial existente (evitar duplicados si se acumula)
    resultados = []
    procesados = set()
    if os.path.exists(CONFIG["REPORTE_JSON"]):
        try:
            with open(CONFIG["REPORTE_JSON"], "r", encoding="utf-8") as f:
                for item in json.load(f):
                    resultados.append(item)
                    procesados.add(item.get("archivo"))
        except Exception:
            pass

    # Filtrar solo pendientes o procesar los solicitados
    pendientes = [a for a in archivos_a_procesar if os.path.basename(a) not in procesados]
    
    # Si todos los archivos específicos ya estaban pero se solicitaron explícitamente, reevaluar
    if archivos_especificos and not pendientes:
        pendientes = archivos_a_procesar
        resultados = [r for r in resultados if r.get("archivo") not in [os.path.basename(a) for a in pendientes]]

    if limite_archivos and len(pendientes) > limite_archivos:
        pendientes = pendientes[:limite_archivos]

    total_evaluar = len(pendientes)
    if total_evaluar == 0:
        return True, "Todos los archivos ya habían sido evaluados previamente."

    print(f"\n[*] Iniciando auditoría de {total_evaluar} archivos con Gemini 3.6 Flash...\n")

    for i, ruta in enumerate(pendientes, start=1):
        nombre = os.path.basename(ruta)
        print(f"[{i}/{total_evaluar}] Evaluando '{nombre}'...")

        evaluacion = evaluar_archivo(ruta, api_key=key_a_usar)
        print(f"  -> Marca: {evaluacion['marca']} | Vehículo: {evaluacion['vehiculo_cotizado']} | Estado: {evaluacion['estado']}")
        print(f"  -> Observación: {evaluacion['observacion'][:90]}...\n")

        # Reemplazar o agregar resultado
        resultados = [r for r in resultados if r.get("archivo") != nombre]
        resultados.append(evaluacion)

        if callback_progreso:
            callback_progreso(i, total_evaluar, evaluacion)

        # Guardar periódicamente
        if i % 3 == 0 or i == total_evaluar:
            generar_reportes(resultados, CONFIG["REPORTE_EXCEL"], CONFIG["REPORTE_JSON"])

        # Pausa para respetar la cuota gratuita de peticiones de Google AI Studio
        if i < total_evaluar:
            time.sleep(3.0)

    generar_reportes(resultados, CONFIG["REPORTE_EXCEL"], CONFIG["REPORTE_JSON"])
    return True, f"Se evaluaron {total_evaluar} archivos exitosamente."

if __name__ == "__main__":
    procesar_pipeline()
