h109du-codex/criar-app-do-zero
from flask import Flask, request, jsonify, render_template

from flask import Flask, request, jsonify
main
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import urllib.request

DB_PATH = 'jarvis.db'

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
    con.commit()
    con.close()


@app.route('/')
def index():
    return jsonify({"mensagem": "Bem-vindo ao Jarviss API"})


h109du-codex/criar-app-do-zero
@app.route("/jarviss")
def jarviss_page():
    return render_template("jarviss.html")


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
    if plano not in PLANS:
        return jsonify({'erro': 'Plano invalido'}), 400
    if plano != 'Gratuito' and pagamento not in ('pix', 'cartao'):
        return jsonify({'erro': 'Metodo de pagamento invalido'}), 400

    if plano != 'Gratuito':
        valor = PLAN_PRICES.get(plano, 0)
        resp = create_infinity_charge(valor, pagamento)
        if 'erro' in resp:
            return jsonify({'erro': 'Falha ao processar pagamento', 'detalhe': resp['erro']}), 502
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
        msg = f'Bem-vindo {usuario}! Plano: {plano}'
        if inad:
            msg += ' (inadimplente)'
        return jsonify({'mensagem': msg}), 200
    return jsonify({'erro': 'Usuário ou senha incorretos'}), 401


@app.route('/logout', methods=['POST'])
def logout():
    # Não há sessão real neste exemplo, mas o endpoint é mantido
    return jsonify({'mensagem': 'Logout realizado com sucesso'})


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


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')
