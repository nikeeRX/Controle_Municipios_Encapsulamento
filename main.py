
Gemini
Nova conversa
Pesquisar conversas
Biblioteca
Novo notebook
BarberCtrl: Guia Completo de Funcionalidades e Gestão de Barbearias
Manual de Operação: Sistema de Impacto de Reajuste de Prestadores
Sistema de Gestão de Negociações de Saúde
Sistema de Controle Pizzaria com Python
E-mail de Análise de Rede Athena Saúde
Associação Pode Vender Bebidas e Alimentação?
Combinando Roupas: Dicas de Estilo
Telha Frankfurter Pfanne em Brasília
Ração para Gatos: Chanin vs. Golden/Gran Plus
Mapeamento de Especialidades Médicas: Amil x Postal
Automação WhatsApp Pizzaria: Pedidos e Reservas
Dúvidas sobre Hospedagem e Preços
Sistema de Gestão de Demandas e Alertas
Criação de Escopo para Melhorias e Plano
Sistema de Mercearia com Código de Barras
Solicitação de Apoio Técnico Amil
PC Reiniciando: Diagnóstico e Soluções
Texto Formalizado e Claro
Música com Voz e Ritmo
Solicitação e Resumo de Documento
Conversor TXT e CSV para Parquet
Mapeamento e Lógica de Código de Impacto
Benner Saúde: Consultando Tabelas SQL
Sistema de Cálculo de Contas de Luz
PDF para Word: Estrutura Preservada
Criação de Sistemas: Arquitetura e Código
Combinando Camisa Vinho e Azul
Nome e Logo para Gestão de Bares
Formalização de Viagem para Alinhamento
Conversão de PDF para Excel
Diagnóstico Rede Unimed CNU: Análise e Recomendações
Cruzamento de Dados e Tabelas
Sistema de Oficina: Ordem de Serviço
Erro no Streamlit: Falta de Informação
Preenchimento de Planilha com Dados PDF
MANO Agora eu tenho um super desafio pra gente, como vi q conseguimos fazer o executável para ler arquivos sacou... tenho um sistema aqui em streamlit onde só que tem acesso é quem está na rede, então quero mudar isso sacou ? quero construir um executável para que todas as regionais tenham acesso a esse Sistema de Impacto de Reajuste de Prestadores - GERED e quero por minha logo nele... aquela que criamos e escolhi... ai teremos que pensar em alguns detalhes... pois o sistema tem uma gama de arquivos muito grande, são bases de faturamento, prestadores, materiais perfurocortantes, dietas e de faixa de eventos... onde ficam no diretório da empresa, porém no executável não poderá ser desse jeito, teremos que pensar em algo que seja atualizável sacou ? por exemplo: se eu subir todos os arquivos de uma vez para o sistema, no outro mes terei q atualizar... como faço para atualizar o sistema pra geral ? tem alguma solução hahahah ? pensa ai e me avisa qd posso mandar os arquivos .py para vc analisar tudo
Conversa com o Gemini
meu mano blz ? então... estou em um projeto no meu trampo, e preciso ter o controle de alguns municipios e regiões de saúde q estamos negociando sacou ? então quero construir um sistema com banco de dados no railway, códigos no git hub bem simples em python tudo blz ? onde vou ter as planilhas em um modelo padrão no qual são essas as colunas e e receberão as informações no formato string sacou ? no print ai... Ai sempre q tiver uma dessas planilhas preenchidas, teremos um campo para fazer o upload desse arquivo sacou ? vai ficar armazenado no banco... e alguns campos de busca... para filtro de todas as colunas q quisermos e uma tabela abaixo mostrando todas as colunas sacou ?

Fala, meu mano! Beleza?

Ideia excelente e super útil para o seu trampo. Organizar essas negociações de redes e regiões de saúde em um banco de dados vai te poupar muita dor de cabeça com planilhas perdidas.

Como a ideia é fazer tudo em Python, usar o GitHub para o código e o Railway para o banco, o caminho mais rápido e eficiente é construir a interface usando o Streamlit. Ele é perfeito para criar esse upload de arquivos, integrar com o banco e já gerar os filtros na tela sem você precisar escrever uma linha de HTML ou JavaScript.

