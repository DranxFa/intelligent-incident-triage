import logging
import os
import httpx
from graph.state import IncidentGraphState

logger = logging.getLogger("incident_triage.alert")


def send_p1_alert(state: IncidentGraphState) -> dict:
    """
    Ruta A: Se activa si la prioridad es P1.
    Envía una notificación formateada mediante un Webhook hacia Discord, Telegram o Correo/Genérico.
    """
    triage = state.get("triage_data")
    texto_orig = state.get("texto_original") or {}

    resumen = (
        triage.resumen_ejecutivo
        if triage
        else texto_orig.get("titulo", "Incidente Crítico")
    )
    sla_horas = triage.sla_horas if triage else 2

    # Mensaje formateado según requerimiento
    alert_message = (
        f"🚨 ALERTA P1: {resumen}. SLA: {sla_horas} horas. Responsable: Turno de guardia."
    )

    alert_sent = False
    delivery_channel = "Log/Simulado"

    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL") or os.getenv("ALERT_WEBHOOK_URL")
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    email_webhook = os.getenv("EMAIL_WEBHOOK_URL")

    try:
        # 1. Discord Webhook
        if discord_webhook and "discord.com" in discord_webhook:
            response = httpx.post(
                discord_webhook,
                json={"content": alert_message},
                timeout=5.0,
            )
            response.raise_for_status()
            alert_sent = True
            delivery_channel = "Discord"

        # 2. Telegram Bot Webhook
        elif telegram_token and telegram_chat_id:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            response = httpx.post(
                url,
                json={"chat_id": telegram_chat_id, "text": alert_message},
                timeout=5.0,
            )
            response.raise_for_status()
            alert_sent = True
            delivery_channel = "Telegram"

        # 3. Correo / Webhook genérico
        elif email_webhook or discord_webhook:
            target_url = email_webhook or discord_webhook
            response = httpx.post(
                target_url,
                json={
                    "channel": "email",
                    "subject": f"ALERTA P1 (SLA: {sla_horas}h)",
                    "message": alert_message,
                    "triage": triage.model_dump() if triage else {},
                },
                timeout=5.0,
            )
            response.raise_for_status()
            alert_sent = True
            delivery_channel = "Correo/Webhook"

        else:
            # Fallback en desarrollo o si no hay webhook configurado
            logger.warning(
                "No hay Webhook configurado (DISCORD_WEBHOOK_URL, TELEGRAM_BOT_TOKEN o EMAIL_WEBHOOK_URL). Notificación simulada."
            )
            alert_sent = True
            delivery_channel = "Simulación interna"

    except Exception as exc:
        logger.error(f"Falla al enviar webhook de alerta P1: {exc}")
        return {
            "alert_sent": False,
            "final_response": f"Error despachando alerta P1: {str(exc)}",
            "error": str(exc),
        }

    return {
        "alert_sent": alert_sent,
        "rag_context": None,
        "final_response": f"[{delivery_channel}] {alert_message}",
        "error": None,
    }
