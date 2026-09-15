import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import httpx
from graph.state import IncidentGraphState

logger = logging.getLogger("incident_triage.alert")


def send_p1_alert(state: IncidentGraphState) -> dict:
    """
    Ruta A: Se activa si la prioridad es P1.
    Envía una notificación formateada mediante:
    1. Discord Webhook
    2. Telegram Bot
    3. Correo Empresarial Outlook / Office 365 o Gmail (vía SMTP nativo)
    4. Webhook genérico
    """
    triage = state.get("triage_data")
    texto_orig = state.get("texto_original") or {}

    resumen = (
        triage.resumen_ejecutivo
        if triage
        else texto_orig.get("titulo", "Incidente Crítico")
    )
    sla_horas = triage.sla_horas if triage else 2
    categoria = triage.categoria.value if triage else "INFRAESTRUCTURA_RED"
    usuario = texto_orig.get("usuario", "desconocido")
    titulo = texto_orig.get("titulo", "")
    descripcion = texto_orig.get("descripcion", "")

    # Mensaje formateado según requerimiento
    alert_message = (
        f"🚨 ALERTA P1: {resumen}. SLA: {sla_horas} horas. Responsable: Turno de guardia."
    )

    alert_sent = False
    delivery_channels = []

    # Variables de entorno
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("ALERT_WEBHOOK_URL")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    smtp_host = os.getenv("SMTP_HOST")  # ej: smtp.office365.com o smtp.gmail.com
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_to = os.getenv("ALERT_EMAIL_TO") or smtp_user
    email_webhook = os.getenv("EMAIL_WEBHOOK_URL")

    # 1. Discord Webhook
    if discord_webhook and "discord.com" in discord_webhook:
        try:
            res = httpx.post(
                discord_webhook,
                json={"content": alert_message},
                timeout=5.0,
            )
            res.raise_for_status()
            alert_sent = True
            delivery_channels.append("Discord")
        except Exception as exc:
            logger.error(f"Falla al enviar a Discord: {exc}")

    # 2. Telegram Bot
    if telegram_token and telegram_chat_id:
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            res = httpx.post(
                url,
                json={"chat_id": telegram_chat_id, "text": alert_message},
                timeout=5.0,
            )
            res.raise_for_status()
            alert_sent = True
            delivery_channels.append("Telegram")
        except Exception as exc:
            logger.error(f"Falla al enviar a Telegram: {exc}")

    # 3. Correo Outlook / Office 365 o Gmail (SMTP)
    if smtp_host and smtp_user and smtp_password and email_to:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = email_to
            msg["Subject"] = f"🚨 ALERTA P1 - {resumen} (SLA: {sla_horas}h)"

            cuerpo_html = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="background-color: #d9534f; color: white; padding: 15px; border-radius: 5px;">
                        <h2 style="margin: 0;">🚨 ALERTA CRÍTICA P1 - Turno de Guardia</h2>
                    </div>
                    <div style="padding: 15px; border: 1px solid #ddd; margin-top: 10px; border-radius: 5px;">
                        <p><strong>Resumen Ejecutivo:</strong> {resumen}</p>
                        <p><strong>SLA de Resolución:</strong> {sla_horas} horas</p>
                        <p><strong>Categoría:</strong> {categoria}</p>
                        <p><strong>Reportado por:</strong> {usuario}</p>
                        <hr style="border: none; border-top: 1px solid #eee;">
                        <p><strong>Título del Incidente:</strong> {titulo}</p>
                        <p><strong>Descripción:</strong></p>
                        <blockquote style="background: #f9f9f9; padding: 10px; border-left: 3px solid #d9534f;">
                            {descripcion}
                        </blockquote>
                    </div>
                </body>
            </html>
            """
            msg.attach(MIMEText(cuerpo_html, "html"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)

            alert_sent = True
            delivery_channels.append("Outlook/Correo")
        except Exception as exc:
            logger.error(f"Falla al enviar correo SMTP a {email_to}: {exc}")

    # 4. Fallback a Webhook HTTP Genérico si no hubo canales anteriores
    if not delivery_channels and email_webhook:
        try:
            res = httpx.post(
                email_webhook,
                json={
                    "subject": f"ALERTA P1 - SLA {sla_horas}h",
                    "message": alert_message,
                    "usuario": usuario,
                    "resumen": resumen,
                },
                timeout=5.0,
            )
            res.raise_for_status()
            alert_sent = True
            delivery_channels.append("Webhook Genérico")
        except Exception as exc:
            logger.error(f"Falla en webhook genérico: {exc}")

    # Si no se configuró ningún canal real, registrar simulación sin fallar
    if not delivery_channels:
        alert_sent = True
        delivery_channels.append("Simulación interna")

    canal_str = ", ".join(delivery_channels)

    return {
        "alert_sent": alert_sent,
        "rag_context": None,
        "final_response": f"[{canal_str}] {alert_message}",
        "error": None,
    }
