import requests
import smtplib
import os
from email.message import EmailMessage

# --- CONFIGURACIÓN SIMPLE ---
# Ahora nos conectamos al contenedor de servicio que está en localhost
proxies = {
    'http': 'socks5://localhost:1080',
    'https': 'socks5://localhost:1080'
}

# --- DATOS DEL CORREO ---
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_DESTINO = os.environ.get('EMAIL_DESTINO')

# --- API ---
URL_DIAS = "https://digital.xalapa.gob.mx/citas_curp/api/dias_disponibles"
URL_HORARIOS = "https://digital.xalapa.gob.mx/citas_curp/api/horarios_disponibles"

HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def enviar_correo(mensaje_cuerpo):
    msg = EmailMessage()
    msg.set_content(mensaje_cuerpo, charset='utf-8')
    msg['Subject'] = '¡CITAS DISPONIBLES (DOCKER)!'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_DESTINO

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Correo enviado.")
    except Exception as e:
        print(f"❌ Error correo: {e}")

def verificar_horarios(fecha):
    try:
        payload = {"fecha": fecha}
        # Timeout de 30s por si la VPN tarda un poco
        response = requests.post(URL_HORARIOS, headers=HEADERS, json=payload, proxies=proxies, timeout=30)
        if response.status_code == 200:
            data = response.json()
            horarios = data.get('result', {}).get('horarios', [])
            return len(horarios) > 0
    except:
        pass
    return False

def verificar_citas():
    print("🌍 Consultando Xalapa a través del túnel VPN Docker...", end="")
    try:
        response = requests.post(URL_DIAS, headers=HEADERS, json={}, proxies=proxies, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            return

        dias_habiles = response.json().get('result', {}).get('dias_validos', [])
        dias_reales = []

        if dias_habiles:
            print(f"\n🔎 Días hábiles: {dias_habiles}")
            for dia in dias_habiles:
                if verificar_horarios(dia):
                    dias_reales.append(dia)
        
        if dias_reales:
            print(f"\n🎉 ¡Citas encontradas!: {dias_reales}")
            enviar_correo(f"¡Funciona! Citas en: {dias_reales}\nLink: https://digital.xalapa.gob.mx/citas_curp")
        else:
            print("\n✅ Conexión exitosa a través de México. No hay horarios libres.")

    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")

if __name__ == "__main__":
    verificar_citas()
