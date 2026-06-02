import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import io

st.set_page_config(page_title="Gestão de Redes de Saúde", layout="wide")

# ==========================================
# 1. CONFIGURAÇÃO DO BANCO DE DADOS
# ==========================================
# Substitua pela sua URL do Railway
DATABASE_URL = "postgresql://usuario:senha@host:porta/banco_de_dados" 

@st.cache_resource
def iniciar_conexao():
    try:
        return create_engine(DATABASE_URL)
    except Exception as e:
        st.error(f"Falha ao conectar no banco: {e}")
        return None

engine = iniciar_conexao()

st.title("🏢 Sistema de Gestão de Redes de Saúde")
st.divider()

# ==========================================
# 2. CRUZAMENTO E UPLOAD DE DADOS
# ==========================================
st.header("⚙️ Upload e Cruzamento de Planilha")

uploaded_file = st.file_uploader("Suba a planilha (.xlsx ou .csv)", type=["xlsx", "csv"])

if uploaded_file is not None:
    # Lendo o arquivo forçando como string
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file, dtype=str)
    else:
        df = pd.read_excel(uploaded_file, dtype=str)

    st.subheader("🚩 Flags de Cruzamento")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ano_flag = st.text_input("Escolha o Ano (ex: 2026)")
    with col2:
        comp_flag = st.text_input("Digite a Competência")
    with col3:
        uf_input = st.text_input("UF para preencher (ex: GO, PR, SC)").upper()

    colunas_basicas = ['IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE']
    colunas_finais = ['UF', 'IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE', 'ANO', 'COMPETENCIA']

    if all(col in df.columns for col in colunas_basicas):
        if st.button("Cruzar e Salvar no Banco"):
            if not ano_flag or not comp_flag or not uf_input:
                st.warning("Preencha todas as Flags (Ano, Competência e UF) antes de salvar!")
            else:
                df['ANO'] = ano_flag
                df['COMPETENCIA'] = comp_flag
                df['UF'] = uf_input 
                
                df_salvar = df[colunas_finais]
                
                try:
                    df_salvar.to_sql('negociacoes', engine, if_exists='append', index=False)
                    st.success(f"✅ Sucesso, mano! {len(df_salvar)} linhas inseridas no banco.")
                except Exception as e:
                    st.error(f"Erro ao salvar no banco: {e}")
    else:
        st.error(f"Erro: A planilha precisa ter pelo menos estas colunas: {colunas_basicas}")

st.divider()

# ==========================================
# 3. BUSCA E EXPORTAÇÃO NO BANCO
# ==========================================
st.header("🔍 Consulta e Exportação")

if engine:
    try:
        df_banco = pd.read_sql("SELECT * FROM negociacoes", engine)
        
        if not df_banco.empty:
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                opcoes_uf = ["Todos"] + list(df_banco['UF'].dropna().unique())
                filtro_uf = st.selectbox("Filtrar por UF", opcoes_uf)
            with col_f2:
                filtro_municipio = st.text_input("Filtrar por Município (digite parte do nome)")
            with col_f3:
                opcoes_ano = ["Todos"] + list(df_banco['ANO'].dropna().unique())
                filtro_ano = st.selectbox("Filtrar por Ano", opcoes_ano)

            # Aplicando filtros
            df_filtrado = df_banco.copy()
            
            if filtro_uf != "Todos":
                df_filtrado = df_filtrado[df_filtrado['UF'] == filtro_uf]
            if filtro_municipio:
                df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(filtro_municipio, case=False, na=False)]
            if filtro_ano != "Todos":
                df_filtrado = df_filtrado[df_filtrado['ANO'] == filtro_ano]

            st.write(f"**Resultados encontrados: {len(df_filtrado)}**")
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
            
            # --- FUNÇÃO DE EXPORTAÇÃO PARA EXCEL ---
            if not df_filtrado.empty:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_filtrado.to_excel(writer, index=False, sheet_name='Resultados')
                
                st.download_button(
                    label="📥 Exportar Tabela para Excel",
                    data=buffer.getvalue(),
                    file_name="resultado_busca.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.info("O banco de dados está vazio. Faça o upload primeiro.")
            
    except Exception as e:
        st.warning(f"Aguardando a criação da tabela no banco ou houve uma falha de conexão: {e}")
