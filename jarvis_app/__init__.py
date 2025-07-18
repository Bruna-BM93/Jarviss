"""
Módulo principal da aplicação Jarvis.

Este arquivo contém a factory `create_app` para criar e configurar
instâncias da aplicação Flask. Ele lida com o carregamento de configurações,
registro de blueprints, e configuração de hooks da aplicação como o teardown
do contexto para fechar conexões de banco de dados.
"""
import os
from flask import Flask, jsonify # Adicionado jsonify para a rota raiz

# Importações de configuração e utilitários de DB
from config import config_by_name
from .core.db_utils import close_db

def create_app(config_name='default'):
    """
    Factory para criar e configurar a instância da aplicação Flask.

    Args:
        config_name (str): O nome da configuração a ser usada (ex: 'development',
                           'production', 'testing'). Padrão é 'default'.

    Returns:
        Flask: A instância da aplicação Flask configurada.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Carrega a configuração da classe correspondente em config.py
    app.config.from_object(config_by_name[config_name])

    # Carrega configurações da pasta 'instance', se existir um application.cfg
    # Isso pode sobrescrever configurações do config.py (ex: JWT_SECRET em produção via instance/application.cfg)
    # O `silent=True` evita erro se o arquivo não existir, o que é comum em dev/test.
    # Para produção, é bom garantir que o arquivo exista se ele for essencial.
    app.config.from_pyfile('application.cfg', silent=True)

    # Garante que a pasta instance exista para o DB e outras necessidades
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError as e:
        app.logger.error(f"Erro ao criar pasta instance {app.instance_path}: {e}")
        # Considerar levantar a exceção ou sair se a pasta for crítica.

    # Define DB_PATH usando instance_path se não estiver já definido na config
    # (ex: TestingConfig pode definir um DB_NAME, que é usado aqui).
    db_name = app.config.get('DB_NAME', 'jarvis.db') # Padrão para 'jarvis.db'
    if not app.config.get('DB_PATH'): # Só define se não vier da classe de config
        app.config['DB_PATH'] = os.path.join(app.instance_path, db_name)

    # Garante que o diretório do DB exista, caso DB_PATH inclua subpastas dentro de instance/
    db_dir = os.path.dirname(app.config['DB_PATH'])
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError as e:
            app.logger.error(f"Erro ao criar diretório para DB {db_dir}: {e}")


    # Configuração de logging (exemplo básico, pode ser expandido)
    if not app.debug and not app.testing: # Não configurar logging se já estiver em modo debug/test
        # Em produção, pode-se usar handlers mais robustos (ex: RotatingFileHandler, SysLogHandler)
        # e formatters mais detalhados.
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(os.path.join(app.instance_path, 'jarvis.log'),
                                           maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Jarvis API startup')


    # Registrar a função para fechar o DB no teardown do contexto da aplicação
    app.teardown_appcontext(close_db)

    # Importar e registrar Blueprints
    # É comum colocar as importações de blueprints aqui para evitar importações circulares
    # e garantir que o app esteja parcialmente configurado antes de carregar as rotas.
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .ia.routes import ia_bp
    app.register_blueprint(ia_bp, url_prefix='/ia')

    from .transactions.routes import transaction_bp
    app.register_blueprint(transaction_bp, url_prefix='/transacoes')

    # Rota raiz de boas-vindas.
    # Pode ser movida para um blueprint "general" ou "home" em aplicações maiores.
    @app.route('/')
    def index():
        """Rota raiz da API, retorna uma mensagem de boas-vindas."""
        return jsonify({"mensagem": "Bem-vindo ao Jarvis API (Reestruturado)!",
                        "documentacao": "/docs" # Exemplo de link para documentação (se houver)
                       })

    return app
