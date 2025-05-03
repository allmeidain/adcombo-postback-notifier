from flask import Flask, request
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz

app = Flask(__name__)

# Configurações (lidas de variáveis de ambiente)
API_KEY = os.environ.get("API_KEY")
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")  # Valor padrão
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))  # Valor padrão
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Verifica se as variáveis obrigatórias estão definidas
if not all([API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
    raise ValueError("Uma ou mais variáveis de ambiente não estão definidas: API_KEY, EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER")

# Verifica se as variáveis do Telegram estão definidas (opcional, para evitar falhas se não configuradas)
if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("Aviso: Variáveis TELEGRAM_BOT_TOKEN e/ou TELEGRAM_CHAT_ID não estão definidas. Notificações pelo Telegram serão ignoradas.")

def convert_to_recife_timezone(dt_str):
    """Converte a string de data do UTC para o fuso horário de Recife (America/Recife)."""
    # Assume que a data de entrada está em UTC
    utc_tz = pytz.UTC
    recife_tz = pytz.timezone('America/Recife')
    
    # Tenta parsear a string de data
    try:
        # Remove '×' inválido e assume formato ISO 8601
        dt_str = dt_str.replace('×', 't')  # Corrige o símbolo incorreto
        utc_dt = utc_tz.localize(datetime.fromisoformat(dt_str.replace('Z', '+00:00')))
        recife_dt = utc_dt.astimezone(recife_tz)
        return recife_dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError as e:
        print(f"Erro ao converter data {dt_str}: {e}")
        return dt_str  # Retorna original se falhar

def send_email(postback_data):
    """Envia e-mail com todos os parâmetros do Postback."""
    # Converte a data para o fuso de Recife
    postback_data['datetime'] = convert_to_recife_timezone(postback_data['datetime'])

    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"Postback - ID {postback_data['trans_id']}"

    body = f"""
    - Offer ID: {postback_data['offer_id']}
    - Revenue: {postback_data['revenue']}
    - Status: {postback_data['status']}
    - Transaction ID: {postback_data['trans_id']}
    - Click ID: {postback_data['clickid']}
    - Datetime: {postback_data['datetime']}
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        print(f"Tentando enviar e-mail de {EMAIL_SENDER} para {EMAIL_RECEIVER}")
        server = smtplib.SMTP(SMTPSERVER, SMTP_PORT)
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

def send_telegram_notification(postback_data):
    """Envia notificação para o Telegram com todos os parâmetros do Postback."""
    if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
        print("Notificação Telegram ignorada: TELEGRAM_BOT_TOKEN e/ou TELEGRAM_CHAT_ID não configurados.")
        return False

    # Converte a data para o fuso de Recife
    postback_data['datetime'] = convert_to_recife_timezone(postback_data['datetime'])

    # Mensagem em texto simples
    message = (
        f"- Offer ID: {postback_data['offer_id']}\n"
        f"- Revenue: {postback_data['revenue']}\n"
        f"- Status: {postback_data['status']}\n"
        f"- Transaction ID: {postback_data['trans_id']}\n"
        f"- Click ID: {postback_data['clickid']}\n"
        f"- Datetime: {postback_data['datetime']}\n"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message
    }

    try:
        print(f"Tentando enviar notificação Telegram para chat ID {TELEGRAM_CHAT_ID}")
        response = requests.post(url, data=payload)
        print(f"Resposta da API do Telegram: {response.status_code} - {response.text}")
        if response.status_code == 200:
            print(f"Notificação Telegram enviada com sucesso para chat ID {TELEGRAM_CHAT_ID}")
            return True
        else:
            print(f"Falha ao enviar notificação Telegram: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Erro ao enviar notificação Telegram: {e}")
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
        'offer_id': request.args.get('offer_id', 'N/A'),
        'rotator_id': request.args.get('rotator_id', 'N/A'),
        'trans_id': request.args.get('trans_id', 'N/A'),
        'revenue': request.args.get('revenue', 'N/A'),
        'status': request.args.get('status', 'N/A'),
        'goal': request.args.get('goal', 'N/A'),
        'clickid': request.args.get('clickid', 'N/A'),
        'click_id': request.args.get('click_id', 'N/A'),
        'subid': request.args.get('subid', 'N/A'),
        'sub_id': request.args.get('sub_id', 'N/A')
    }

    # Envia notificação por e-mail e Telegram
    email_success = send_email(postback_data)
    telegram_success = send_telegram_notification(postback_data)

    if email_success or telegram_success:
        return f"Postback processado (Status: {postback_data['status']}) - E-mail: {'enviado' if email_success else 'falhou'} - Telegram: {'enviado' if telegram_success else 'falhou'}", 200
    else:
        return "Erro ao enviar notificações por e-mail e Telegram", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Usa a porta definida pelo Render
    app.run(host="0.0.0.0", port=port)
