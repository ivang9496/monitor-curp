import requests
import smtplib
import os
from email.message import EmailMessage

# --- CONFIGURACIÓN ---
# No usamos proxies aquí porque la VPN ya está puesta en el sistema (GitHub Actions)
# El script navega "libre" a través de la interfaz de red tun0 de México.

# --- DATOS DEL CORREO (Secretos) ---
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_DESTINO = os.environ.get('EMAIL_DESTINO')

# --- API XALAPA ---
URL_DIAS = "https://digital.xalapa.gob.mx/citas_curp/api/dias_disponibles"
URL_HORARIOS = "https://digital.xalapa.gob.mx/citas_curp/api/horarios_disponibles"

HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://digital.xalapa.gob.mx/citas_curp',
    'Origin': 'https://digital.xalapa.gob.mx'
}

def enviar_correo(mensaje_cuerpo):
    print("📧 Preparando envío de correo...")
    msg = EmailMessage()
    msg.set_content(mensaje_cuerpo, charset='utf-8')
    msg['Subject'] = '¡ALERTA: CITAS DETALLADAS DISPONIBLES!'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_DESTINO

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Correo enviado con el reporte detallado.")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

def obtener_horarios(fecha):
    """
    Retorna la lista de horarios (o lista vacía) para una fecha.
    """
    try:
        payload = {"fecha": fecha}
        # Timeout de 20s
        response = requests.post(URL_HORARIOS, headers=HEADERS, json=payload, timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            # La API suele devolver una lista de objetos o strings en 'horarios'
            horarios = data.get('result', {}).get('horarios', [])
            return horarios
    except Exception as e:
        print(f"⚠️ Error obteniendo horarios para {fecha}: {e}")
    return []

def verificar_citas():
    print("🌍 Consultando Xalapa (Modo Detallado)...")
    
    try:
        # 1. Consultar días
        response = requests.post(URL_DIAS, headers=HEADERS, json={}, timeout=20)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP al ver días: {response.status_code}")
            return

        data = response.json()
        dias_habiles = data.get('result', {}).get('dias_validos', [])
        
        if not dias_habiles:
            print("✅ Conexión exitosa. Calendario lleno (sin días).")
            return

        print(f"🔎 Días abiertos preliminares: {dias_habiles}")
        
        # Variable para construir el mensaje final
        reporte_final = "¡CORRE! SE ENCONTRARON CITAS DISPONIBLES:\n\n"
        encontrado_algo = False

        # 2. Barrer cada día para ver horas y cantidad
        for dia in dias_habiles:
            horarios = obtener_horarios(dia)
            
            if horarios:
                cantidad = len(horarios)
                
                # Intentamos formatear bonito la lista de horas
                # A veces la API manda objetos [{'hora':'10:00'}] o strings ['10:00']
                lista_horas_texto = []
                for h in horarios:
                    if isinstance(h, dict):
                        lista_horas_texto.append(h.get('hora', str(h)))
                    else:
                        lista_horas_texto.append(str(h))
                
                horas_string = ", ".join(lista_horas_texto)
                
                # Agregamos al reporte
                reporte_final += f"📅 FECHA: {dia}\n"
                reporte_final += f"🔢 Cantidad: {cantidad} turnos\n"
                reporte_final += f"⏰ Horarios: {horas_string}\n"
                reporte_final += "-------------------------------------\n"
                
                encontrado_algo = True
                print(f"   -> ¡Día {dia} tiene {cantidad} citas!")

        # 3. Enviar correo solo si realmente confirmamos horarios
        if encontrado_algo:
            reporte_final += "\n🔗 Reserva aquí rápido: https://digital.xalapa.gob.mx/citas_curp"
            print("\n🎉 ¡Encontramos oro! Enviando reporte...")
            enviar_correo(reporte_final)
        else:
            print("\n✅ Había días marcados, pero al revisar horarios estaban llenos (falsos positivos).")

    except Exception as e:
        print(f"❌ Error general de conexión: {e}")

if __name__ == "__main__":
    verificar_citas()
