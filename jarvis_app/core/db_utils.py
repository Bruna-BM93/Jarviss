"""
Utilitários para gerenciamento de banco de dados SQLite.

Este módulo fornece funções para criar, obter e fechar conexões com o banco de dados,
bem como para inicializar o schema do banco de dados e outras funções auxiliares
relacionadas ao acesso a dados e informações de usuário baseadas em token.
"""
import sqlite3
from datetime import datetime

import jwt # Para decodificar JWT e exceções relacionadas
from flask import current_app, g, request # Para contexto da aplicação, g e request


def _create_db_connection():
    """Cria uma nova conexão com o banco de dados."""
    db_path = current_app.config['DB_PATH']
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row # Para acessar colunas por nome
    current_app.logger.debug(f"Criada nova conexão com o banco de dados: {db_path}")
    return conn

def get_db():
    """
    Retorna a conexão com o banco de dados para a requisição atual.
    Se não existir, cria uma e armazena em flask.g.
    """
    if 'db' not in g:
        g.db = _create_db_connection()
        current_app.logger.debug("Conexão com DB armazenada em g.db")
    return g.db

def close_db(e=None):
    """Fecha a conexão com o banco de dados, se existir em flask.g."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
        current_app.logger.debug("Conexão com DB fechada.")

def init_db_command_for_cli(app_context):
    """
    Comando CLI para inicializar o banco de dados (exemplo).

    Para usar como um comando Flask CLI 'flask init-db', você precisaria
    registrar esta função como um comando na sua aplicação.
    Exemplo em `jarvis_app/__init__.py` (ou um arquivo de comandos dedicado):

    ```python
    # import click
    # from .core.db_utils import init_db_command_for_cli
    #
    # @app.cli.command('init-db')
    # def init_db_cli_command():
    #     """Limpa os dados existentes e cria novas tabelas."""
    #     init_db_command_for_cli(app.app_context())
    #     click.echo('Banco de dados inicializado.')
    ```
    A inicialização automática em `run.py` já cobre o caso de uso principal ao iniciar o app.
    """
    # O app_context já deve estar ativo se chamado via app.cli
    # ou explicitamente como em run.py
    db = get_db()

    # Script de criação de tabelas. Pode ser lido de um arquivo .sql para schemas maiores.
    schema_script = """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            usuario TEXT NOT NULL UNIQUE,
            senha TEXT NOT NULL,
            cpf TEXT,
            cnpj TEXT,
            plano TEXT NOT NULL DEFAULT 'Gratuito',
            pagamento TEXT,
            inadimplente INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS transacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),
            data TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        );
        """
        try:
            db.executescript(schema_script) # executescript lida com múltiplos statements
            db.commit() # Importante commitar após executescript se ele não autocommita DDL
            current_app.logger.info(f"Tabelas do banco de dados verificadas/criadas em {current_app.config['DB_PATH']}")

            # Adicionar colunas se não existirem (para bancos de dados mais antigos)
            # Esta lógica é mais complexa com executescript, melhor fazer com execute individual
            cursor = db.cursor() # Obter cursor para PRAGMA e ALTER TABLE
            existing_cols_usuarios = [col[1] for col in cursor.execute("PRAGMA table_info(usuarios)").fetchall()]
            cols_to_add_usuarios = {
                'cpf': 'TEXT',
                'cnpj': 'TEXT',
                'pagamento': 'TEXT'
            }
            for col_name, col_type in cols_to_add_usuarios.items():
                if col_name not in existing_cols_usuarios:
                    try:
                        cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {col_name} {col_type}")
                        current_app.logger.info(f"Coluna {col_name} adicionada à tabela usuarios.")
                    except sqlite3.OperationalError as e:
                        current_app.logger.warning(f"Falha ao adicionar coluna {col_name} a usuarios: {e}")
            db.commit() # Commit das alterações de ALTER TABLE

        except sqlite3.Error as e:
            current_app.logger.error(f"Erro ao executar script do schema: {e}")
            # Considerar rollback ou tratamento mais específico se necessário
        # Não fechar db aqui, será feito por close_db via teardown_appcontext

def init_db():
    """
    Inicializa o banco de dados: cria tabelas e adiciona colunas faltantes.

    Esta função é chamada dentro de um contexto de aplicação (ex: de `run.py`)
    para garantir que `current_app` e `g` estejam disponíveis.
    Usa `get_db()` para obter a conexão, que será gerenciada por `g`.
    """
    db = get_db()

    schema_script = """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        usuario TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        cpf TEXT,
        cnpj TEXT,
        plano TEXT NOT NULL DEFAULT 'Gratuito',
        pagamento TEXT,
        inadimplente INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER NOT NULL,
        descricao TEXT NOT NULL,
        valor REAL NOT NULL,
        tipo TEXT NOT NULL CHECK(tipo IN ('receita', 'despesa')),
        data TEXT NOT NULL,
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
    );
    """
    try:
        db.executescript(schema_script)
        db.commit() # Importante para DDL com executescript
        current_app.logger.info(f"Tabelas do banco de dados verificadas/criadas em {current_app.config['DB_PATH']}")

        cursor = db.cursor()
        existing_cols_usuarios = [col[1] for col in cursor.execute("PRAGMA table_info(usuarios)").fetchall()]
        cols_to_add_usuarios = {'cpf': 'TEXT', 'cnpj': 'TEXT', 'pagamento': 'TEXT'}
        for col_name, col_type in cols_to_add_usuarios.items():
            if col_name not in existing_cols_usuarios:
                try:
                    cursor.execute(f"ALTER TABLE usuarios ADD COLUMN {col_name} {col_type}")
                    current_app.logger.info(f"Coluna {col_name} adicionada à tabela usuarios.")
                except sqlite3.OperationalError as e:
                    current_app.logger.warning(f"Falha ao adicionar coluna {col_name} a usuarios: {e}")
        db.commit()
    except sqlite3.Error as e:
        current_app.logger.error(f"Erro ao inicializar DB com script: {e}")
    # A conexão é gerenciada por g e será fechada por teardown_appcontext


# A função _create_db_connection e get_db_connection foram efetivamente substituídas
# pela combinação de _create_db_connection (privada) e get_db (pública).

# Funções auxiliares para manipulação de token e dados do usuário.
# Estas funções dependem do contexto da requisição Flask (request, current_app, g).

def get_usuario_id_from_token():
    """
    Obtém o ID do usuário do banco de dados a partir do nome de usuário ('sub')
    contido no token JWT. Retorna o ID do usuário ou None se não encontrado.
    Lança exceções JWT se o token for inválido/expirado.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header or not auth_header.startswith('Bearer '):
        current_app.logger.warning("Tentativa de obter usuario_id sem token Bearer.")
        return None

    token = auth_header.split(' ', 1)[1]
    decoded_token = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
    usuario_jwt_sub = decoded_token['sub']

    db = get_db() # Usa a conexão gerenciada por g
    # Não precisa de db.cursor() explícito para SELECT fetchone/fetchall
    user_row = db.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario_jwt_sub,)).fetchone()
    # conn.close() removido - será feito por close_db


    if not user_row:
        current_app.logger.error(f"Usuário JWT '{usuario_jwt_sub}' não encontrado no banco de dados.")
        return None
    return user_row['id'] # sqlite3.Row permite acesso por nome de coluna


