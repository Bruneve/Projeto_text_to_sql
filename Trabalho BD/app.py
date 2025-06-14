import streamlit as st
import os
import pandas as pd
from dotenv import load_dotenv
import ast
import re

from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

LLM_MODEL_NAME = "llama3-8b-8192"


def get_sql_chain(db: SQLDatabase):
    template = """
    Você é um especialista em SQL. Dada uma pergunta do usuário e um esquema de tabela, escreva uma consulta SQL que responda à pergunta do usuário.
    Considere o histórico da conversa, se houver.
    Escreva APENAS a consulta SQL e nada mais. Não envolva a consulta SQL em nenhum outro texto, nem mesmo acentos graves (backticks) ou marcadores de linguagem.

    <SCHEMA>{schema}</SCHEMA>
    
    Histórico da Conversa (se aplicável): {chat_history}
    
    Pergunta: {question}
    Consulta SQL:
    """
    prompt = ChatPromptTemplate.from_template(template)
    llm = ChatGroq(model=LLM_MODEL_NAME, temperature=0)
  
    def get_schema(_):
        return db.get_table_info()
  
    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
    )
    
def formatar_resposta_ia(db_schema: str, user_question: str, sql_query: str, sql_data_str: str):
    template_formatador = """
    Sua única tarefa é formatar a 'String de Dados Brutos' (que é o resultado de uma consulta SQL) em um texto legível para um humano, 
    respondendo à 'Pergunta Original do Usuário'.
    - Use os dados EXATAMENTE como aparecem na string. NÃO invente, adicione, omita ou altere nenhuma informação.
    - NÃO adicione saudações, opiniões ou texto extra não solicitado.
    - Se a string contiver uma lista de itens, formate-os como uma lista com marcadores ou de forma narrativa clara.
    - Se for um valor único (como uma contagem), apresente-o em uma frase curta e direta.
    - Se a lista estiver vazia ("[]"), diga que a consulta não retornou resultados.
    - Se um valor for 'None' (Python) ou 'NULL' (SQL), represente-o como '(não informado)' ou '(vazio)'.
    - Se encontrar representações de datas ou horas (ex: "datetime.date(YYYY, MM, DD)"), formate-as como "DD/MM/YYYY".
    - Não mencione o esquema do banco (<SCHEMA>) ou a query SQL (<SQL>) na sua resposta final.
    Exemplo 1 (Lista de strings):
    
                 String de Dados Brutos: "[('Vendas',), ('Marketing',), ('Engenharia',)]"
                Sua Saída Formatada:
                Os dados encontrados foram:
                - Vendas
                - Marketing
                - Engenharia

                Exemplo 2 (Valor único numérico):
                String de Dados Brutos: "[(55,)]"
                Sua Saída Formatada:
                O resultado da consulta é: 55

                Exemplo 3 (Lista vazia):
                String de Dados Brutos: "[]"
                Sua Saída Formatada:
                A consulta não retornou resultados.

                Exemplo 4 (Múltiplos tipos de dados, incluindo data e None):
                String de Dados Brutos: "[('Ana Silva', 30, datetime.date(2023, 10, 5), None), ('Carlos Souza', 250.75, datetime.date(2022, 3, 1), 'Ativo')]"
                Sua Saída Formatada:
                Os dados encontrados foram:
                - Registro 1: Ana Silva, 30, 05/10/2023, (não informado)
                - Registro 2: Carlos Souza, 250.75, 01/03/2022, Ativo
                
                Exemplo 5 (Lista com múltiplos campos por item, como no seu caso):
                String de Dados Brutos: "[('Lucas Silva', 'CL01'), ('Julia Costa', 'CL02'), ('Roberto Lima', 'CL03'), ('Fernanda Rocha', 'CL04'), ('Paula Mendes', 'CL05')]"
                Sua Saída Formatada:
                Os nomes dos clientes e seus respectivos IDs são:
                - Lucas Silva, ID: CL01
                - Julia Costa, ID: CL02
                - Roberto Lima, ID: CL03
                - Fernanda Rocha, ID: CL04
                - Paula Mendes, ID: CL05
                
                Caso a resposta do seja maior do que 5 siga o esquema de formatação dos exemplos anteriores
                Nunca altere independete da quantidade de resultados obtidos.

    <SCHEMA>{schema}</SCHEMA>

    Pergunta Original do Usuário: {question}
    Consulta SQL Executada: <SQL>{query}</SQL>
    String de Dados Brutos: {dados_brutos}
    
    Sua Saída Formatada (responda em português):
    """
   
    prompt_formatador = PromptTemplate(
        input_variables=["schema", "question", "query", "dados_brutos"], 
        template=template_formatador
    )
    llm = ChatGroq(model=LLM_MODEL_NAME, temperature=0)
    cadeia_formatadora = prompt_formatador | llm | StrOutputParser()
    
    
    return cadeia_formatadora.invoke({
        "schema": db_schema,
        "question": user_question,
        "query": sql_query,
        "dados_brutos": sql_data_str
    })


st.set_page_config(
    page_title="Consultor de Banco de Dados",
    page_icon="🗃️",
    layout="wide"
)


st.title("🗃️ Consultor de Banco de Dados")
st.markdown("Trabalho de banco de dados text-to-sql")
st.write("Bruno Gutierres Mattarazzo de Souza")


col1, col2 = st.columns(2)


