import os
import io
import json
import pandas as pd
from flask import Flask, request, render_template_string, send_file, flash, redirect, url_for, session, make_response
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
# 3. INTERFACES HTML E CSS RESPONSIVO (PWA)
# ==========================================
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#2c3e50">
    <link rel="manifest" href="/manifest.json">
    <title>Login - Gestão de Redes</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; padding: 20px; box-sizing: border-box; }
        .login-box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; text-align: center; }
        h2 { color: #2c3e50; margin-bottom: 20px; font-size: 1.5rem; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; font-size: 16px; box-sizing: border-box; }
        .btn { width: 100%; background-color: #3498db; color: white; border: none; padding: 14px; border-radius: 5px; font-size: 16px; font-weight: bold; cursor: pointer; margin-top: 15px; }
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#2c3e50">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <link rel="manifest" href="/manifest.json">
    <title>Gestão de Redes de Saúde</title>
    <style>
        :root { --primary: #2c3e50; --secondary: #3498db; --light: #f4f7f6; --success: #27ae60; --danger: #e74c3c; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--light); color: #333; margin: 0; padding: 15px; }
        .container { max-width: 1200px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--light); padding-bottom: 15px; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        h1, h2 { color: var(--primary); margin: 0; font-size: 1.5rem; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        
        .logout-btn { background-color: var(--danger); color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 14px; }
        
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; }
        label { font-weight: bold; margin-bottom: 5px; font-size: 14px; color: var(--primary); }
        input, select { padding: 12px; border: 1px solid #ccc; border-radius: 5px; font-size: 15px; }
        
        .btn { background-color: var(--secondary); color: white; border: none; padding: 14px 20px; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: bold; width: 100%; text-align: center; display: inline-block; box-sizing: border-box; }
        .btn-limpar { background-color: #95a5a6; margin-top: 10px; }
        .btn-export { background-color: var(--success); margin-top: 15px; }
        
        .table-responsive { overflow-x: auto; margin-top: 20px; border-radius: 5px; border: 1px solid #ddd; }
        table { width: 100%; border-collapse: collapse; min-width: 600px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; font-size: 13px; }
        th { background-color: var(--primary); color: white; position: sticky; top: 0; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; color: white; font-weight: bold; line-height: 1.5; font-size: 14px; }
        .alert.success { background-color: var(--success); }
        .alert.error { background-color: var(--danger); }
        .alert.info { background-color: var(--secondary); }

        #pwa-banner { display: none; position: fixed; bottom: 0; left: 0; width: 100%; background: var(--primary); color: white; padding: 15px; box-sizing: border-box; box-shadow: 0 -2px 10px rgba(0,0,0,0.2); z-index: 1000; justify-content: space-between; align-items: center; }
        #ios-banner { display: none; position: fixed; bottom: 10px; left: 50%; transform: translateX(-50%); width: 90%; background: white; color: black; padding: 15px; box-sizing: border-box; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.3); z-index: 1000; text-align: center; border: 2px solid var(--secondary); }

        @media (max-width: 768px) {
            .container { padding: 15px; margin-top: 5px; }
            .form-grid { grid-template-columns: 1fr; }
            .header { flex-direction: column; align-items: stretch; }
            .user-info { justify-content: space-between; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Gestão de Redes</h1>
            <div class="user-info">
                <span style="font-weight: bold; color: var(--primary);">Olá, {{ nome_usuario }}!</span>
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
        <h2>📥 Nova Importação ou Atualização</h2>
        <form action="/upload" method="POST" enctype="multipart/form-data">
            <div class="form-grid">
                <div class="form-group">
                    <label>Arquivo (.xlsx ou .csv):</label>
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
        <hr style="margin: 30px 0; border: 1px solid #eee;">
        {% endif %}

        <h2>🔍 Consulta</h2>
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
                    <input list="municipios_lista" name="busca_municipio" id="busca_municipio" placeholder="Digite..." value="{{ request.args.get('busca_municipio', '') }}" autocomplete="off">
                    <datalist id="municipios_lista"></datalist>
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
                    <label>Data Vigência:</label>
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
            <a href="/" class="btn btn-limpar">Limpar Filtros</a>
        </form>

        {% if tabela_html %}
            <form action="/exportar" method="POST">
                <input type="hidden" name="busca_uf" value="{{ request.args.get('busca_uf', '') }}">
                <input type="hidden" name="busca_municipio" value="{{ request.args.get('busca_municipio', '') }}">
                <input type="hidden" name="busca_rede" value="{{ request.args.get('busca_rede', '') }}">
                <input type="hidden" name="busca_vigencia" value="{{ request.args.get('busca_vigencia', '') }}">
                <input type="hidden" name="busca_odonto" value="{{ request.args.get('busca_odonto', '') }}">
                <button type="submit" class="btn btn-export">📥 Exportar Excel</button>
            </form>
            
            <p style="margin-top: 15px;"><strong>Resultados encontrados: {{ total_linhas }}</strong></p>
            <div class="table-responsive">
                {{ tabela_html | safe }}
            </div>
        {% else %}
            <div class="alert info" style="margin-top: 20px;">O banco está vazio ou nenhum dado corresponde.</div>
        {% endif %}
    </div>

    <div id="pwa-banner">
        <span>📲 Instale o App para acesso rápido!</span>
        <div>
            <button id="pwa-install-btn" style="background:var(--success); color:white; border:none; padding:8px 15px; border-radius:5px; font-weight:bold;">Instalar</button>
            <button onclick="document.getElementById('pwa-banner').style.display='none'" style="background:none; border:none; color:white; font-weight:bold; font-size:18px; margin-left:10px;">×</button>
        </div>
    </div>

    <div id="ios-banner">
        <p style="margin: 0 0 10px 0; font-weight: bold; color: var(--primary);">📲 Instalar App no iPhone</p>
        <p style="font-size: 13px; margin:0;">Toque em <b>Compartilhar</b> (quadrado com a seta pra cima) na barra do Safari e depois em <b>"Adicionar à Tela de Início"</b>.</p>
        <button onclick="document.getElementById('ios-banner').style.display='none'" style="margin-top:10px; width:100%; padding:8px; background:#ddd; border:none; border-radius:5px; font-weight:bold;">Entendi</button>
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

        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js').catch(err => console.log('SW falhou: ', err));
            });
        }

        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('pwa-banner').style.display = 'flex';
        });

        document.getElementById('pwa-install-btn').addEventListener('click', async () => {
            document.getElementById('pwa-banner').style.display = 'none';
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                deferredPrompt = null;
            }
        });

        const isIos = () => {
            const userAgent = window.navigator.userAgent.toLowerCase();
            return /iphone|ipad|ipod/.test(userAgent);
        };
        const isInStandaloneMode = () => ('standalone' in window.navigator) && (window.navigator.standalone);

        if (isIos() && !isInStandaloneMode()) {
            setTimeout(() => {
                document.getElementById('ios-banner').style.display = 'block';
            }, 2000);
        }
    </script>
</body>
</html>
"""

# ==========================================
# 4. ROTAS DO PWA (APP CELULAR)
# ==========================================
@app.route('/manifest.json')
def manifest():
    manifest_data = {
        "name": "Gestão de Redes Saúde",
        "short_name": "Redes",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f4f7f6",
        "theme_color": "#2c3e50",
        "icons": [
            {
                "src": "https://cdn-icons-png.flaticon.com/512/3063/3063206.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    response = make_response(json.dumps(manifest_data))
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/sw.js')
def service_worker():
    js = """
    self.addEventListener('install', (e) => {
        self.skipWaiting();
    });
    self.addEventListener('fetch', (e) => {
        e.respondWith(fetch(e.request).catch(() => new Response("Você está offline!")));
    });
    """
    response = make_response(js)
    response.headers["Content-Type"] = "application/javascript"
    return response

# ==========================================
# 5. ROTAS DO SISTEMA DE DADOS
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

        # Preparando os dados
        df_salvar = df[colunas_basicas].copy()
        df_salvar['DATA_VIGENCIA'] = data_vigencia
        df_salvar['ODONTO'] = odonto_flag
        
        # Criando a chave única IBGE + REDE para comparar o que já existe
        df_salvar['CHAVE'] = df_salvar['IBGE'].astype(str) + "_" + df_salvar['REDE'].astype(str)

        # Lendo o que já tem no banco
        df_existentes = pd.read_sql('SELECT "IBGE", "REDE" FROM negociacoes_v2', engine)
        df_existentes['CHAVE'] = df_existentes['IBGE'].astype(str) + "_" + df_existentes['REDE'].astype(str)
        chaves_banco = set(df_existentes['CHAVE'].tolist())

        # Separando o que é INSERT (novo) do que é UPDATE (atualização silenciosa)
        df_novos = df_salvar[~df_salvar['CHAVE'].isin(chaves_banco)].copy()
        df_atualizar = df_salvar[df_salvar['CHAVE'].isin(chaves_banco)].copy()

        linhas_atualizadas = 0
        linhas_inseridas = 0

        # 1. Fazendo o UPDATE dos existentes silenciosamente (Sem Crítica)
        if not df_atualizar.empty:
            with engine.connect() as conn:
                for _, row in df_atualizar.iterrows():
                    conn.execute(
                        text('UPDATE negociacoes_v2 SET "ODONTO" = :odonto, "DATA_VIGENCIA" = :vigencia WHERE "IBGE" = :ibge AND "REDE" = :rede'),
                        {"odonto": row['ODONTO'], "vigencia": row['DATA_VIGENCIA'], "ibge": row['IBGE'], "rede": row['REDE']}
                    )
                conn.commit()
                linhas_atualizadas = len(df_atualizar)

        # 2. Fazendo o INSERT dos novos
        if not df_novos.empty:
            df_novos = df_novos.drop(columns=['CHAVE'])
            df_novos.to_sql('negociacoes_v2', engine, if_exists='append', index=False)
            linhas_inseridas = len(df_novos)

        flash(f"Sucesso! {linhas_inseridas} novos registros inseridos e {linhas_atualizadas} municípios existentes atualizados sem problemas.", "success")

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
