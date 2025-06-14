from flask import Flask, request, jsonify, render_template
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import json
import urllib.request
import requests
import re
import logging
from datetime import datetime, timedelta
import jwt
from functools import wraps

DB_PATH = os.environ.get('JARVISS_DB', 'jarvis.db')

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

CPF_RE = re.compile(r'^\d{11}$')
CNPJ_RE = re.compile(r'^\d{14}$')
PASSWORD_RE = re.compile(r'^(?=.*\d).{6,}$')

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get('JWT_SECRET', 'CHANGE_ME')


def is_valid_cpf(cpf: str) -> bool:
    """Valida CPF verificando digitos verificadores e repeticoes."""
    cpf = re.sub(r"\D", "", cpf or "")
    if not CPF_RE.match(cpf) or cpf == cpf[0] * 11:
        return False
    soma1 = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma1 * 10 % 11) % 10
    soma2 = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma2 * 10 % 11) % 10
    return d1 == int(cpf[9]) and d2 == int(cpf[10])


def is_valid_cnpj(cnpj: str) -> bool:
    """Valida CNPJ conferindo digitos e se todos numeros sao iguais."""
    cnpj = re.sub(r"\D", "", cnpj or "")
    if not CNPJ_RE.match(cnpj) or cnpj == cnpj[0] * 14:
        return False
    nums = [int(d) for d in cnpj]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma1 = sum(nums[i] * pesos1[i] for i in range(12))
    d1 = 11 - soma1 % 11
    d1 = 0 if d1 >= 10 else d1
    pesos2 = [6] + pesos1
    soma2 = sum(nums[i] * pesos2[i] for i in range(13))
    d2 = 11 - soma2 % 11
    d2 = 0 if d2 >= 10 else d2
    return nums[12] == d1 and nums[13] == d2


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


def generate_token(usuario: str) -> str:
    payload = {
        'sub': usuario,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def token_required(f):
    @wraps(f)
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
    return wrapper


def init_db():
    """Create database tables if they do not exist."""
    with sqlite3.connect(DB_PATH) as con:
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
            "cep TEXT," \
            "logradouro TEXT," \
            "numero TEXT," \
            "bairro TEXT," \
            "cidade TEXT," \
            "estado TEXT," \
            "complemento TEXT," \
            "inadimplente INTEGER NOT NULL DEFAULT 0"
            ")"
        )
        for coluna, tipo in (
            ('cpf', 'TEXT'),
            ('cnpj', 'TEXT'),
            ('pagamento', 'TEXT'),
            ('cep', 'TEXT'),
            ('logradouro', 'TEXT'),
            ('numero', 'TEXT'),
            ('bairro', 'TEXT'),
            ('cidade', 'TEXT'),
            ('estado', 'TEXT'),
            ('complemento', 'TEXT'),
        ):
            try:
                cur.execute(f"ALTER TABLE usuarios ADD COLUMN {coluna} {tipo}")
            except sqlite3.OperationalError:
                pass
        con.commit()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS transacoes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "usuario TEXT NOT NULL,"
            "tipo TEXT NOT NULL,"
            "valor REAL NOT NULL,"
            "descricao TEXT,"
            "data TEXT NOT NULL"
            ")"
        )
        con.commit()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS tarefas ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "usuario TEXT NOT NULL,"
            "descricao TEXT NOT NULL,"
            "data_hora TEXT NOT NULL,"
            "concluida INTEGER NOT NULL DEFAULT 0"
            ")"
        )
        con.commit()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS lembretes ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "usuario TEXT NOT NULL,"
            "mensagem TEXT NOT NULL,"
            "data_hora TEXT NOT NULL,"
            "enviado INTEGER NOT NULL DEFAULT 0"
            ")"
        )
        con.commit()


@app.route('/')
def index():
    return jsonify({"mensagem": "Bem vindo me chamo Jarvis, serei o seu Novo Assistente Empresarial"})


@app.route("/jarviss")
def jarviss_page():
    return render_template("jarviss.html")