with col1:
    st.header("Sua Pergunta")

    db_selection = st.selectbox(
        "1. Selecione o Banco de Dados:",
        ("MySQL", "PostgreSQL")
    )

    db = None
    lista_tabelas = []
    try:
        if db_selection == "MySQL":
            db_uri = os.getenv("MYSQL_URI")
            query_tabelas = "SHOW TABLES;"
        elif db_selection == "PostgreSQL":
            db_uri = os.getenv("POSTGRES_URI")
            query_tabelas = "SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema';"
        
        if db_uri:
            db = SQLDatabase.from_uri(db_uri)
            st.info(f"Conectado com sucesso ao banco {db_selection}!")
            
            lista_tabelas_bruta = db.run(query_tabelas)
            lista_tabelas = [item[0] for item in ast.literal_eval(lista_tabelas_bruta)]
        else:
            st.warning(f"URI para {db_selection} não encontrada. Verifique o arquivo .env.")

    except Exception as e:
        lista_tabelas = []
        st.error(f"Não foi possível conectar ao banco {db_selection}. Erro: {e}")

    with st.expander("Clique para ver as tabelas encontradas no banco de dados"):
        if lista_tabelas:
            tabelas_formatadas = "\n".join([f"- `{tabela}`" for tabela in lista_tabelas])
            st.markdown(tabelas_formatadas)
        else:
            st.write("Nenhuma tabela foi encontrada ou a conexão falhou.")

    user_question = st.text_area(
        "2. Digite sua pergunta aqui:",
        height=200,
        placeholder="Ex: Liste os nomes de todos os clientes e suas cidades."
    )

    execute_button = st.button("Executar Consulta")


with col2:
    st.header("Resultados da Consulta")

    if execute_button:
        if not user_question:
            st.warning("Por favor, digite uma pergunta para continuar.")
        elif not db:
            st.error("A conexão com o banco de dados não foi estabelecida. Verifique as configurações na coluna da esquerda.")
        else:
            try:
                with st.spinner(f"Gerando a consulta SQL para o {db_selection}..."):
                    sql_chain_runnable = get_sql_chain(db)
                    sql_gerado = sql_chain_runnable.invoke({
                        "question": user_question,
                        "chat_history": [] 
                    })

                sql_limpo = sql_gerado.strip()
                if sql_limpo.startswith("```sql"):
                    sql_limpo = sql_limpo[len("```sql"):].strip()
                if sql_limpo.startswith("```"):
                    sql_limpo = sql_limpo[len("```"):].strip()
                if sql_limpo.endswith("```"):
                    sql_limpo = sql_limpo[:-len("```")].strip()
                sql_limpo = sql_limpo.strip()
                if (sql_limpo.startswith("'") and sql_limpo.endswith("'")) or \
                   (sql_limpo.startswith('"') and sql_limpo.endswith('"')):
                    sql_limpo = sql_limpo[1:-1]
                
                sql_gerado_final = sql_limpo

                if not sql_gerado_final.strip() or not sql_gerado_final.strip().upper().startswith(("SELECT", "SHOW", "DESCRIBE", "WITH")):
                    st.error(f"A IA não conseguiu gerar uma consulta SQL válida. Tentativa: '{sql_gerado_final}'")
                else:
                    with st.spinner(f"Executando a consulta no {db_selection}..."):
                        dados_brutos_str = db.run(sql_gerado_final)

                    st.success("Consulta finalizada!")

                    with st.spinner("Formatando a resposta..."):
                        
                        texto_formatado = formatar_resposta_ia(
                            db_schema=db.get_table_info(),
                            user_question=user_question,
                            sql_query=sql_gerado_final,
                            sql_data_str=dados_brutos_str
                        )
                    
                    tab_formatada, tab_dados, tab_sql = st.tabs(["💡 Resposta Formatada", "📊 Dados em Tabela", "🔍 SQL Gerado"])

                    with tab_formatada:
                        st.markdown(texto_formatado)
                    
                    with tab_dados:
                        st.markdown("#### Dados retornados diretamente do banco de dados:")
                        try:
                            dados_brutos_lista = ast.literal_eval(dados_brutos_str)
                            if dados_brutos_lista:
                                match = re.search(r"SELECT(.*?)FROM", sql_gerado_final, re.IGNORECASE | re.DOTALL)
                                if match:
                                    colunas_str_match = match.group(1).strip()
                                    nomes_colunas_finais = [p.strip().replace('`', '').split('.')[-1] for p in colunas_str_match.split(',')]
                                else:
                                    nomes_colunas_finais = None
                                df = pd.DataFrame(dados_brutos_lista, columns=nomes_colunas_finais)
                                st.dataframe(df, use_container_width=True)
                            else:
                                st.info("A consulta foi executada, mas não retornou nenhum dado.")
                        except Exception as e:
                            st.warning(f"Não foi possível formatar os dados em tabela (Erro: {e}). Exibindo resultado bruto:")
                            st.code(dados_brutos_str)

                    with tab_sql:
                        st.code(sql_gerado_final, language="sql")
            
            except Exception as e:
                error_message = str(e)
                if "1146" in error_message and "doesn't exist" in error_message:
                    st.error("❌ Erro de Consulta: A tabela que você pediu não foi encontrada no banco de dados.")
                else:
                    st.error(f"Ocorreu um erro fatal durante a execução: {e}")
    else:
        st.info("Aguardando sua pergunta.")