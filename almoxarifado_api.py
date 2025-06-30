from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = 'stock.db'

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS itens ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "nome TEXT NOT NULL,"
        "quantidade INTEGER NOT NULL DEFAULT 0"
        ")"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS movimentacoes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "item_id INTEGER NOT NULL,"
        "tipo TEXT NOT NULL,"
        "quantidade INTEGER NOT NULL,"
        "data TEXT NOT NULL,"
        "FOREIGN KEY(item_id) REFERENCES itens(id)"
        ")"
    )
    con.commit()
    con.close()


def add_item(nome, quantidade):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('INSERT INTO itens (nome, quantidade) VALUES (?, ?)', (nome, quantidade))
    con.commit()
    con.close()


def add_movimentacao(item_id, tipo, quantidade):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT quantidade FROM itens WHERE id = ?', (item_id,))
    row = cur.fetchone()
    if not row:
        con.close()
        return False
    saldo = row[0]
    if tipo == 'saida' and saldo < quantidade:
        con.close()
        return False
    novo_saldo = saldo + quantidade if tipo == 'entrada' else saldo - quantidade
    cur.execute('UPDATE itens SET quantidade = ? WHERE id = ?', (novo_saldo, item_id))
    cur.execute(
        'INSERT INTO movimentacoes (item_id, tipo, quantidade, data) VALUES (?, ?, ?, ?)',
        (item_id, tipo, quantidade, datetime.utcnow().isoformat()),
    )
    con.commit()
    con.close()
    return True


def get_saldo(item_id):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT nome, quantidade FROM itens WHERE id = ?', (item_id,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    return {'id': item_id, 'nome': row[0], 'saldo': row[1]}


def get_movimentos(item_id, inicio=None, fim=None):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    query = 'SELECT tipo, quantidade, data FROM movimentacoes WHERE item_id = ?'
    params = [item_id]
    if inicio:
        query += ' AND data >= ?'
        params.append(inicio)
    if fim:
        query += ' AND data <= ?'
        params.append(fim)
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    con.close()
    return [{'tipo': r[0], 'quantidade': r[1], 'data': r[2]} for r in rows]


def itens_baixo_estoque(limite=10):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute('SELECT id, nome, quantidade FROM itens WHERE quantidade <= ?', (limite,))
    rows = cur.fetchall()
    con.close()
    return [{'id': r[0], 'nome': r[1], 'saldo': r[2]} for r in rows]


def media_mensal(item_id, meses=3):
    fim = datetime.utcnow()
    inicio = fim - timedelta(days=30 * meses)
    movimentos = get_movimentos(item_id, inicio.isoformat(), fim.isoformat())
    saidas = [m for m in movimentos if m['tipo'] == 'saida']
    total = sum(m['quantidade'] for m in saidas)
    return total / meses if meses else 0


app = Flask(__name__)

@app.route('/stock/add_item', methods=['POST'])
def route_add_item():
    dados = request.json or {}
    nome = dados.get('nome')
    quantidade = int(dados.get('quantidade', 0))
    if not nome:
        return jsonify({'erro': 'Nome obrigatorio'}), 400
    add_item(nome, quantidade)
    return jsonify({'mensagem': 'Item adicionado'}), 201


@app.route('/stock/move', methods=['POST'])
def route_move():
    dados = request.json or {}
    item_id = dados.get('item_id')
    tipo = dados.get('tipo')
    quantidade = int(dados.get('quantidade', 0))
    if tipo not in ('entrada', 'saida'):
        return jsonify({'erro': 'Tipo invalido'}), 400
    if not item_id or quantidade <= 0:
        return jsonify({'erro': 'Dados invalidos'}), 400
    if not add_movimentacao(item_id, tipo, quantidade):
        return jsonify({'erro': 'Operacao invalida'}), 400
    return jsonify({'mensagem': 'Movimentacao registrada'})


@app.route('/stock/saldo/<int:item_id>')
def route_saldo(item_id):
    info = get_saldo(item_id)
    if not info:
        return jsonify({'erro': 'Item nao encontrado'}), 404
    return jsonify(info)


@app.route('/stock/historico/<int:item_id>')
def route_historico(item_id):
    inicio = request.args.get('inicio')
    fim = request.args.get('fim')
    movimentos = get_movimentos(item_id, inicio, fim)
    return jsonify({'movimentacoes': movimentos})


@app.route('/stock/baixo')
def route_baixo():
    limite = int(request.args.get('limite', 10))
    itens = itens_baixo_estoque(limite)
    return jsonify({'itens': itens})


@app.route('/stock/media/<int:item_id>')
def route_media(item_id):
    meses = int(request.args.get('meses', 3))
    media = media_mensal(item_id, meses)
    return jsonify({'media_mensal': media})


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')
