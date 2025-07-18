"""
Ponto de entrada para executar a aplicação Flask Jarvis.

Este script cria uma instância da aplicação usando a factory `create_app`
e inicializa o banco de dados antes de iniciar o servidor de desenvolvimento Flask.

A configuração da aplicação (development, production, testing) pode ser
controlada pela variável de ambiente FLASK_CONFIG.
"""
import os
from jarvis_app import create_app
from jarvis_app.core.db_utils import init_db

# Determina qual configuração usar.
# Prioriza a variável de ambiente FLASK_CONFIG. Se não definida, usa 'default'
# que geralmente aponta para 'development' em config.py.
CONFIG_NAME = os.environ.get('FLASK_CONFIG', 'default')

# Cria a instância da aplicação Flask com a configuração selecionada.
app = create_app(CONFIG_NAME)

# Inicializa o banco de dados.
# Isso garante que as tabelas sejam criadas/verificadas ao iniciar a aplicação.
# Ocorre dentro do contexto da aplicação para que init_db possa acessar app.config.
with app.app_context():
    init_db()

if __name__ == '__main__':
    # Executa o servidor de desenvolvimento Flask.
    # host='0.0.0.0' torna o servidor acessível externamente (útil para Docker/VMs).
    # O modo debug é controlado pela configuração carregada em `app`.
    # A porta 5000 é o padrão do Flask.
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', False) # Pega DEBUG da config, fallback para False
    )
