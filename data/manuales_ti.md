# Base de Conocimiento de TI - Manuales de Soporte y Operaciones

---

## 1. Cómo reiniciar el servicio de base de datos PostgreSQL
**Categoría**: INFRAESTRUCTURA_RED
**Contenido**:
Para reiniciar el servicio de base de datos PostgreSQL en servidores Linux/Debian/Ubuntu:
1. Conéctese por SSH al servidor con usuario autorizado.
2. Compruebe el estado actual ejecutando: `sudo systemctl status postgresql`.
3. Si el servicio está caído o bloqueado, reinícielo con: `sudo systemctl restart postgresql`.
4. Verifique que el puerto 5432 esté escuchando: `sudo ss -tuln | grep 5432`.
5. Revise los registros de error en `/var/log/postgresql/postgresql-XX-main.log` para confirmar que no existan bloqueos de transacciones corruptas o falta de espacio en disco.

---

## 2. Cómo solicitar accesos y licencias a SAP
**Categoría**: ACCESOS_Y_SEGURIDAD
**Contenido**:
Procedimiento formal para solicitar roles o transacciones en el sistema ERP SAP:
1. Ingrese al portal de autoservicio de TI en la intranet de la empresa.
2. Seleccione 'Solicitud de Accesos a Sistemas Corporativos > SAP ECC / S4HANA'.
3. Especifique el módulo requerido (FI, CO, MM, SD o HCM) y los códigos de transacción (T-Codes) solicitados.
4. Adjunte la autorización por correo electrónico de su jefatura directa o líder de área.
5. El equipo de Seguridad de la Información procesará la solicitud en un plazo de 24 a 48 horas una vez aprobada por el responsable del módulo.

---

## 3. Solución al error de impresora de red sin conexión (Offline)
**Categoría**: HARDWARE_EQUIPOS
**Contenido**:
Pasos para solucionar cuando una impresora departamental aparece en estado 'Sin conexión' en Windows:
1. Abra el panel 'Ejecutar' (Windows + R), escriba `services.msc` y presione Enter.
2. Busque el servicio llamado 'Cola de impresión' (Print Spooler), haga clic derecho y seleccione 'Reiniciar'.
3. Abra la consola CMD y verifique conectividad a la IP de la impresora ejecutando: `ping IP_IMPRESORA`.
4. Si responde pero sigue offline, vaya a 'Configuración > Dispositivos > Impresoras y escáneres', seleccione la impresora, haga clic en 'Abrir cola de impresión' y desmarque la opción 'Usar impresora sin conexión' en el menú 'Impresora'.
5. Si persiste, apague la impresora por 30 segundos, vuelva a encenderla y reconecte el cable de red LAN.

---

## 4. Desbloqueo de cuenta y reseteo de contraseña en Active Directory
**Categoría**: ACCESOS_Y_SEGURIDAD
**Contenido**:
Instrucciones para usuarios con cuentas bloqueadas tras intentos fallidos de inicio de sesión:
1. Acceda al portal web de autoservicio de contraseñas desde su celular o equipo secundario: `https://selfservice.empresa.com`.
2. Ingrese su usuario corporativo y complete la autenticación multifactor (código SMS o notificación en Microsoft Authenticator).
3. Seleccione 'Desbloquear mi cuenta' o 'Cambiar contraseña'.
4. La nueva contraseña debe tener al menos 12 caracteres, incluir mayúsculas, minúsculas, números y símbolos especiales, y no coincidir con las últimas 5 utilizadas.
5. Si el portal no le permite el autoservicio, comuníquese a la extensión de HelpDesk (ext. 5000) para validar identidad y forzar el reseteo manual.

---

## 5. Solución a fallas de conexión a la VPN corporativa
**Categoría**: ACCESOS_Y_SEGURIDAD
**Contenido**:
Guía de solución de problemas de conexión mediante Cisco AnyConnect o FortiClient:
1. Verifique que su conexión a internet doméstica esté funcionando abriendo cualquier sitio web externo.
2. En el cliente VPN, verifique que la dirección del gateway sea: `vpn.empresa.com`.
3. Abra el Administrador de Dispositivos de Windows (`devmgmt.msc`), expanda 'Adaptadores de red', haga clic derecho en el adaptador virtual 'Cisco AnyConnect Secure Mobility' o 'Fortinet Virtual NIC' y seleccione 'Deshabilitar dispositivo', espere 5 segundos y haga clic en 'Habilitar dispositivo'.
4. Reinicie el cliente VPN e introduzca sus credenciales completas junto con el código token MFA.
5. Si el mensaje indica 'Certificate validation failure', sincronice la fecha y hora de su computador desde la configuración de Windows.

---