Aqui está o passo a passo e o código completo de como estruturar esse sistema.

1. Preparando o Banco no Railway
Entre no Railway, crie um novo projeto e adicione um PostgreSQL.

Vá na aba "Connect" do seu banco no Railway e copie a Postgres Connection URL (vai ser algo como postgresql://postgres:senha@host:porta/railway).

2. Estrutura do Projeto
No seu computador (e no GitHub), você vai precisar de dois arquivos básicos:

app.py (O código do sistema)

requirements.txt (As bibliotecas que o sistema precisa)

Seu requirements.txt deve ter:

Plaintext
streamlit
pandas
sqlalchemy
psycopg2-binary
openpyxl
3. O Código do Sistema (app.py)
Esse código já cria a tela de upload, garante que tudo suba como string (texto), salva no banco PostgreSQL e cria a tabela com filtros logo abaixo.

Python
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# 1. Configuração da Página
st.set_page_config(page_title="Controle de Negociações - Redes", layout="wide")

# 2. Conexão com o Banco de Dados (Substitua pela URL do seu Railway localmente ou use st.secrets)
# DICA: No Railway/GitHub, é melhor usar variáveis de ambiente, mas para testar, cole a URL aqui.
DATABASE_URL = "SUA_URL_DO_RAILWAY_AQUI" 
engine = create_engine(DATABASE_URL)

st.title("📊 Gestão de Redes e Regiões de Saúde")
st.write("Sistema para controle e negociação de municípios.")

st.divider()

# ==========================================
# SEÇÃO 1: UPLOAD DA PLANILHA
# ==========================================
st.header("📁 Upload de Nova Planilha")
uploaded_file = st.file_uploader("Suba a planilha padrão (Excel ou CSV)", type=["xlsx", "csv"])

# Colunas que o sistema espera encontrar (exatamente como no seu print)
colunas_padrao = ['UF', 'IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE']

if uploaded_file is not None:
    try:
        # Lendo o arquivo e forçando TUDO a ser string (dtype=str) como você pediu
        if uploaded_file.name.endswith('.csv'):
            df_novo = pd.read_csv(uploaded_file, dtype=str)
        else:
            df_novo = pd.read_excel(uploaded_file, dtype=str)

        # Verifica se as colunas da planilha batem com o padrão
        if all(col in df_novo.columns for col in colunas_padrao):
            st.success("Planilha validada com sucesso! Clique abaixo para salvar.")
            
            if st.button("Salvar no Banco de Dados"):
                # Filtra apenas as colunas de interesse para evitar sujeira
                df_salvar = df_novo[colunas_padrao]
                
                # Envia para o banco de dados (tabela 'negociacoes')
                df_salvar.to_sql('negociacoes', engine, if_exists='append', index=False)
                st.success("✅ Dados inseridos no banco com sucesso!")
        else:
            st.error(f"Erro: A planilha deve conter exatamente as colunas: {', '.join(colunas_padrao)}")
            
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}")

st.divider()

# ==========================================
# SEÇÃO 2: FILTROS E TABELA GERAL
# ==========================================
st.header("🔍 Consulta de Municípios Negociados")

try:
    # Puxa os dados atualizados do banco
    df_banco = pd.read_sql("SELECT * FROM negociacoes", engine)
    
    if not df_banco.empty:
        # Criando colunas lado a lado para os filtros
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            filtro_uf = st.multiselect("Filtrar por UF", options=df_banco['UF'].dropna().unique())
        with col2:
            filtro_ibge = st.text_input("Buscar por IBGE")
        with col3:
            filtro_municipio = st.text_input("Buscar por Município")
        with col4:
            filtro_regiao = st.multiselect("Região de Saúde", options=df_banco['REGIAO_DE_SAUDE'].dropna().unique())
        with col5:
            filtro_rede = st.multiselect("Filtrar por Rede", options=df_banco['REDE'].dropna().unique())

        # Aplicando a lógica de filtro
        df_filtrado = df_banco.copy()
        
        if filtro_uf:
            df_filtrado = df_filtrado[df_filtrado['UF'].isin(filtro_uf)]
        if filtro_ibge:
            df_filtrado = df_filtrado[df_filtrado['IBGE'].str.contains(filtro_ibge, case=False, na=False)]
        if filtro_municipio:
            df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(filtro_municipio, case=False, na=False)]
        if filtro_regiao:
            df_filtrado = df_filtrado[df_filtrado['REGIAO_DE_SAUDE'].isin(filtro_regiao)]
        if filtro_rede:
            df_filtrado = df_filtrado[df_filtrado['REDE'].isin(filtro_rede)]

        # Mostrando a tabela na tela
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
        
        # Métrica rápida de quantos registros existem na busca
        st.caption(f"Total de registros encontrados: {len(df_filtrado)}")
    else:
        st.info("O banco de dados está vazio. Faça o upload da primeira planilha acima.")

