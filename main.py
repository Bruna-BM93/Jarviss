from flask import Flask, request, jsonify
import psycopg2
import psycopg2.errors
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import urllib.request

# Database connection parameters from environment variables
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'jarvisdb')
DB_USER = os.environ.get('DB_USER', 'jarvisuser')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'jarvispass')
DB_PORT = os.environ.get('DB_PORT', '5432')

PLANS = ['Gratuito', 'Plus', 'Premium']
FEATURES_BY_PLAN = {
    'Gratuito': {'basica'},
    'Plus': {'basica', 'plus'},
    'Premium': {'basica', 'plus', 'premium'},
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

app = Flask(__name__)

def get_db_connection():
    """Establishes and returns a psycopg2 connection and cursor."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn, conn.cursor()
    except (Exception, psycopg2.Error) as error:
        app.logger.error(f"Error while connecting to PostgreSQL: {error}")
        # If connection fails, we might want to raise an error or handle it
        # For now, let it propagate to be caught by endpoint error handlers
        # or return None, None and check in calling functions.
        # Returning None, None for now, callers must check.
        if conn: # If connection object exists but cursor creation failed or other error
            conn.close()
        return None, None


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
        # It's better to log this error and return a generic message
        app.logger.error(f"Infinity Pay API error: {exc}")
        return {'erro': 'Falha ao comunicar com o processador de pagamento.'}


def init_db():
    """Create database tables if they do not exist."""
    conn, cur = None, None
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            app.logger.error("Failed to get DB connection in init_db.")
            return

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome TEXT NOT NULL,
                usuario TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL,
                cpf TEXT,
                cnpj TEXT,
                plano TEXT NOT NULL DEFAULT 'Gratuito',
                pagamento TEXT,
                inadimplente INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()
        app.logger.info("Database initialized successfully.")
    except (Exception, psycopg2.Error) as error:
        app.logger.error(f"Error while initializing PostgreSQL table: {error}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/')
def index():
    return jsonify({"mensagem": "Bem-vindo ao Jarviss API"})


@app.route('/register', methods=['POST'])
def register():
    dados = request.json or {}
    nome = dados.get('nome')
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    cpf = dados.get('cpf')
    cnpj = dados.get('cnpj')
    plano = dados.get('plano', 'Gratuito')
    pagamento_method = dados.get('pagamento') if plano != 'Gratuito' else None # Renamed to avoid conflict
    pagamento_info = None

    if not nome or not usuario or not senha:
        return jsonify({'erro': 'Dados incompletos'}), 400
    if not cpf and not cnpj: # Basic validation, consider more specific format checks
        return jsonify({'erro': 'CPF ou CNPJ obrigatorio'}), 400
    if plano not in PLANS:
        return jsonify({'erro': 'Plano invalido'}), 400
    if plano != 'Gratuito' and pagamento_method not in ('pix', 'cartao'):
        return jsonify({'erro': 'Metodo de pagamento invalido'}), 400

    if plano != 'Gratuito':
        valor = PLAN_PRICES.get(plano, 0)
        if valor == 0 :
             return jsonify({'erro': 'Valor do plano inválido ou não encontrado.'}), 400
        resp = create_infinity_charge(valor, pagamento_method)
        if 'erro' in resp:
            # Log detail internally, return generic error to user
            app.logger.error(f"Payment processing error for {usuario}: {resp.get('detalhe', resp['erro'])}")
            return jsonify({'erro': 'Falha ao processar pagamento'}), 502
        pagamento_info = json.dumps({'metodo': pagamento_method, 'id': resp.get('id')})

    senha_hash = generate_password_hash(senha)

    conn, cur = None, None
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            return jsonify({'erro': 'Erro de conexão com o banco de dados'}), 500

        cur.execute(
            'INSERT INTO usuarios (nome, usuario, senha, cpf, cnpj, plano, pagamento) '
            'VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (nome, usuario, senha_hash, cpf, cnpj, plano, pagamento_info)
        )
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        return jsonify({'erro': 'Usuário já existe'}), 400
    except (Exception, psycopg2.Error) as error:
        app.logger.error(f"Database error during registration for {usuario}: {error}")
        return jsonify({'erro': 'Erro ao registrar usuário'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return jsonify({'mensagem': 'Usuário cadastrado com sucesso'})


@app.route('/login', methods=['POST'])
def login():
    dados = request.json or {}
    usuario_param = dados.get('usuario') # Renamed to avoid conflict
    senha = dados.get('senha')
    if not usuario_param or not senha:
        return jsonify({'erro': 'Dados incompletos'}), 400

    conn, cur = None, None
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            return jsonify({'erro': 'Erro de conexão com o banco de dados'}), 500

        cur.execute('SELECT senha, plano, inadimplente, nome FROM usuarios WHERE usuario = %s', (usuario_param,))
        row = cur.fetchone()

        if row and check_password_hash(row[0], senha):
            plano = row[1]
            inad = bool(row[2])
            # nome_usuario = row[3] # Assuming 'nome' is the user's name from DB
            # msg = f'Bem-vindo {nome_usuario}! Plano: {plano}'
            msg = f'Bem-vindo {usuario_param}! Plano: {plano}' # Using login username for now
            if inad:
                msg += ' (inadimplente)'
            return jsonify({'mensagem': msg}), 200
        return jsonify({'erro': 'Usuário ou senha incorretos'}), 401
    except (Exception, psycopg2.Error) as error:
        app.logger.error(f"Database error during login for {usuario_param}: {error}")
        return jsonify({'erro': 'Erro ao tentar fazer login'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


@app.route('/logout', methods=['POST'])
def logout():
    # For stateless APIs (like one using JWT), logout is typically handled client-side
    # by deleting the token. This endpoint can remain as a no-op or be removed.
    return jsonify({'mensagem': 'Logout realizado com sucesso'})


@app.route('/set_plan', methods=['POST'])
def set_plan():
    dados = request.json or {}
    usuario = dados.get('usuario')
    plano = dados.get('plano')
    if not usuario or plano not in PLANS:
        return jsonify({'erro': 'Dados invalidos'}), 400

    conn, cur = None, None
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            return jsonify({'erro': 'Erro de conexão com o banco de dados'}), 500

        cur.execute('UPDATE usuarios SET plano = %s WHERE usuario = %s', (plano, usuario))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
    except (Exception, psycopg2.Error) as error:
        app.logger.error(f"Database error during set_plan for {usuario}: {error}")
        return jsonify({'erro': 'Erro ao atualizar plano'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return jsonify({'mensagem': 'Plano atualizado'})


@app.route('/set_inadimplente', methods=['POST'])
def set_inadimplente():
    dados = request.json or {}
    usuario = dados.get('usuario')
    inad_status = dados.get('inadimplente') # Renamed
    if usuario is None or inad_status is None: # Explicitly check for None
        return jsonify({'erro': 'Dados invalidos'}), 400

    conn, cur = None, None
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            return jsonify({'erro': 'Erro de conexão com o banco de dados'}), 500

        # Ensure inad_status is boolean then convert to 0 or 1
        db_inad_val = 1 if bool(inad_status) else 0
        cur.execute('UPDATE usuarios SET inadimplente = %s WHERE usuario = %s', (db_inad_val, usuario))
        conn.commit()
        if cur.rowcount == 0:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
    except (Exception, psycopg2.Error) as error:
        app.logger.error(f"Database error during set_inadimplente for {usuario}: {error}")
        return jsonify({'erro': 'Erro ao atualizar status de inadimplencia'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return jsonify({'mensagem': 'Status de inadimplencia atualizado'})


@app.route('/feature/<nome_feature>', methods=['GET']) # Renamed path variable
def feature(nome_feature):
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'erro': 'Usuario nao informado'}), 400

    conn, cur = None, None
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            return jsonify({'erro': 'Erro de conexão com o banco de dados'}), 500

        cur.execute('SELECT plano, inadimplente FROM usuarios WHERE usuario = %s', (usuario,))
        row = cur.fetchone()

        if not row:
            return jsonify({'erro': 'Usuario nao encontrado'}), 404

        plano, inad = row
        if inad: # This means inadimplente == 1 (True)
            return jsonify({'erro': 'Acesso bloqueado por inadimplencia'}), 403

        if nome_feature not in FEATURES_BY_PLAN.get(plano, set()):
            return jsonify({'erro': 'Funcionalidade nao disponivel para seu plano'}), 403

        return jsonify({'mensagem': f'Funcionalidade {nome_feature} liberada'}), 200
    except (Exception, psycopg2.Error) as error:
        app.logger.error(f"Database error during feature access for {usuario}, feature {nome_feature}: {error}")
        return jsonify({'erro': 'Erro ao verificar funcionalidade'}), 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


if __name__ == '__main__':
    # Configure basic logging for the app
    # In a production environment, you'd likely use a more robust logging setup
    # controlled by environment variables or a config file.
    if not app.debug: # Only set basicConfig if not in debug mode (where Flask might set its own)
        import logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    init_db() # Initialize DB schema if needed
    app.run(debug=os.environ.get('FLASK_DEBUG', 'True').lower() == 'true', host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
