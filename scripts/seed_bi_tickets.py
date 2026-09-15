import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database import Incident, IncidentStateRecord, get_db_context
from schemas import CategoryEnum, PriorityEnum, SLA_HOURS_MAP
from services.embeddings import _generate_fallback_vector

# Datos realistas de TI para generación de tickets
INCIDENT_TEMPLATES = [
    # ACCESOS_Y_SEGURIDAD
    {
        "categoria": CategoryEnum.ACCESOS_Y_SEGURIDAD,
        "titulo": "Cuenta bloqueada por intentos fallidos de contraseña",
        "descripcion": "El usuario ingresó su contraseña incorrecta 3 veces en Windows y su cuenta de Active Directory quedó bloqueada.",
        "solucion": "Se verificó identidad vía llamada telefónica y se desbloqueó la cuenta en Active Directory Users and Computers.",
    },
    {
        "categoria": CategoryEnum.ACCESOS_Y_SEGURIDAD,
        "titulo": "Solicitud de acceso a módulo de compras en SAP ERP",
        "descripcion": "Nuevo analista de compras requiere permisos de creación y visualización de órdenes de compra (ME21N/ME23N).",
        "solucion": "Se validó la aprobación del jefe de área y se asignó el rol Z_COMPRAS_ORDENES en SAP GRC.",
    },
    {
        "categoria": CategoryEnum.ACCESOS_Y_SEGURIDAD,
        "titulo": "Falla de certificado en cliente VPN Cisco AnyConnect",
        "descripcion": "Al intentar conectar a la red corporativa aparece el mensaje 'Untrusted Server Certificate' y rechaza la conexión.",
        "solucion": "Se reinstaló el certificado raíz de la CA corporativa en el almacén de certificados de Windows del usuario.",
    },
    {
        "categoria": CategoryEnum.ACCESOS_Y_SEGURIDAD,
        "titulo": "Pérdida de acceso a carpeta compartida de Recursos Humanos",
        "descripcion": "El colaborador no puede abrir la ruta de red \\\\nas01\\rrhh\\nominas arrojando error de 'Acceso Denegado'.",
        "solucion": "Se agregó al usuario al grupo de seguridad 'SEC_RRHH_NOMINAS_RO' en el controlador de dominio.",
    },
    {
        "categoria": CategoryEnum.ACCESOS_Y_SEGURIDAD,
        "titulo": "Reinicio de factor de autenticación MFA en Microsoft Authenticator",
        "descripcion": "Usuario cambió de smartphone y no puede recibir los códigos de verificación para ingresar a su correo institucional.",
        "solucion": "Se forzó el re-registro de MFA en Microsoft Entra ID (Azure AD) para que configure su nuevo dispositivo.",
    },

    # SOFTWARE_APLICACIONES
    {
        "categoria": CategoryEnum.SOFTWARE_APLICACIONES,
        "titulo": "Error 500 al emitir facturas electrónicas en el ERP",
        "descripcion": "Al pulsar el botón 'Emitir Comprobante', la aplicación web arroja un error interno 500 y no conecta con el servicio tributario.",
        "solucion": "Se reinició el worker pool del servicio de facturación y se liberaron conexiones bloqueadas en la base de datos.",
    },
    {
        "categoria": CategoryEnum.SOFTWARE_APLICACIONES,
        "titulo": "Microsoft Outlook se congela al sincronizar buzón de correo",
        "descripcion": "La aplicación de escritorio de Outlook se cuelga en 'Sincronizando bandeja de entrada' y requiere forzar cierre.",
        "solucion": "Se reparó el archivo de datos OST local mediante SCANPST.EXE y se depuraron 2GB de correos antiguos a archivo.",
    },
    {
        "categoria": CategoryEnum.SOFTWARE_APLICACIONES,
        "titulo": "Bug visual en formulario de cotizaciones del CRM",
        "descripcion": "Al seleccionar productos con descuento especial, los totales se recalculan con decimales incorrectos en pantalla.",
        "solucion": "El equipo de desarrollo desplegó un parche hotfix en frontend para redondear a 2 decimales según estándar.",
    },
    {
        "categoria": CategoryEnum.SOFTWARE_APLICACIONES,
        "titulo": "Excel no permite guardar archivos en OneDrive corporativo",
        "descripcion": "Aparece un mensaje de conflicto de versiones 'No se pudo guardar la copia en la nube' en hojas compartidas.",
        "solucion": "Se limpiaron las credenciales en caché de Windows Credential Manager y se resincronizó el cliente OneDrive.",
    },
    {
        "categoria": CategoryEnum.SOFTWARE_APLICACIONES,
        "titulo": "Error 502 Bad Gateway en portal interno de nóminas",
        "descripcion": "Los colaboradores que intentan descargar sus boletas de pago reciben mensaje 502 de Nginx.",
        "solucion": "El contenedor backend de NodeJS se había quedado sin memoria (OOM). Se reinició y se duplicó el límite de RAM.",
    },

    # INFRAESTRUCTURA_RED
    {
        "categoria": CategoryEnum.INFRAESTRUCTURA_RED,
        "titulo": "Caída del switch de acceso en el piso 3 de oficinas",
        "descripcion": "Todos los puestos de trabajo del ala norte perdieron conexión por cable y los teléfonos IP se apagaron.",
        "solucion": "Se identificó fallo en la fuente de alimentación PoE del switch Cisco Catalyst. Se sustituyó por switch de respaldo.",
    },
    {
        "categoria": CategoryEnum.INFRAESTRUCTURA_RED,
        "titulo": "Lentitud generalizada en enlace de internet de la sede principal",
        "descripcion": "Pérdida de paquetes del 25% y alta latencia hacia servicios en la nube como Teams y Salesforce.",
        "solucion": "El proveedor de fibra óptica reportó corte por obras viales. Se conmutó el tráfico al enlace secundario de backup.",
    },
    {
        "categoria": CategoryEnum.INFRAESTRUCTURA_RED,
        "titulo": "Servidor de base de datos PostgreSQL no responde a conexiones",
        "descripcion": "Las aplicaciones backend reportan timeout 'server closed the connection unexpectedly' en el puerto 5432.",
        "solucion": "Se liberó espacio en el volumen de transacciones WAL (/var/lib/postgresql/data) y se reinició el demonio PostgreSQL.",
    },
    {
        "categoria": CategoryEnum.INFRAESTRUCTURA_RED,
        "titulo": "Falla en el punto de acceso Wi-Fi de sala de conferencias",
        "descripcion": "Los directores no pueden conectar sus laptops a la red 'CORP_WIFI' durante la reunión mensual.",
        "solucion": "Se reinició el Access Point Aruba mediante la consola controladora y se actualizó el firmware del equipo.",
    },

    # HARDWARE_EQUIPOS
    {
        "categoria": CategoryEnum.HARDWARE_EQUIPOS,
        "titulo": "Impresora departamental de Logística fuera de línea",
        "descripcion": "La impresora láser HP LaserJet no recibe trabajos de impresión y en Windows aparece como 'Sin conexión'.",
        "solucion": "Se reinició el servicio Spooler en Windows, se desmarcó 'Usar sin conexión' y se reconectó el cable de red LAN.",
    },
    {
        "categoria": CategoryEnum.HARDWARE_EQUIPOS,
        "titulo": "Laptop corporativa no enciende tras descarga de batería",
        "descripcion": "Equipo Lenovo ThinkPad de la gerencia no da señales de encendido ni enciende LED de carga al enchufar cargador.",
        "solucion": "Se realizó drenado de energía estática mediante el botón reset en la parte inferior y se reemplazó cargador de 65W.",
    },
    {
        "categoria": CategoryEnum.HARDWARE_EQUIPOS,
        "titulo": "Pantalla azul BSOD recurrente en equipo de diseño",
        "descripcion": "La estación de trabajo se reinicia cada 2 horas con el código de detención MEMORY_MANAGEMENT.",
        "solucion": "Se detectó módulo RAM DDR4 con bloques corruptos mediante MemTest86. Se reemplazó el módulo de 16GB defectuoso.",
    },
    {
        "categoria": CategoryEnum.HARDWARE_EQUIPOS,
        "titulo": "Monitor secundario no da video por cable HDMI",
        "descripcion": "La pantalla Dell parpadea y muestra 'Sin señal' cuando se conecta a la estación de trabajo.",
        "solucion": "Se reemplazó el cable HDMI dañado y se actualizó el controlador de gráficos integrados de Intel.",
    },

    # CONSULTA_OPERATIVA
    {
        "categoria": CategoryEnum.CONSULTA_OPERATIVA,
        "titulo": "Duda sobre exportación de reportes mensuales a formato Excel",
        "descripcion": "Usuario de contabilidad consulta cómo exportar el libro diario a archivo .xlsx sin que se corte el texto.",
        "solucion": "Se indicó la ruta 'Reportes Contables > Exportar > Libro Diario' y se recomendó seleccionar formato XLSX nativo.",
    },
    {
        "categoria": CategoryEnum.CONSULTA_OPERATIVA,
        "titulo": "Consulta de configuración de cámara y micrófono en Microsoft Teams",
        "descripcion": "Nueva colaboradora solicita apoyo para configurar sus auriculares USB en la aplicación de videollamadas.",
        "solucion": "Se guió paso a paso por videollamada para seleccionar el dispositivo en 'Configuración > Dispositivos' de Teams.",
    },
    {
        "categoria": CategoryEnum.CONSULTA_OPERATIVA,
        "titulo": "Solicitud de guía para programar mensaje de fuera de oficina",
        "descripcion": "¿Cómo programar una respuesta automática de vacaciones en Outlook para remitentes externos?",
        "solucion": "Se remitió el manual interno y se indicó el menú 'Archivo > Respuestas automáticas (Fuera de la oficina)' de Outlook.",
    },
]

