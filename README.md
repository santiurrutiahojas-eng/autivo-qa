# Autivo QA

Dashboard para evaluar conversaciones de agentes de IA en WhatsApp y Web, revisar hallazgos y exportar un informe Excel.

## Qué incluye

- Carga de varios PDF/TXT y de archivos ZIP con conversaciones en subcarpetas.
- Evaluación con OpenAI API o Google Gemini; OpenAI queda seleccionado por defecto.
- Lectura visual de PDF escaneados al usar OpenAI Responses API.
- Procesamiento concurrente configurable (1–10 conversaciones a la vez).
- Panel con filtros, indicadores, revisión de evidencia y descarga Excel.
- Errores de lectura o API separados de los rechazos de calidad y enviados a **Revisión**.
- Citas/evidencias y resúmenes para apoyar la revisión humana.

## Ejecutar localmente

Requiere Python 3.10 o superior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app_dashboard.py
```

La app usa el login y las claves configuradas en Streamlit Secrets o en variables de entorno. No hay usuarios ni contraseñas predeterminadas.

## Secretos requeridos

En Streamlit Community Cloud, configura estos valores en **Settings → Secrets**. Para evaluación con OpenAI, la clave mínima es `OPENAI_API_KEY`.

```toml
OPENAI_API_KEY = "tu_clave_de_openai"
OPENAI_MODEL = "gpt-4.1-mini"
LOGIN_EMAIL = "tu_correo_autorizado"
LOGIN_PASSWORD = "define_una_clave_larga_y_unica"
QA_CONCURRENCY = "4"
```

Para usar Gemini, cambia el proveedor en la barra lateral y agrega `GEMINI_API_KEY`. Opcionalmente configura `GEMINI_MODEL`. Para autorizar más de un usuario, usa `LOGIN_EMAILS = "correo1,correo2"`; se conserva un único secreto `LOGIN_PASSWORD` para esa instalación.

No guardes claves en `.config_qa.json`, en el código ni en GitHub. Si una clave real llegó a un repositorio remoto, revócala y crea una nueva.

## Uso por lotes

1. Inicia sesión y abre **Subir / Auditar PDFs**.
2. Selecciona una o más conversaciones TXT/PDF o sube ZIP de Autivo.
3. Elige proveedor, modelo y concurrencia. Empieza con 4 procesos simultáneos; reduce el valor si tu cuenta limita las solicitudes.
4. Revisa los casos **Aprobado**, **Rechazado** y **Revisión** en el dashboard.
5. Descarga `reporte_qa_autivo.xlsx` para compartir el resultado.

Límites de esta versión: máximo 2.000 conversaciones por lote, 50 MB por archivo subido, 25 MB por archivo dentro de ZIP y 500 MB descomprimidos por lote. Los ZIP se procesan en una carpeta temporal y se eliminan al terminar.

## Despliegue

- Repositorio: `santiurrutiahojas-eng/autivo-qa`
- Rama: `main`
- Entrada de Streamlit: `app_dashboard.py`
- Dependencias: `requirements.txt`
- Secretos: `OPENAI_API_KEY`, `LOGIN_EMAIL`, `LOGIN_PASSWORD`; los secretos de Gemini son opcionales.

Mantén fuera del control de versiones las claves, transcripciones y resultados. `.gitignore` cubre secretos locales, los archivos de configuración y los reportes con datos de chats.

## Privacidad y límites de evaluación

Los archivos cargados se usan en memoria temporal durante el lote; las copias extraídas del ZIP se eliminan al finalizar. El dashboard conserva el resumen de evaluación en el historial JSON y exporta Excel, que pueden contener datos personales: mantenlos privados y no los subas a GitHub. Al seleccionar un proveedor, el contenido de las conversaciones se envía a su API para su evaluación. Protege el enlace del dashboard y la clave de API; un login de aplicación no sustituye la configuración de acceso del servicio de hosting.

La evaluación automática es una ayuda de QA, no un dictamen infalible. Revisa manualmente los casos rechazados y los casos técnicos enviados a **Revisión**, y valida el criterio del juez con una muestra etiquetada por personas antes de usar los resultados para decisiones sobre agentes.
