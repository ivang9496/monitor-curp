import requests
import smtplib
import os
import urllib.parse # Importante para limpiar la contraseña
from email.message import EmailMessage

# --- CREDENCIALES DEL PROXY (NORDVPN) ---
PROXY_HOST = os.environ.get('PROXY_HOST')
PROXY_USER = os.environ.get('PROXY_USER')
PROXY_PASS = os.environ.get('PROXY_PASS')

# --- PREPARAR LA CONEXIÓN (FIX DNS + ENCODING) ---
if PROXY_HOST and PROXY_USER and PROXY_PASS:
    # 1. Codificamos usuario y contraseña para evitar errores con símbolos raros
    safe_user = urllib.parse.quote(PROXY_USER, safe='')
    safe_pass = urllib.parse.quote(PROXY_PASS, safe='')
    
    # 2. Usamos 'socks5h' (con h) para que el DNS lo resuelva NordVPN (Remote DNS)
    proxy_url = f"socks5h://{safe_user}:{safe_pass}@{PROXY_HOST}:1080"
    
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    print(f"🔒 Proxy configurado: {PROXY_HOST} (DNS Remoto activo)")
else:
    proxies = None
    print("⚠️ SIN PROXY: Usando conexión directa (Probablemente falle).")

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
    msg['Subject'] = '¡CITAS DISPONIBLES (NORDVPN)!'
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
        # Timeout extendido a 40s porque la redirección de DNS toma tiempo
        response = requests.post(URL_HORARIOS, headers=HEADERS, json=payload, proxies=proxies, timeout=40)
        if response.status_code == 200:
            data = response.json()
            horarios = data.get('result', {}).get('horarios', [])
            return len(horarios) > 0
    except:
        pass
    return False

def verificar_citas():
    print("🌍 Conectando vía NordVPN...", end="")
    try:
        response = requests.post(URL_DIAS, headers=HEADERS, json={}, proxies=proxies, timeout=40)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP: {response.status_code}")
            return

        dias_habiles = response.json().get('result', {}).get('dias_validos', [])
        dias_reales = []

        if dias_habiles:
            print(f"\n🔎 Días hábiles encontrados: {dias_habiles}")
            for dia in dias_habiles:
                if verificar_horarios(dia):
                    dias_reales.append(dia)
        
        if dias_reales:
            print(f"\n🎉 ¡Citas reales!: {dias_reales}")
            enviar_correo(f"¡HAY CITAS!: {dias_reales}\nLink: https://digital.xalapa.gob.mx/citas_curp")
        else:
            print("\n✅ Conexión OK. No hay horarios libres por el momento.")

    except Exception as e:
        print(f"\n❌ Error de conexión: {e}")

if __name__ == "__main__":
    verificar_citas()