except Exception as e:
    st.warning("Ainda não há dados no banco ou houve uma falha de conexão. Suba uma planilha para criar a tabela.")
Dicas para rodar e botar em produção:
Para testar localmente: No seu terminal, instale as libs (pip install -r requirements.txt) e rode o comando: streamlit run app.py. O sistema vai abrir direto no seu navegador.

O Segredo da Segurança: No código acima, tem o espaço DATABASE_URL = "...". Quando você for mandar isso pro GitHub (para não expor a senha do seu banco do Railway), substitua isso por:

Python
DATABASE_URL = st.secrets["DATABASE_URL"]
Hospedando (Deploy): Como você vai jogar os códigos no GitHub, você pode hospedar o próprio Streamlit dentro do Railway de graça vinculando o repositório, ou usar o Streamlit Community Cloud (que lê direto do GitHub com 2 cliques).

Basta criar as planilhas seguindo o modelo do seu print e jogar no sistema. Qualquer dúvida na hora de rodar ou cruzar essas informações depois, é só mandar, meu mano!

mano n precisa de streamlit... vamos fazer full python

Entendi o recado, meu mano! Se a ideia é fazer algo "Full Python" raiz, sem depender de frameworks web para interface, nós vamos criar um sistema de terminal (CLI - Command Line Interface) interativo.

Você vai rodar o script no seu terminal, e ele vai te dar um menu com opções para digitar o caminho da planilha (o seu "upload") e fazer as buscas direto pelo teclado. É um código extremamente leve, perfeito para rodar na sua máquina e integrar com o banco no Railway.

Aqui está o mapa do que vamos fazer.

1. Bibliotecas necessárias (requirements.txt)
Você vai precisar de menos coisas agora. Crie o arquivo e coloque:

Plaintext
pandas
sqlalchemy
psycopg2-binary
openpyxl
2. O Código do Sistema (main.py)
Esse script vai conectar no seu Railway, ler a planilha localmente (forçando tudo para string), jogar no banco de dados e ter um menu de busca interativo.

Python
import pandas as pd
from sqlalchemy import create_engine
import sys

# ==========================================
# 1. CONFIGURAÇÃO DO BANCO DE DADOS
# ==========================================
# Substitua pela sua URL do PostgreSQL no Railway
DATABASE_URL = "postgresql://usuario:senha@host:porta/banco_de_dados" 

try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    print(f"❌ Erro ao conectar no banco: {e}")
    sys.exit()

COLUNAS_PADRAO = ['UF', 'IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE']

