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
