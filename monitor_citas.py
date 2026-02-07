import requests
import smtplib
import os
from email.message import EmailMessage

# --- CONFIGURACIÓN ---
URL_API = "https://digital.xalapa.gob.mx/citas_curp/api/dias_disponibles"
HEADERS = {'Content-Type': 'application/json'}

def enviar_telegram(mensaje):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": mensaje}
    
    try:
        requests.post(url, json=payload)
        print("Notificación de Telegram enviada.")
    except Exception as e:
        print(f"Error en Telegram: {e}")

def enviar_correo(mensaje_cuerpo):
    email_user = os.environ.get('EMAIL_USER')
    email_pass = os.environ.get('EMAIL_PASS')
    # Si quieres que lleguen al mismo, usamos email_user como destino
    email_destino = os.environ.get('EMAIL_DESTINO') or email_user 

    msg = EmailMessage()
    msg.set_content(mensaje_cuerpo)
    msg['Subject'] = '¡HAY CITAS CURP XALAPA!'
    msg['From'] = email_user
    msg['To'] = email_destino

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email_user, email_pass)
        server.send_message(msg)
        server.quit()
        print("Correo enviado con éxito.")
    except Exception as e:
        print(f"Error en Correo: {e}")

def verificar_citas():
    try:
        response = requests.post(URL_API, headers=HEADERS, json={})
        data = response.json()
        result = data.get('result', {})
        dias = result.get('dias_validos', [])

        if dias and len(dias) > 0:
            aviso = f"🚨 ¡CITAS DISPONIBLES! 🚨\nFechas: {', '.join(dias)}\nEntra ya: https://digital.xalapa.gob.mx/citas_curp"
            
            enviar_telegram(aviso)
            enviar_correo(aviso)
        else:
            print("Sin disponibilidad aún.")
    except Exception as e:
        print(f"Error al consultar API: {e}")

if __name__ == "__main__":
    verificar_citas()

