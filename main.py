import os
import io
import json
import pandas as pd
from flask import Flask, request, render_template_string, send_file, flash, redirect, url_for, session
from sqlalchemy import create_engine, text

app = Flask(__name__)
app.secret_key = "chave_super_secreta_sistema_redes"

# ==========================================
# 1. CONFIGURAÇÃO E CRIAÇÃO DO BANCO
# ==========================================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:hMNxRensWWNVbiZJuMRBVCawLZfPSQXo@postgres.railway.internal:5432/railway")
engine = create_engine(DATABASE_URL)

def criar_tabelas():
    try:
        with engine.connect() as conn:
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
# 2. USUÁRIOS DO SISTEMA
# ==========================================
USUARIOS = {
    "admin": {"senha": "123", "role": "admin", "nome": "Administrador"},
    "consulta": {"senha": "123", "role": "consulta", "nome": "Equipe de Consulta"}
}

# ==========================================
# 3. INTERFACES HTML (LOGIN E SISTEMA)
# ==========================================
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Gestão de Redes</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
        h2 { color: #2c3e50; margin-bottom: 20px; }
        input { width: 90%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; font-size: 16px; }
        .btn { width: 100%; background-color: #3498db; color: white; border: none; padding: 12px; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 15px; }
        .btn:hover { background-color: #2980b9; }
        .alert { color: #e74c3c; margin-bottom: 15px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🏥 Acesso ao Sistema</h2>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <div class="alert">{{ messages[0] }}</div>
          {% endif %}
        {% endwith %}
        <form action="/login" method="POST">
            <input type="text" name="usuario" placeholder="Nome de usuário" required>
            <input type="password" name="senha" placeholder="Senha" required>
            <button type="submit" class="btn">Entrar</button>
        </form>
    </div>
</body>
</html>
"""

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestão de Redes de Saúde</title>
    <style>
        :root { --primary: #2c3e50; --secondary: #3498db; --light: #f4f7f6; --success: #27ae60; --danger: #e74c3c; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--light); color: #333; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--light); padding-bottom: 10px; margin-bottom: 20px; }
        h1, h2 { color: var(--primary); margin: 0; }
        .logout-btn { background-color: var(--danger); color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 14px; }
        .logout-btn:hover { background-color: #c0392b; }
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
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; color: white; font-weight: bold; line-height: 1.5; }
        .alert.success { background-color: var(--success); }
        .alert.error { background-color: var(--danger); }
        .alert.info { background-color: var(--secondary); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Gestão de Redes de Saúde</h1>
            <div>
                <span style="margin-right: 15px; font-weight: bold; color: var(--primary);">Olá, {{ nome_usuario }}!</span>
                <a href="/logout" class="logout-btn">Sair</a>
            </div>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% if messages %}
            {% for category, message in messages %}
              <div class="alert {{ category }}">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}

        {% if role == 'admin' %}
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
        {% endif %}

        <h2>🔍 Consulta de Municípios</h2>
        <form action="/" method="GET" id="formBusca">
            <div class="form-grid">
                <div class="form-group">
                    <label>UF:</label>
                    <select name="busca_uf" id="busca_uf">
                        <option value="">Todas</option>
                        {% for uf in lista_ufs %}
                            <option value="{{ uf }}" {% if request.args.get('busca_uf') == uf %}selected{% endif %}>{{ uf }}</option>
                        {% endfor %}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Município:</label>
                    <input list="municipios_lista" name="busca_municipio" id="busca_municipio" placeholder="Digite para buscar..." value="{{ request.args.get('busca_municipio', '') }}" autocomplete="off">
                    <datalist id="municipios_lista">
                        </datalist>
                </div>

                <div class="form-group">
                    <label>Rede:</label>
                    <select name="busca_rede">
                        <option value="">Todas as Redes</option>
                        {% for rede in lista_redes %}
                            <option value="{{ rede }}" {% if request.args.get('busca_rede') == rede %}selected{% endif %}>{{ rede }}</option>
                        {% endfor %}
                    </select>
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
                <input type="hidden" name="busca_rede" value="{{ request.args.get('busca_rede', '') }}">
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

    <script>
        const mapaUfs = {{ mapa_ufs_json | safe }};
        const selectUf = document.getElementById('busca_uf');
        const datalistMunicipios = document.getElementById('municipios_lista');
        const inputMunicipio = document.getElementById('busca_municipio');

        function atualizarMunicipios() {
            const ufSelecionada = selectUf.value;
            datalistMunicipios.innerHTML = ''; 
            
            let municipiosDisponiveis = [];

            if (ufSelecionada && mapaUfs[ufSelecionada]) {
                municipiosDisponiveis = mapaUfs[ufSelecionada];
            } else {
                Object.values(mapaUfs).forEach(lista => {
                    municipiosDisponiveis = municipiosDisponiveis.concat(lista);
                });
            }

            municipiosDisponiveis = [...new Set(municipiosDisponiveis)].sort();

            municipiosDisponiveis.forEach(mun => {
                let option = document.createElement('option');
                option.value = mun;
                datalistMunicipios.appendChild(option);
            });
            
            if(ufSelecionada && !municipiosDisponiveis.includes(inputMunicipio.value)) {
                inputMunicipio.value = '';
            }
        }

        selectUf.addEventListener('change', atualizarMunicipios);
        window.addEventListener('DOMContentLoaded', atualizarMunicipios);
    </script>
</body>
</html>
"""

# ==========================================
# 4. ROTAS DO SISTEMA
# ==========================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        senha = request.form.get("senha")
        
        if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
            session["usuario"] = usuario
            session["role"] = USUARIOS[usuario]["role"]
            session["nome"] = USUARIOS[usuario]["nome"]
            return redirect(url_for("index"))
        else:
            flash("Usuário ou senha incorretos!", "error")
            
    return render_template_string(LOGIN_TEMPLATE)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "usuario" not in session:
        return redirect(url_for("login"))

    lista_ufs = []
    lista_redes = []
    mapa_ufs = {}
    tabela_html = ""
    total_linhas = 0

    try:
        df_banco = pd.read_sql("SELECT * FROM negociacoes_v2", engine)
        
        if not df_banco.empty:
            lista_ufs = sorted(df_banco['UF'].dropna().unique())
            lista_redes = sorted(df_banco['REDE'].dropna().unique())
            
            for uf in lista_ufs:
                municipios_da_uf = df_banco[df_banco['UF'] == uf]['MUNICIPIO'].dropna().unique().tolist()
                mapa_ufs[uf] = sorted(municipios_da_uf)

            # Resgatando filtros
            busca_uf = request.args.get('busca_uf', '').upper()
            busca_municipio = request.args.get('busca_municipio', '')
            busca_rede = request.args.get('busca_rede', '')
            busca_vigencia = request.args.get('busca_vigencia', '')
            busca_odonto = request.args.get('busca_odonto', '')

            df_filtrado = df_banco.copy()

            if busca_uf:
                df_filtrado = df_filtrado[df_filtrado['UF'] == busca_uf]
            if busca_municipio:
                df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(busca_municipio, case=False, na=False)]
            if busca_rede:
                df_filtrado = df_filtrado[df_filtrado['REDE'] == busca_rede]
            if busca_vigencia:
                df_filtrado = df_filtrado[df_filtrado['DATA_VIGENCIA'] == busca_vigencia]
            if busca_odonto:
                df_filtrado = df_filtrado[df_filtrado['ODONTO'] == busca_odonto]

            total_linhas = len(df_filtrado)
            if total_linhas > 0:
                tabela_html = df_filtrado.to_html(index=False, classes="", border=0)

    except Exception as e:
        print(f"Erro ao consultar banco: {e}")

    mapa_ufs_json = json.dumps(mapa_ufs)

    return render_template_string(
        HTML_TEMPLATE, 
        role=session.get("role"),
        nome_usuario=session.get("nome"),
        lista_ufs=lista_ufs, 
        lista_redes=lista_redes,
        mapa_ufs_json=mapa_ufs_json,
        tabela_html=tabela_html, 
        total_linhas=total_linhas
    )


@app.route("/upload", methods=["POST"])
def upload():
    if "usuario" not in session or session.get("role") != "admin":
        return redirect(url_for("index"))

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

        colunas_basicas = ['UF', 'IBGE', 'MUNICIPIO', 'REDE']
        colunas_finais = ['UF', 'IBGE', 'MUNICIPIO', 'REDE', 'DATA_VIGENCIA', 'ODONTO']

        if 'REGIAO_DE_SAUDE' in df.columns:
            df = df.drop(columns=['REGIAO_DE_SAUDE'])

        falta_coluna = [col for col in colunas_basicas if col not in df.columns]
        if falta_coluna:
            flash(f"Erro: A planilha enviada não tem as colunas necessárias: {falta_coluna}", "error")
            return redirect(url_for("index"))

        # ==========================================
        # TRAVA CONTRA DUPLICIDADE DE IBGE
        # ==========================================
        df_existentes = pd.read_sql('SELECT "IBGE", "MUNICIPIO" FROM negociacoes_v2', engine)
        ibges_no_banco = df_existentes['IBGE'].dropna().unique().tolist()
        
        # Encontra se na planilha nova tem algum IBGE que já tá no banco
        df_duplicados = df[df['IBGE'].isin(ibges_no_banco)]
        
        if not df_duplicados.empty:
            municipios_duplicados = df_duplicados['MUNICIPIO'].unique().tolist()
            
            # Limita a lista de nomes pra não explodir a tela se forem muitos
            if len(municipios_duplicados) > 10:
                msg_mun = ", ".join(municipios_duplicados[:10]) + f" e mais {len(municipios_duplicados)-10} outros."
            else:
                msg_mun = ", ".join(municipios_duplicados)
                
            flash(f"⛔ UPLOAD CANCELADO: Os seguintes municípios (IBGE) já existem no banco e não podem ser duplicados: {msg_mun}", "error")
            return redirect(url_for("index"))

        # Se passou na trava, insere os dados
        df['DATA_VIGENCIA'] = data_vigencia
        df['ODONTO'] = odonto_flag

        df_salvar = df[colunas_finais]
        
        df_salvar.to_sql('negociacoes_v2', engine, if_exists='append', index=False)
        flash(f"Sucesso! {len(df_salvar)} municípios da rede inseridos com a vigência {data_vigencia}.", "success")

    except Exception as e:
        flash(f"Erro ao processar o arquivo: {str(e)}", "error")

    return redirect(url_for("index"))


@app.route("/exportar", methods=["POST"])
def exportar():
    if "usuario" not in session:
        return redirect(url_for("login"))

    try:
        busca_uf = request.form.get('busca_uf', '').upper()
        busca_municipio = request.form.get('busca_municipio', '')
        busca_rede = request.form.get('busca_rede', '')
        busca_vigencia = request.form.get('busca_vigencia', '')
        busca_odonto = request.form.get('busca_odonto', '')

        df_banco = pd.read_sql("SELECT * FROM negociacoes_v2", engine)
        df_filtrado = df_banco.copy()

        if busca_uf:
            df_filtrado = df_filtrado[df_filtrado['UF'] == busca_uf]
        if busca_municipio:
            df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(busca_municipio, case=False, na=False)]
        if busca_rede:
            df_filtrado = df_filtrado[df_filtrado['REDE'] == busca_rede]
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
