import requests
import smtplib
import os
from email.message import EmailMessage

# --- CREDENCIALES DEL PROXY (NORDVPN) ---
# GitHub las tomará de los "Secrets" que acabas de configurar
PROXY_HOST = os.environ.get('PROXY_HOST')
PROXY_USER = os.environ.get('PROXY_USER')
PROXY_PASS = os.environ.get('PROXY_PASS')

# Configuración de la conexión segura vía SOCKS5
if PROXY_HOST and PROXY_USER and PROXY_PASS:
    proxy_url = f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:1080"
    proxies = {
        'http': proxy_url,
        'https': proxy_url
    }
    print(f"🔒 Configurando Proxy con servidor: {PROXY_HOST}")
else:
    proxies = None
    print("⚠️ ADVERTENCIA: No se detectaron credenciales de Proxy. Usando conexión directa.")

# --- DATOS DEL CORREO ---
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
EMAIL_DESTINO = os.environ.get('EMAIL_DESTINO')

# --- URLS DE LA API ---
URL_DIAS = "https://digital.xalapa.gob.mx/citas_curp/api/dias_disponibles"
URL_HORARIOS = "https://digital.xalapa.gob.mx/citas_curp/api/horarios_disponibles"

HEADERS = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def enviar_correo(mensaje_cuerpo):
    msg = EmailMessage()
    msg.set_content(mensaje_cuerpo, charset='utf-8')
    msg['Subject'] = '¡CITAS DISPONIBLES (VÍA NORDVPN)!'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_DESTINO

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ Correo de aviso enviado.")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")

def verificar_horarios(fecha):
    try:
        payload = {"fecha": fecha}
        # Nota el timeout más alto (30s) porque los proxies a veces son lentos
        response = requests.post(URL_HORARIOS, headers=HEADERS, json=payload, proxies=proxies, timeout=30)
        if response.status_code == 200:
            data = response.json()
            horarios = data.get('result', {}).get('horarios', [])
            return len(horarios) > 0
    except Exception as e:
        print(f"Error verificando horario: {e}")
    return False

def verificar_citas():
    print("🌍 Conectando a Xalapa vía NordVPN...", end="")
    try:
        # Paso 1: Buscar días
        response = requests.post(URL_DIAS, headers=HEADERS, json={}, proxies=proxies, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Falló conexión. Código: {response.status_code}")
            return

        dias_habiles = response.json().get('result', {}).get('dias_validos', [])
        dias_reales = []

        # Paso 2: Verificar horarios reales
        if dias_habiles:
            print(f"\n🔎 Revisando días hábiles: {dias_habiles}")
            for dia in dias_habiles:
                if verificar_horarios(dia):
                    dias_reales.append(dia)
        
        if dias_reales:
            print(f"\n🎉 ¡ÉXITO! Citas reales en: {dias_reales}")
            enviar_correo(f"¡Funciona el Proxy! Hay citas en: {dias_reales}\nLink: https://digital.xalapa.gob.mx/citas_curp")
        else:
            print("\n✅ Conexión exitosa, pero NO hay horarios disponibles (o están llenos).")

    except Exception as e:
        print(f"\n❌ Error grave de conexión: {e}")

if __name__ == "__main__":
    verificar_citas()


