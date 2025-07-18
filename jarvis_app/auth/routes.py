"""
Rotas para autenticação e gerenciamento de usuários.

Este Blueprint lida com registro, login, logout, e outras operações
relacionadas à autenticação e perfil de usuário.
"""
import json
import re
import sqlite3
import urllib.request
from datetime import datetime, timedelta

import jwt # Para geração e validação de JWT
from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from jarvis_app.auth.decorators import token_required
from jarvis_app.core.db_utils import get_db

auth_bp = Blueprint('auth', __name__)
# O prefixo '/auth' é definido em jarvis_app/__init__.py ao registrar o blueprint.

# Regexes movidas para cá, pois são específicas da lógica de autenticação/registro
CPF_RE = re.compile(r'^\d{11}$')
CNPJ_RE = re.compile(r'^\d{14}$')
PASSWORD_RE = re.compile(r'^(?=.*\d).{6,}$') # Exemplo: Pelo menos 6 chars, 1 dígito

# --- Constantes e Regexes Específicas do Módulo ---
CPF_RE = re.compile(r'^\d{11}$')
CNPJ_RE = re.compile(r'^\d{14}$')
PASSWORD_RE = re.compile(r'^(?=.*\d).{6,}$') # Pelo menos 6 chars, 1 dígito

# --- Funções Auxiliares ---