# ==========================================
# 2. FUNÇÃO DE "UPLOAD" (INSERIR PLANILHA)
# ==========================================
def inserir_planilha():
    print("\n--- 📁 UPLOAD DE PLANILHA ---")
    caminho_arquivo = input("Digite o caminho completo do arquivo (.xlsx ou .csv): ").strip()
    
    # Remove aspas caso você arraste o arquivo para o terminal
    caminho_arquivo = caminho_arquivo.replace('"', '').replace("'", "")

    try:
        if caminho_arquivo.endswith('.csv'):
            df_novo = pd.read_csv(caminho_arquivo, dtype=str)
        elif caminho_arquivo.endswith('.xlsx'):
            df_novo = pd.read_excel(caminho_arquivo, dtype=str)
        else:
            print("❌ Formato inválido! Use .csv ou .xlsx")
            return

        # Validação das colunas
        if all(col in df_novo.columns for col in COLUNAS_PADRAO):
            df_salvar = df_novo[COLUNAS_PADRAO] # Filtra só as colunas que importam
            
            print("⏳ Salvando no banco de dados...")
            df_salvar.to_sql('negociacoes', engine, if_exists='append', index=False)
            print(f"✅ Sucesso! {len(df_salvar)} linhas foram inseridas no banco.")
        else:
            print(f"❌ Erro: A planilha precisa ter exatamente estas colunas: {COLUNAS_PADRAO}")

    except FileNotFoundError:
        print("❌ Erro: Arquivo não encontrado. Verifique o caminho digitado.")
    except Exception as e:
        print(f"❌ Erro inesperado ao processar: {e}")

# ==========================================
# 3. FUNÇÃO DE BUSCA E FILTROS
# ==========================================
def buscar_dados():
    print("\n--- 🔍 BUSCA DE MUNICÍPIOS ---")
    try:
        # Puxa os dados do banco
        df_banco = pd.read_sql("SELECT * FROM negociacoes", engine)
        
        if df_banco.empty:
            print("⚠️ O banco está vazio. Faça o upload de uma planilha primeiro.")
            return

        print("Deixe o campo em branco e aperte ENTER se não quiser filtrar por ele.")
        
        filtro_uf = input("Filtrar por UF (ex: SP): ").strip().upper()
        filtro_ibge = input("Filtrar por IBGE: ").strip()
        filtro_municipio = input("Filtrar por Município: ").strip()
        filtro_rede = input("Filtrar por Rede: ").strip()

        # Aplicando os filtros sequencialmente
        df_filtrado = df_banco.copy()
        
        if filtro_uf:
            df_filtrado = df_filtrado[df_filtrado['UF'] == filtro_uf]
        if filtro_ibge:
            df_filtrado = df_filtrado[df_filtrado['IBGE'].str.contains(filtro_ibge, na=False)]
        if filtro_municipio:
            # case=False faz a busca ignorar maiúsculas/minúsculas
            df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(filtro_municipio, case=False, na=False)]
        if filtro_rede:
            df_filtrado = df_filtrado[df_filtrado['REDE'].str.contains(filtro_rede, case=False, na=False)]

        print("\n" + "="*50)
        print(f"📊 RESULTADOS ENCONTRADOS: {len(df_filtrado)}")
        print("="*50)
        
        if not df_filtrado.empty:
            # Exibe a tabela no terminal de forma organizada
            print(df_filtrado.to_string(index=False))
        else:
            print("Nenhum registro bateu com seus filtros.")

    except Exception as e:
        print(f"❌ Erro ao consultar o banco: {e}")

# ==========================================
# 4. MENU PRINCIPAL
# ==========================================
def menu():
    while True:
        print("\n" + "="*30)
        print("🏢 SISTEMA DE NEGOCIAÇÕES")
        print("="*30)
        print("[ 1 ] Subir nova planilha")
        print("[ 2 ] Consultar e filtrar dados")
        print("[ 3 ] Sair do sistema")
        print("="*30)
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            inserir_planilha()
        elif opcao == '2':
            buscar_dados()
        elif opcao == '3':
            print("Saindo... Valeu, mano!")
            break
        else:
            print("❌ Opção inválida. Tente novamente.")

if __name__ == "__main__":
    menu()
Como usar no seu dia a dia:
Instale as dependências: Abra o terminal na pasta do projeto e rode pip install -r requirements.txt.

Ajuste o Banco: Coloque a URL de conexão do Railway na variável DATABASE_URL lá no topo do código.

Rode o script: Digite python main.py no terminal.

"Upload": Quando você escolher a opção [ 1 ], o sistema vai pedir o caminho do arquivo. Basta você arrastar a sua planilha do Windows Explorer/Finder para dentro do terminal que ele copia o caminho sozinho, ou você digita manualmente (ex: C:/Users/seu_usuario/Downloads/planilha_saude.xlsx).

