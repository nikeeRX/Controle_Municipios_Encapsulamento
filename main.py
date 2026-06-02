import os
import io
import pandas as pd
from flask import Flask, request, render_template_string, send_file, flash, redirect, url_for
from sqlalchemy import create_engine, text

app = Flask(__name__)
app.secret_key = "chave_super_secreta_sistema_redes"

# ==========================================
# 1. CONFIGURAÇÃO E CRIAÇÃO DO BANCO
# ==========================================
# Substitua pela sua URL do Railway
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:hMNxRensWWNVbiZJuMRBVCawLZfPSQXo@postgres.railway.internal:5432/railway")
engine = create_engine(DATABASE_URL)

def criar_tabelas():
    try:
        with engine.connect() as conn:
            # Força a criação da tabela e colunas caso não existam (Resolve o erro do print!)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS negociacoes (
                    "UF" VARCHAR(10),
                    "IBGE" VARCHAR(50),
                    "MUNICIPIO" VARCHAR(255),
                    "REGIAO_DE_SAUDE" VARCHAR(255),
                    "REDE" VARCHAR(255),
                    "ANO" VARCHAR(10),
                    "COMPETENCIA" VARCHAR(50)
                )
            """))
            conn.commit()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")

criar_tabelas()

# ==========================================
# 2. INTERFACE HTML E CSS
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestão de Redes e Regiões de Saúde</title>
    <style>
        :root {
            --primary: #2c3e50;
            --secondary: #3498db;
            --light: #f4f7f6;
            --success: #27ae60;
            --danger: #e74c3c;
        }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--light); color: #333; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1, h2 { color: var(--primary); border-bottom: 2px solid var(--light); padding-bottom: 10px; }
        
        /* Grid de Formulários */
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; }
        label { font-weight: bold; margin-bottom: 5px; font-size: 14px; color: var(--primary); }
        input, select { padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; }
        input[type="file"] { padding: 7px; }
        
        /* Botões */
        .btn { background-color: var(--secondary); color: white; border: none; padding: 12px 20px; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold; transition: 0.3s; text-decoration: none; display: inline-block; }
        .btn:hover { background-color: #2980b9; }
        .btn-export { background-color: var(--success); margin-top: 15px; }
        .btn-export:hover { background-color: #219653; }
        
        /* Tabelas */
        .table-responsive { overflow-x: auto; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; font-size: 14px; }
        th { background-color: var(--primary); color: white; position: sticky; top: 0; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        
        /* Alertas */
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; color: white; font-weight: bold; }
        .alert.success { background-color: var(--success); }
        .alert.error { background-color: var(--danger); }
        .alert.info { background-color: var(--secondary); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Gestão de Redes e Regiões de Saúde</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert {{ category }}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        <h2>📥 Upload e Cruzamento de Dados</h2>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <div class="form-grid">
                <div class="form-group">
                    <label>Arquivo Planilha (.xlsx ou .csv):</label>
                    <input type="file" name="arquivo" accept=".xlsx, .csv" required>
                </div>
                <div class="form-group">
                    <label>Escolher Ano (Flag):</label>
                    <input type="text" name="ano" placeholder="Ex: 2026" required>
                </div>
                <div class="form-group">
                    <label>Competência (Flag):</label>
                    <input type="text" name="competencia" placeholder="Ex: Maio" required>
                </div>
                <div class="form-group">
                    <label>UF no momento do cruzamento:</label>
                    <input type="text" name="uf" placeholder="Ex: GO, PR, SC" required>
                </div>
            </div>
            <button type="submit" class="btn">Cruzar e Salvar no Banco</button>
        </form>

        <br><br>

        <h2>🔍 Consulta de Municípios Negociados</h2>
        <form action="/" method="GET">
            <div class="form-grid">
                <div class="form-group">
                    <label>Filtrar por UF:</label>
                    <select name="busca_uf">
                        <option value="">Todas as UFs</option>
                        {% for uf in lista_ufs %}
                            <option value="{{ uf }}" {% if request.args.get('busca_uf') == uf %}selected{% endif %}>{{ uf }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>Filtrar por Município:</label>
                    <input type="text" name="busca_municipio" placeholder="Digite o nome..." value="{{ request.args.get('busca_municipio', '') }}">
                </div>
                <div class="form-group">
                    <label>Filtrar por Ano:</label>
                    <select name="busca_ano">
                        <option value="">Todos os Anos</option>
                        {% for ano in lista_anos %}
                            <option value="{{ ano }}" {% if request.args.get('busca_ano') == ano %}selected{% endif %}>{{ ano }}</option>
                        {% endfor %}
                    </select>
                </div>
            </div>
            <button type="submit" class="btn">Aplicar Filtros</button>
            <a href="/" class="btn" style="background-color: #95a5a6;">Limpar</a>
        </form>

        {% if tabela_html %}
            <form action="/exportar" method="POST">
                <input type="hidden" name="busca_uf" value="{{ request.args.get('busca_uf', '') }}">
                <input type="hidden" name="busca_municipio" value="{{ request.args.get('busca_municipio', '') }}">
                <input type="hidden" name="busca_ano" value="{{ request.args.get('busca_ano', '') }}">
                <button type="submit" class="btn btn-export">📥 Exportar Tabela para Excel</button>
            </form>
            
            <p><strong>Resultados encontrados: {{ total_linhas }}</strong></p>
            <div class="table-responsive">
                {{ tabela_html | safe }}
            </div>
        {% else %}
            <div class="alert info" style="margin-top: 20px;">O banco está vazio ou nenhum dado corresponde aos filtros.</div>
        {% endif %}
    </div>
</body>
</html>
"""

