"""
Módulo Core.

Este pacote pode conter utilitários centrais, modelos base, ou outras lógicas
que são compartilhadas por múltiplos blueprints da aplicação Jarvis.
Atualmente, contém `db_utils.py` para interações com o banco de dados.
"""
# Deixar este arquivo __init__.py vazio é comum se o pacote serve apenas
# para agrupar módulos como db_utils.py, e não expõe nada diretamente no nível do pacote.
# Se houvesse classes ou funções a serem importadas diretamente de 'from jarvis_app.core import ...',
# elas poderiam ser importadas aqui. Ex: from .db_utils import get_db
# Mas geralmente, é melhor importar diretamente do módulo específico.
