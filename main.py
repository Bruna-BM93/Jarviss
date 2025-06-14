idfwsp-codex/criar-app-do-zero
from flask import Flask, request, jsonify, render_template

h109du-codex/criar-app-do-zero
from flask import Flask, request, jsonify, render_template

from flask import Flask, request, jsonify
main
main
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import urllib.request
idfwsp-codex/criar-app-do-zero
import re
import logging
from datetime import datetime, timedelta, date # Adicionado date para validação de data
import jwt
import openai # Adicionado para IA

main

DB_PATH = 'jarvis.db'

PLANS = ['Gratuito', 'Plus', 'Premium']
FEATURES_BY_PLAN = {
    'Gratuito': {'basica', 'ia_chat'},
    'Plus': {'basica', 'plus', 'ia_chat', 'ia_interpretacao_notificacao'}, # ia_interpretacao_notificacao adicionada
    'Premium': {'basica', 'plus', 'premium', 'ia_chat', 'ia_interpretacao_notificacao'}, # ia_interpretacao_notificacao adicionada
}

# Configurações da Infinity Pay
INFINITY_PAY_TOKEN = os.environ.get('INFINITY_PAY_TOKEN')
INFINITY_PAY_URL = 'https://api.infinitypay.com.br/v2/charges'
# Dados da conta que recebe os pagamentos
INFINITY_PAY_RECEIVER = {
    'tag': '$nalenhacomferreira',
    'name': 'Jarviss',
    'document': '46102173000111',
    'bank_code': '542',
    'agency': '001',
    'account': '989248-7',
    'bank_name': 'Cloudwalk instituicao de pagamento'
}
PLAN_PRICES = {
    'Plus': 1500,     # em centavos (R$ 15,00)
    'Premium': 3000,  # em centavos (R$ 30,00)
}
idfwsp-codex/criar-app-do-zero

CPF_RE = re.compile(r'^\d{11}$')
CNPJ_RE = re.compile(r'^\d{14}$')
PASSWORD_RE = re.compile(r'^(?=.*\d).{6,}$')

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get('JWT_SECRET', 'CHANGE_ME')



app = Flask(__name__)

main

def create_infinity_charge(valor_centavos: int, metodo: str):
    """Envia uma requisicao de cobranca para a Infinity Pay."""
    if not INFINITY_PAY_TOKEN:
        return {'erro': 'Token da Infinity Pay nao configurado'}

    payload = json.dumps({
        'amount': valor_centavos,
        'payment_type': 'CREDIT_CARD' if metodo == 'cartao' else 'PIX',
        'receiver': INFINITY_PAY_RECEIVER,
        'description': 'Pagamento Jarviss',
        'statement_descriptor': 'Jarviss'
    }).encode()

    req = urllib.request.Request(INFINITY_PAY_URL, data=payload)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {INFINITY_PAY_TOKEN}')
    try:
        with urllib.request.urlopen(req) as resp:
            return json.load(resp)
    except Exception as exc:
        return {'erro': str(exc)}


idfwsp-codex/criar-app-do-zero
def generate_token(usuario: str) -> str:
    payload = {
        'sub': usuario,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def token_required(f):
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'erro': 'Token ausente'}), 401
        token = auth.split(' ', 1)[1]
        try:
            jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except Exception:
            return jsonify({'erro': 'Token invalido'}), 401
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper



main
def init_db():
    """Create database tables if they do not exist."""
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS usuarios ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT," \
        "nome TEXT NOT NULL," \
        "usuario TEXT NOT NULL UNIQUE," \
        "senha TEXT NOT NULL," \
        "cpf TEXT," \
        "cnpj TEXT," \
        "plano TEXT NOT NULL DEFAULT 'Gratuito'," \
        "pagamento TEXT," \
        "inadimplente INTEGER NOT NULL DEFAULT 0"
        ")"
    )
    # adjust columns for older databases
    for coluna, tipo in (('cpf', 'TEXT'), ('cnpj', 'TEXT'), ('pagamento', 'TEXT')):
        try:
            cur.execute(f"ALTER TABLE usuarios ADD COLUMN {coluna} {tipo}")
        except sqlite3.OperationalError:
            pass

    # Criação da tabela transacoes
    cur.execute(
        "CREATE TABLE IF NOT EXISTS transacoes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "usuario_id INTEGER NOT NULL,"
        "descricao TEXT NOT NULL,"
        "valor REAL NOT NULL,"
        "tipo TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),"
        "data TEXT NOT NULL,"
        "FOREIGN KEY (usuario_id) REFERENCES usuarios (id)"
        ")"
    )
    con.commit()
    con.close()