@app.route('/consultar_cnpj/<cnpj>')
def consultar_cnpj(cnpj):
    """Consulta dados do CNPJ na API publica.cnpj.ws"""
    try:
        resp = requests.get(f'https://publica.cnpj.ws/cnpj/{cnpj}')
        if resp.status_code == 200:
            dados = resp.json()
            return jsonify({
                'razao_social': dados.get('razao_social'),
                'nome_fantasia': dados.get('estabelecimento', {}).get('nome_fantasia'),
                'logradouro': dados.get('estabelecimento', {}).get('logradouro'),
                'numero': dados.get('estabelecimento', {}).get('numero'),
                'bairro': dados.get('estabelecimento', {}).get('bairro'),
                'cep': dados.get('estabelecimento', {}).get('cep'),
                'cidade': dados.get('estabelecimento', {}).get('cidade', {}).get('nome'),
                'estado': dados.get('estabelecimento', {}).get('estado', {}).get('sigla'),
                'cnae': dados.get('estabelecimento', {}).get('atividade_principal', {}).get('descricao'),
                'status': dados.get('estabelecimento', {}).get('situacao_cadastral'),
            })
        return jsonify({'erro': 'CNPJ nao encontrado'}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@app.route('/consultar_cep/<cep>')
def consultar_cep(cep):
    """Consulta endereco completo a partir do CEP usando ViaCEP"""
    try:
        resp = requests.get(f'https://viacep.com.br/ws/{cep}/json/')
        if resp.status_code == 200:
            dados = resp.json()
            if 'erro' in dados:
                return jsonify({'erro': 'CEP invalido'}), 400
            return jsonify({
                'logradouro': dados.get('logradouro'),
                'bairro': dados.get('bairro'),
                'cidade': dados.get('localidade'),
                'estado': dados.get('uf'),
                'complemento': dados.get('complemento'),
            })
        return jsonify({'erro': 'Erro na API ViaCEP'}), 500
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@app.route('/cidades/<uf>')
def listar_cidades(uf):
    """Lista municipios do estado informado usando a API do IBGE."""
    try:
        resp = requests.get(
            f'https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios'
        )
        if resp.status_code == 200:
            nomes = [m['nome'] for m in resp.json()]
            return jsonify({'uf': uf.upper(), 'cidades': nomes})
        return jsonify({'erro': 'Estado nao encontrado'}), 404
    except Exception as exc:
        return jsonify({'erro': str(exc)}), 500


@app.route('/indicadores')
def indicadores():
    """Retorna taxas SELIC, CDI e IPCA da API do Banco Central."""
    series = {
        'selic': 11,
        'cdi': 12,
        'ipca': 433,
    }
    dados = {}
    for nome, codigo in series.items():
        try:
            r = requests.get(
                f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados/ultimos/1?formato=json',
                timeout=5,
            )
            if r.status_code == 200 and r.json():
                dados[nome] = r.json()[0]['valor']
        except Exception as exc:
            dados[nome] = f'erro: {exc}'
    return jsonify(dados)

@app.route('/register', methods=['POST'])
def register():
    dados = request.json or {}
    nome = dados.get('nome')
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    cpf = dados.get('cpf')
    cnpj = dados.get('cnpj')
    cep = dados.get('cep')
    logradouro = dados.get('logradouro')
    numero = dados.get('numero')
    bairro = dados.get('bairro')
    cidade = dados.get('cidade')
    estado = dados.get('estado')
    complemento = dados.get('complemento')
    plano = dados.get('plano', 'Gratuito')
    pagamento = dados.get('pagamento') if plano != 'Gratuito' else None
    pagamento_info = None

    if not nome or not usuario or not senha:
        return jsonify({'erro': 'Dados incompletos'}), 400
    if not cpf and not cnpj:
        return jsonify({'erro': 'CPF ou CNPJ obrigatorio'}), 400
    if cpf and not is_valid_cpf(cpf):
        return jsonify({'erro': 'CPF invalido'}), 400
    if cnpj and not is_valid_cnpj(cnpj):
        return jsonify({'erro': 'CNPJ invalido'}), 400
    if cnpj:
        try:
            resp = requests.get(f'https://publica.cnpj.ws/cnpj/{cnpj}')
            if resp.status_code != 200:
                return jsonify({'erro': 'CNPJ nao encontrado'}), 400
        except Exception as exc:
            logger.error('Erro ao consultar CNPJ: %s', exc)
            return jsonify({'erro': 'Falha ao validar CNPJ'}), 502
    if not PASSWORD_RE.match(senha):
        return jsonify({'erro': 'Senha fraca'}), 400
    if plano not in PLANS:
        return jsonify({'erro': 'Plano invalido'}), 400
    if plano != 'Gratuito' and pagamento not in ('pix', 'cartao'):
        return jsonify({'erro': 'Metodo de pagamento invalido'}), 400

    if plano != 'Gratuito':
        valor = PLAN_PRICES.get(plano, 0)
        resp = create_infinity_charge(valor, pagamento)
        if 'erro' in resp:
            logger.error('Falha Infinity Pay: %s', resp['erro'])
            return jsonify({'erro': 'Falha ao processar pagamento'}), 502
        pagamento_info = json.dumps({'metodo': pagamento, 'id': resp.get('id')})

    senha_hash = generate_password_hash(senha)
    try:
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            cur.execute(
                'INSERT INTO usuarios (nome, usuario, senha, cpf, cnpj, plano, pagamento, cep, logradouro, numero, bairro, cidade, estado, complemento) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    nome,
                    usuario,
                    senha_hash,
                    cpf,
                    cnpj,
                    plano,
                    pagamento_info,
                    cep,
                    logradouro,
                    numero,
                    bairro,
                    cidade,
                    estado,
                    complemento,
                )
            )
            con.commit()
    except sqlite3.IntegrityError:
        return jsonify({'erro': 'Usuário já existe'}), 400
    return jsonify({'mensagem': 'Usuário cadastrado com sucesso'})


