import requests
import smtplib
import os
from email.message import EmailMessage

# --- CONFIGURACIÓN DEL PROXY (DOCKER) ---
# Como el contenedor de NordVPN está corriendo al lado, 
# nos conectamos a él a través del puerto 1080 local.
proxies = {
    'http': 'socks5://localhost:1080',
    'https': 'socks5://localhost:1080'
}

# --- DATOS DEL CORREO (Desde Secrets) ---
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_DESTINO = os.environ.get('EMAIL_DESTINO')

# --- CONFIGURACIÓN DE LA API ---
URL_DIAS = "https://digital.xalapa.gob.mx/citas_curp/api/dias_disponibles"
URL_HORARIOS = "https://digital.xalapa.gob.mx/citas_curp/api/horarios_disponibles"

HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://digital.xalapa.gob.mx/citas_curp',
    'Origin': 'https://digital.xalapa.gob.mx'
}

def enviar_correo(mensaje_cuerpo):
    print("📧 Intentando enviar correo...")
    msg = EmailMessage()
    msg.set_content(mensaje_cuerpo, charset='utf-8')
    msg['Subject'] = '¡CITAS DISPONIBLES (VÍA VPN)!'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_DESTINO

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Correo enviado con éxito.")
    except Exception as e:
        print(f"❌ Error al enviar correo: {e}")

def verificar_horarios(fecha):
    """
    Verifica si una fecha específica tiene horas disponibles.
    """
    try:
        payload = {"fecha": fecha}
        # Timeout de 30s para dar tiempo a la VPN
        response = requests.post(URL_HORARIOS, headers=HEADERS, json=payload, proxies=proxies, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            horarios = data.get('result', {}).get('horarios', [])
            return len(horarios) > 0 # Retorna True si hay horarios
    except Exception as e:
        print(f"⚠️ Error verificando horario para {fecha}: {e}")
    return False

def verificar_citas():
    print("🌍 Conectando a Xalapa a través del túnel VPN (localhost:1080)...")
    
    try:
        # Paso 1: Buscar días hábiles en el calendario
        response = requests.post(URL_DIAS, headers=HEADERS, json={}, proxies=proxies, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ La página respondió con error: {response.status_code}")
            return

        data = response.json()
        dias_habiles = data.get('result', {}).get('dias_validos', [])

        dias_con_cupo = []

        # Paso 2: Si hay días hábiles, verificar si tienen cupo real
        if dias_habiles:
            print(f"🔎 Días hábiles encontrados (validando cupo): {dias_habiles}")
            
            for dia in dias_habiles:
                if verificar_horarios(dia):
                    print(f"   -> ¡Día {dia} tiene horarios!")
                    dias_con_cupo.append(dia)
                else:
                    print(f"   -> Día {dia} está lleno.")
        
        # Paso 3: Resultados finales
        if dias_con_cupo:
            print(f"\n🎉 ¡ÉXITO! Se encontraron citas en: {dias_con_cupo}")
            enviar_correo(f"¡EL MONITOR FUNCIONÓ!\nHay citas disponibles en: {dias_con_cupo}\n\nEntra rápido: https://digital.xalapa.gob.mx/citas_curp")
        else:
            print("\n✅ Conexión exitosa a través de México, pero NO hay citas disponibles por el momento.")

    except Exception as e:
        print(f"\n❌ Error de conexión (VPN o API caída): {e}")

if __name__ == "__main__":
    verificar_citas()