def _generate_token(usuario_sub: str) -> str:
    """
    Gera um token JWT para o usuário especificado.
    O token inclui o 'sub' (subject/usuário), 'iat' (issued at), e 'exp' (expiration).
    """
    payload = {
        'sub': usuario_sub,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(
            hours=current_app.config.get('JWT_EXPIRATION_HOURS', 1) # Default de 1 hora
        )
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')

def _create_infinity_charge(valor_centavos: int, metodo_pagamento: str, config: dict) -> dict:
    """
    Cria uma cobrança usando a API da Infinity Pay.
    Esta função é um exemplo e precisaria de tratamento de erro mais robusto
    e possivelmente logging mais detalhado em um ambiente de produção.
    Poderia ser movida para um módulo de integrações/pagamentos.
    """
    infinity_pay_token = config.get('INFINITY_PAY_TOKEN')
    infinity_pay_url = config.get('INFINITY_PAY_URL')
    infinity_pay_receiver = config.get('INFINITY_PAY_RECEIVER')

    if not all([infinity_pay_token, infinity_pay_url, infinity_pay_receiver]):
        current_app.logger.error("Configurações da Infinity Pay (token, URL ou receiver) estão incompletas.")
        return {'erro': 'Serviço de pagamento temporariamente indisponível. Contate o suporte.'}

    payload_dict = {
        'amount': valor_centavos,
        'payment_type': 'CREDIT_CARD' if metodo_pagamento == 'cartao' else 'PIX',
        'receiver': infinity_pay_receiver,
        'description': f'Pagamento Assinatura Jarviss - Plano {config.get("CURRENT_PLAN_NAME_FOR_PAYMENT", "")}', # Exemplo
        'statement_descriptor': 'JarvissApp' # O que aparece na fatura
    }
    payload_json = json.dumps(payload_dict).encode('utf-8')

    req = urllib.request.Request(infinity_pay_url, data=payload_json, method='POST')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Authorization', f'Bearer {infinity_pay_token}')

    try:
        with urllib.request.urlopen(req, timeout=15) as response: # Timeout aumentado para 15s
            response_content = response.read().decode('utf-8')
            response_data = json.loads(response_content)
            if response.status >= 400:
                 current_app.logger.error(f"Erro da API Infinity Pay {response.status}: {response_content}")
                 # Tenta extrair uma mensagem de erro mais amigável do corpo, se disponível
                 error_message = response_data.get('message', response_data.get('error', 'Erro desconhecido do gateway.'))
                 if isinstance(error_message, list): # Algumas APIs retornam lista de erros
                     error_message = "; ".join(error_message)
                 return {'erro': f"Gateway de pagamento: {error_message}"}
            return response_data
    except urllib.error.HTTPError as http_err:
        error_body = http_err.read().decode('utf-8', errors='ignore')
        current_app.logger.error(f"Exceção HTTPError na Infinity Pay: {http_err.code} - {error_body}")
        return {'erro': f"Erro HTTP ({http_err.code}) com o gateway de pagamento."}
    except urllib.error.URLError as url_err:
        current_app.logger.error(f"Exceção URLError na Infinity Pay: {url_err.reason}")
        return {'erro': f"Erro de conexão com o gateway de pagamento: {url_err.reason}."}
    except json.JSONDecodeError as json_err:
        current_app.logger.error(f"Erro ao decodificar resposta JSON da Infinity Pay: {json_err}")
        return {'erro': "Erro ao processar resposta do gateway de pagamento."}
    except Exception as e:
        current_app.logger.exception(f"Exceção genérica ao chamar Infinity Pay: {e}") # Usar .exception para logar stack trace
        return {'erro': "Erro inesperado no sistema de pagamento. Tente novamente mais tarde."}

# --- Rotas ---

@auth_bp.route('/register', methods=['POST'])
def register():
    """Registra um novo usuário na aplicação."""
    dados = request.json
    if not dados:
        return jsonify({'erro': 'Corpo da requisição JSON não pode ser vazio'}), 400

    # Validação de campos obrigatórios e tipos básicos
    campos_obrigatorios = {
        'nome': str, 'usuario': str, 'senha': str,
        # CPF ou CNPJ será validado abaixo, mas um deles deve estar presente
    }
    for campo, tipo_esperado in campos_obrigatorios.items():
        if campo not in dados:
            return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        if not isinstance(dados[campo], tipo_esperado):
            return jsonify({'erro': f'Campo {campo} deve ser do tipo {tipo_esperado.__name__}'}), 400
        if tipo_esperado == str and not dados[campo].strip():
            return jsonify({'erro': f'Campo {campo} não pode ser vazio ou apenas espaços'}), 400

    nome = dados['nome'].strip()
    usuario = dados['usuario'].strip()
    senha = dados['senha'] # Validação de força abaixo

    cpf = dados.get('cpf')
    cnpj = dados.get('cnpj')

    if cpf is not None and not isinstance(cpf, str):
        return jsonify({'erro': 'Campo cpf deve ser uma string'}), 400
    if cnpj is not None and not isinstance(cnpj, str):
        return jsonify({'erro': 'Campo cnpj deve ser uma string'}), 400

    cpf = cpf.strip() if cpf else None
    cnpj = cnpj.strip() if cnpj else None

    if not cpf and not cnpj:
        return jsonify({'erro': 'CPF ou CNPJ é obrigatório'}), 400
    if cpf and not CPF_RE.match(cpf):
        return jsonify({'erro': 'CPF inválido. Deve conter 11 dígitos.'}), 400
    if cnpj and not CNPJ_RE.match(cnpj):
        return jsonify({'erro': 'CNPJ inválido. Deve conter 14 dígitos.'}), 400

    if not PASSWORD_RE.match(senha):
        return jsonify({'erro': 'Senha fraca. Deve ter no mínimo 6 caracteres e incluir pelo menos um dígito.'}), 400

    plano = dados.get('plano', 'Gratuito') # Default para 'Gratuito'
    if not isinstance(plano, str):
        return jsonify({'erro': 'Campo plano deve ser uma string'}), 400
    if plano not in current_app.config['PLANS']:
        return jsonify({'erro': f"Plano '{plano}' inválido. Planos disponíveis: {', '.join(current_app.config['PLANS'])}"}), 400

    metodo_pagamento = dados.get('pagamento')
    pagamento_info_db = None

    if plano != 'Gratuito':
        if not metodo_pagamento:
            return jsonify({'erro': 'Campo pagamento é obrigatório para planos pagos'}), 400
        if not isinstance(metodo_pagamento, str):
            return jsonify({'erro': 'Campo pagamento deve ser uma string'}), 400
        if metodo_pagamento not in ('pix', 'cartao'):
            return jsonify({'erro': "Método de pagamento inválido. Aceitos: 'pix' ou 'cartao'"}), 400

        valor_plano_centavos = current_app.config['PLAN_PRICES'].get(plano)
        if valor_plano_centavos is None:
            current_app.logger.error(f"Preço não definido para o plano {plano}")
            return jsonify({'erro': 'Erro ao processar plano. Contate o suporte.'}), 500

        # Processar pagamento
        # Em um cenário real, isso seria mais complexo, possivelmente assíncrono.
        resp_pagamento = _create_infinity_charge(valor_plano_centavos, metodo_pagamento, current_app.config)
        if 'erro' in resp_pagamento:
            current_app.logger.error(f"Falha no pagamento para {usuario} no plano {plano}: {resp_pagamento['erro']}")
            return jsonify({'erro': f"Falha ao processar pagamento: {resp_pagamento['erro']}"}), 502 # 502 Bad Gateway

        # Guardar alguma referência do pagamento, se necessário
        pagamento_info_db = json.dumps({'metodo': metodo_pagamento, 'id_gateway': resp_pagamento.get('id'), 'status': resp_pagamento.get('status')})
        current_app.logger.info(f"Pagamento processado para {usuario}, plano {plano}: {pagamento_info_db}")


    senha_hash = generate_password_hash(senha)
    db = get_db() # Usa get_db()
    try:
        # db.execute pode não retornar cursor para INSERTs da mesma forma,
        # mas para INSERT não precisamos do cursor diretamente aqui.
        db.execute(
            'INSERT INTO usuarios (nome, usuario, senha, cpf, cnpj, plano, pagamento) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (nome, usuario, senha_hash, cpf, cnpj, plano, pagamento_info_db)
        )
        db.commit() # Commit da transação
    except sqlite3.IntegrityError:
        # db.rollback() # Rollback não é necessário explicitamente com SQLite se a transação falhar antes do commit
        # e a conexão for fechada/reaberta. Mas não faz mal se usado em um bloco try/except maior.
        # No entanto, como get_db() gerencia a conexão por request, o rollback implícito pode ocorrer.
        # Para ser explícito, um db.rollback() seria bom aqui se a conexão persistisse.
        # Dado que cada request tem sua g.db, a falha não afetará outros requests.
        current_app.logger.warning(f"Falha ao registrar usuário {usuario} devido à violação de integridade (ex: duplicado).")
        return jsonify({'erro': 'Usuário ou documento já cadastrado'}), 409 # Conflict
    except sqlite3.Error as e:
        current_app.logger.error(f"Erro de DB ao registrar usuário {usuario}: {e}")
        return jsonify({'erro': 'Erro interno ao registrar usuário'}), 500
    # finally:
        # conn.close() # Removido, será feito por teardown_appcontext

    current_app.logger.info(f"Usuário {usuario} registrado com sucesso no plano {plano}.")
    return jsonify({'mensagem': f'Usuário {usuario} cadastrado com sucesso no plano {plano}!'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    dados = request.json
    if not dados:
        return jsonify({'erro': 'Corpo da requisição JSON não pode ser vazio'}), 400

    usuario_login = dados.get('usuario')
    senha_login = dados.get('senha')

    if not usuario_login:
        return jsonify({'erro': 'Campo usuario é obrigatório'}), 400
    if not isinstance(usuario_login, str) or not usuario_login.strip():
        return jsonify({'erro': 'Campo usuario deve ser uma string não vazia'}), 400

    if not senha_login:
        return jsonify({'erro': 'Campo senha é obrigatório'}), 400
    if not isinstance(senha_login, str): # Senha pode ser só espaços, mas não nula
         return jsonify({'erro': 'Campo senha deve ser uma string'}), 400


    db = get_db()
    user_row = db.execute('SELECT id, usuario, senha, plano, inadimplente FROM usuarios WHERE usuario = ?', (usuario_login,)).fetchone()
    # conn.close() # Removido

    if user_row and check_password_hash(user_row['senha'], senha_login):
        if user_row['inadimplente']:
            current_app.logger.warning(f"Tentativa de login do usuário inadimplente: {usuario_login}")
            # Considerar se quer retornar um erro diferente ou o mesmo de credenciais inválidas
            return jsonify({'erro': 'Acesso bloqueado. Por favor, regularize sua assinatura.'}), 403 # Forbidden

        token = _generate_token(user_row['usuario'])
        current_app.logger.info(f"Login bem-sucedido para usuário: {usuario_login}, plano: {user_row['plano']}")
        return jsonify({
            'mensagem': f"Login bem-sucedido! Bem-vindo {user_row['usuario']}.",
            'token': token,
            'plano': user_row['plano']
        }), 200

    current_app.logger.warning(f"Falha no login para usuário: {usuario_login}")
    return jsonify({'erro': 'Usuário ou senha incorretos'}), 401


@auth_bp.route('/logout', methods=['POST'])
@token_required # Assegura que só usuários logados podem "deslogar"
def logout():
    # Em um sistema stateless com JWT, o logout do lado do servidor é mais complexo
    # (ex: blacklisting de tokens). Para este escopo, um simples ACK é suficiente.
    # O cliente deve destruir o token localmente.
    # Pode-se adicionar o JTI (JWT ID) a uma blacklist aqui se implementado.

    # Exemplo de como obter o 'sub' do token se necessário para logging do logout
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.split(' ', 1)[1]
        decoded_token = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
        usuario_sub = decoded_token.get('sub')
        current_app.logger.info(f"Usuário {usuario_sub} realizou logout.")
    except Exception as e:
        current_app.logger.warning(f"Erro ao decodificar token no logout (possivelmente já inválido): {e}")
        # Não falhar o logout por isso, apenas logar.

    return jsonify({'mensagem': 'Logout realizado com sucesso. Lembre-se de limpar o token no cliente.'}), 200

# Rotas de gerenciamento de plano e inadimplência (exemplos, podem precisar de mais lógica/segurança)
# Estas rotas deveriam provavelmente ser protegidas por um nível de admin ou lógica de permissão mais fina.
# Por agora, @token_required garante que apenas um usuário logado (qualquer um) pode chamar.

@auth_bp.route('/set_plan', methods=['POST'])
@token_required # TODO: Idealmente, proteger para admin ou usuário específico alterando seu próprio plano com validações.
def set_plan():
    dados = request.json
    if not dados:
        return jsonify({'erro': 'Corpo da requisição JSON não pode ser vazio'}), 400

    usuario_a_alterar = dados.get('usuario')
    novo_plano = dados.get('plano')

    if not usuario_a_alterar:
        return jsonify({'erro': 'Campo usuario é obrigatório'}), 400
    if not isinstance(usuario_a_alterar, str) or not usuario_a_alterar.strip():
        return jsonify({'erro': 'Campo usuario deve ser uma string não vazia'}), 400

    if not novo_plano:
        return jsonify({'erro': 'Campo plano é obrigatório'}), 400
    if not isinstance(novo_plano, str):
        return jsonify({'erro': 'Campo plano deve ser uma string'}), 400
    if novo_plano not in current_app.config['PLANS']:
        return jsonify({'erro': f"Plano '{novo_plano}' inválido. Planos disponíveis: {', '.join(current_app.config['PLANS'])}"}), 400

    # TODO: Adicionar lógica de permissão: quem pode alterar o plano de quem?
    # Por agora, qualquer usuário autenticado pode alterar o plano de qualquer outro.

    db = get_db()
    try:
        cursor = db.execute('UPDATE usuarios SET plano = ? WHERE usuario = ?', (novo_plano, usuario_a_alterar))
        db.commit()
        if cursor.rowcount == 0: # rowcount ainda é acessível a partir do cursor retornado por execute
            return jsonify({'erro': f'Usuário {usuario_a_alterar} não encontrado'}), 404
    except sqlite3.Error as e:
        # db.rollback() # Considerar se necessário; commit falharia de qualquer forma
        current_app.logger.error(f"Erro de DB ao alterar plano para {usuario_a_alterar}: {e}")
        return jsonify({'erro': 'Erro interno ao alterar plano'}), 500
    # finally:
        # conn.close() # Removido

    current_app.logger.info(f"Plano do usuário {usuario_a_alterar} alterado para {novo_plano}.")
    return jsonify({'mensagem': f'Plano de {usuario_a_alterar} atualizado para {novo_plano}'})


@auth_bp.route('/set_inadimplente', methods=['POST'])
@token_required # TODO: Idealmente, proteger para admin.
def set_inadimplente():
    dados = request.json
    if not dados:
        return jsonify({'erro': 'Corpo da requisição JSON não pode ser vazio'}), 400

    usuario_alvo = dados.get('usuario')
    status_inadimplente = dados.get('inadimplente')

    if not usuario_alvo:
        return jsonify({'erro': 'Campo usuario é obrigatório'}), 400
    if not isinstance(usuario_alvo, str) or not usuario_alvo.strip():
        return jsonify({'erro': 'Campo usuario deve ser uma string não vazia'}), 400

    if status_inadimplente is None:
        return jsonify({'erro': 'Campo inadimplente é obrigatório'}), 400
    if not isinstance(status_inadimplente, bool):
        return jsonify({'erro': 'Campo inadimplente deve ser um booleano (true/false)'}), 400

    valor_db = 1 if status_inadimplente else 0

    db = get_db() # Usa get_db()
    try:
        cursor = db.execute('UPDATE usuarios SET inadimplente = ? WHERE usuario = ?', (valor_db, usuario_alvo))
        db.commit()
        if cursor.rowcount == 0:
            return jsonify({'erro': f'Usuário {usuario_alvo} não encontrado'}), 404
    except sqlite3.Error as e:
        # db.rollback()
        current_app.logger.error(f"Erro de DB ao definir inadimplência para {usuario_alvo}: {e}")
        return jsonify({'erro': 'Erro interno ao definir inadimplência'}), 500
    # finally:
        # conn.close() # Removido

    status_msg = "marcado como inadimplente" if status_inadimplente else "marcado como adimplente"
    current_app.logger.info(f"Usuário {usuario_alvo} {status_msg}.")
    return jsonify({'mensagem': f'Status de inadimplência de {usuario_alvo} atualizado.'})
