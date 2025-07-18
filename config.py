"""
Configurações da aplicação Flask Jarvis.

Este arquivo define as configurações base e configurações específicas para diferentes
ambientes (desenvolvimento, produção, teste). As configurações são carregadas
na factory da aplicação em `jarvis_app/__init__.py`.

Segredos como JWT_SECRET, OPENAI_API_KEY, INFINITY_PAY_TOKEN devem ser
definidos como variáveis de ambiente ou no arquivo `instance/application.cfg`.
"""
import os

class Config:
    """Configuração base para a aplicação."""
    DEBUG = False
    TESTING = False

    # O DB_PATH é definido dinamicamente na factory `create_app`
    # usando `app.instance_path` para garantir que o banco de dados
    # resida na pasta 'instance', que não é versionada.
    # Exemplo: app.config['DB_PATH'] = os.path.join(app.instance_path, 'jarvis.db')

    # Chave secreta para assinar JWTs.
    # É crucial que esta chave seja mantida em segredo em produção.
    # O fallback é inseguro e serve apenas para desenvolvimento inicial.
    JWT_SECRET = os.environ.get('JWT_SECRET', 'entwicklungsschluessel_bitte_aendern') # Chave de desenvolvimento

    # Chave da API da OpenAI para funcionalidades de IA.
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

    # Definição de planos e features associadas.
    PLANS = ['Gratuito', 'Plus', 'Premium']
    FEATURES_BY_PLAN = {
        'Gratuito': {'basica', 'ia_chat'},
        'Plus': {'basica', 'plus', 'ia_chat', 'ia_interpretacao_notificacao'},
        'Premium': {'basica', 'plus', 'premium', 'ia_chat', 'ia_interpretacao_notificacao'},
    }

    # Configurações para integração com a Infinity Pay.
    INFINITY_PAY_TOKEN = os.environ.get('INFINITY_PAY_TOKEN')
    INFINITY_PAY_URL = os.environ.get('INFINITY_PAY_URL', 'https://api.infinitypay.com.br/v2/charges')
    INFINITY_PAY_RECEIVER = { # Estes valores são exemplos e devem ser configurados via variáveis de ambiente ou instance/application.cfg
        'tag': os.environ.get('INFINITY_PAY_RECEIVER_TAG', '$jarvisDefaultTag'),
        'name': os.environ.get('INFINITY_PAY_RECEIVER_NAME', 'Jarviss Pagamentos'),
        'document': os.environ.get('INFINITY_PAY_RECEIVER_DOCUMENT', '00000000000000'),
        'bank_code': os.environ.get('INFINITY_PAY_RECEIVER_BANK_CODE', '000'),
        'agency': os.environ.get('INFINITY_PAY_RECEIVER_AGENCY', '0001'),
        'account': os.environ.get('INFINITY_PAY_RECEIVER_ACCOUNT', '000000-0'),
        'bank_name': os.environ.get('INFINITY_PAY_RECEIVER_BANK_NAME', 'Banco Exemplo S.A.')
    }
    # Preços dos planos em centavos.
    PLAN_PRICES = {
        'Plus': 1500,     # R$ 15,00
        'Premium': 3000,  # R$ 30,00
    }

    # Regexes para validação foram movidas para os respectivos blueprints (auth.routes)
    # onde são utilizadas, para manter a configuração mais limpa.

# Para permitir diferentes configurações, por exemplo:
class DevelopmentConfig(Config):
    """Configurações para o ambiente de desenvolvimento."""
    DEBUG = True
    # Um JWT_SECRET específico para desenvolvimento, se diferente do fallback da Config base.
    # JWT_SECRET = os.environ.get('DEV_JWT_SECRET', 'dev_secret_key_for_jarvis')

class ProductionConfig(Config):
    """Configurações para o ambiente de produção."""
    DEBUG = False
    TESTING = False
    # Em produção, é crucial que JWT_SECRET seja definido via variável de ambiente.
    # Se os.environ.get('JWT_SECRET') retornar None, a aplicação pode falhar ao iniciar
    # ou usar um valor inseguro, dependendo de como é tratado na app factory.
    # A factory deve garantir que um JWT_SECRET válido esteja presente.
    JWT_SECRET = os.environ.get('JWT_SECRET')
    # Configurações de logging mais robustas, URLs de banco de dados de produção, etc.

class TestingConfig(Config):
    """Configurações para o ambiente de teste."""
    TESTING = True
    # Chave JWT específica e previsível para testes.
    JWT_SECRET = 'test_jwt_secret_key_for_jarvis_app'
    # Define um DB_PATH específico para testes, preferencialmente em memória ou um arquivo dedicado.
    # A factory `create_app` usará `app.instance_path` para prefixar este nome de arquivo.
    DB_NAME = 'test_jarvis.db'
    # DB_PATH será app.instance_path + DB_NAME, definido na factory.
    # Ex: OPENAI_API_KEY = 'fake_test_key' # Para evitar chamadas reais em testes

# Mapeamento de nomes para classes de configuração para uso na app factory.
# Permite selecionar a configuração via variável de ambiente FLASK_CONFIG.
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig # Configuração padrão se FLASK_CONFIG não estiver definida.
}

    # Configuração da OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
