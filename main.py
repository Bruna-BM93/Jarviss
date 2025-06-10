import sqlite3
print(sqlite3.sqlite_version)

def conectar():
    con = sqlite3.connect("jarvis.db")
    return con


from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Bem-vindo ao Jarvis API"

@app.route('/login', methods=['POST'])
def login():
    dados = request.json
    usuario = dados.get("usuario")
    senha = dados.get("senha")
    if usuario == "admin" and senha == "123":
        return jsonify({"mensagem": "Login autorizado"})
    return jsonify({"erro": "Usuário ou senha incorretos"}), 401

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/logout', methods=['POST'])
def logout():
    # Aqui você pode adicionar lógica para encerrar a sessão do usuário
    return jsonify({"mensagem": "Logout realizado com sucesso"})
{
  "usuario": "admin",
  "senha": "123"
}

{
  "mensagem": "Login autorizado"
}