@app.route('/login', methods=['POST'])
def login():
    dados = request.json or {}
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    if not usuario or not senha:
        return jsonify({'erro': 'Dados incompletos'}), 400

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute('SELECT senha, plano, inadimplente FROM usuarios WHERE usuario = ?', (usuario,))
        row = cur.fetchone()

    if row and check_password_hash(row[0], senha):
        plano = row[1]
        inad = bool(row[2])
        token = generate_token(usuario)
        msg = f'Bem-vindo {usuario}! Plano: {plano}'
        if inad:
            msg += ' (inadimplente)'
        return jsonify({'mensagem': msg, 'token': token}), 200
    return jsonify({'erro': 'Usuário ou senha incorretos'}), 401


@app.route('/logout', methods=['POST'])
@token_required
def logout():
    # Não há sessão real neste exemplo, mas o endpoint é mantido
    return jsonify({'mensagem': 'Logout realizado com sucesso'})


@app.route('/set_plan', methods=['POST'])
@token_required
def set_plan():
    dados = request.json or {}
    usuario = dados.get('usuario')
    plano = dados.get('plano')
    if not usuario or plano not in PLANS:
        return jsonify({'erro': 'Dados invalidos'}), 400
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute('UPDATE usuarios SET plano = ? WHERE usuario = ?', (plano, usuario))
        con.commit()
    return jsonify({'mensagem': 'Plano atualizado'})


@app.route('/set_inadimplente', methods=['POST'])
@token_required
def set_inadimplente():
    dados = request.json or {}
    usuario = dados.get('usuario')
    inad = dados.get('inadimplente')
    if usuario is None or inad is None:
        return jsonify({'erro': 'Dados invalidos'}), 400
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute('UPDATE usuarios SET inadimplente = ? WHERE usuario = ?', (1 if inad else 0, usuario))
        con.commit()
    return jsonify({'mensagem': 'Status de inadimplencia atualizado'})


