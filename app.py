import os
import io
import json
from datetime import datetime
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
                CREATE TABLE IF NOT EXISTS negociacoes_v3 (
                    "UF" VARCHAR(10),
                    "IBGE" VARCHAR(50),
                    "MUNICIPIO" VARCHAR(255),
                    "REDE" VARCHAR(255),
                    "DATA_VIGENCIA" VARCHAR(50),
                    "SAUDE" VARCHAR(10),
                    "ODONTO" VARCHAR(10),
                    "ARQUIVO" VARCHAR(255)
                )
            """))
            conn.commit()
    except Exception as e:
        print(f"Erro ao criar tabelas: {e}")

criar_tabelas()

def formatar_data_br(data_iso):
    """Converte YYYY-MM-DD para DD/MM/YYYY"""
    if not data_iso: return ""
    try:
        return datetime.strptime(data_iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return data_iso

# ==========================================
# 2. USUÁRIOS DO SISTEMA
# ==========================================
USUARIOS = {
    "admin": {"senha": "123", "role": "admin", "nome": "Administrador"},
    "consulta": {"senha": "123", "role": "consulta", "nome": "Equipe de Consulta"}
}

# ==========================================
# 3. INTERFACES HTML E CSS RESPONSIVO
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
    <link rel="manifest" href="/manifest.json">
    <title>Gestão de Redes de Saúde</title>
    <style>
        :root { --primary: #2c3e50; --secondary: #3498db; --light: #f4f7f6; --success: #27ae60; --danger: #e74c3c; --warning: #f1c40f; --dark: #34495e; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: var(--light); color: #333; margin: 0; padding: 15px; }
        .container { max-width: 1300px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--light); padding-bottom: 15px; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        h1 { color: var(--primary); margin: 0; font-size: 1.5rem; }
        h2 { color: var(--primary); margin-top: 0; border-left: 4px solid var(--secondary); padding-left: 10px; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        
        .logout-btn { background-color: var(--danger); color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold; font-size: 14px; }
        
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 20px; }
        .form-group { display: flex; flex-direction: column; }
        label { font-weight: bold; margin-bottom: 5px; font-size: 13px; color: var(--primary); }
        input, select { padding: 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 14px; }
        
        .btn { background-color: var(--secondary); color: white; border: none; padding: 12px 20px; border-radius: 5px; cursor: pointer; font-size: 14px; font-weight: bold; transition: 0.3s; }
        .btn-limpar { background-color: #95a5a6; }
        .btn-export { background-color: var(--success); margin-top: 15px; }
        .btn-full { width: 100%; }
        
        .table-responsive { overflow-x: auto; margin-top: 15px; border-radius: 5px; border: 1px solid #ddd; max-height: 500px; }
        table { width: 100%; border-collapse: collapse; min-width: 700px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 13px; }
        th { background-color: var(--primary); color: white; position: sticky; top: 0; z-index: 10; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f1f1f1; }
        
        .btn-action { padding: 6px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; margin-right: 5px; font-weight: bold; }
        .btn-edit { background-color: var(--warning); color: #000; }
        .btn-delete { background-color: var(--danger); color: #fff; }
        .btn-lote { background-color: var(--dark); color: #fff; width: 100%; margin-bottom: 5px; }

        .alert { padding: 15px; margin-bottom: 20px; border-radius: 5px; color: white; font-weight: bold; line-height: 1.5; font-size: 14px; }
        .alert.success { background-color: var(--success); }
        .alert.error { background-color: var(--danger); }
        .alert.info { background-color: var(--secondary); }
        
        hr { border: 0; height: 1px; background-color: #ddd; margin: 30px 0; }

        /* Modal */
        .modal { display: none; position: fixed; z-index: 2000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.6); backdrop-filter: blur(3px); }
        .modal-content { background-color: #fff; margin: 5% auto; padding: 25px; border-radius: 10px; width: 90%; max-width: 500px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: #000; }

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
                    <label>Saúde:</label>
                    <select name="saude_flag" required>
                        <option value="SIM">SIM</option>
                        <option value="NÃO">NÃO</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Odonto:</label>
                    <select name="odonto_flag" required>
                        <option value="SIM">SIM</option>
                        <option value="NÃO">NÃO</option>
                    </select>
                </div>
            </div>
            <button type="submit" class="btn btn-full">🚀 Processar e Salvar Planilha</button>
        </form>
        
        <hr>

        <h2>📂 Gerenciar Arquivos Importados (Lotes)</h2>
        <div class="table-responsive" style="max-height: 300px;">
            <table>
                <thead>
                    <tr>
                        <th>NOME DO ARQUIVO</th>
                        <th>MUNICÍPIOS VINCULADOS</th>
                        <th style="width: 150px;">AÇÕES DO LOTE</th>
                    </tr>
                </thead>
                <tbody>
                    {% for lote in lotes %}
                    <tr>
                        <td><strong>{{ lote.ARQUIVO }}</strong></td>
                        <td>{{ lote.QTD }}</td>
                        <td>
                            <button type="button" class="btn-action btn-lote" onclick="abrirModalLote('{{ lote.ARQUIVO }}')">✏️ Editar Lote</button>
                            <form action="/excluir_lote" method="POST" style="margin:0;" onsubmit="return confirm('ATENÇÃO: Deseja excluir TODOS os {{ lote.QTD }} registros vinculados ao arquivo {{ lote.ARQUIVO }}?');">
                                <input type="hidden" name="arquivo" value="{{ lote.ARQUIVO }}">
                                <button type="submit" class="btn-action btn-delete" style="width: 100%;">🗑️ Excluir Lote</button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="3">Nenhum arquivo importado no banco de dados.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <hr>
        {% endif %}

        <h2>🔍 Consulta de Municípios</h2>
        <form action="/" method="GET" id="formBusca">
            <div class="form-grid">
                <div class="form-group">
                    <label>UF:</label>
                    <select name="busca_uf" id="busca_uf">
                        <option value="">-- Todas --</option>
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
                        <option value="">-- Todas as Redes --</option>
                        {% for rede in lista_redes %}
                            <option value="{{ rede }}" {% if request.args.get('busca_rede') == rede %}selected{% endif %}>{{ rede }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label>Saúde:</label>
                    <select name="busca_saude">
                        <option value="">-- Selecione --</option>
                        <option value="SIM" {% if request.args.get('busca_saude') == 'SIM' %}selected{% endif %}>SIM</option>
                        <option value="NÃO" {% if request.args.get('busca_saude') == 'NÃO' %}selected{% endif %}>NÃO</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Odonto:</label>
                    <select name="busca_odonto">
                        <option value="">-- Selecione --</option>
                        <option value="SIM" {% if request.args.get('busca_odonto') == 'SIM' %}selected{% endif %}>SIM</option>
                        <option value="NÃO" {% if request.args.get('busca_odonto') == 'NÃO' %}selected{% endif %}>NÃO</option>
                    </select>
                </div>
            </div>
            <div style="display: flex; gap: 10px;">
                <button type="submit" class="btn">Aplicar Filtros</button>
                <a href="/" class="btn btn-limpar" style="text-decoration:none; display:flex; align-items:center;">Limpar</a>
            </div>
        </form>

        {% if registros %}
            <form action="/exportar" method="POST">
                <input type="hidden" name="busca_uf" value="{{ request.args.get('busca_uf', '') }}">
                <input type="hidden" name="busca_municipio" value="{{ request.args.get('busca_municipio', '') }}">
                <input type="hidden" name="busca_rede" value="{{ request.args.get('busca_rede', '') }}">
                <input type="hidden" name="busca_saude" value="{{ request.args.get('busca_saude', '') }}">
                <input type="hidden" name="busca_odonto" value="{{ request.args.get('busca_odonto', '') }}">
                <button type="submit" class="btn btn-export">📥 Exportar Tabela para Excel</button>
            </form>
            
            <p style="margin-top: 15px;"><strong>Resultados encontrados: {{ total_linhas }}</strong></p>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>UF</th>
                            <th>IBGE</th>
                            <th>MUNICÍPIO</th>
                            <th>REDE</th>
                            <th>DATA VIGÊNCIA</th>
                            <th>SAÚDE</th>
                            <th>ODONTO</th>
                            {% if role == 'admin' %}
                            <th>ARQUIVO ORIGEM</th>
                            <th style="min-width: 90px;">AÇÕES</th>
                            {% endif %}
                        </tr>
                    </thead>
                    <tbody>
                        {% for row in registros %}
                        <tr>
                            <td>{{ row.UF }}</td>
                            <td>{{ row.IBGE }}</td>
                            <td>{{ row.MUNICIPIO }}</td>
                            <td>{{ row.REDE }}</td>
                            <td>{{ row.DATA_VIGENCIA_BR }}</td>
                            <td>{{ row.SAUDE }}</td>
                            <td>{{ row.ODONTO }}</td>
                            {% if role == 'admin' %}
                            <td style="font-size: 11px; color:#555;">{{ row.ARQUIVO }}</td>
                            <td>
                                <button type="button" class="btn-action btn-edit" title="Editar"
                                    data-ibge="{{ row.IBGE }}" 
                                    data-mun="{{ row.MUNICIPIO }}" 
                                    data-rede="{{ row.REDE }}" 
                                    data-vig="{{ row.DATA_VIGENCIA }}" 
                                    data-saude="{{ row.SAUDE }}" 
                                    data-odonto="{{ row.ODONTO }}" 
                                    onclick="abrirModalIndividual(this)">✏️</button>
                                
                                <form action="/excluir" method="POST" style="display:inline;" onsubmit="return confirm('Tem certeza que deseja EXCLUIR {{ row.MUNICIPIO }} da rede {{ row.REDE }}?');">
                                    <input type="hidden" name="ibge" value="{{ row.IBGE }}">
                                    <input type="hidden" name="rede" value="{{ row.REDE }}">
                                    <button type="submit" class="btn-action btn-delete" title="Excluir">🗑️</button>
                                </form>
                            </td>
                            {% endif %}
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        {% else %}
            <div class="alert info" style="margin-top: 20px;">O banco está vazio ou nenhum dado corresponde aos filtros.</div>
        {% endif %}
    </div>

    <div id="modalIndividual" class="modal">
        <div class="modal-content">
            <span class="close" onclick="document.getElementById('modalIndividual').style.display='none'">&times;</span>
            <h3 style="color:var(--primary); margin-top:0;">✏️ Editar Município</h3>
            <p style="color: #555;">Município: <strong id="lbl_municipio"></strong></p>
            <form action="/editar" method="POST">
                <input type="hidden" name="ibge" id="edit_ibge">
                <input type="hidden" name="rede_antiga" id="edit_rede_antiga">
                
                <div class="form-group"><label>Rede:</label><input type="text" name="nova_rede" id="edit_rede" required></div>
                <div class="form-group" style="margin-top: 10px;"><label>Data Vigência:</label><input type="date" name="nova_vigencia" id="edit_vigencia" required></div>
                <div class="form-group" style="margin-top: 10px;">
                    <label>Saúde:</label>
                    <select name="novo_saude" id="edit_saude" required>
                        <option value="SIM">SIM</option>
                        <option value="NÃO">NÃO</option>
                    </select>
                </div>
                <div class="form-group" style="margin-top: 10px;">
                    <label>Odonto:</label>
                    <select name="novo_odonto" id="edit_odonto" required>
                        <option value="SIM">SIM</option>
                        <option value="NÃO">NÃO</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-full" style="margin-top: 20px;">💾 Salvar Alterações</button>
            </form>
        </div>
    </div>

    <div id="modalLote" class="modal">
        <div class="modal-content">
            <span class="close" onclick="document.getElementById('modalLote').style.display='none'">&times;</span>
            <h3 style="color:var(--dark); margin-top:0;">📦 Editar Lote de Importação</h3>
            <p style="color: #555; font-size: 14px;">As alterações afetarão TODOS os municípios do arquivo:<br><strong id="lbl_arquivo_lote" style="word-break: break-all; color: var(--primary);"></strong></p>
            <form action="/editar_lote" method="POST">
                <input type="hidden" name="arquivo_lote" id="input_arquivo_lote">
                
                <div class="form-group">
                    <label>Nova Rede (opcional):</label>
                    <input type="text" name="nova_rede" placeholder="Deixe em branco para não alterar">
                </div>
                <div class="form-group" style="margin-top: 10px;">
                    <label>Nova Data Vigência (opcional):</label>
                    <input type="date" name="nova_vigencia">
                </div>
                <div class="form-group" style="margin-top: 10px;">
                    <label>Alterar Saúde (opcional):</label>
                    <select name="novo_saude">
                        <option value="">-- Não Alterar --</option>
                        <option value="SIM">SIM</option>
                        <option value="NÃO">NÃO</option>
                    </select>
                </div>
                <div class="form-group" style="margin-top: 10px;">
                    <label>Alterar Odonto (opcional):</label>
                    <select name="novo_odonto">
                        <option value="">-- Não Alterar --</option>
                        <option value="SIM">SIM</option>
                        <option value="NÃO">NÃO</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-full" style="background-color: var(--dark); margin-top: 20px;">💾 Salvar Alteração em Lote</button>
            </form>
        </div>
    </div>

    <script>
        function abrirModalIndividual(btn) {
            document.getElementById('edit_ibge').value = btn.getAttribute('data-ibge');
            document.getElementById('lbl_municipio').innerText = btn.getAttribute('data-mun') + " (" + btn.getAttribute('data-ibge') + ")";
            document.getElementById('edit_rede_antiga').value = btn.getAttribute('data-rede');
            
            document.getElementById('edit_rede').value = btn.getAttribute('data-rede');
            document.getElementById('edit_vigencia').value = btn.getAttribute('data-vig');
            document.getElementById('edit_saude').value = btn.getAttribute('data-saude');
            document.getElementById('edit_odonto').value = btn.getAttribute('data-odonto');
            
            document.getElementById('modalIndividual').style.display = 'block';
        }

        function abrirModalLote(arquivo) {
            document.getElementById('input_arquivo_lote').value = arquivo;
            document.getElementById('lbl_arquivo_lote').innerText = arquivo;
            document.getElementById('modalLote').style.display = 'block';
        }

        window.onclick = function(event) {
            if (event.target == document.getElementById('modalIndividual')) document.getElementById('modalIndividual').style.display = 'none';
            if (event.target == document.getElementById('modalLote')) document.getElementById('modalLote').style.display = 'none';
        }

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
        "icons": [{"src": "https://cdn-icons-png.flaticon.com/512/3063/3063206.png", "sizes": "512x512", "type": "image/png"}]
    }
    response = make_response(json.dumps(manifest_data))
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/sw.js')
def service_worker():
    js = """
    self.addEventListener('install', (e) => { self.skipWaiting(); });
    self.addEventListener('fetch', (e) => { e.respondWith(fetch(e.request).catch(() => new Response("Offline"))); });
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

    lista_ufs, lista_redes, mapa_ufs, registros, lotes = [], [], {}, [], []
    total_linhas = 0

    try:
        df_banco = pd.read_sql("SELECT * FROM negociacoes_v3", engine)
        
        if session.get("role") == "admin":
            df_lotes = pd.read_sql('SELECT "ARQUIVO", COUNT(*) as "QTD" FROM negociacoes_v3 GROUP BY "ARQUIVO" ORDER BY "ARQUIVO"', engine)
            lotes = df_lotes.to_dict('records')

        if not df_banco.empty:
            lista_ufs = sorted(df_banco['UF'].dropna().unique())
            lista_redes = sorted(df_banco['REDE'].dropna().unique())
            
            for uf in lista_ufs:
                municipios_da_uf = df_banco[df_banco['UF'] == uf]['MUNICIPIO'].dropna().unique().tolist()
                mapa_ufs[uf] = sorted(municipios_da_uf)

            busca_uf = request.args.get('busca_uf', '').upper()
            busca_municipio = request.args.get('busca_municipio', '')
            busca_rede = request.args.get('busca_rede', '')
            busca_saude = request.args.get('busca_saude', '')
            busca_odonto = request.args.get('busca_odonto', '')

            df_filtrado = df_banco.copy()

            if busca_uf: df_filtrado = df_filtrado[df_filtrado['UF'] == busca_uf]
            if busca_municipio: df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(busca_municipio, case=False, na=False)]
            if busca_rede: df_filtrado = df_filtrado[df_filtrado['REDE'] == busca_rede]
            if busca_saude: df_filtrado = df_filtrado[df_filtrado['SAUDE'] == busca_saude]
            if busca_odonto: df_filtrado = df_filtrado[df_filtrado['ODONTO'] == busca_odonto]

            total_linhas = len(df_filtrado)
            if total_linhas > 0:
                df_filtrado['DATA_VIGENCIA_BR'] = df_filtrado['DATA_VIGENCIA'].apply(formatar_data_br)
                registros = df_filtrado.to_dict('records')

    except Exception as e:
        print(f"Erro ao consultar banco: {e}")

    return render_template_string(
        HTML_TEMPLATE, 
        role=session.get("role"),
        nome_usuario=session.get("nome"),
        lista_ufs=lista_ufs, 
        lista_redes=lista_redes,
        mapa_ufs_json=json.dumps(mapa_ufs),
        registros=registros, 
        lotes=lotes,
        total_linhas=total_linhas
    )


