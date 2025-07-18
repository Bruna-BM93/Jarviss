from flask import Blueprint, request, jsonify
from services.openai_service import generate_response
from models.user import UserModel

ai_blueprint = Blueprint('ai', __name__)

@ai_blueprint.route('/chat', methods=['POST'])
def chat():
    dados = request.json or {}
    user = UserModel.find_by_username(dados['username'])
    if not user:
        return jsonify({'message': 'User not found.'}), 404

    # This is a simplified example. In a real application, you would
    # check the user's plan and limit the number of questions.
    if user.plan == 'Gratuito':
        # Logic to limit questions for free users
        pass

    prompt = dados.get('prompt')
    if not prompt:
        return jsonify({'message': 'Prompt is required.'}), 400

    response = generate_response(prompt)
    return jsonify({'response': response})
