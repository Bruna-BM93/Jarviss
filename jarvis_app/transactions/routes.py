"""
Rotas para gerenciamento de transações financeiras.

Este Blueprint lida com a criação e listagem de transações (receitas/despesas)
para usuários autenticados.
"""
import sqlite3

import jwt # Para exceções de token ao chamar get_usuario_id_from_token
from flask import Blueprint, current_app, jsonify, request

from jarvis_app.auth.decorators import token_required
from jarvis_app.core.db_utils import (get_db, get_usuario_id_from_token,
                                      validate_date_format)

transaction_bp = Blueprint('transactions', __name__)
# O prefixo '/transacoes' é definido em jarvis_app/__init__.py ao registrar o blueprint.

@transaction_bp.route('', methods=['POST'])
@token_required
def adicionar_transacao_route():
    """
    Adiciona uma nova transação financeira (receita ou despesa) para o usuário autenticado.
    Espera um corpo JSON com 'descricao', 'valor', 'tipo', e 'data'.
    """
    try:
        usuario_id = get_usuario_id_from_token()
        if not usuario_id:
            # get_usuario_id_from_token já loga o erro
            return jsonify({'erro': 'Falha ao identificar usuário a partir do token.'}), 401
    except jwt.ExpiredSignatureError:
        current_app.logger.info("Token expirado ao tentar adicionar transação.")
        return jsonify({'erro': 'Token expirado.'}), 401
    except jwt.InvalidTokenError:
        current_app.logger.info("Token inválido ao tentar adicionar transação.")
        return jsonify({'erro': 'Token inválido.'}), 401
    except Exception as e:
        current_app.logger.exception(f"Erro ao obter usuario_id do token em POST /transacoes: {e}")
        return jsonify({'erro': 'Erro interno ao processar token.'}), 500

    dados = request.json
    if not dados:
        return jsonify({'erro': 'Corpo da requisição JSON não pode ser vazio'}), 400

    # Validação de campos obrigatórios e tipos
    campos_obrigatorios = {
        'descricao': str,
        'valor': (int, float), # Aceita int ou float, será convertido para float
        'tipo': str,
        'data': str
    }
    erros_validacao = []

    for campo, tipo_esperado in campos_obrigatorios.items():
        if campo not in dados:
            erros_validacao.append(f'Campo {campo} é obrigatório.')
            continue # Pula para o próximo campo se este estiver ausente

        valor_campo = dados[campo]

        if isinstance(tipo_esperado, tuple): # Para o campo 'valor' que aceita int ou float
            if not any(isinstance(valor_campo, t) for t in tipo_esperado):
                tipos_str = ", ".join([t.__name__ for t in tipo_esperado])
                erros_validacao.append(f'Campo {campo} deve ser um dos tipos: {tipos_str}. Recebido: {type(valor_campo).__name__}')
        elif not isinstance(valor_campo, tipo_esperado):
            erros_validacao.append(f'Campo {campo} deve ser do tipo {tipo_esperado.__name__}. Recebido: {type(valor_campo).__name__}')

        # Validação de string não vazia para campos string
        if tipo_esperado == str and isinstance(valor_campo, str) and not valor_campo.strip():
            erros_validacao.append(f'Campo {campo} não pode ser vazio ou apenas espaços.')

    if erros_validacao:
        return jsonify({'erro': 'Erros de validação encontrados', 'detalhes': erros_validacao}), 400

    descricao = dados['descricao'].strip()
    tipo = dados['tipo'].strip().lower() # Normaliza para minúsculas
    data_transacao = dados['data'].strip()

    # Validação de conteúdo específico
    try:
        valor = float(dados['valor']) # Converte para float após checagem de tipo
        if valor <= 0:
            erros_validacao.append('Valor da transação deve ser positivo.')
    except (ValueError, TypeError): # TypeError se dados['valor'] não for numérico
        erros_validacao.append('Valor da transação deve ser um número válido.')


    if tipo not in ['receita', 'despesa']:
        erros_validacao.append("Tipo de transação deve ser 'receita' ou 'despesa'.")

    if not validate_date_format(data_transacao):
        erros_validacao.append("Formato de data inválido. Use YYYY-MM-DD.")

    if erros_validacao:
        return jsonify({'erro': 'Erros de validação encontrados', 'detalhes': erros_validacao}), 400

    db = get_db()
    try:
        cursor = db.execute( # db.execute retorna um cursor
            "INSERT INTO transacoes (usuario_id, descricao, valor, tipo, data) VALUES (?, ?, ?, ?, ?)",
            (usuario_id, descricao, valor, tipo, data_transacao)
        )
        transacao_id = cursor.lastrowid
        db.commit() # Commit da transação

        # Busca a transação recém-criada para retornar ao cliente
        nova_transacao_row = db.execute("SELECT id, usuario_id, descricao, valor, tipo, data FROM transacoes WHERE id = ?", (transacao_id,)).fetchone()

    except sqlite3.Error as e: # Mais específico para erros de DB
        # db.rollback() # Opcional, pois a conexão será fechada e a transação não commitada não persistirá
        current_app.logger.error(f"Erro de DB ao inserir transação para usuário ID {usuario_id}: {str(e)}")
        return jsonify({'erro': 'Erro ao salvar transação no banco de dados'}), 500
    # finally:
        # if conn: conn.close() # Removido

    if nova_transacao_row:
        return jsonify({
            'id': nova_transacao_row['id'],
            'usuario_id': nova_transacao_row['usuario_id'],
            'descricao': nova_transacao_row['descricao'],
            'valor': nova_transacao_row['valor'],
            'tipo': nova_transacao_row['tipo'],
            'data': nova_transacao_row['data']
        }), 201
    else:
        # Isso não deveria acontecer se lastrowid for válido e não houver commit/rollback inesperado
        current_app.logger.error(f"Falha ao buscar transação recém-criada ID {transacao_id} para usuário ID {usuario_id}")
        return jsonify({'erro': 'Falha ao recuperar transação após criação'}), 500