@app.route("/upload", methods=["POST"])
def upload():
    if "usuario" not in session or session.get("role") != "admin":
        return redirect(url_for("index"))

    arquivo = request.files.get("arquivo")
    data_vigencia = request.form.get("data_vigencia", "").strip()
    saude_flag = request.form.get("saude_flag", "").strip()
    odonto_flag = request.form.get("odonto_flag", "").strip()

    if not arquivo or arquivo.filename == '':
        flash("Nenhum arquivo enviado.", "error")
        return redirect(url_for("index"))

    try:
        if arquivo.filename.endswith('.csv'): df = pd.read_csv(arquivo, dtype=str)
        else: df = pd.read_excel(arquivo, dtype=str)

        colunas_basicas = ['UF', 'IBGE', 'MUNICIPIO', 'REDE']
        colunas_finais = ['UF', 'IBGE', 'MUNICIPIO', 'REDE', 'DATA_VIGENCIA', 'SAUDE', 'ODONTO', 'ARQUIVO']

        if 'REGIAO_DE_SAUDE' in df.columns: df = df.drop(columns=['REGIAO_DE_SAUDE'])

        falta_coluna = [col for col in colunas_basicas if col not in df.columns]
        if falta_coluna:
            flash(f"Erro: A planilha enviada não tem as colunas necessárias: {falta_coluna}", "error")
            return redirect(url_for("index"))

        df_salvar = df[colunas_basicas].copy()
        df_salvar['DATA_VIGENCIA'] = data_vigencia
        df_salvar['SAUDE'] = saude_flag
        df_salvar['ODONTO'] = odonto_flag
        df_salvar['ARQUIVO'] = arquivo.filename
        
        df_salvar['CHAVE'] = df_salvar['IBGE'].astype(str) + "_" + df_salvar['REDE'].astype(str)

        df_existentes = pd.read_sql('SELECT "IBGE", "REDE", "SAUDE", "ODONTO" FROM negociacoes_v3', engine)
        
        if not df_existentes.empty:
            df_existentes['CHAVE'] = df_existentes['IBGE'].astype(str) + "_" + df_existentes['REDE'].astype(str)
            chaves_banco = set(df_existentes['CHAVE'].tolist())
        else:
            chaves_banco = set()

        df_novos = df_salvar[~df_salvar['CHAVE'].isin(chaves_banco)].copy()
        df_atualizar = df_salvar[df_salvar['CHAVE'].isin(chaves_banco)].copy()

        linhas_atualizadas = 0
        linhas_inseridas = 0

        # ==============================================================
        # MÁGICA DA SOMA DO "SIM" E PRESERVAÇÃO DO ARQUIVO ORIGINAL
        # ==============================================================
        if not df_atualizar.empty:
            df_atualizar = pd.merge(df_atualizar, df_existentes[['CHAVE', 'SAUDE', 'ODONTO']], on='CHAVE', suffixes=('', '_DB'))
            
            with engine.connect() as conn:
                for _, row in df_atualizar.iterrows():
                    
                    # Se já era SIM no banco ou veio SIM agora na planilha, fica SIM. Senão fica NÃO.
                    saude_final = "SIM" if (str(row.get('SAUDE_DB', '')).strip().upper() == "SIM" or str(row['SAUDE']).strip().upper() == "SIM") else "NÃO"
                    odonto_final = "SIM" if (str(row.get('ODONTO_DB', '')).strip().upper() == "SIM" or str(row['ODONTO']).strip().upper() == "SIM") else "NÃO"
                    
                    # Não alteramos a coluna "ARQUIVO". Ela mantém o nome de quando o município foi inserido a primeira vez.
                    conn.execute(
                        text('UPDATE negociacoes_v3 SET "SAUDE" = :saude, "ODONTO" = :odonto, "DATA_VIGENCIA" = :vigencia WHERE "IBGE" = :ibge AND "REDE" = :rede'),
                        {"saude": saude_final, "odonto": odonto_final, "vigencia": row['DATA_VIGENCIA'], "ibge": row['IBGE'], "rede": row['REDE']}
                    )
                conn.commit()
                linhas_atualizadas = len(df_atualizar)

        # Insere os novos com as flags e o nome do arquivo atual
        if not df_novos.empty:
            df_novos = df_novos.drop(columns=['CHAVE'])
            df_novos.to_sql('negociacoes_v3', engine, if_exists='append', index=False)
            linhas_inseridas = len(df_novos)

        flash(f"Sucesso! {linhas_inseridas} novos inseridos e {linhas_atualizadas} atualizados (preservando o lote original e acumulando os SIMs).", "success")

    except Exception as e:
        flash(f"Erro ao processar o arquivo: {str(e)}", "error")

    return redirect(url_for("index"))

