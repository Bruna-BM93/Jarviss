import unittest
import json
import os
import sys

"""
Testes unitários e de integração para a aplicação Flask Jarvis.

Este módulo contém testes para as rotas da API, cobrindo cenários de sucesso,
erros de validação de dados e autenticação.
"""
import unittest
import json
import os
# sys não é mais necessário aqui se os testes forem executados como um módulo
# ou com o discovery do unittest a partir da raiz do projeto.

from jarvis_app import create_app
from jarvis_app.core.db_utils import init_db
# JWT_SECRET e outras configs são carregadas pelo app de teste via TestingConfig

class FlaskAppTests(unittest.TestCase):
    """Suite de testes para a aplicação Flask Jarvis."""

    @classmethod
    def setUpClass(cls):
        """Configuração que roda uma vez antes de todos os testes da classe."""
        cls.app = create_app(config_name='testing') # Usa a config 'testing'
        cls.app_context = cls.app.app_context()
        cls.app_context.push() # Ativa o contexto da aplicação

        # O DB_PATH agora vem da config 'testing'
        cls.db_path = cls.app.config['DB_PATH']

        # Garante que a pasta instance exista para testes (se DB_PATH for relativo a instance)
        instance_folder = cls.app.instance_path
        if not os.path.exists(instance_folder):
            os.makedirs(instance_folder, exist_ok=True)

        # Limpa o banco de dados de teste, se existir de uma execução anterior
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

        init_db() # Inicializa o banco de dados de teste DENTRO do contexto

    @classmethod
    def tearDownClass(cls):
        """Limpeza que roda uma vez depois de todos os testes da classe."""
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
        cls.app_context.pop() # Desativa o contexto da aplicação

    def setUp(self):
        """Configuração que roda antes de cada teste."""
        self.client = self.app.test_client() # Usa o cliente do app da classe

        # Limpa e reinicializa o banco de dados para cada teste para garantir isolamento
        # Isso é crucial se os testes modificam o estado do DB que outros testes dependem.
        if os.path.exists(self.db_path): # Usa self.db_path da classe
            os.remove(self.db_path)
        init_db() # Recria tabelas

        self.test_user_token = self._get_test_user_token()

    def tearDown(self):
        """Limpeza que roda depois de cada teste."""
        # O banco de dados é limpo no setUp do próximo teste.
        # Nenhuma ação específica aqui, a menos que precise limpar algo criado durante o teste
        # que não seja o DB (ex: arquivos temporários).
        pass

    def _get_test_user_token(self):
        """
        Registra um usuário de teste e faz login para obter um token JWT.
        Este é um método auxiliar para os testes que requerem autenticação.
        """
        register_data = {
            "nome": "Test User",
            "usuario": "testuser",
            "senha": "password123", # Senha que passa na validação
            "cpf": "12345678901",  # CPF válido para o regex
            "plano": "Premium"     # Plano que permite acesso a todas as features
        }
        # Não verificamos o resultado do registro aqui, pois é um setup para outros testes.
        # Assumimos que o registro funciona conforme testado em `test_register_user_success` (se existir).
        self.client.post('/auth/register', json=register_data)

        login_data = {
            "usuario": "testuser",
            "senha": "password123"
        }
        response = self.client.post('/auth/login', json=login_data) # Adicionado prefixo /auth
        data = json.loads(response.data.decode())
        token = data.get('token')
        self.assertIsNotNone(token, "Falha ao obter token de teste.")
        return token

    # --- Testes para POST /transacoes --- (agora com prefixo /transacoes)

    def test_add_transaction_success(self):
        """Testa adicionar uma transação com sucesso."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")

        transaction_data = {
            "descricao": "Compra de teste bem sucedida", # Descrição mais específica
            "valor": 100.50,
            "tipo": "despesa",
            "data": "2023-10-27"
        }
        headers = {
            'Authorization': f'Bearer {self.test_user_token}'
        }
        response = self.client.post('/transacoes', json=transaction_data, headers=headers) # Rota agora é /transacoes

        self.assertEqual(response.status_code, 201, f"Resposta: {response.data.decode()}")
        data = json.loads(response.data.decode())
        self.assertIn('id', data)
        self.assertEqual(data['descricao'], transaction_data['descricao'])
        self.assertEqual(data['valor'], transaction_data['valor'])
        self.assertEqual(data['tipo'], transaction_data['tipo'])
        self.assertEqual(data['data'], transaction_data['data'])

    def test_add_transaction_missing_fields(self):
        """Testa adicionar transação com campos obrigatórios faltando."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")

        # Testar faltando 'descricao'
        transaction_data_no_desc = {"valor": 50.0, "tipo": "receita", "data": "2023-10-28"}
        headers = {'Authorization': f'Bearer {self.test_user_token}'}
        response = self.client.post('/transacoes', json=transaction_data_no_desc, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        self.assertIn('detalhes', data) # Espera a chave 'detalhes' com a lista de erros
        self.assertTrue(any('Campo descricao é obrigatório' in detail for detail in data['detalhes']))

        # Testar faltando 'valor'
        transaction_data_no_valor = {"descricao": "Sem valor", "tipo": "despesa", "data": "2023-10-28"}
        response = self.client.post('/transacoes', json=transaction_data_no_valor, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any('Campo valor é obrigatório' in detail for detail in data['detalhes']))

        # Testar faltando 'tipo'
        transaction_data_no_tipo = {"descricao": "Sem tipo", "valor": 10.0, "data": "2023-10-28"}
        response = self.client.post('/transacoes', json=transaction_data_no_tipo, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any('Campo tipo é obrigatório' in detail for detail in data['detalhes']))

        # Testar faltando 'data'
        transaction_data_no_data = {"descricao": "Sem data", "valor": 20.0, "tipo": "receita"}
        response = self.client.post('/transacoes', json=transaction_data_no_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any('Campo data é obrigatório' in detail for detail in data['detalhes']))

    def test_add_transaction_empty_json_body(self):
        """Testa adicionar transação com corpo JSON vazio."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")
        headers = {'Authorization': f'Bearer {self.test_user_token}'}
        response = self.client.post('/transacoes', json={}, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        # A mensagem exata pode variar, mas deve indicar que campos são obrigatórios ou o corpo está vazio.
        # A validação atual retornará múltiplos erros em 'detalhes'
        self.assertIn('detalhes', data)
        self.assertTrue(any('Campo descricao é obrigatório' in detail for detail in data['detalhes']))


    def test_add_transaction_invalid_token(self):
        """Testa adicionar transação com token inválido."""
        transaction_data = {
            "descricao": "Compra com token inválido",
            "valor": 50.0,
            "tipo": "receita",
            "data": "2023-10-28"
        }
        headers = {
            'Authorization': 'Bearer INVALID_TOKEN_VALUE'
        }
        response = self.client.post('/transacoes', json=transaction_data, headers=headers)
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        self.assertEqual(data['erro'], 'Token inválido')

    def test_add_transaction_no_token(self):
        """Testa adicionar transação sem token."""
        transaction_data = {
            "descricao": "Compra sem token",
            "valor": 20.0,
            "tipo": "despesa",
            "data": "2023-10-29"
        }
        # Sem header de Authorization
        response = self.client.post('/transacoes', json=transaction_data)
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        self.assertEqual(data['erro'], 'Token ausente ou Bearer token esperado')


    def test_add_transaction_invalid_content_type(self):
        """Testa adicionar transação com tipo de conteúdo inválido (não JSON)."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")
        headers = {
            'Authorization': f'Bearer {self.test_user_token}',
            'Content-Type': 'application/xml' # Tipo de conteúdo inválido
        }
        # O Flask normalmente já rejeita isso antes de chegar na nossa validação de 'dados'
        # dependendo de como ele lida com 'request.json' para content-types inesperados.
        # Se request.json for None devido a isso, nosso primeiro 'if not dados:' pegaria.
        response = self.client.post('/transacoes', data="<xml></xml>", headers=headers)
        self.assertEqual(response.status_code, 400) # Flask >= 1.1 retorna 400 para JSON malformado ou content-type errado
        data = json.loads(response.data.decode())
        self.assertIn('erro', data)
        # A mensagem pode ser genérica como "Failed to decode JSON object" ou a nossa de "Corpo da requisição JSON não pode ser vazio"
        # ou "Unsupported Media Type" (415) se o Flask tratar antes.
        # A validação atual retornará "Corpo da requisição JSON não pode ser vazio" se request.json for None.


    def test_add_transaction_specific_field_validations(self):
        """Testa validações de conteúdo específico para campos de transação."""
        self.assertIsNotNone(self.test_user_token, "Token não obtido para teste")
        headers = {'Authorization': f'Bearer {self.test_user_token}'}

        # Tipo inválido
        data_inv_tipo = {"descricao": "Tipo Inválido", "valor": 10.0, "tipo": "investimento", "data": "2023-11-01"}
        response = self.client.post('/transacoes', json=data_inv_tipo, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any("Tipo de transação deve ser 'receita' ou 'despesa'" in detail for detail in data['detalhes']))

        # Valor negativo
        data_neg_valor = {"descricao": "Valor Negativo", "valor": -5.0, "tipo": "despesa", "data": "2023-11-01"}
        response = self.client.post('/transacoes', json=data_neg_valor, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any("Valor da transação deve ser positivo" in detail for detail in data['detalhes']))

        # Valor zero
        data_zero_valor = {"descricao": "Valor Zero", "valor": 0.0, "tipo": "receita", "data": "2023-11-01"}
        response = self.client.post('/transacoes', json=data_zero_valor, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any("Valor da transação deve ser positivo" in detail for detail in data['detalhes']))

        # Valor não numérico
        data_nan_valor = {"descricao": "Valor NaN", "valor": "abc", "tipo": "despesa", "data": "2023-11-01"}
        response = self.client.post('/transacoes', json=data_nan_valor, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any("Campo valor deve ser um dos tipos: int, float" in detail for detail in data['detalhes']))
        # Nota: A validação de "Valor da transação deve ser um número válido" também pode aparecer dependendo da ordem.

        # Data em formato inválido
        data_inv_data = {"descricao": "Data Inválida", "valor": 20.0, "tipo": "receita", "data": "01-12-2023"}
        response = self.client.post('/transacoes', json=data_inv_data, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any("Formato de data inválido. Use YYYY-MM-DD" in detail for detail in data['detalhes']))

        # Descrição vazia
        data_empty_desc = {"descricao": "  ", "valor": 25.0, "tipo": "despesa", "data": "2023-11-01"}
        response = self.client.post('/transacoes', json=data_empty_desc, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any("Campo descricao não pode ser vazio ou apenas espaços" in detail for detail in data['detalhes']))

        # Descrição não string
        data_nstr_desc = {"descricao": 123, "valor": 30.0, "tipo": "receita", "data": "2023-11-01"}
        response = self.client.post('/transacoes', json=data_nstr_desc, headers=headers)
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertTrue(any("Campo descricao deve ser do tipo str" in detail for detail in data['detalhes']))

    # --- Testes para /register (Opcional) ---
    def test_register_user_validation_errors(self):
        """Testa erros de validação ao registrar usuário."""
        # Faltando nome
        response = self.client.post('/auth/register', json={
            "usuario": "newuser", "senha": "password123", "cpf": "00011122233"
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['erro'], "Campo nome é obrigatório")

        # Plano inválido
        response = self.client.post('/auth/register', json={
            "nome": "New User", "usuario": "newuser2", "senha": "password123",
            "cpf": "11122233344", "plano": "Inexistente"
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertIn("Plano 'Inexistente' inválido", data['erro'])

        # Senha fraca
        response = self.client.post('/auth/register', json={
            "nome": "New User", "usuario": "newuser3", "senha": "123",
            "cpf": "22233344455"
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data.decode())
        self.assertEqual(data['erro'], "Senha fraca. Deve ter no mínimo 6 caracteres e incluir pelo menos um dígito.")


if __name__ == '__main__':
    unittest.main()
# Removida a limpeza manual de DB_PATH e restauração, pois setUpClass/tearDownClass cuidam disso
# com a configuração de teste.