@transaction_bp.route('', methods=['GET'])
@token_required
def listar_transacoes_route():
    """Lista todas as transações financeiras do usuário autenticado."""
    try:
        usuario_id = get_usuario_id_from_token()
        if not usuario_id:
            return jsonify({'erro': 'Falha ao identificar usuário a partir do token.'}), 401
    except jwt.ExpiredSignatureError:
        current_app.logger.info("Token expirado ao tentar listar transações.")
        return jsonify({'erro': 'Token expirado.'}), 401
    except jwt.InvalidTokenError:
        current_app.logger.info("Token inválido ao tentar listar transações.")
        return jsonify({'erro': 'Token inválido.'}), 401
    except Exception as e:
        current_app.logger.exception(f"Erro ao obter usuario_id do token em GET /transacoes: {e}")
        return jsonify({'erro': 'Erro interno ao processar token.'}), 500

    db = get_db()
    try:
        # Ordena por data (mais recente primeiro) e depois por ID (para consistência se datas iguais)
        transacoes_rows = db.execute("SELECT id, descricao, valor, tipo, data FROM transacoes WHERE usuario_id = ? ORDER BY data DESC, id DESC", (usuario_id,)).fetchall()
    except sqlite3.Error as e:
        current_app.logger.error(f"Erro de DB ao listar transações para usuário ID {usuario_id}: {str(e)}")
        return jsonify({'erro': 'Erro ao buscar transações no banco de dados'}), 500
    # finally:
        # if conn: conn.close() # Removido

    transacoes_lista = []
    for row in transacoes_rows:
        transacoes_lista.append({
            'id': row['id'],
            'descricao': row['descricao'],
            'valor': row['valor'],
            'tipo': row['tipo'],
            'data': row['data']
        })

    return jsonify(transacoes_lista)