# ==========================================
# 6. ROTAS DE EDIÇÃO E EXCLUSÃO
# ==========================================
@app.route("/editar", methods=["POST"])
def editar():
    if "usuario" not in session or session.get("role") != "admin": return redirect(url_for("index"))
    try:
        with engine.connect() as conn:
            conn.execute(
                text('UPDATE negociacoes_v3 SET "REDE" = :n_rede, "DATA_VIGENCIA" = :n_vigencia, "SAUDE" = :n_saude, "ODONTO" = :n_odonto WHERE "IBGE" = :ibge AND "REDE" = :r_antiga'),
                {"n_rede": request.form.get("nova_rede"), "n_vigencia": request.form.get("nova_vigencia"), "n_saude": request.form.get("novo_saude"), "n_odonto": request.form.get("novo_odonto"), "ibge": request.form.get("ibge"), "r_antiga": request.form.get("rede_antiga")}
            )
            conn.commit()
        flash("Registro atualizado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao atualizar: {str(e)}", "error")
    return redirect(request.referrer or url_for("index"))

@app.route("/excluir", methods=["POST"])
def excluir():
    if "usuario" not in session or session.get("role") != "admin": return redirect(url_for("index"))
    try:
        with engine.connect() as conn:
            conn.execute(text('DELETE FROM negociacoes_v3 WHERE "IBGE" = :ibge AND "REDE" = :rede'), {"ibge": request.form.get("ibge"), "rede": request.form.get("rede")})
            conn.commit()
        flash("Registro excluído permanentemente.", "success")
    except Exception:
        flash("Erro ao excluir registro.", "error")
    return redirect(request.referrer or url_for("index"))