Assim você tem 100% de controle, tudo feito em Python puro, e os dados ficam centralizados e seguros lá no seu banco de dados do Railway para consultar a qualquer momento. Se quiser que eu te mostre como ocultar essa senha do banco de dados antes de jogar o código no GitHub, é só avisar!

esse da esquerda mano pdc ? ele é o q já fiz o banco sacou... bora bora

Pode crer, meu mano! Massa demais que o banco no Railway já tá no esquema. Bora acelerar isso aí!

Esse script rodando liso no terminal vai agilizar bastante a construção do diagnóstico situacional do compartilhamento de redes, facilitando muito o controle das informações quando você for mapear os municípios de GO, MS, MT, PR, RS, SC e TO.

Como você já preparou a base e o foco é fazer aquele cruzamento de dados inteligente pelo terminal, atualizei o código. Nele, já inseri as Flags de Ano e Competência antes de enviar os dados, e a coluna UF (essa mesma da esquerda do seu print) é preenchida automaticamente durante o cruzamento, direto pelo teclado. E fica tranquilo: o código roda direto na sua máquina, sem pedir privilégios de administrador que possam travar no PC do trampo.

Aqui está o código completo para você rodar:

Python
import pandas as pd
from sqlalchemy import create_engine
import sys

# ==========================================
# 1. CONFIGURAÇÃO DO BANCO DE DADOS
# ==========================================
# Substitua pela sua URL do Railway
DATABASE_URL = "postgresql://usuario:senha@host:porta/banco_de_dados" 

try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    print(f"❌ Erro ao conectar no banco: {e}")
    sys.exit()

# ==========================================
# 2. CRUZAMENTO E UPLOAD DE DADOS
# ==========================================
def cruzar_e_inserir():
    print("\n--- ⚙️ UPLOAD E CRUZAMENTO DE PLANILHA ---")
    caminho = input("Arraste a planilha ou digite o caminho (.xlsx/.csv): ").strip().replace('"', '').replace("'", "")
    
    try:
        if caminho.endswith('.csv'):
            df = pd.read_csv(caminho, dtype=str)
        elif caminho.endswith('.xlsx'):
            df = pd.read_excel(caminho, dtype=str)
        else:
            print("❌ Formato inválido! Use .csv ou .xlsx")
            return

        print("\n--- 🚩 FLAGS DE CRUZAMENTO ---")
        ano_flag = input("Escolha o Ano (ex: 2026): ").strip()
        comp_flag = input("Digite a Competência: ").strip()
        
        # Preenchendo a UF da esquerda no momento do cruzamento
        uf_input = input("Digite a UF para preencher no cruzamento (ex: GO, PR, SC): ").strip().upper()

        # Atribuindo as flags e a UF ao DataFrame
        df['ANO'] = ano_flag
        df['COMPETENCIA'] = comp_flag
        df['UF'] = uf_input 

        # Colunas esperadas para salvar no banco
        colunas_finais = ['UF', 'IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE', 'ANO', 'COMPETENCIA']
        colunas_basicas = ['IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE']

        # Valida se a planilha tem o básico antes de prosseguir
        if all(col in df.columns for col in colunas_basicas):
            df_salvar = df[colunas_finais]
            
            print("\n⏳ Subindo os dados cruzados para o Railway...")
            df_salvar.to_sql('negociacoes', engine, if_exists='append', index=False)
            print(f"✅ Sucesso, mano! {len(df_salvar)} linhas inseridas no banco.")
        else:
            print(f"❌ Erro: A planilha original precisa ter pelo menos estas colunas: {colunas_basicas}")

    except Exception as e:
        print(f"❌ Erro ao processar o arquivo: {e}")

