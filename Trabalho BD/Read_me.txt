# 🗃️ Consultor de Banco de Dados (Text-to-SQL)

Este projeto é uma aplicação web construída com Streamlit que permite aos usuários fazer perguntas em linguagem natural a um banco de dados (MySQL ou PostgreSQL) e receber respostas geradas por uma Inteligência Artificial. A aplicação traduz a pergunta do usuário para uma consulta SQL, executa-a no banco de dados e formata o resultado em um texto de fácil compreensão.

**Autor:** Bruno Gutierres Mattarazzo de Souza

---

## ⚙️ Pré-requisitos

Antes de começar, certifique-se de que você tem os seguintes programas instalados no seu computador:

* Python 3.8+
* Git
* Acesso a um banco de dados **MySQL** ou **PostgreSQL** que você queira consultar.

---

## 🚀 Instalação e Configuração (Passo a Passo)

Siga estes passos para configurar e rodar o projeto em seu computador.

### 1. Clonar o Repositório

Primeiro, abra seu terminal (ou Prompt de Comando no Windows) e clone este projeto para a sua máquina.

# Criar o ambiente virtual
python3 -m venv .venv

#Ative o ambiente virtual (mac/linux)
source .venv/bin/activate

#Windows
.venv\Scripts\activate

#Instale as bibliotecas
pip install -r requirements.txt
Certifique-se de que você tem um arquivo requirements.txt com todas as bibliotecas como streamlit, langchain-groq, etc.

#Configuração da conexão com o banco de dados
Na pasta do projeto, você encontrará um arquivo chamado .env.example. Renomeie este arquivo para .env.

Abra o arquivo .env com um editor de texto. Você verá o seguinte conteúdo:

# Chave da API do Groq (necessária para a IA funcionar)
GROQ_API_KEY="SUA_CHAVE_GROQ_AQUI"

# String de conexão para o MySQL
MYSQL_URI="mysql+mysqlconnector://SEU_USUARIO:SUA_SENHA@ENDERECO_DO_SERVIDOR:PORTA/NOME_DO_BANCO"

# String de conexão para o PostgreSQL
POSTGRES_URI="postgresql://SEU_USUARIO:SUA_SENHA@ENDERECO_DO_SERVIDOR:PORTA/NOME_DO_BANCO"

Edite as linhas MYSQL_URI e/ou POSTGRES_URI com as informações do seu banco de dados:

SEU_USUARIO: O nome de usuário do seu banco (ex: root para MySQL, postgres para PostgreSQL).
SUA_SENHA: A senha que você usa para acessar o banco.
ENDERECO_DO_SERVIDOR: Se o banco de dados estiver rodando na sua própria máquina, use localhost. Se estiver em outro computador ou servidor, use o endereço IP dele.
PORTA: A porta padrão é 3306 para MySQL e 5432 para PostgreSQL.
NOME_DO_BANCO: O nome específico do banco de dados ao qual você quer se conectar.\

#Para rodar a aplicação com o ##(ambiente virtual)##
streamlit run app.py