@app.route("/editar_lote", methods=["POST"])
def editar_lote():
    if "usuario" not in session or session.get("role") != "admin": return redirect(url_for("index"))
    
    arquivo = request.form.get("arquivo_lote")
    updates = []
    params = {"arquivo": arquivo}

    if request.form.get("nova_rede"):
        updates.append('"REDE" = :rede'); params["rede"] = request.form.get("nova_rede").strip()
    if request.form.get("nova_vigencia"):
        updates.append('"DATA_VIGENCIA" = :vigencia'); params["vigencia"] = request.form.get("nova_vigencia")
    if request.form.get("novo_saude"):
        updates.append('"SAUDE" = :saude'); params["saude"] = request.form.get("novo_saude")
    if request.form.get("novo_odonto"):
        updates.append('"ODONTO" = :odonto'); params["odonto"] = request.form.get("novo_odonto")

    if not updates:
        flash("Nenhuma alteração foi preenchida para o lote.", "info")
        return redirect(url_for("index"))

    try:
        with engine.connect() as conn:
            conn.execute(text(f'UPDATE negociacoes_v3 SET {", ".join(updates)} WHERE "ARQUIVO" = :arquivo'), params)
            conn.commit()
        flash(f"Lote '{arquivo}' atualizado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao atualizar lote: {str(e)}", "error")

    return redirect(url_for("index"))

