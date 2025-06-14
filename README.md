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

O cadastro inicial solicita nome da empresa, CPF ou CNPJ, além do usuário e senha. O endereço pode ser preenchido automaticamente através da consulta de CNPJ ou CEP e é sempre mostrado para confirmação antes de ser salvo. Para planos pagos é possível escolher pagamento via **Pix** ou **cartão de crédito**. Os pagamentos são processados automaticamente pela **Infinity Pay**. Defina a variável de ambiente `INFINITY_PAY_TOKEN` com o token da sua conta para habilitar a integração. Configure também `JWT_SECRET` para personalizar a chave dos tokens. Para alterar o caminho do banco SQLite utilize `JARVISS_DB`. Nunca compartilhe esses segredos publicamente e utilize HTTPS em produção.
As cobranças são emitidas em nome **Jarviss** (CNPJ `46102173000111`) e encaminhadas para a conta da tag `$nalenhacomferreira` no banco Cloudwalk (código `542`, agência `001`, conta `989248-7`).

## Geração de APK

Para criar um APK Android, pode-se utilizar [Buildozer](https://github.com/kivy/buildozer). Um arquivo `buildozer.spec` já está incluído neste repositório e define o identificador do aplicativo como **com.bruna.bm93.App.Jarviss**. Após instalar as dependências, execute:

```bash
buildozer -v android debug
```

O arquivo `.apk` será gerado na pasta `bin/`. Esse procedimento requer um ambiente Linux com as dependências do Android SDK instaladas.

## Firebase e `google-services.json`

Caso utilize um aplicativo Android com Firebase (por exemplo, React Native ou
Flutter), será necessário incluir o arquivo `google-services.json` gerado pelo
console do Firebase. Ele **deve** ficar em
`android/app/google-services.json` dentro do projeto mobile. Após mover o
arquivo, adicione ao `android/build.gradle` geral:

```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.3.15'
    }
}
```

E em `android/app/build.gradle` aplique o plugin:

```gradle
apply plugin: 'com.google.gms.google-services'
```

Essas configurações habilitam a autenticação e demais serviços do Firebase no
aplicativo.

## Aplicativo móvel (Kivy)

Um cliente simples em Kivy está disponível em `mobile_client/main.py`. Ele realiza login na API Flask. Para executá-lo:

```bash
pip install kivy requests
python3 mobile_client/main.py
```

Certifique-se de que o backend Flask esteja em execução em `http://localhost:5000` ou ajuste `API_URL` no código do aplicativo.

Tokens JWT são gerados no login e devem ser enviados no cabeçalho `Authorization: Bearer <token>` para acessar os demais endpoints.

## Publicação na Play Store

Para publicar a aplicação móvel, o identificador do pacote definido no `buildozer.spec` é `com.bruna.bm93.App.Jarviss`. Caso utilize a conta de desenvolvedor do exemplo, o ID associado é `7479072546592163623`.

## Consulta de CNPJ e CEP

Para auxiliar no preenchimento de cadastros, há dois endpoints que consultam APIs públicas:

* `/consultar_cnpj/<cnpj>` usa [publica.cnpj.ws](https://publica.cnpj.ws) para validar o CNPJ e retornar razão social, endereço e demais dados da empresa.
* `/consultar_cep/<cep>` consulta [ViaCEP](https://viacep.com.br) e devolve o endereço completo do CEP informado.

Exemplo de chamada:

```bash
curl http://localhost:5000/consultar_cnpj/00000000000191
curl http://localhost:5000/consultar_cep/01001000
```

## Aplicativo Flutter

Para demonstrar gráficos financeiros e metas em uma interface moderna, há um exemplo em Flutter dentro de `flutter_app`. Ele utiliza o pacote `fl_chart` para renderizar gráficos em tempo real e exibe notificações bancárias simuladas.

Para executar o aplicativo Flutter:

```bash
cd flutter_app
flutter run
```

É necessário ter o SDK do Flutter instalado. O `pubspec.yaml` já declara a dependência `fl_chart`.

## APIs adicionais

Além das consultas de CNPJ e CEP, a aplicação expõe alguns recursos auxiliares gratuitos.

* `/cidades/<UF>` retorna a lista de municípios do estado informado utilizando a API do [IBGE](https://servicodados.ibge.gov.br).
* `/indicadores` exibe as últimas taxas financeiras (SELIC, CDI e IPCA) obtidas a partir da API do [Banco Central](https://dadosabertos.bcb.gov.br).

Esses serviços podem ser usados para enriquecer cadastros e relatórios dentro do Jarviss.

## Lembretes via WhatsApp

O projeto inclui um agendador em `scheduler.py` que verifica periodicamente a tabela `lembretes` no banco de dados. Quando a data e hora de um lembrete chegam, uma mensagem é enviada pelo WhatsApp utilizando a API da Twilio.

Para registrar um lembrete envie uma requisição `POST` para `/lembretes` com token JWT e os campos:

```json
{
  "usuario": "seu_usuario",
  "mensagem": "Pagar boleto da luz",
  "data_hora": "2025-06-18 08:00"
}
```

Execute o agendador separadamente com:

```bash
python3 scheduler.py
```

Configure as variáveis `TWILIO_SID`, `TWILIO_TOKEN`, `TWILIO_FROM` e `TWILIO_TO` para habilitar o envio pelo WhatsApp.