# ==========================================
# 3. BUSCA NO BANCO
# ==========================================
def buscar_dados():
    print("\n--- 🔍 CONSULTA DE MUNICÍPIOS ---")
    try:
        df_banco = pd.read_sql("SELECT * FROM negociacoes", engine)
        
        if df_banco.empty:
            print("⚠️ O banco está vazio. Faça o upload primeiro.")
            return

        print("Pressione ENTER para pular um filtro.")
        filtro_uf = input("Filtrar por UF: ").strip().upper()
        filtro_municipio = input("Filtrar por Município: ").strip()
        filtro_ano = input("Filtrar por Ano: ").strip()

        df_filtrado = df_banco.copy()
        
        if filtro_uf:
            df_filtrado = df_filtrado[df_filtrado['UF'] == filtro_uf]
        if filtro_municipio:
            df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(filtro_municipio, case=False, na=False)]
        if filtro_ano:
            df_filtrado = df_filtrado[df_filtrado['ANO'] == filtro_ano]

        print("\n" + "="*60)
        print(f"📊 RESULTADOS ENCONTRADOS: {len(df_filtrado)}")
        print("="*60)
        
        if not df_filtrado.empty:
            print(df_filtrado.to_string(index=False))
        else:
            print("Nenhum dado encontrado com esses filtros.")

    except Exception as e:
        print(f"❌ Erro ao buscar no banco: {e}")

# ==========================================
# 4. MENU
# ==========================================
def menu():
    while True:
        print("\n" + "="*40)
        print("🏢 GESTÃO DE REDES DE SAÚDE")
        print("="*40)
        print("[ 1 ] Fazer Upload e Cruzamento")
        print("[ 2 ] Consultar Banco de Dados")
        print("[ 3 ] Sair")
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            cruzar_e_inserir()
        elif opcao == '2':
            buscar_dados()
        elif opcao == '3':
            print("Valeu, mano! Até a próxima.")
            break
        else:
            print("❌ Opção inválida.")

if __name__ == "__main__":
    menu()
Você quer que eu adicione uma função nesse menu para exportar os resultados dos filtros de volta para uma planilha Excel, ou apenas visualizar a tabela no terminal já resolve para as negociações?

quero exportar tbm a tabela escolhida

Seu script atualizado em Python está pronto!
Ícone do app PY
main
PY

Feito, meu mano! Coloquei a funcionalidade de exportação embutida direto na função de consulta (buscar_dados).

Agora, assim que o sistema terminar de cruzar os filtros (como UF, município ou ano) e exibir a tabela no terminal, ele vai te perguntar:

📥 Deseja exportar essa tabela filtrada para Excel? (S/N):

Se você apertar S, ele te dá a opção de digitar o nome do arquivo que você quer gerar (ou é só apertar ENTER que ele salva automaticamente como resultado_busca.xlsx na mesma pasta do código).

Ele já exporta no formato .xlsx usando o openpyxl (que já estava nos requisitos que te passei), mantendo todos os formatos cruzados para você anexar nos documentos ou e-mails do trampo.

Basta baixar o arquivo main.py acima, atualizar a variável DATABASE_URL lá no topo com os dados do seu Railway, e rodar o código de novo. Qualquer outra adaptação que precisar, é só dar o grito!




O Gemini é uma IA e pode cometer erros.

import pandas as pd
from sqlalchemy import create_engine
import sys

# ==========================================
# 1. CONFIGURAÇÃO DO BANCO DE DADOS
# ==========================================
# Substitua pela sua URL do Railway
DATABASE_URL = "postgresql://usuario:senha@host:porta/banco_de_dados" 

try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    print(f"❌ Erro ao conectar no banco: {e}")
    sys.exit()

