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
# URL interna do Railway configurada
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:hMNxRensWWNVbiZJuMRBVCawLZfPSQXo@postgres.railway.internal:5432/railway")
engine = create_engine(DATABASE_URL)

def criar_tabelas():
    try:
        with engine.connect() as conn:
            # Criando a tabela V2 para se adequar ao novo modelo de importação
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS negociacoes_v2 (
                    "UF" VARCHAR(10),
                    "IBGE" VARCHAR(50),
                    "MUNICIPIO" VARCHAR(255),
                    "REDE" VARCHAR(255),
                    "DATA_VIGENCIA" VARCHAR(50),
                    "ODONTO" VARCHAR(10)
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
        
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; }
        label { font-weight: bold; margin-bottom: 5px; font-size: 14px; color: var(--primary); }
        input, select { padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; }
        input[type="file"] { padding: 7px; }
        
        .btn { background-color: var(--secondary); color: white; border: none; padding: 12px 20px; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold; transition: 0.3s; text-decoration: none; display: inline-block; }
        .btn:hover { background-color: #2980b9; }
        .btn-export { background-color: var(--success); margin-top: 15px; }
        .btn-export:hover { background-color: #219653; }
        
        .table-responsive { overflow-x: auto; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; font-size: 14px; }
        th { background-color: var(--primary); color: white; position: sticky; top: 0; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; color: white; font-weight: bold; }
        .alert.success { background-color: var(--success); }
        .alert.error { background-color: var(--danger); }
        .alert.info { background-color: var(--secondary); }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 Gestão de Redes de Saúde</h1>
        
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
                    <label>Data de Vigência:</label>
                    <input type="date" name="data_vigencia" required>
                </div>
                <div class="form-group">
                    <label>Odonto:</label>
                    <select name="odonto_flag" required>
                        <option value="NÃO">NÃO</option>
                        <option value="SIM">SIM</option>
                    </select>
                </div>
            </div>
            <button type="submit" class="btn">Processar e Salvar</button>
        </form>

        <br><br>

        <h2>🔍 Consulta de Municípios</h2>
        <form action="/" method="GET">
            <div class="form-grid">
                <div class="form-group">
                    <label>UF:</label>
                    <select name="busca_uf">
                        <option value="">Todas</option>
                        {% for uf in lista_ufs %}
                            <option value="{{ uf }}" {% if request.args.get('busca_uf') == uf %}selected{% endif %}>{{ uf }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Município:</label>
                    <input list="municipios_lista" name="busca_municipio" placeholder="Digite para buscar..." value="{{ request.args.get('busca_municipio', '') }}" autocomplete="off">
                    <datalist id="municipios_lista">
                        {% for mun in lista_municipios %}
                            <option value="{{ mun }}">
                        {% endfor %}
                    </datalist>
                </div>

                <div class="form-group">
                    <label>Data de Vigência:</label>
                    <input type="date" name="busca_vigencia" value="{{ request.args.get('busca_vigencia', '') }}">
                </div>
                
                <div class="form-group">
                    <label>Odonto:</label>
                    <select name="busca_odonto">
                        <option value="">Ambos</option>
                        <option value="SIM" {% if request.args.get('busca_odonto') == 'SIM' %}selected{% endif %}>SIM</option>
                        <option value="NÃO" {% if request.args.get('busca_odonto') == 'NÃO' %}selected{% endif %}>NÃO</option>
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
                <input type="hidden" name="busca_vigencia" value="{{ request.args.get('busca_vigencia', '') }}">
                <input type="hidden" name="busca_odonto" value="{{ request.args.get('busca_odonto', '') }}">
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
    lista_municipios = []
    tabela_html = ""
    total_linhas = 0

    try:
        # Lendo da tabela V2
        df_banco = pd.read_sql("SELECT * FROM negociacoes_v2", engine)
        
        if not df_banco.empty:
            lista_ufs = sorted(df_banco['UF'].dropna().unique())
            # Popular o Datalist com todos os municípios do banco
            lista_municipios = sorted(df_banco['MUNICIPIO'].dropna().unique())

            # Resgatando filtros
            busca_uf = request.args.get('busca_uf', '').upper()
            busca_municipio = request.args.get('busca_municipio', '')
            busca_vigencia = request.args.get('busca_vigencia', '')
            busca_odonto = request.args.get('busca_odonto', '')

            df_filtrado = df_banco.copy()

            if busca_uf:
                df_filtrado = df_filtrado[df_filtrado['UF'] == busca_uf]
            if busca_municipio:
                # Filtrando exatamente pelo nome clicado/digitado na lista
                df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(busca_municipio, case=False, na=False)]
            if busca_vigencia:
                df_filtrado = df_filtrado[df_filtrado['DATA_VIGENCIA'] == busca_vigencia]
            if busca_odonto:
                df_filtrado = df_filtrado[df_filtrado['ODONTO'] == busca_odonto]

            total_linhas = len(df_filtrado)
            if total_linhas > 0:
                tabela_html = df_filtrado.to_html(index=False, classes="", border=0)

    except Exception as e:
        print(f"Erro ao consultar banco: {e}")

    return render_template_string(
        HTML_TEMPLATE, 
        lista_ufs=lista_ufs, 
        lista_municipios=lista_municipios,
        tabela_html=tabela_html, 
        total_linhas=total_linhas
    )


@app.route("/upload", methods=["POST"])
def upload():
    arquivo = request.files.get("arquivo")
    data_vigencia = request.form.get("data_vigencia", "").strip()
    odonto_flag = request.form.get("odonto_flag", "").strip()

    if not arquivo or arquivo.filename == '':
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for("index"))

    try:
        if arquivo.filename.endswith('.csv'):
            df = pd.read_csv(arquivo, dtype=str)
        else:
            df = pd.read_excel(arquivo, dtype=str)

        # O novo modelo esperado na planilha
        colunas_basicas = ['UF', 'IBGE', 'MUNICIPIO', 'REDE']
        colunas_finais = ['UF', 'IBGE', 'MUNICIPIO', 'REDE', 'DATA_VIGENCIA', 'ODONTO']

        # Remove a coluna antiga se ela ainda vier perdida na planilha
        if 'REGIAO_DE_SAUDE' in df.columns:
            df = df.drop(columns=['REGIAO_DE_SAUDE'])

        falta_coluna = [col for col in colunas_basicas if col not in df.columns]
        if falta_coluna:
            flash(f"Erro: A planilha enviada não tem as colunas básicas necessárias: {falta_coluna}", "error")
            return redirect(url_for("index"))

        # Preenchendo as novas informações
        df['DATA_VIGENCIA'] = data_vigencia
        df['ODONTO'] = odonto_flag

        df_salvar = df[colunas_finais]
        
        # Salvando na tabela V2
        df_salvar.to_sql('negociacoes_v2', engine, if_exists='append', index=False)
        flash(f"Sucesso! {len(df_salvar)} municípios da rede inseridos com a vigência {data_vigencia}.", "success")

    except Exception as e:
        flash(f"Erro ao processar o arquivo: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/exportar", methods=["POST"])
def exportar():
    try:
        busca_uf = request.form.get('busca_uf', '').upper()
        busca_municipio = request.form.get('busca_municipio', '')
        busca_vigencia = request.form.get('busca_vigencia', '')
        busca_odonto = request.form.get('busca_odonto', '')

        df_banco = pd.read_sql("SELECT * FROM negociacoes_v2", engine)
        df_filtrado = df_banco.copy()

        if busca_uf:
            df_filtrado = df_filtrado[df_filtrado['UF'] == busca_uf]
        if busca_municipio:
            df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(busca_municipio, case=False, na=False)]
        if busca_vigencia:
            df_filtrado = df_filtrado[df_filtrado['DATA_VIGENCIA'] == busca_vigencia]
        if busca_odonto:
            df_filtrado = df_filtrado[df_filtrado['ODONTO'] == busca_odonto]

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Negociacoes_Vigentes')
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name="municipios_negociados.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        flash(f"Erro ao gerar Excel: {str(e)}", "error")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=8000)
