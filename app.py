from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
import qrcode

app = Flask(__name__)

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

# ⚠️ IMPORTANTE: Rodar SEMPRE, até na nuvem!
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
        with sqlite3.connect('caixas.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO caixas VALUES (?, ?, ?, ?, ?, ?)', dados)
            conn.commit()

        # URL base pública do Render
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
    return render_template('caixa.html', dados=dados)
