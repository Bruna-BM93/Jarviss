import sqlite3
from flask import Flask, request, jsonify

print(sqlite3.sqlite_version)


def conectar():
    """Cria uma conexão com o banco de dados SQLite."""
    return sqlite3.connect("jarvis.db")


app = Flask(__name__)


@app.route("/")
def home():
    return "Bem-vindo ao Jarvis API"


@app.route("/login", methods=["POST"])
def login():
    dados = request.json
    usuario = dados.get("usuario")
    senha = dados.get("senha")
    if usuario == "admin" and senha == "123":
        return jsonify({"mensagem": "Login autorizado"})
    return jsonify({"erro": "Usuário ou senha incorretos"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    """Endpoint simples para logout."""
    return jsonify({"mensagem": "Logout realizado com sucesso"})


if __name__ == "__main__":
    app.run(debug=True)
