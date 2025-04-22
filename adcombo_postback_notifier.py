from flask import Flask, request
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)

# Configurações (lidas de variáveis de ambiente)
API_KEY = os.environ.get("API_KEY")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")  # Valor padrão
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))  # Valor padrão
HOLDS_FILE = "holds.json"

# Verifica se as variáveis obrigatórias estão definidas
if not all([API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
    raise ValueError("Uma ou mais variáveis de ambiente não estão definidas: API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER")

def load_processed_holds():
    """Carrega holds já processados do arquivo."""
    if os.path.exists(HOLDS_FILE):
        with open(HOLDS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_processed_holds(holds):
    """Salva holds processados no arquivo."""
    with open(HOLDS_FILE, 'w') as f:
        json.dump(holds, f, indent=4)

def send_email(hold_data):
    """Envia e-mail com detalhes do hold."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"Novo Hold Detectado - ID {hold_data['conversion_id']}"

    body = f"""
    Novo hold detectado em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:
    - ID da Conversão: {hold_data['conversion_id']}
    - Oferta: {hold_data['offer_name']}
    - Valor: {hold_data['amount']} {hold_data['currency']}
    - Data: {hold_data['created_at']}
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print(f"E-mail enviado para hold ID {hold_data['conversion_id']}")
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

@app.route('/postback', methods=['GET'])
def handle_postback():
    """Processa o Postback da AdCombo."""
    # Verifica a chave de API
    received_api_key = request.args.get('api_key')
    print(f"API_KEY configurada: {API_KEY}")  # Linha de depuração
    print(f"Chave recebida: {received_api_key}")  # Linha de depuração
    if received_api_key != API_KEY:
        return "Chave de API inválida", 403

    # Obtém os parâmetros do Postback
    status = request.args.get('status')
    if status != 'hold':
        return "Ignorado: Não é um hold", 200

    hold_data = {
        'conversion_id': request.args.get('conversion_id', 'N/A'),
        'offer_name': request.args.get('offer_name', 'N/A'),
        'amount': request.args.get('amount', 'N/A'),
        'currency': request.args.get('currency', 'N/A'),
        'created_at': request.args.get('created_at', 'N/A')
    }

    # Carrega holds processados
    processed_holds = load_processed_holds()
    processed_ids = {hold['conversion_id'] for hold in processed_holds}

    # Verifica se o hold é novo
    if hold_data['conversion_id'] not in processed_ids:
        # Envia e-mail
        if send_email(hold_data):
            processed_holds.append(hold_data)
            save_processed_holds(processed_holds)
            return "Hold processado e e-mail enviado", 200
        else:
            return "Erro ao enviar e-mail", 500
    else:
        return "Hold já processado", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Usa a porta definida pelo Render
    app.run(host="0.0.0.0", port=port)