@app.route('/')
def index():
    return jsonify({"mensagem": "Bem-vindo ao Jarviss API"})


idfwsp-codex/criar-app-do-zero

h109du-codex/criar-app-do-zero
main
@app.route("/jarviss")
def jarviss_page():
    return render_template("jarviss.html")

idfwsp-codex/criar-app-do-zero


main
main
@app.route('/register', methods=['POST'])
def register():
    dados = request.json or {}
    nome = dados.get('nome')
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    cpf = dados.get('cpf')
    cnpj = dados.get('cnpj')
    plano = dados.get('plano', 'Gratuito')
    pagamento = dados.get('pagamento') if plano != 'Gratuito' else None
    pagamento_info = None

    if not nome or not usuario or not senha:
        return jsonify({'erro': 'Dados incompletos'}), 400
    if not cpf and not cnpj:
        return jsonify({'erro': 'CPF ou CNPJ obrigatorio'}), 400
idfwsp-codex/criar-app-do-zero
    if cpf and not CPF_RE.match(cpf):
        return jsonify({'erro': 'CPF invalido'}), 400
    if cnpj and not CNPJ_RE.match(cnpj):
        return jsonify({'erro': 'CNPJ invalido'}), 400
    if not PASSWORD_RE.match(senha):
        return jsonify({'erro': 'Senha fraca'}), 400

main
    if plano not in PLANS:
        return jsonify({'erro': 'Plano invalido'}), 400
    if plano != 'Gratuito' and pagamento not in ('pix', 'cartao'):
        return jsonify({'erro': 'Metodo de pagamento invalido'}), 400

    if plano != 'Gratuito':
        valor = PLAN_PRICES.get(plano, 0)
        resp = create_infinity_charge(valor, pagamento)
        if 'erro' in resp:
idfwsp-codex/criar-app-do-zero
            logger.error('Falha Infinity Pay: %s', resp['erro'])
            return jsonify({'erro': 'Falha ao processar pagamento'}), 502

            return jsonify({'erro': 'Falha ao processar pagamento', 'detalhe': resp['erro']}), 502
main
        pagamento_info = json.dumps({'metodo': pagamento, 'id': resp.get('id')})

    senha_hash = generate_password_hash(senha)
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute(
            'INSERT INTO usuarios (nome, usuario, senha, cpf, cnpj, plano, pagamento) '
            'VALUES (?, ?, ?, ?, ?, ?, ?)',
            (nome, usuario, senha_hash, cpf, cnpj, plano, pagamento_info)
        )
        con.commit()
    except sqlite3.IntegrityError:
        return jsonify({'erro': 'Usuário já existe'}), 400
    finally:
        con.close()
    return jsonify({'mensagem': 'Usuário cadastrado com sucesso'})


@app.route('/login', methods=['POST'])
def login():
    dados = request.json or {}
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    if not usuario or not senha:
        return jsonify({'erro': 'Dados incompletos'}), 400

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT senha, plano, inadimplente FROM usuarios WHERE usuario = ?', (usuario,))
    row = cur.fetchone()
    con.close()

    if row and check_password_hash(row[0], senha):
        plano = row[1]
        inad = bool(row[2])
idfwsp-codex/criar-app-do-zero
        token = generate_token(usuario)
        msg = f'Bem-vindo {usuario}! Plano: {plano}'
        if inad:
            msg += ' (inadimplente)'
        return jsonify({'mensagem': msg, 'token': token}), 200

        msg = f'Bem-vindo {usuario}! Plano: {plano}'
        if inad:
            msg += ' (inadimplente)'
        return jsonify({'mensagem': msg}), 200
main
    return jsonify({'erro': 'Usuário ou senha incorretos'}), 401


