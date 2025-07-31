from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os
import qrcode
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB por arquivo

# Extensões permitidas
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Cria banco e tabela se não existir
def init_db():
    with sqlite3.connect('caixas.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS caixas (
                codigo TEXT PRIMARY KEY,
                documento TEXT,
                cliente TEXT,
                periodo TEXT,
                localizacao TEXT,
                obs TEXT
            )
        ''')
        conn.commit()

init_db()

@app.route('/')
def home():
    return redirect(url_for('cadastrar'))

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        dados = (
            request.form['codigo'],
            request.form['documento'],
            request.form['cliente'],
            request.form['periodo'],
            request.form['localizacao'],
            request.form['obs']
        )
        # Salva info da caixa
        with sqlite3.connect('caixas.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO caixas VALUES (?, ?, ?, ?, ?, ?)', dados)
            conn.commit()

        # Salva os PDFs enviados
        files = request.files.getlist('arquivos')
        caixa_dir = os.path.join(app.config['UPLOAD_FOLDER'], dados[0])
        os.makedirs(caixa_dir, exist_ok=True)
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(caixa_dir, filename))

        # Gera QR Code
        base_url = "https://caixas-qr.onrender.com"
        qr_path = os.path.join('static', f"qr_{dados[0]}.png")
        img = qrcode.make(f"{base_url}/caixa/{dados[0]}")
        img.save(qr_path)

        return redirect(url_for('ver_caixa', codigo=dados[0]))
    return render_template('form.html')

@app.route('/caixa/<codigo>')
def ver_caixa(codigo):
    with sqlite3.connect('caixas.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM caixas WHERE codigo = ?', (codigo,))
        dados = cursor.fetchone()
    # Lista PDFs da caixa
    caixa_dir = os.path.join(app.config['UPLOAD_FOLDER'], codigo)
    arquivos = []
    if os.path.exists(caixa_dir):
        arquivos = [f for f in os.listdir(caixa_dir) if allowed_file(f)]
    return render_template('caixa.html', dados=dados, arquivos=arquivos, codigo=codigo)

# Para servir arquivos PDF (não obrigatório, mas seguro)
@app.route('/static/uploads/<codigo>/<filename>')
def download_arquivo(codigo, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], codigo), filename)

