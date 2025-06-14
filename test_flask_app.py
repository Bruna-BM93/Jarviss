import unittest
import json
import os
import sys

# Adiciona o diretório raiz ao sys.path para permitir importações de main.py
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from main import app, init_db, DB_PATH as MAIN_DB_PATH, JWT_SECRET

# Variável global para armazenar o caminho original do DB
ORIGINAL_DB_PATH = MAIN_DB_PATH
TEST_DB_PATH = 'test_jarvis.db'

class FlaskAppTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Configuração que roda uma vez antes de todos os testes da classe."""
        app.config['TESTING'] = True
        # Altera o caminho do banco de dados para o de teste
        # Esta é uma forma de sobrescrever a variável global em main.py para o contexto dos testes.
        # Em projetos maiores, a configuração do app Flask seria mais flexível.
        import main
        main.DB_PATH = TEST_DB_PATH

        init_db() # Inicializa o banco de dados de teste

    @classmethod
    def tearDownClass(cls):
        """Limpeza que roda uma vez depois de todos os testes da classe."""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        # Restaura o caminho original do DB (embora o impacto seja limitado se os testes rodam isoladamente)
        import main
        main.DB_PATH = ORIGINAL_DB_PATH


    def setUp(self):
        """Configuração que roda antes de cada teste."""
        self.client = app.test_client()
        # Limpa e reinicializa o banco de dados para cada teste para garantir isolamento
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        init_db()
        self.test_user_token = self._get_test_user_token()

    def tearDown(self):
        """Limpeza que roda depois de cada teste."""
        # O banco de dados é limpo no setUp do próximo teste ou no tearDownClass
        pass

    def _get_test_user_token(self):
        """Registra um usuário de teste e faz login para obter um token."""
        register_data = {
            "nome": "Test User",
            "usuario": "testuser",
            "senha": "password123",
            "cpf": "12345678901", # CPF válido para o regex
            "plano": "Premium" # Para ter acesso a todas as features
        }
        self.client.post('/register', json=register_data)

        login_data = {
            "usuario": "testuser",
            "senha": "password123"
        }
        response = self.client.post('/login', json=login_data)
        data = json.loads(response.data.decode())
        return data.get('token')

    # --- Testes para POST /transacoes ---

    def test_add_transaction_success(self):
        """Testa adicionar uma transação com sucesso."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")

        transaction_data = {
            "descricao": "Compra de teste",
            "valor": 100.50,
            "tipo": "despesa",
            "data": "2023-10-27"
        }
        headers = {
            'Authorization': f'Bearer {self.test_user_token}'
        }
        response = self.client.post('/transacoes', json=transaction_data, headers=headers)

        self.assertEqual(response.status_code, 201, f"Resposta: {response.data.decode()}")
        data = json.loads(response.data.decode())
        self.assertIn('id', data)
        self.assertEqual(data['descricao'], transaction_data['descricao'])
        self.assertEqual(data['valor'], transaction_data['valor'])
        self.assertEqual(data['tipo'], transaction_data['tipo'])
        self.assertEqual(data['data'], transaction_data['data'])

        # Verificar no banco (opcional, mas bom para garantir)
        # Esta parte requer acesso direto ao DB de teste, o que pode ser complexo
        # de configurar de forma limpa aqui sem ORM. Por ora, confiamos na resposta.

    def test_add_transaction_missing_data(self):
        """Testa adicionar transação com dados faltando."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")
        transaction_data = {
            "descricao": "Faltando valor"
            # valor, tipo, data estão faltando
        }
        headers = {
            'Authorization': f'Bearer {self.test_user_token}'
        }
        response = self.client.post('/transacoes', json=transaction_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        self.assertIn('Dados incompletos', data['erro'])


    def test_add_transaction_invalid_token(self):
        """Testa adicionar transação com token inválido."""
        transaction_data = {
            "descricao": "Teste com token ruim",
            "valor": 50.0,
            "tipo": "receita",
            "data": "2023-10-28"
        }
        headers = {
            'Authorization': 'Bearer INVALID_TOKEN_VALUE'
        }
        response = self.client.post('/transacoes', json=transaction_data, headers=headers)
        self.assertEqual(response.status_code, 401) # Esperado 401 Unauthorized
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        self.assertIn('Token inválido', data['erro']) # Ou 'Token ausente' se a validação for diferente

    def test_add_transaction_no_token(self):
        """Testa adicionar transação sem token."""
        transaction_data = {
            "descricao": "Teste sem token",
            "valor": 20.0,
            "tipo": "despesa",
            "data": "2023-10-29"
        }
        # Sem header de Authorization
        response = self.client.post('/transacoes', json=transaction_data)
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        self.assertIn('Token ausente', data['erro'])


    def test_add_transaction_invalid_type(self):
        """Testa adicionar transação com tipo inválido."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")
        transaction_data = {
            "descricao": "Tipo errado",
            "valor": 10.0,
            "tipo": "investimento", # Tipo inválido
            "data": "2023-10-30"
        }
        headers = {
            'Authorization': f'Bearer {self.test_user_token}'
        }
        response = self.client.post('/transacoes', json=transaction_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        self.assertIn("Tipo de transação inválido", data['erro'])


    def test_add_transaction_negative_value(self):
        """Testa adicionar transação com valor negativo."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")
        transaction_data = {
            "descricao": "Valor negativo",
            "valor": -5.0, # Valor inválido
            "tipo": "despesa",
            "data": "2023-10-31"
        }
        headers = {
            'Authorization': f'Bearer {self.test_user_token}'
        }
        response = self.client.post('/transacoes', json=transaction_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        self.assertIn("Valor deve ser positivo", data['erro'])

if __name__ == '__main__':
    # Garante que o DB original seja restaurado mesmo se o teste for interrompido.
    try:
        unittest.main()
    finally:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        import main
        main.DB_PATH = ORIGINAL_DB_PATH