@app.route('/logout', methods=['POST'])
@token_required
def logout():
    # Não há sessão real neste exemplo, mas o endpoint é mantido
    return jsonify({'mensagem': 'Logout realizado com sucesso'})
idfwsp-codex/criar-app-do-zero


@app.route('/set_plan', methods=['POST'])
@token_required
def set_plan():
    dados = request.json or {}
    usuario = dados.get('usuario')
    plano = dados.get('plano')
    if not usuario or plano not in PLANS:
        return jsonify({'erro': 'Dados invalidos'}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('UPDATE usuarios SET plano = ? WHERE usuario = ?', (plano, usuario))
    con.commit()
    con.close()
    return jsonify({'mensagem': 'Plano atualizado'})


@app.route('/set_inadimplente', methods=['POST'])
@token_required
def set_inadimplente():
    dados = request.json or {}
    usuario = dados.get('usuario')
    inad = dados.get('inadimplente')
    if usuario is None or inad is None:
        return jsonify({'erro': 'Dados invalidos'}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('UPDATE usuarios SET inadimplente = ? WHERE usuario = ?', (1 if inad else 0, usuario))
    con.commit()
    con.close()
    return jsonify({'mensagem': 'Status de inadimplencia atualizado'})


@app.route('/feature/<nome>', methods=['GET'])
@token_required



@app.route('/set_plan', methods=['POST'])
def set_plan():
    dados = request.json or {}
    usuario = dados.get('usuario')
    plano = dados.get('plano')
    if not usuario or plano not in PLANS:
        return jsonify({'erro': 'Dados invalidos'}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('UPDATE usuarios SET plano = ? WHERE usuario = ?', (plano, usuario))
    con.commit()
    con.close()
    return jsonify({'mensagem': 'Plano atualizado'})


@app.route('/set_inadimplente', methods=['POST'])
def set_inadimplente():
    dados = request.json or {}
    usuario = dados.get('usuario')
    inad = dados.get('inadimplente')
    if usuario is None or inad is None:
        return jsonify({'erro': 'Dados invalidos'}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('UPDATE usuarios SET inadimplente = ? WHERE usuario = ?', (1 if inad else 0, usuario))
    con.commit()
    con.close()
    return jsonify({'mensagem': 'Status de inadimplencia atualizado'})


@app.route('/feature/<nome>', methods=['GET'])
main
def feature(nome):
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'erro': 'Usuario nao informado'}), 400
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT plano, inadimplente FROM usuarios WHERE usuario = ?', (usuario,))
    row = cur.fetchone()
    con.close()
    if not row:
        return jsonify({'erro': 'Usuario nao encontrado'}), 404
    plano, inad = row
    if inad:
        return jsonify({'erro': 'Acesso bloqueado por inadimplencia'}), 403
    if nome not in FEATURES_BY_PLAN.get(plano, set()):
        return jsonify({'erro': 'Funcionalidade nao disponivel para seu plano'}), 403
    return jsonify({'mensagem': f'Funcionalidade {nome} liberada'}), 200


@app.route('/ia/perguntar', methods=['POST'])
@token_required
def ia_perguntar():
    # Obter o nome do usuário a partir do token JWT
    # Em um cenário ideal, o @token_required injetaria isso em 'g.user' ou similar.
    # Por agora, vamos decodificar o token novamente para obter o 'sub'.
    token = request.headers.get('Authorization', '').split(' ', 1)[1]
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        usuario = decoded_token['sub']
    except jwt.ExpiredSignatureError:
        logger.error("Token expirado ao tentar acessar /ia/perguntar")
        return jsonify({'erro': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        logger.error("Token inválido ao tentar acessar /ia/perguntar")
        return jsonify({'erro': 'Token inválido'}), 401

    pergunta = request.json.get('pergunta')
    if not pergunta:
        return jsonify({'erro': 'Pergunta não fornecida'}), 400

    # Simulação da Verificação do Plano do Usuário
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute('SELECT plano FROM usuarios WHERE usuario = ?', (usuario,))
        user_row = cur.fetchone()
    except Exception as e:
        logger.error(f"Erro ao conectar ao banco de dados para verificar plano: {str(e)}")
        return jsonify({'erro': 'Erro interno do servidor ao verificar plano'}), 500
    finally:
        if 'con' in locals() and con:
            con.close()

    if not user_row:
        logger.error(f"Usuário {usuario} não encontrado no banco de dados durante verificação de plano para /ia/perguntar.")
        return jsonify({'erro': 'Usuário não encontrado'}), 404

    plano_usuario = user_row[0]
    if 'ia_chat' not in FEATURES_BY_PLAN.get(plano_usuario, set()):
        logger.warning(f"Usuário {usuario} no plano {plano_usuario} tentou acessar 'ia_chat' sem permissão.")
        return jsonify({'erro': 'Funcionalidade não disponível para seu plano'}), 403

    # Obter chave da API OpenAI
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY não configurada no servidor.")
        return jsonify({'erro': 'Chave da API OpenAI não configurada no servidor'}), 500
    openai.api_key = openai_api_key

    try:
        logger.info(f"Usuário {usuario} perguntou: {pergunta}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente empresarial útil."},
                {"role": "user", "content": pergunta}
            ]
        )
        resposta_ia = response.choices[0].message['content'].strip()
        logger.info(f"Resposta da IA para {usuario}: {resposta_ia}")
        return jsonify({'resposta': resposta_ia})
    except openai.error.AuthenticationError as e:
        logger.error(f"Erro de autenticação com a API OpenAI: {str(e)}")
        return jsonify({'erro': f'Erro de autenticação com a API OpenAI: {str(e)}'}), 502
    except openai.error.OpenAIError as e:
        logger.error(f"Erro ao contatar IA (OpenAI): {str(e)}")
        return jsonify({'erro': f'Erro ao contatar IA: {str(e)}'}), 502
    except Exception as e:
        logger.error(f"Erro inesperado na chamada da API OpenAI: {str(e)}")
        return jsonify({'erro': f'Erro inesperado ao processar sua pergunta: {str(e)}'}), 500


# Função auxiliar para obter usuario_id do token
def _get_usuario_id_from_token():
    token = request.headers.get('Authorization', '').split(' ', 1)[1]
    decoded_token = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    usuario_jwt = decoded_token['sub']

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario_jwt,))
    user_row = cur.fetchone()
    con.close()

    if not user_row:
        return None
    return user_row[0]

