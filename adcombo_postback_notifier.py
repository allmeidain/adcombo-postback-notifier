from flask import Flask, request
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

# Verifica se as variáveis obrigatórias estão definidas
if not all([API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
    raise ValueError("Uma ou mais variáveis de ambiente não estão definidas: API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER")

def send_email(postback_data):
    """Envia e-mail com todos os parâmetros do Postback."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"Novo Postback Recebido - ID {postback_data['trans_id']}"

    body = f"""
    Novo Postback recebido em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:
    - Offer Name: {postback_data['offer_id']}
    - Amount: {postback_data['revenue']}
    - Status: {postback_data['status']}
    - Transaction ID: {postback_data['trans_id']}
    - Click ID: {postback_data['clickid']}
    - Datetime: {postback_data['datetime']}
    - Timestamp: {postback_data['timestamp']}
    - Created At: {postback_data['created']}
    - Rotator ID: {postback_data['rotator_id']}
    - Goal: {postback_data['goal']}
    - Click ID (alternative): {postback_data['click_id']}
    - Sub ID: {postback_data['subid']}
    - Sub ID (alternative): {postback_data['sub_id']}
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        print(f"Tentando enviar e-mail de {EMAIL_SENDER} para {EMAIL_RECEIVER}")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        print("Conexão SMTP estabelecida")
        server.starttls()
        print("STARTTLS ativado")
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        print("Login SMTP bem-sucedido")
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print(f"E-mail enviado para Postback ID {postback_data['trans_id']} - Destinatário: {EMAIL_RECEIVER}")
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

@app.route('/ping', methods=['GET'])
def ping():
    """Endpoint para manter o serviço ativo."""
    return "Service is awake!", 200

@app.route('/postback', methods=['GET'])
def handle_postback():
    """Processa o Postback da AdCombo."""
    # Verifica a chave de API
    received_api_key = request.args.get('api_key')
    print(f"API_KEY configurada: {API_KEY}")
    print(f"Chave recebida: {received_api_key}")
    if received_api_key != API_KEY:
        return "Chave de API inválida", 403

    # Obtém todos os parâmetros do Postback
    postback_data = {
        'datetime': request.args.get('datetime', 'N/A'),
        'timestamp': request.args.get('timestamp', 'N/A'),
        'created': request.args.get('created_at', 'N/A'),
        'offer_id': request.args.get('offer_name', 'N/A'),
        'rotator_id': request.args.get('rotator_id', 'N/A'),
        'trans_id': request.args.get('trans_id', 'N/A'),
        'revenue': request.args.get('amount', 'N/A'),
        'status': request.args.get('status', 'N/A'),
        'goal': request.args.get('goal', 'N/A'),
        'clickid': request.args.get('clickid', 'N/A'),
        'click_id': request.args.get('click_id', 'N/A'),
        'subid': request.args.get('subid', 'N/A'),
        'sub_id': request.args.get('sub_id', 'N/A')
    }

    # Envia e-mail com todos os parâmetros
    if send_email(postback_data):
        return f"Postback processado e e-mail enviado (Status: {postback_data['status']})", 200
    else:
        return "Erro ao enviar e-mail", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Usa a porta definida pelo Render
    app.run(host="0.0.0.0", port=port)
