import requests
import smtplib
import os
from email.message import EmailMessage

# --- CONFIGURACIÓN DE PROXY NORDVPN ---
PROXY_HOST = os.environ.get('PROXY_HOST')
PROXY_USER = os.environ.get('PROXY_USER')
PROXY_PASS = os.environ.get('PROXY_PASS')

# Construimos la URL del proxy SOCKS5
# Formato: socks5://usuario:contraseña@servidor:1080
proxy_url = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:1080"

proxies = {
    'http': proxy_url,
    'https': proxy_url
}

# --- DATOS DEL CORREO ---
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_DESTINO = os.environ.get('EMAIL_DESTINO')

# --- CONFIGURACIÓN DE LA PÁGINA ---
URL_API = "https://digital.xalapa.gob.mx/citas_curp/api/dias_disponibles"
HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def enviar_correo(mensaje_cuerpo):
    msg = EmailMessage()
    msg.set_content(mensaje_cuerpo, charset='utf-8')
    msg['Subject'] = 'CITAS DISPONIBLES (NORDVPN)'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_DESTINO

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("Correo enviado.")
    except Exception as e:
        print(f"Error correo: {e}")

def verificar_citas():
    print("Conectando vía NordVPN...", end="")
    try:
        # AQUÍ ESTÁ LA MAGIA: pasamos el argumento 'proxies'
        response = requests.post(URL_API, headers=HEADERS, json={}, proxies=proxies, timeout=30)
        
        if response.status_code != 200:
            print(f" Falló la conexión (Status: {response.status_code})")
            return

        data = response.json()
        dias = data.get('result', {}).get('dias_validos', [])

        if dias:
            print(f" ¡ÉXITO! Días: {dias}")
            enviar_correo(f"¡NordVPN funcionó! Hay citas: {dias}")
        else:
            print(" Conexión exitosa, pero sin citas.")

    except Exception as e:
        print(f" Error de conexión con Proxy: {e}")

if __name__ == "__main__":
    verificar_citas()


