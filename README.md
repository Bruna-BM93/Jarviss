# Jarvis – Assistente Empresarial

Este repositório contém um exemplo simplificado de API em Flask para registrar usuários e empresas, realizar login, controlar planos (Gratuito, Plus e Premium) e bloquear funcionalidades em caso de inadimplência.

## Execução

```bash
python3 main.py
```

A aplicação será iniciada em `http://localhost:5000`.

O cadastro inicial solicita nome da empresa, CPF ou CNPJ, além do usuário e senha. Para planos pagos é possível escolher pagamento via **Pix** (liberação por um mês) ou **cartão de crédito**.

## Geração de APK

Para criar um APK Android, pode-se utilizar [Buildozer](https://github.com/kivy/buildozer). Após instalar as dependências, execute:

```bash
buildozer init  # gera buildozer.spec
buildozer -v android debug
```

O arquivo `.apk` será gerado na pasta `bin/`. Esse procedimento requer um ambiente Linux com as dependências do Android SDK instaladas.