# ==========================================
# 2. CRUZAMENTO E UPLOAD DE DADOS
# ==========================================
def cruzar_e_inserir():
    print("\n--- ⚙️ UPLOAD E CRUZAMENTO DE PLANILHA ---")
    caminho = input("Arraste a planilha ou digite o caminho (.xlsx/.csv): ").strip().replace('"', '').replace("'", "")
    
    try:
        if caminho.endswith('.csv'):
            df = pd.read_csv(caminho, dtype=str)
        elif caminho.endswith('.xlsx'):
            df = pd.read_excel(caminho, dtype=str)
        else:
            print("❌ Formato inválido! Use .csv ou .xlsx")
            return

        print("\n--- 🚩 FLAGS DE CRUZAMENTO ---")
        ano_flag = input("Escolha o Ano (ex: 2026): ").strip()
        comp_flag = input("Digite a Competência: ").strip()
        
        # Preenchendo a UF da esquerda no momento do cruzamento
        uf_input = input("Digite a UF para preencher no cruzamento (ex: GO, PR, SC): ").strip().upper()

        # Atribuindo as flags e a UF ao DataFrame
        df['ANO'] = ano_flag
        df['COMPETENCIA'] = comp_flag
        df['UF'] = uf_input 

        # Colunas esperadas para salvar no banco
        colunas_finais = ['UF', 'IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE', 'ANO', 'COMPETENCIA']
        colunas_basicas = ['IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE']

        # Valida se a planilha tem o básico antes de prosseguir
        if all(col in df.columns for col in colunas_basicas):
            df_salvar = df[colunas_finais]
            
            print("\n⏳ Subindo os dados cruzados para o Railway...")
            df_salvar.to_sql('negociacoes', engine, if_exists='append', index=False)
            print(f"✅ Sucesso, mano! {len(df_salvar)} linhas inseridas no banco.")
        else:
            print(f"❌ Erro: A planilha original precisa ter pelo menos estas colunas: {colunas_basicas}")

    except Exception as e:
        print(f"❌ Erro ao processar o arquivo: {e}")

# ==========================================
# 3. BUSCA NO BANCO E EXPORTAÇÃO
# ==========================================
def buscar_dados():
    print("\n--- 🔍 CONSULTA DE MUNICÍPIOS ---")
    try:
        df_banco = pd.read_sql("SELECT * FROM negociacoes", engine)
        
        if df_banco.empty:
            print("⚠️ O banco está vazio. Faça o upload primeiro.")
            return

        print("Pressione ENTER para pular um filtro.")
        filtro_uf = input("Filtrar por UF: ").strip().upper()
        filtro_municipio = input("Filtrar por Município: ").strip()
        filtro_ano = input("Filtrar por Ano: ").strip()

        df_filtrado = df_banco.copy()
        
        if filtro_uf:
            df_filtrado = df_filtrado[df_filtrado['UF'] == filtro_uf]
        if filtro_municipio:
            df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(filtro_municipio, case=False, na=False)]
        if filtro_ano:
            df_filtrado = df_filtrado[df_filtrado['ANO'] == filtro_ano]

        print("\n" + "="*60)
        print(f"📊 RESULTADOS ENCONTRADOS: {len(df_filtrado)}")
        print("="*60)
        
        if not df_filtrado.empty:
            print(df_filtrado.to_string(index=False))
            
            # --- NOVA FUNCIONALIDADE DE EXPORTAÇÃO ---
            print("\n" + "-"*40)
            exportar = input("📥 Deseja exportar essa tabela filtrada para Excel? (S/N): ").strip().upper()
            
            if exportar == 'S':
                nome_arquivo = input("Digite o nome do arquivo (ou ENTER para 'resultado_busca.xlsx'): ").strip()
                if not nome_arquivo:
                    nome_arquivo = "resultado_busca.xlsx"
                if not nome_arquivo.endswith('.xlsx'):
                    nome_arquivo += '.xlsx'
                
                try:
                    # Exporta garantindo que tudo continue como texto formatado no Excel
                    df_filtrado.to_excel(nome_arquivo, index=False)
                    print(f"✅ Feito! Tabela exportada com sucesso como: {nome_arquivo}")
                except Exception as e:
                    print(f"❌ Erro ao gerar o arquivo Excel: {e}")
        else:
            print("Nenhum dado encontrado com esses filtros.")

    except Exception as e:
        print(f"❌ Erro ao buscar no banco: {e}")

# ==========================================
# 4. MENU PRINCIPAL
# ==========================================
def menu():
    while True:
        print("\n" + "="*40)
        print("🏢 GESTÃO DE REDES DE SAÚDE")
        print("="*40)
        print("[ 1 ] Fazer Upload e Cruzamento")
        print("[ 2 ] Consultar e Exportar Dados")
        print("[ 3 ] Sair")
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            cruzar_e_inserir()
        elif opcao == '2':
            buscar_dados()
        elif opcao == '3':
            print("Valeu, mano! Até a próxima.")
            break
        else:
            print("❌ Opção inválida.")

if __name__ == "__main__":
    menu()
main.py
Exibindo main.py.
