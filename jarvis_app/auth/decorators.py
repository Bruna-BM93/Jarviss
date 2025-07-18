"""
Decoradores de autenticação para a aplicação Jarvis.

Este módulo fornece decoradores para proteger rotas, como a verificação
de tokens JWT.
"""
from functools import wraps

import jwt # Para decodificar JWT e exceções relacionadas
from flask import current_app, jsonify, request # Para contexto da aplicação, respostas JSON e objeto request

def token_required(f):
    """
    Decorador para proteger rotas que exigem um token JWT válido.

    Verifica a presença e validade de um token 'Bearer' no cabeçalho
    'Authorization'. Retorna um erro 401 se o token estiver ausente,
    mal formatado, expirado ou inválido.

    Args:
        f (function): A função da rota a ser decorada.

    Returns:
        function: A função decorada.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            current_app.logger.info("Tentativa de acesso sem token Bearer ou token ausente.")
            return jsonify({'erro': 'Token de autenticação ausente ou mal formatado. Use Bearer token.'}), 401

        token_parts = auth_header.split(' ')
        if len(token_parts) != 2 or token_parts[0].lower() != 'bearer':
            current_app.logger.info("Token Bearer mal formatado.")
            return jsonify({'erro': 'Token Bearer mal formatado.'}), 401

        token = token_parts[1]

        try:
            # Decodifica o token para validar sua assinatura e expiração.
            # O payload decodificado não é explicitamente passado para a rota aqui,
            # pois as rotas podem usar `get_user_details_from_token` ou similar
            # de `db_utils` se precisarem dos dados do token.
            jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            current_app.logger.warning(f"Token expirado fornecido por {request.remote_addr}.")
            return jsonify({'erro': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            current_app.logger.warning(f"Token inválido fornecido por {request.remote_addr}.")
            return jsonify({'erro': 'Token inválido'}), 401
        except Exception as e:
            # Captura outras exceções que podem ocorrer durante a decodificação do token.
            current_app.logger.error(f"Erro inesperado na validação do token de {request.remote_addr}: {e}")
            return jsonify({'erro': 'Erro interno ao processar token'}), 401 # 401 ou 500 dependendo da política

        return f(*args, **kwargs)
    return decorated_function