def get_user_details_from_token():
    """
    Obtém o ID e o plano do usuário a partir do token JWT.
    Retorna um dicionário {'id': user_id, 'plano': user_plan, 'username': username} ou None.
    Lança exceções JWT se o token for inválido/expirado.
    """
    auth_header = request.headers.get('Authorization', '')
    if not auth_header or not auth_header.startswith('Bearer '):
        current_app.logger.warning("Tentativa de obter detalhes do usuário sem token Bearer.")
        return None

    token = auth_header.split(' ', 1)[1]
    decoded_token = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
    username = decoded_token['sub']

    db = get_db() # Usa a conexão gerenciada por g
    user_row = db.execute("SELECT id, plano FROM usuarios WHERE usuario = ?", (username,)).fetchone()
    # conn.close() removido

    if not user_row:
        current_app.logger.error(f"Usuário JWT '{username}' não encontrado no banco de dados.")
        return None
    return {'id': user_row['id'], 'plano': user_row['plano'], 'username': username}


def validate_date_format(date_string, date_format='%Y-%m-%d'):
    """Valida o formato de uma string de data."""
    try:
        datetime.strptime(date_string, date_format)
        return True
    except ValueError:
        return False

# O decorador token_required também pode vir para cá ou para um módulo de 'auth_utils' ou 'decorators'
# Por agora, vou deixá-lo para ser definido no blueprint de auth, pois é específico para rotas.O arquivo `jarvis_app/core/db_utils.py` foi criado com:
*   `init_db()`: Adaptado para usar `current_app.config['DB_PATH']`. Adicionei logs e uma forma mais segura de adicionar colunas (verificando se existem), embora migrações sejam melhores para produção.
*   `get_db_connection()`: Uma nova função utilitária para obter conexões de banco de dados, configurando `row_factory` para acesso por nome de coluna.
*   `get_usuario_id_from_token()`: Adaptado para usar `current_app.config['JWT_SECRET']` e `get_db_connection()`.
*   `get_user_details_from_token()`: Uma nova função, similar à anterior, mas que retorna mais detalhes do usuário (id, plano, username), útil para verificações de feature.
*   `validate_date_format()`: Movido e sem alterações funcionais diretas, mas agora reside em `db_utils`.

**Passo 4: Crie os Módulos de Blueprint e Mova as Rotas**

Vou começar com o módulo `auth`.

**4.1. Módulo `auth`**

**4.1.1. `jarvis_app/auth/decorators.py` (para `token_required`)**
