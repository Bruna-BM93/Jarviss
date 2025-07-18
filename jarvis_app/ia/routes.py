"""
Rotas para funcionalidades de Inteligência Artificial.

Este Blueprint agrupa endpoints que interagem com modelos de IA,
como chat e interpretação de texto.
"""
import json
import re

import jwt # Para exceções de token ao chamar get_user_details_from_token
import openai # Para interagir com a API da OpenAI
from flask import Blueprint, current_app, jsonify, request

from jarvis_app.auth.decorators import token_required
from jarvis_app.core.db_utils import get_user_details_from_token

ia_bp = Blueprint('ia', __name__)
# O prefixo '/ia' é definido em jarvis_app/__init__.py ao registrar o blueprint.

@ia_bp.route('/perguntar', methods=['POST'])
@token_required
def ia_perguntar():
    """
    Endpoint para enviar uma pergunta para a IA (chat genérico).
    Requer autenticação e verifica se a feature 'ia_chat' está no plano do usuário.
    A pergunta é enviada para o modelo GPT da OpenAI.
    """
    try:
        user_details = get_user_details_from_token()
        if not user_details:
            return jsonify({'erro': 'Usuário do token não encontrado ou token inválido'}), 401
    except jwt.ExpiredSignatureError:
        current_app.logger.info("Token expirado ao acessar /ia/perguntar.")
        return jsonify({'erro': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        current_app.logger.info("Token inválido ao tentar acessar /ia/perguntar.")
        return jsonify({'erro': 'Token inválido'}), 401
    except Exception as e:
        current_app.logger.exception(f"Erro ao obter detalhes do usuário do token em /ia/perguntar: {e}")
        return jsonify({'erro': 'Erro interno ao processar token'}), 500

    plano_usuario = user_details['plano']
    # Removido usuario_id e usuario_sub não utilizados diretamente aqui, exceto para logging
    # Se precisar deles para lógica de negócios, podem ser mantidos.
    usuario_sub_for_log = user_details['username']

    # Verificação de feature do plano
    if 'ia_chat' not in current_app.config['FEATURES_BY_PLAN'].get(plano_usuario, {}): # Usar {} como fallback
        current_app.logger.warning(
            f"Usuário {usuario_sub_for_log} (ID: {user_details['id']}) no plano {plano_usuario} "
            "tentou acessar 'ia_chat' sem permissão."
        )
        return jsonify({'erro': 'Funcionalidade ia_chat não disponível para seu plano.'}), 403

    dados_req = request.json
    if not dados_req: # Validação já feita no subtask anterior, mas mantida por segurança
        return jsonify({'erro': 'Corpo da requisição JSON não pode ser vazio.'}), 400

    pergunta = dados_req.get('pergunta')
    if not pergunta: # Validação já feita
        return jsonify({'erro': 'Campo pergunta é obrigatório.'}), 400
    if not isinstance(pergunta, str) or not pergunta.strip(): # Validação já feita
        return jsonify({'erro': 'Campo pergunta deve ser uma string não vazia.'}), 400

    openai_api_key = current_app.config.get("OPENAI_API_KEY")
    if not openai_api_key:
        current_app.logger.error("OPENAI_API_KEY não configurada no servidor para /ia/perguntar.")
        return jsonify({'erro': 'Serviço de IA temporariamente indisponível.'}), 500 # Erro 500 mais genérico para o cliente

    openai.api_key = openai_api_key

    try:
        current_app.logger.info(f"Usuário {usuario_sub_for_log} perguntou à IA: {pergunta[:100]}...") # Log truncado
        response = openai.ChatCompletion.create(
            model=current_app.config.get("OPENAI_CHAT_MODEL", "gpt-3.5-turbo"), # Modelo configurável
            messages=[
                {"role": "system", "content": "Você é um assistente empresarial útil."},
                {"role": "user", "content": pergunta}
            ],
            temperature=current_app.config.get("OPENAI_CHAT_TEMPERATURE", 0.7) # Temp configurável
        )
        resposta_ia = response.choices[0].message['content'].strip()
        current_app.logger.info(f"Resposta da IA para {usuario_sub_for_log} (Chat): {resposta_ia[:100]}...") # Log truncado
        return jsonify({'resposta': resposta_ia})
    except openai.error.AuthenticationError as e:
        current_app.logger.error(f"Erro de autenticação com OpenAI para {usuario_sub_for_log} (Chat): {e}")
        return jsonify({'erro': 'Falha na autenticação com o serviço de IA.'}), 502
    except openai.error.OpenAIError as e:
        current_app.logger.error(f"Erro da API OpenAI para {usuario_sub_for_log} (Chat): {e}")
        return jsonify({'erro': 'Erro ao comunicar com o serviço de IA. Tente mais tarde.'}), 502
    except Exception as e:
        current_app.logger.exception(f"Erro inesperado na chamada OpenAI para {usuario_sub_for_log} (Chat): {e}")
        return jsonify({'erro': 'Erro inesperado ao processar sua pergunta.'}), 500


@ia_bp.route('/interpretar_notificacao', methods=['POST'])
@token_required
def ia_interpretar_notificacao():
    """
    Endpoint para interpretar o texto de uma notificação bancária usando IA.
    Requer autenticação e verifica a feature 'ia_interpretacao_notificacao'.
    Espera um JSON com 'texto_notificacao' e retorna os dados interpretados.
    """
    try:
        user_details = get_user_details_from_token()
        if not user_details:
            return jsonify({'erro': 'Usuário do token não encontrado ou token inválido.'}), 401
    except jwt.ExpiredSignatureError:
        current_app.logger.info("Token expirado ao acessar /ia/interpretar_notificacao.")
        return jsonify({'erro': 'Token expirado.'}), 401
    except jwt.InvalidTokenError:
        current_app.logger.info("Token inválido ao tentar acessar /ia/interpretar_notificacao.")
        return jsonify({'erro': 'Token inválido.'}), 401
    except Exception as e:
        current_app.logger.exception(f"Erro ao obter detalhes do token em /ia/interpretar_notificacao: {e}")
        return jsonify({'erro': 'Erro interno ao processar token.'}), 500

    plano_usuario = user_details['plano']
    usuario_sub_for_log = user_details['username']

    if 'ia_interpretacao_notificacao' not in current_app.config['FEATURES_BY_PLAN'].get(plano_usuario, {}):
        current_app.logger.warning(
            f"Usuário {usuario_sub_for_log} (ID: {user_details['id']}) no plano {plano_usuario} "
            "tentou acessar 'ia_interpretacao_notificacao' sem permissão."
        )
        return jsonify({'erro': 'Funcionalidade de interpretação de notificação não disponível para seu plano.'}), 403

    dados_req = request.json
    if not dados_req:
        return jsonify({'erro': 'Corpo da requisição JSON não pode ser vazio'}), 400

    pergunta = dados_req.get('pergunta')
    if not pergunta:
        return jsonify({'erro': 'Campo pergunta é obrigatório'}), 400
    if not isinstance(pergunta, str) or not pergunta.strip():
        return jsonify({'erro': 'Campo pergunta deve ser uma string não vazia'}), 400

    openai_api_key = current_app.config.get("OPENAI_API_KEY")
    if not openai_api_key:
        current_app.logger.error("OPENAI_API_KEY não configurada no servidor.")
        return jsonify({'erro': 'Chave da API OpenAI não configurada no servidor'}), 500
    openai.api_key = openai_api_key

    system_prompt = """Você é um assistente financeiro especialista em interpretar notificações bancárias.
Analise o texto da notificação fornecido pelo usuário.
Extraia as seguintes informações:
- 'tipo': deve ser "receita" ou "despesa".
- 'valor': deve ser um número (float ou int), representando o montante da transação.
- 'descricao_sugerida': uma breve descrição para a transação (ex: "Pagamento Spotify", "Transferência recebida de João").
Responda APENAS com um objeto JSON contendo esses três campos.
Por exemplo: {"tipo": "despesa", "valor": 50.00, "descricao_sugerida": "Compra em Supermercado"}
Se não conseguir determinar algum campo com clareza, use null para seu valor.
Se o valor for explicitamente R$0,00 ou similar, interprete como 0.0.
Não adicione nenhuma explicação ou texto adicional fora do JSON.
"""

    try:
        current_app.logger.info(
            f"Usuário {usuario_sub_for_log} (ID: {user_details['id']}) enviou notificação para interpretação: "
            f"{texto_notificacao[:100]}..." # Log truncado
        )
        response = openai.ChatCompletion.create(
            model=current_app.config.get("OPENAI_INTERPRET_MODEL", "gpt-3.5-turbo"), # Modelo configurável
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": texto_notificacao}
            ],
            temperature=current_app.config.get("OPENAI_INTERPRET_TEMPERATURE", 0.2) # Temp configurável
        )

        ia_response_content = response.choices[0].message['content'].strip()
        current_app.logger.info(
            f"Resposta bruta da IA para {usuario_sub_for_log} (Interpretação): {ia_response_content}"
        )

        # Tenta extrair o JSON da resposta, mesmo que haja texto adicional
        json_match = re.search(r'\{.*\}', ia_response_content, re.DOTALL)
        if not json_match:
            log_msg = (f"Nenhum JSON encontrado na resposta da IA para {usuario_sub_for_log} "
                       f"(Interpretação): {ia_response_content}")
            current_app.logger.error(log_msg)
            return jsonify({'erro': 'Falha ao interpretar resposta da IA: JSON não encontrado.'}), 502

        json_str = json_match.group(0)

        try:
            interpreted_data = json.loads(json_str)
        except json.JSONDecodeError as json_err:
            log_msg = (f"Falha ao decodificar JSON da IA para {usuario_sub_for_log} "
                       f"(Interpretação): {json_err}. JSON String: {json_str}")
            current_app.logger.error(log_msg)
            return jsonify({'erro': f'Falha ao decodificar resposta JSON da IA: {json_err}.'}), 502

        # Validação dos campos esperados na resposta da IA
        required_keys = ['tipo', 'valor', 'descricao_sugerida']
        if not all(key in interpreted_data for key in required_keys):
            log_msg = (f"Resposta da IA não contém todos os campos esperados ({required_keys}) "
                       f"para {usuario_sub_for_log} (Interpretação). Recebido: {interpreted_data}")
            current_app.logger.error(log_msg)
            return jsonify({'erro': 'Resposta da IA está incompleta ou mal formatada.'}), 502

        # Validações adicionais dos tipos de dados retornados pela IA (exemplo)
        tipo_retornado = interpreted_data.get('tipo')
        if tipo_retornado is not None and tipo_retornado not in ['receita', 'despesa']:
             current_app.logger.warning(
                 f"Tipo inválido '{tipo_retornado}' retornado pela IA para {usuario_sub_for_log} (Interpretação)."
             )

        valor_retornado = interpreted_data.get('valor')
        if valor_retornado is not None and not isinstance(valor_retornado, (int, float)):
            current_app.logger.warning(
                f"Valor não numérico '{valor_retornado}' retornado pela IA para {usuario_sub_for_log} (Interpretação)."
            )

        current_app.logger.info(
            f"Dados interpretados para {usuario_sub_for_log} (Interpretação): {interpreted_data}"
        )
        return jsonify(interpreted_data)

    except openai.error.AuthenticationError as e:
        current_app.logger.error(f"Erro de autenticação OpenAI para {usuario_sub_for_log} (Interpretação): {e}")
        return jsonify({'erro': 'Falha na autenticação com o serviço de IA.'}), 502
    except openai.error.OpenAIError as e:
        current_app.logger.error(f"Erro da API OpenAI para {usuario_sub_for_log} (Interpretação): {e}")
        return jsonify({'erro': 'Erro ao comunicar com o serviço de IA. Tente mais tarde.'}), 502
    except Exception as e:
        current_app.logger.exception(f"Erro inesperado na interpretação de notificação para {usuario_sub_for_log}: {e}")
        return jsonify({'erro': 'Erro inesperado ao processar sua notificação.'}), 500
