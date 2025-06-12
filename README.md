# Jarvis – Assistente Empresarial

Este repositório contém um exemplo simplificado de API em Flask para registrar usuários e empresas, realizar login, controlar planos (Gratuito, Plus e Premium) e bloquear funcionalidades em caso de inadimplência.

## Execução

```bash
python3 main.py
```

Para executar em um contêiner Docker:

```bash
docker compose up --build
```

A aplicação será iniciada em `http://localhost:5000`.
Visite http://localhost:5000/jarviss para acessar a interface web com uma imagem de robô inteligente.

O cadastro inicial solicita nome da empresa, CPF ou CNPJ, além do usuário e senha. Para planos pagos é possível escolher pagamento via **Pix** ou **cartão de crédito**. Os pagamentos são processados automaticamente pela **Infinity Pay**. Defina a variável de ambiente `INFINITY_PAY_TOKEN` com o token da sua conta para habilitar a integração. Configure também `JWT_SECRET` para personalizar a chave dos tokens. Nunca compartilhe esses segredos publicamente e utilize HTTPS em produção.
As cobranças são emitidas em nome **Jarviss** (CNPJ `46102173000111`) e encaminhadas para a conta da tag `$nalenhacomferreira` no banco Cloudwalk (código `542`, agência `001`, conta `989248-7`).

## Geração de APK

Para criar um APK Android, pode-se utilizar [Buildozer](https://github.com/kivy/buildozer). Após instalar as dependências, execute:

```bash
buildozer init  # gera buildozer.spec
buildozer -v android debug
```

O arquivo `.apk` será gerado na pasta `bin/`. Esse procedimento requer um ambiente Linux com as dependências do Android SDK instaladas.

## Aplicativo móvel (Kivy)

Um cliente simples em Kivy está disponível em `mobile_client/main.py`. Ele realiza login na API Flask. Para executá-lo:

```bash
pip install kivy requests
python3 mobile_client/main.py
```

Certifique-se de que o backend Flask esteja em execução em `http://localhost:5000` ou ajuste `API_URL` no código do aplicativo.

Tokens JWT são gerados no login e devem ser enviados no cabeçalho `Authorization: Bearer <token>` para acessar os demais endpoints.

## Aplicativo Flutter

Para demonstrar gráficos financeiros e metas em uma interface moderna, há um exemplo em Flutter dentro de `flutter_app`. Ele utiliza o pacote `fl_chart` para renderizar gráficos em tempo real e exibe notificações bancárias simuladas.

Para executar o aplicativo Flutter:

```bash
cd flutter_app
flutter run
```

É necessário ter o SDK do Flutter instalado. O `pubspec.yaml` já declara a dependência `fl_chart`.
