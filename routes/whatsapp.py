from flask import Blueprint, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from models.user import UserModel
import re

whatsapp_blueprint = Blueprint('whatsapp', __name__)

@whatsapp_blueprint.route('/webhook', methods=['POST'])
def webhook():
    message = request.form.get('Body')
    sender_id = request.form.get('From')
    resp = MessagingResponse()

    # Basic state management
    # In a real app, you'd use a database to store conversation state
    state = "start"

    if state == "start":
        resp.message("Qual seu nome?")
        # Transition to the next state
        # In a real app, you would save the state for the user
    elif state == "get_name":
        name = message
        # Save the name
        resp.message("Envie sua dúvida ou orçamento")
        # Transition to the next state
    else:
        # Handle the user's query
        resp.message("Obrigado por sua mensagem. Entraremos em contato em breve.")

    return Response(str(resp), mimetype="application/xml")
