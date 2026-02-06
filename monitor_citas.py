import requests
import smtplib
import os
from email.msg import EmailMessage

# Configuraciones de la API (obtenidas de tu código JS)
URL_API = "https://digital.xalapa.gob.mx/citas_curp/api/dias_disponibles"
HEADERS = {'Content-Type': 'application/json'}

def enviar_correo(mensaje_cuerpo):
    email_origen = os.environ.get('EMAIL_USER')
    email_destino = os.environ.get('EMAIL_DESTINO')
    password = os.environ.get('EMAIL_PASS')

    msg = EmailMessage()
    msg.set_content(mensaje_cuerpo)
    msg['Subject'] = '¡CITAS DISPONIBLES CURP XALAPA!'
    msg['From'] = email_origen
    msg['To'] = email_destino

    try:
        # Servidor SMTP de Gmail (puedes cambiarlo si usas otro)
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(email_origen, password)
        server.send_message(msg)
        server.quit()
        print("Correo enviado con éxito.")
    except Exception as e:
        print(f"Error al enviar correo: {e}")

def verificar_citas():
    try:
        # Hacemos la petición igual que la hace la página
        response = requests.post(URL_API, headers=HEADERS, json={})
        data = response.json()
        
        # Basado en tu JS: result.dias_validos
        result = data.get('result', {})
        dias = result.get('dias_validos', [])

        if dias and len(dias) > 0:
            msg = f"Se encontraron citas disponibles en las siguientes fechas: {', '.join(dias)}\n\nCorre a: https://digital.xalapa.gob.mx/citas_curp"
            print("¡Citas encontradas!")
            enviar_correo(msg)
        else:
            print("Sigue sin haber citas...")

    except Exception as e:
        print(f"Error al consultar la API: {e}")

if __name__ == "__main__":
    verificar_citas()