## 6. Diagnóstico y recuperación ante pantallas azules (BSOD) en Windows
**Categoría**: HARDWARE_EQUIPOS
**Contenido**:
Acciones inmediatas ante reinicios inesperados con pantalla azul en laptops corporativas:
1. Anote el código de parada (ej: CRITICAL_PROCESS_DIED, DPC_WATCHDOG_VIOLATION o MEMORY_MANAGEMENT).
2. Desconecte periféricos externos no esenciales (docks USB, monitores adicionales, discos externos).
3. Inicie Windows en Modo Seguro manteniendo presionada la tecla Shift mientras selecciona 'Reiniciar' en el menú inicio.
4. Ejecute en una terminal de PowerShell como administrador el verificador de archivos del sistema: `sfc /scannow` y posteriormente `dism /online /cleanup-image /restorehealth`.
5. Ejecute la herramienta de diagnóstico de memoria de Windows presionando Windows + R y escribiendo `mdsched.exe`. Si se detectan fallas físicas, se programará reemplazo de módulo de memoria con el técnico de guardia.

---

## 7. Reparación de sincronización y perfiles dañados en Microsoft Outlook
**Categoría**: SOFTWARE_APLICACIONES
**Contenido**:
Pasos para corregir problemas de envío/recepción y congelamientos en Microsoft Outlook:
1. Cierre Outlook completamente y verifique en el Administrador de Tareas que el proceso `OUTLOOK.EXE` haya finalizado.
2. Inicie Outlook en modo seguro presionando Windows + R y ejecutando: `outlook.exe /safe`.
3. Si abre correctamente en modo seguro, vaya a 'Archivo > Opciones > Complementos', seleccione 'Complementos COM' y deshabilite complementos de terceros no necesarios.
4. Para reparar el archivo de datos local (.ost): vaya a 'Panel de Control > Correo (Microsoft Outlook) > Archivos de datos', identifique la ruta del archivo `.ost`, ciérrelo, renómbrelo a `.ost.old` y vuelva a abrir Outlook para que se regenere automáticamente desde Exchange Online.

---

## 8. Solución a errores 500 y 502 Bad Gateway en aplicaciones web internas
**Categoría**: SOFTWARE_APLICACIONES
**Contenido**:
Procedimiento de verificación ante errores de servidor en portales internos de la compañía:
1. Limpie la memoria caché del navegador web presionando Ctrl + F5 o pruebe en una ventana de incógnito.
2. Si el error persiste para varios usuarios, valide el estado del contenedor o servidor de backend.
3. Para Nginx/Apache como proxy inverso: revise el log de errores con `tail -n 100 /var/log/nginx/error.log` para confirmar si el upstream (Node/Python/Java) rechazó la conexión.
4. Reinicie el servicio de backend con `systemctl restart <nombre_servicio>` o `docker restart <nombre_contenedor>`.
5. Compruebe que no se haya agotado el espacio en la partición `/var` o `/tmp` con el comando `df -h`.

---

## 9. Configuración de micrófono y cámara en Microsoft Teams / Zoom
**Categoría**: CONSULTA_OPERATIVA
**Contenido**:
Instrucciones paso a paso para resolver problemas de audio y video en videollamadas:
1. En Windows, abra 'Configuración > Privacidad y seguridad > Cámara' y asegúrese de que el acceso a la cámara para aplicaciones esté activado.
2. Realice el mismo paso en 'Privacidad y seguridad > Micrófono'.
3. Dentro de Microsoft Teams, haga clic en 'Configuración (tres puntos) > Dispositivos'.
4. En 'Entrada de audio' elija el micrófono de sus auriculares (no el integrado si tiene headset conectado).
5. Haga clic en el botón 'Hacer una llamada de prueba' para escuchar la grabación de su voz y validar la respuesta del sistema antes de entrar a su reunión.

---

## 10. Diagnóstico y reporte de lentitud o saturación en la red de oficina
**Categoría**: INFRAESTRUCTURA_RED
**Contenido**:
Procedimiento para diagnosticar problemas de conectividad o lentitud en sedes corporativas:
1. Identifique si el problema afecta a cable Ethernet o conexión Wi-Fi corporativa.
2. Abra CMD y verifique latencia y pérdida de paquetes contra el gateway local y contra internet:
   - `ping -n 20 192.168.1.1` (o la IP de su puerta de enlace).
   - `ping -n 20 8.8.8.8`.
3. Ejecute una prueba de velocidad en `fast.com` o el servidor local de iPerf para comprobar ancho de banda disponible.
4. Si hay pérdida de paquetes en toda la oficina, valide el consumo en el firewall/router perimetral para descartar sincronizaciones masivas de OneDrive o respaldos no programados.
5. Reporte el incidente al equipo de Redes con la IP del equipo, sede y porcentaje de pérdida de paquetes obtenido.