def _validate_date_format(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

@app.route('/transacoes', methods=['POST'])
@token_required
def adicionar_transacao():
    try:
        usuario_id = _get_usuario_id_from_token()
        if not usuario_id:
            return jsonify({'erro': 'Usuário do token não encontrado no banco de dados'}), 404
    except jwt.ExpiredSignatureError:
        logger.error("Token expirado ao tentar adicionar transação")
        return jsonify({'erro': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        logger.error("Token inválido ao tentar adicionar transação")
        return jsonify({'erro': 'Token inválido'}), 401
    except Exception as e:
        logger.error(f"Erro ao obter usuario_id do token: {str(e)}")
        return jsonify({'erro': 'Erro ao processar token'}), 500

    dados = request.json
    descricao = dados.get('descricao')
    valor_str = dados.get('valor')
    tipo = dados.get('tipo')
    data_transacao = dados.get('data')

    if not all([descricao, valor_str is not None, tipo, data_transacao]):
        return jsonify({'erro': 'Dados incompletos (descrição, valor, tipo, data são obrigatórios)'}), 400

    try:
        valor = float(valor_str)
        if valor <= 0:
            return jsonify({'erro': 'Valor deve ser positivo'}), 400
    except ValueError:
        return jsonify({'erro': 'Valor inválido, deve ser um número'}), 400

    if tipo not in ['receita', 'despesa']:
        return jsonify({'erro': "Tipo de transação inválido (deve ser 'receita' ou 'despesa')"}), 400

    if not _validate_date_format(data_transacao):
        return jsonify({'erro': "Formato de data inválido (deve ser YYYY-MM-DD)"}), 400

    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute(
            "INSERT INTO transacoes (usuario_id, descricao, valor, tipo, data) VALUES (?, ?, ?, ?, ?)",
            (usuario_id, descricao, valor, tipo, data_transacao)
        )
        transacao_id = cur.lastrowid
        con.commit()

        cur.execute("SELECT id, usuario_id, descricao, valor, tipo, data FROM transacoes WHERE id = ?", (transacao_id,))
        nova_transacao = cur.fetchone()

    except sqlite3.Error as e:
        logger.error(f"Erro ao inserir transação no banco de dados: {str(e)}")
        return jsonify({'erro': 'Erro ao salvar transação'}), 500
    finally:
        if con:
            con.close()

    return jsonify({
        'id': nova_transacao[0],
        'usuario_id': nova_transacao[1],
        'descricao': nova_transacao[2],
        'valor': nova_transacao[3],
        'tipo': nova_transacao[4],
        'data': nova_transacao[5]
    }), 201


@app.route('/transacoes', methods=['GET'])
@token_required
def listar_transacoes():
    try:
        usuario_id = _get_usuario_id_from_token()
        if not usuario_id:
            return jsonify({'erro': 'Usuário do token não encontrado no banco de dados'}), 404
    except jwt.ExpiredSignatureError:
        logger.error("Token expirado ao tentar listar transações")
        return jsonify({'erro': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        logger.error("Token inválido ao tentar listar transações")
        return jsonify({'erro': 'Token inválido'}), 401
    except Exception as e:
        logger.error(f"Erro ao obter usuario_id do token: {str(e)}")
        return jsonify({'erro': 'Erro ao processar token'}), 500

    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id, descricao, valor, tipo, data FROM transacoes WHERE usuario_id = ? ORDER BY data DESC", (usuario_id,))
        transacoes_rows = cur.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar transações no banco de dados: {str(e)}")
        return jsonify({'erro': 'Erro ao buscar transações'}), 500
    finally:
        if con:
            con.close()

    transacoes_lista = []
    for row in transacoes_rows:
        transacoes_lista.append({
            'id': row[0],
            'descricao': row[1],
            'valor': row[2],
            'tipo': row[3],
            'data': row[4]
        })

    return jsonify(transacoes_lista)


@app.route('/ia/interpretar_notificacao', methods=['POST'])
@token_required
def ia_interpretar_notificacao():
    usuario_id = None
    usuario_sub = None # Para logging, caso _get_usuario_id_from_token falhe em obter o id mas não o sub
    try:
        # Decodifica o token para obter o nome de usuário ('sub') e o ID do usuário
        token = request.headers.get('Authorization', '').split(' ', 1)[1]
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        usuario_sub = decoded_token['sub'] # Nome de usuário do token

        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        cur.execute("SELECT id, plano FROM usuarios WHERE usuario = ?", (usuario_sub,))
        user_db_row = cur.fetchone()

        if not user_db_row:
            logger.error(f"Usuário '{usuario_sub}' do token não encontrado no banco de dados.")
            return jsonify({'erro': 'Usuário do token não encontrado'}), 404

        usuario_id = user_db_row[0]
        plano_usuario = user_db_row[1]
        con.close()

    except jwt.ExpiredSignatureError:
        logger.error("Token expirado ao tentar acessar /ia/interpretar_notificacao")
        return jsonify({'erro': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        logger.error("Token inválido ao tentar acessar /ia/interpretar_notificacao")
        return jsonify({'erro': 'Token inválido'}), 401
    except sqlite3.Error as e:
        logger.error(f"Erro de banco de dados ao buscar usuário '{usuario_sub}': {str(e)}")
        return jsonify({'erro': 'Erro interno ao verificar permissões'}), 500
    except Exception as e:
        logger.error(f"Erro inesperado ao processar token/usuário para /ia/interpretar_notificacao: {str(e)}")
        return jsonify({'erro': 'Erro ao processar token ou permissões'}), 500

    # Verificação de feature do plano
    if 'ia_interpretacao_notificacao' not in FEATURES_BY_PLAN.get(plano_usuario, set()):
        logger.warning(f"Usuário {usuario_sub} (ID: {usuario_id}) no plano {plano_usuario} tentou acessar 'ia_interpretacao_notificacao' sem permissão.")
        return jsonify({'erro': 'Funcionalidade não disponível para seu plano'}), 403

    texto_notificacao = request.json.get('texto_notificacao')
    if not texto_notificacao:
        logger.warning(f"Nenhum texto_notificacao fornecido por {usuario_sub} (ID: {usuario_id}).")
        return jsonify({'erro': 'texto_notificacao não fornecido'}), 400

    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY não configurada no servidor.")
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
        logger.info(f"Usuário {usuario_sub} (ID: {usuario_id}) enviou notificação para interpretação: {texto_notificacao}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", # ou "gpt-4" se disponível e desejado
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": texto_notificacao}
            ],
            temperature=0.2, # Baixa temperatura para respostas mais determinísticas e focadas no formato JSON
        )

        ia_response_content = response.choices[0].message['content'].strip()
        logger.info(f"Resposta bruta da IA para {usuario_sub} (ID: {usuario_id}): {ia_response_content}")

        # Tentar extrair o JSON da resposta, mesmo que haja texto adicional (comum com alguns modelos)
        json_match = re.search(r'\{.*\}', ia_response_content, re.DOTALL)
        if not json_match:
            logger.error(f"Nenhum JSON encontrado na resposta da IA para {usuario_sub} (ID: {usuario_id}): {ia_response_content}")
            return jsonify({'erro': 'Falha ao interpretar a resposta da IA: JSON não encontrado'}), 502

        json_str = json_match.group(0)

        try:
            interpreted_data = json.loads(json_str)
        except json.JSONDecodeError as json_err:
            logger.error(f"Falha ao decodificar JSON da IA para {usuario_sub} (ID: {usuario_id}): {json_err}. JSON String: {json_str}")
            return jsonify({'erro': f'Falha ao decodificar JSON da IA: {json_err}'}), 502

        # Validação básica dos campos esperados
        if not all(key in interpreted_data for key in ['tipo', 'valor', 'descricao_sugerida']):
            logger.error(f"Resposta da IA não contém todos os campos esperados (tipo, valor, descricao_sugerida) para {usuario_sub} (ID: {usuario_id}). Recebido: {interpreted_data}")
            return jsonify({'erro': 'Resposta da IA incompleta'}), 502

        # Validação adicional do tipo e valor
        if interpreted_data.get('tipo') not in ['receita', 'despesa'] and interpreted_data.get('tipo') is not None:
            logger.warning(f"Tipo inválido '{interpreted_data.get('tipo')}' retornado pela IA para {usuario_sub} (ID: {usuario_id}).")
            # Poderia retornar erro ou tentar corrigir/assumir um padrão. Por ora, aceita se for null.

        if not isinstance(interpreted_data.get('valor'), (int, float)) and interpreted_data.get('valor') is not None:
            logger.warning(f"Valor não numérico '{interpreted_data.get('valor')}' retornado pela IA para {usuario_sub} (ID: {usuario_id}).")
            # Poderia tentar converter ou retornar erro. Por ora, aceita se for null.


        logger.info(f"Dados interpretados para {usuario_sub} (ID: {usuario_id}): {interpreted_data}")
        return jsonify(interpreted_data)

    except openai.error.AuthenticationError as e:
        logger.error(f"Erro de autenticação com a API OpenAI para {usuario_sub} (ID: {usuario_id}): {str(e)}")
        return jsonify({'erro': f'Erro de autenticação com a API OpenAI: {str(e)}'}), 502
    except openai.error.OpenAIError as e:
        logger.error(f"Erro ao contatar IA (OpenAI) para {usuario_sub} (ID: {usuario_id}): {str(e)}")
        return jsonify({'erro': f'Erro ao contatar IA: {str(e)}'}), 502
    except Exception as e:
        logger.error(f"Erro inesperado na interpretação de notificação para {usuario_sub} (ID: {usuario_id}): {str(e)}")
        return jsonify({'erro': f'Erro inesperado ao processar sua notificação: {str(e)}'}), 500


if __name__ == '__main__':
    init_db()
idfwsp-codex/criar-app-do-zero
    logger.info('Iniciando Jarviss API na porta 5000')

main
    app.run(debug=True, host='0.0.0.0')