# ==========================================
# 3. ROTAS DO SISTEMA
# ==========================================
@app.route("/")
def index():
    lista_ufs = []
    lista_anos = []
    tabela_html = ""
    total_linhas = 0

    try:
        # Puxa os dados para popular os selects
        df_banco = pd.read_sql("SELECT * FROM negociacoes", engine)
        
        if not df_banco.empty:
            lista_ufs = sorted(df_banco['UF'].dropna().unique())
            lista_anos = sorted(df_banco['ANO'].dropna().unique())

            # Pegando os filtros da URL
            busca_uf = request.args.get('busca_uf', '').upper()
            busca_municipio = request.args.get('busca_municipio', '')
            busca_ano = request.args.get('busca_ano', '')

            df_filtrado = df_banco.copy()

            if busca_uf:
                df_filtrado = df_filtrado[df_filtrado['UF'] == busca_uf]
            if busca_municipio:
                df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(busca_municipio, case=False, na=False)]
            if busca_ano:
                df_filtrado = df_filtrado[df_filtrado['ANO'] == busca_ano]

            total_linhas = len(df_filtrado)
            if total_linhas > 0:
                tabela_html = df_filtrado.to_html(index=False, classes="", border=0)

    except Exception as e:
        print(f"Erro ao consultar banco: {e}")

    return render_template_string(
        HTML_TEMPLATE, 
        lista_ufs=lista_ufs, 
        lista_anos=lista_anos, 
        tabela_html=tabela_html, 
        total_linhas=total_linhas
    )


@app.route("/upload", methods=["POST"])
def upload():
    arquivo = request.files.get("arquivo")
    ano_flag = request.form.get("ano", "").strip()
    comp_flag = request.form.get("competencia", "").strip()
    uf_input = request.form.get("uf", "").strip().upper()

    if not arquivo or arquivo.filename == '':
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for("index"))

    try:
        if arquivo.filename.endswith('.csv'):
            df = pd.read_csv(arquivo, dtype=str)
        else:
            df = pd.read_excel(arquivo, dtype=str)

        colunas_basicas = ['IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE']
        colunas_finais = ['UF', 'IBGE', 'MUNICIPIO', 'REGIAO_DE_SAUDE', 'REDE', 'ANO', 'COMPETENCIA']

        # Validando se a planilha tem o padrão
        falta_coluna = [col for col in colunas_basicas if col not in df.columns]
        if falta_coluna:
            flash(f"Erro: Faltam colunas na planilha: {falta_coluna}", "error")
            return redirect(url_for("index"))

        # Inserindo as flags e a UF no DataFrame
        df['ANO'] = ano_flag
        df['COMPETENCIA'] = comp_flag
        df['UF'] = uf_input

        df_salvar = df[colunas_finais]
        
        # Salvando no banco
        df_salvar.to_sql('negociacoes', engine, if_exists='append', index=False)
        flash(f"Sucesso! {len(df_salvar)} linhas foram inseridas no banco.", "success")

    except Exception as e:
        flash(f"Erro ao processar o arquivo: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/exportar", methods=["POST"])
def exportar():
    try:
        # Recupera os mesmos filtros que estavam na tela
        busca_uf = request.form.get('busca_uf', '').upper()
        busca_municipio = request.form.get('busca_municipio', '')
        busca_ano = request.form.get('busca_ano', '')

        df_banco = pd.read_sql("SELECT * FROM negociacoes", engine)
        df_filtrado = df_banco.copy()

        if busca_uf:
            df_filtrado = df_filtrado[df_filtrado['UF'] == busca_uf]
        if busca_municipio:
            df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(busca_municipio, case=False, na=False)]
        if busca_ano:
            df_filtrado = df_filtrado[df_filtrado['ANO'] == busca_ano]

        # Gerando o Excel em memória
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Negociacoes')
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="resultado_busca.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        flash(f"Erro ao gerar Excel: {str(e)}", "error")
        return redirect(url_for("index"))


if __name__ == "__main__":
    # Rodando localmente caso queira testar na sua máquina depois
    app.run(debug=True, port=8000)
