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

def send_email(hold_data, status):
    """Envia e-mail com detalhes do Postback, incluindo o status."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"Novo Postback Recebido - ID {hold_data['conversion_id']}"

    body = f"""
    Novo Postback recebido em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:
    - Status: {status}
    - ID da Conversão: {hold_data['conversion_id']}
    - Oferta: {hold_data['offer_name']}
    - Valor: {hold_data['amount']} {hold_data['currency']}
    - Data: {hold_data['created_at']}
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
        print(f"E-mail enviado para Postback ID {hold_data['conversion_id']} - Destinatário: {EMAIL_RECEIVER}")
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

    # Obtém os parâmetros do Postback
    status = request.args.get('status')
    hold_data = {
        'conversion_id': request.args.get('conversion_id', 'N/A'),
        'offer_name': request.args.get('offer_name', 'N/A'),
        'amount': request.args.get('amount', 'N/A'),
        'currency': request.args.get('currency', 'N/A'),
        'created_at': request.args.get('created_at', 'N/A')
    }

    # Envia e-mail com o status
    if send_email(hold_data, status):
        return f"Postback processado e e-mail enviado (Status: {status})", 200
    else:
        return "Erro ao enviar e-mail", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Usa a porta definida pelo Render
    app.run(host="0.0.0.0", port=port)