@app.route('/lembretes', methods=['POST'])
@token_required
def novo_lembrete():
    dados = request.json or {}
    usuario = dados.get('usuario')
    mensagem = dados.get('mensagem')
    data_hora = dados.get('data_hora')
    if not usuario or not mensagem or not data_hora:
        return jsonify({'erro': 'Dados incompletos'}), 400
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            'INSERT INTO lembretes (usuario, mensagem, data_hora) VALUES (?, ?, ?)',
            (usuario, mensagem, data_hora),
        )
        con.commit()
    return jsonify({'mensagem': 'Lembrete registrado'})


@app.route('/transacoes', methods=['POST'])
@token_required
def nova_transacao():
    dados = request.json or {}
    usuario = dados.get('usuario')
    tipo = dados.get('tipo')
    valor = dados.get('valor')
    descricao = dados.get('descricao', '')
    if not usuario or tipo not in ('receita', 'despesa') or valor is None:
        return jsonify({'erro': 'Dados invalidos'}), 400
    data = datetime.utcnow().strftime('%Y-%m-%d')
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            'INSERT INTO transacoes (usuario, tipo, valor, descricao, data) VALUES (?, ?, ?, ?, ?)',
            (usuario, tipo, float(valor), descricao, data),
        )
        con.commit()
    return jsonify({'mensagem': 'Transacao registrada'})


@app.route('/tarefas', methods=['POST'])
@token_required
def nova_tarefa():
    dados = request.json or {}
    usuario = dados.get('usuario')
    descricao = dados.get('descricao')
    data_hora = dados.get('data_hora')
    if not usuario or not descricao or not data_hora:
        return jsonify({'erro': 'Dados incompletos'}), 400
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            'INSERT INTO tarefas (usuario, descricao, data_hora) VALUES (?, ?, ?)',
            (usuario, descricao, data_hora),
        )
        con.commit()
    return jsonify({'mensagem': 'Tarefa adicionada'})


@app.route('/tarefas/<int:tid>/concluir', methods=['POST'])
@token_required
def concluir_tarefa(tid):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute('UPDATE tarefas SET concluida = 1 WHERE id = ?', (tid,))
        con.commit()
    return jsonify({'mensagem': 'Tarefa concluida'})


@app.route('/dashboard_data')
@token_required
def dashboard_data():
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'erro': 'Usuario nao informado'}), 400
    hoje = datetime.utcnow().strftime('%Y-%m-%d')
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute(
            'SELECT SUM(valor) FROM transacoes WHERE usuario = ? AND tipo = "receita" AND data = ?',
            (usuario, hoje),
        )
        receita = cur.fetchone()[0] or 0
        cur.execute(
            'SELECT SUM(valor) FROM transacoes WHERE usuario = ? AND tipo = "despesa" AND data = ?',
            (usuario, hoje),
        )
        despesa = cur.fetchone()[0] or 0
        cur.execute(
            'SELECT id, descricao, data_hora, concluida FROM tarefas WHERE usuario = ? AND date(data_hora) = ? ORDER BY data_hora',
            (usuario, hoje),
        )
        tarefas = [
            {
                'id': t[0],
                'descricao': t[1],
                'hora': t[2][11:16],
                'concluida': bool(t[3]),
            }
            for t in cur.fetchall()
        ]
        cur.execute(
            'SELECT mensagem, data_hora FROM lembretes WHERE usuario = ? AND enviado = 0 ORDER BY data_hora LIMIT 1',
            (usuario,),
        )
        r = cur.fetchone()
        lembrete = f"{r[0]} – {r[1][11:16]}" if r else None
    saldo = receita - despesa
    return jsonify({
        'receita': receita,
        'despesa': despesa,
        'saldo': saldo,
        'tarefas': tarefas,
        'proximo_lembrete': lembrete,
    })


@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')


@app.route('/feature/<nome>', methods=['GET'])
@token_required
def feature(nome):
    usuario = request.args.get('usuario')
    if not usuario:
        return jsonify({'erro': 'Usuario nao informado'}), 400
    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.execute('SELECT plano, inadimplente FROM usuarios WHERE usuario = ?', (usuario,))
        row = cur.fetchone()
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
    logger.info('Iniciando Jarviss API na porta 5000')
    app.run(debug=True, host='0.0.0.0')