@app.route("/excluir_lote", methods=["POST"])
def excluir_lote():
    if "usuario" not in session or session.get("role") != "admin": return redirect(url_for("index"))
    arquivo = request.form.get("arquivo")
    try:
        with engine.connect() as conn:
            conn.execute(text('DELETE FROM negociacoes_v3 WHERE "ARQUIVO" = :arquivo'), {"arquivo": arquivo})
            conn.commit()
        flash(f"Todos os registros do lote '{arquivo}' foram excluídos.", "success")
    except Exception:
        flash("Erro ao excluir lote.", "error")
    return redirect(url_for("index"))

@app.route("/exportar", methods=["POST"])
def exportar():
    if "usuario" not in session: return redirect(url_for("login"))
    try:
        df_banco = pd.read_sql("SELECT * FROM negociacoes_v3", engine)
        df_filtrado = df_banco.copy()

        busca_uf = request.form.get('busca_uf', '').upper()
        if busca_uf: df_filtrado = df_filtrado[df_filtrado['UF'] == busca_uf]
        
        busca_municipio = request.form.get('busca_municipio', '')
        if busca_municipio: df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].str.contains(busca_municipio, case=False, na=False)]
        
        busca_rede = request.form.get('busca_rede', '')
        if busca_rede: df_filtrado = df_filtrado[df_filtrado['REDE'] == busca_rede]
        
        busca_saude = request.form.get('busca_saude', '')
        if busca_saude: df_filtrado = df_filtrado[df_filtrado['SAUDE'] == busca_saude]

        busca_odonto = request.form.get('busca_odonto', '')
        if busca_odonto: df_filtrado = df_filtrado[df_filtrado['ODONTO'] == busca_odonto]

        if not df_filtrado.empty:
            df_filtrado['DATA_VIGENCIA'] = df_filtrado['DATA_VIGENCIA'].apply(formatar_data_br)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, index=False, sheet_name='Negociacoes_Vigentes')
        buffer.seek(0)

        return send_file(buffer, as_attachment=True, download_name="municipios_negociados.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        flash("Erro ao gerar Excel.", "error")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=8000)
