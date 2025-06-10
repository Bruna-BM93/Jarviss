import sqlite3

def conectar():
    return sqlite3.connect("jarvis.db")

@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    usuario = dados.get("usuario")
    senha = dados.get("senha")

    con = conectar()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM usuarios WHERE usuario = ? AND senha = ?", (usuario, senha))
    user = cursor.fetchone()
    con.close()

    if user:
        return jsonify({"mensagem": f"Bem-vindo {usuario}!"})
    return jsonify({"erro": "Usuário ou senha incorretos"}), 401
