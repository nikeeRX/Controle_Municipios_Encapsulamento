import pandas as pd
from sqlalchemy import create_engine
import sys

# ==========================================
# 1. CONFIGURACAO DO BANCO DE DADOS
# ==========================================
# Substitua pela sua URL do Railway
DATABASE_URL = "postgresql://usuario:senha@host:porta/banco_de_dados" 

try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    print(f"[ERRO] Falha ao conectar no banco: {e}")
    sys.exit()

# ==========================================
# 2. CRUZAMENTO E UPLOAD DE DADOS
# ==========================================
def cruzar_e_inserir():
    print("\n--- UPLOAD E CRUZAMENTO DE PLANILHA ---")
    caminho = input("Arraste a planilha ou digite o caminho (.xlsx/.csv): ").strip().replace('"', '').replace("'", "")
    
    try:
        if caminho.endswith('.csv'):
            df = pd.read_csv(caminho, dtype=str)
        elif caminho.endswith('.xlsx'):
            df = pd.read_excel(caminho, dtype=str)
        else:
            print("[ERRO] Formato invalido! Use .csv ou .xlsx")
            return

        print("\n--- FLAGS DE CRUZAMENTO ---")
        ano_flag = input("Escolha o Ano (ex: 2026): ").strip()
        comp_flag = input("Digite a Competencia: ").strip()
        
        # Preenchendo a UF da esquerda no momento do cruzamento
        uf_input = input("Digite a UF para preencher no cruzamento (ex: GO, PR, SC): ").strip().upper()

        # Atribuindo as flags e a UF ao DataFrame
        df['ANO'] = ano_flag
        df['COMPETENCIA'] = comp_flag
        df['UF'] = uf_input 

        # Colunas esperadas para salvar no banco
        colunas_finais = ['UF', 'IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE', 'ANO', 'COMPETENCIA']
        colunas_basicas = ['IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE']

        # Valida se a planilha tem o basico antes de prosseguir
        if all(col in df.columns for col in colunas_basicas):
            df_salvar = df[colunas_finais]
            
            print("\n[Aguarde] Subindo os dados cruzados para o Railway...")
            df_salvar.to_sql('negociacoes', engine, if_exists='append', index=False)
            print(f"[SUCESSO] {len(df_salvar)} linhas inseridas no banco.")
        else:
            print(f"[ERRO] A planilha original precisa ter pelo menos estas colunas: {colunas_basicas}")

    except Exception as e:
        print(f"[ERRO] Falha ao processar o arquivo: {e}")

# ==========================================
# 3. BUSCA NO BANCO E EXPORTACAO
# ==========================================
def buscar_dados():
    print("\n--- CONSULTA DE MUNICIPIOS ---")
    try:
        df_banco = pd.read_sql("SELECT * FROM negociacoes", engine)
        
        if df_banco.empty:
            print("[AVISO] O banco esta vazio. Faca o upload primeiro.")
            return

        print("Pressione ENTER para pular um filtro.")
        filtro_uf = input("Filtrar por UF: ").strip().upper()
        filtro_municipio = input("Filtrar por Municipio: ").strip()
        filtro_ano = input("Filtrar por Ano: ").strip()

        df_filtrado = df_banco.copy()
        
        if filtro_uf:
            df_filtrado = df_filtrado[df_filtrado['UF'] == filtro_uf]
        if filtro_municipio:
            df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(filtro_municipio, case=False, na=False)]
        if filtro_ano:
            df_filtrado = df_filtrado[df_filtrado['ANO'] == filtro_ano]

        print("\n" + "="*60)
        print(f"RESULTADOS ENCONTRADOS: {len(df_filtrado)}")
        print("="*60)
        
        if not df_filtrado.empty:
            print(df_filtrado.to_string(index=False))
            
            print("\n" + "-"*40)
            exportar = input("Deseja exportar essa tabela filtrada para Excel? (S/N): ").strip().upper()
            
            if exportar == 'S':
                nome_arquivo = input("Digite o nome do arquivo (ou ENTER para 'resultado_busca.xlsx'): ").strip()
                if not nome_arquivo:
                    nome_arquivo = "resultado_busca.xlsx"
                if not nome_arquivo.endswith('.xlsx'):
                    nome_arquivo += '.xlsx'
                
                try:
                    df_filtrado.to_excel(nome_arquivo, index=False)
                    print(f"[SUCESSO] Feito! Tabela exportada com sucesso como: {nome_arquivo}")
                except Exception as e:
                    print(f"[ERRO] Falha ao gerar o arquivo Excel: {e}")
        else:
            print("Nenhum dado encontrado com esses filtros.")

    except Exception as e:
        print(f"[ERRO] Falha ao buscar no banco: {e}")

# ==========================================
# 4. MENU PRINCIPAL
# ==========================================
def menu():
    while True:
        print("\n" + "="*40)
        print("SISTEMA DE GESTAO DE REDES DE SAUDE")
        print("="*40)
        print("[ 1 ] Fazer Upload e Cruzamento")
        print("[ 2 ] Consultar e Exportar Dados")
        print("[ 3 ] Sair")
        
        opcao = input("Escolha uma opcao: ").strip()
        
        if opcao == '1':
            cruzar_e_inserir()
        elif opcao == '2':
            buscar_dados()
        elif opcao == '3':
            print("Valeu, mano! Ate a proxima.")
            break
        else:
            print("[ERRO] Opcao invalida.")

if __name__ == "__main__":
    menu()