USUARIOS_SAMPLE = [
    "marta_ventas", "carlos_finanzas", "lucas_dev", "ana_rrhh", "diego_ops",
    "sofia_legal", "javier_logistica", "elena_marketing", "roberto_contabilidad",
    "gabriela_ti", "fernando_gerencia", "valeria_compras", "pedro_almacen",
    "camila_atencion", "martin_sistemas", "andrea_auditoria", "hugo_calidad"
]


def generate_bi_tickets(total_tickets: int = 300) -> int:
    """
    Genera entre 200 y 400 tickets ficticios realistas distribuidos en los últimos 3 meses:
    - 80% en estado RESUELTO con resolved_at coherente y tiempo_resolucion calculado.
      * ~80% de los resueltos cumplieron su SLA.
      * ~20% de los resueltos superaron su SLA (incumplimiento).
    - 20% en estado ABIERTO o EN_PROCESO con resolved_at = NULL y tiempo_resolucion = NULL.
    """
    now = datetime.now(timezone.utc)
    ninety_days_ago = now - timedelta(days=90)

    # Cantidades según porcentajes
    resueltos_count = int(total_tickets * 0.80)
    abiertos_count = total_tickets - resueltos_count

    tickets_data = []

    # 1. Generar los 80% RESUELTOS
    for _ in range(resueltos_count):
        template = random.choice(INCIDENT_TEMPLATES)
        usuario = random.choice(USUARIOS_SAMPLE)

        # Distribución de prioridades: P1 (10%), P2 (25%), P3 (45%), P4 (20%)
        p_rand = random.random()
        if p_rand < 0.10:
            prioridad = PriorityEnum.P1
        elif p_rand < 0.35:
            prioridad = PriorityEnum.P2
        elif p_rand < 0.80:
            prioridad = PriorityEnum.P3
        else:
            prioridad = PriorityEnum.P4

        sla_horas = SLA_HOURS_MAP[prioridad]
        sla_minutos = sla_horas * 60

        # Fecha de creación aleatoria entre hace 90 días y hace 2 días
        days_offset = random.uniform(2, 88)
        created_at = now - timedelta(days=days_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))

        # Cumplimiento del SLA: 80% cumple SLA, 20% se pasa del tiempo límite
        cumplio_sla = random.random() < 0.80

        if cumplio_sla:
            # Tiempo de resolución menor o igual al SLA (ej. entre 20% y 95% del SLA)
            duration_minutes = max(15, int(sla_minutos * random.uniform(0.20, 0.95)))
        else:
            # Tiempo de resolución que excede el SLA (ej. entre 1.1x y 2.5x del SLA)
            duration_minutes = int(sla_minutos * random.uniform(1.15, 2.80))

        resolved_at = created_at + timedelta(minutes=duration_minutes)

        if prioridad == PriorityEnum.P1:
            accion_ia = "ALERTA_P1"
        elif template["categoria"] == CategoryEnum.CONSULTA_OPERATIVA or "SAP" in template["titulo"] or "impresora" in template["titulo"]:
            accion_ia = "SUGERENCIA_RAG"
        else:
            accion_ia = "COLA_REGULAR"

        tickets_data.append({
            "usuario": usuario,
            "titulo": template["titulo"],
            "descripcion": template["descripcion"],
            "categoria": template["categoria"].value,
            "prioridad": prioridad.value,
            "sla_horas": sla_horas,
            "accion_ia": accion_ia,
            "estado": "RESUELTO",
            "created_at": created_at,
            "resolved_at": resolved_at,
            "tiempo_resolucion": duration_minutes,
            "solucion_sugerida": template["solucion"],
        })

    # 2. Generar los 20% ABIERTOS / EN_PROCESO
    for _ in range(abiertos_count):
        template = random.choice(INCIDENT_TEMPLATES)
        usuario = random.choice(USUARIOS_SAMPLE)

        p_rand = random.random()
        if p_rand < 0.10:
            prioridad = PriorityEnum.P1
        elif p_rand < 0.35:
            prioridad = PriorityEnum.P2
        elif p_rand < 0.80:
            prioridad = PriorityEnum.P3
        else:
            prioridad = PriorityEnum.P4

        sla_horas = SLA_HOURS_MAP[prioridad]

        # Creados recientemente (últimos 7 a 14 días)
        days_offset = random.uniform(0.1, 14)
        created_at = now - timedelta(days=days_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))

        # 60% Abiertos, 40% En Proceso
        estado = "EN_PROCESO" if random.random() < 0.40 else "ABIERTO"

        if prioridad == PriorityEnum.P1:
            accion_ia = "ALERTA_P1"
        elif template["categoria"] == CategoryEnum.CONSULTA_OPERATIVA or "SAP" in template["titulo"] or "impresora" in template["titulo"]:
            accion_ia = "SUGERENCIA_RAG"
        else:
            accion_ia = "COLA_REGULAR"

        tickets_data.append({
            "usuario": usuario,
            "titulo": template["titulo"],
            "descripcion": template["descripcion"],
            "categoria": template["categoria"].value,
            "prioridad": prioridad.value,
            "sla_horas": sla_horas,
            "accion_ia": accion_ia,
            "estado": estado,
            "created_at": created_at,
            "resolved_at": None,
            "tiempo_resolucion": None,
            "solucion_sugerida": template["solucion"] if estado == "EN_PROCESO" else None,
        })

    # Mezclar aleatoriamente el orden
    random.shuffle(tickets_data)

    print(f"[+] Limpiando incidentes previos y generando {len(tickets_data)} nuevos tickets...")

    inserted_count = 0
    with get_db_context() as db:
        # Limpieza de data previa para asegurar catálogo 100% normalizado
        db.query(IncidentStateRecord).delete()
        db.query(Incident).delete()
        db.commit()

        for t in tickets_data:
            # Generar vector determinista rápido de 768 dimensiones
            text_to_embed = f"{t['titulo']}. {t['descripcion']}"
            vector = _generate_fallback_vector(text_to_embed, dimension=768)

            incident = Incident(
                usuario=t["usuario"],
                titulo=t["titulo"],
                descripcion=t["descripcion"],
                prioridad=t["prioridad"],
                sla_horas=t["sla_horas"],
                categoria=t["categoria"],
                accion_ia=t["accion_ia"],
                estado=t["estado"],
                created_at=t["created_at"],
                resolved_at=t["resolved_at"],
                tiempo_resolucion=t["tiempo_resolucion"],
                solucion_sugerida=t["solucion_sugerida"],
                vector_embedding=vector,
            )
            db.add(incident)
            db.flush()

            # Insertar registro de estado asociado en incident_states
            state_record = IncidentStateRecord(
                incident_id=incident.id,
                created_at=t["created_at"],
                texto_original={
                    "titulo": t["titulo"],
                    "descripcion": t["descripcion"],
                    "usuario": t["usuario"],
                },
                triage_data={
                    "categoria": t["categoria"],
                    "prioridad": t["prioridad"],
                    "sla_horas": t["sla_horas"],
                    "resumen_ejecutivo": t["titulo"],
                    "requiere_rag": (t["accion_ia"] == "SUGERENCIA_RAG"),
                },
                alert_sent=(t["accion_ia"] == "ALERTA_P1"),
                rag_context=["Manual de referencia institucional"] if t["accion_ia"] == "SUGERENCIA_RAG" else None,
                final_response=t["solucion_sugerida"] or "Ticket en cola regular de soporte.",
                error=None,
            )
            db.add(state_record)
            inserted_count += 1

        db.commit()

    print(f"[OK] Se insertaron exitosamente {inserted_count} tickets con sus estados en la base de datos.")
    return inserted_count


def main():
    parser = argparse.ArgumentParser(
        description="Generador de tickets ficticios de TI para Power BI."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=300,
        help="Número total de tickets a generar (por defecto: 300).",
    )
    args = parser.parse_args()

    count = generate_bi_tickets(total_tickets=args.count)
    print(f"Listo. Conéctate desde Power BI a PostgreSQL en localhost:5432/triage_db.")


if __name__ == "__main__":
    main()
