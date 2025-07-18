from flask import Blueprint, request, jsonify
from services.google_calendar_service import create_event
from models.user import UserModel

calendar_blueprint = Blueprint('calendar', __name__)

@calendar_blueprint.route('/create-event', methods=['POST'])
def create_calendar_event():
    dados = request.json or {}
    user = UserModel.find_by_username(dados['username'])
    if not user:
        return jsonify({'message': 'User not found.'}), 404

    if user.plan != 'Premium':
        return jsonify({'message': 'This feature is only available for Premium users.'}), 403

    summary = dados.get('summary')
    start_time = dados.get('start_time')
    end_time = dados.get('end_time')

    if not all([summary, start_time, end_time]):
        return jsonify({'message': 'Missing required fields.'}), 400

    event_link = create_event(summary, start_time, end_time)
    return jsonify({'event_link': event_link})
