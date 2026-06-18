"""
EnglishFlow Server — Flask Backend
Painel do aluno + Admin de materiais + API para o bot
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from database import init_db, get_user_by_code, get_user_by_telegram_id, create_user, get_materials, add_material, delete_material, create_payment, confirm_payment, get_all_users, toggle_material_progress, get_user_progress, get_completed_materials, get_admin_stats

# ── CONFIG ──
app = Flask(__name__)
app.secret_key = os.environ.get("ENGLISHFLOW_SECRET", "englishflow_secret_key_2026")
ADMIN_PASSWORD = os.environ.get("ENGLISHFLOW_ADMIN_PASS", "admin123")

BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "materiais")
TEMPLATE_FOLDER = os.path.join(BASE_DIR, "templates")
STATIC_FOLDER = os.path.join(BASE_DIR, "assets")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TEMPLATE_FOLDER, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.template_folder = TEMPLATE_FOLDER

# Initialize database
init_db()

# ── SERVE STATIC (landing page + assets) ──

@app.route('/')
def home():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory(STATIC_FOLDER, filename)

@app.route('/privacidade')
def privacidade():
    return send_from_directory(BASE_DIR, 'privacidade.html')

# ── LOGIN ──

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        user = get_user_by_code(code)
        if user:
            session['user'] = user
            return redirect(url_for('painel'))
        else:
            return render_template('login.html', error='Codigo invalido. Verifique e tente novamente.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))


# ── PAINEL DO ALUNO ──

@app.route('/painel')
def painel():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = session['user']
    materials = get_materials(plan=user.get('plan'), user_id=user.get('id'))
    progress = get_user_progress(user['id'])
    completed = get_completed_materials(user['id'])
    return render_template('painel.html', user=user, materials=materials, progress=progress, completed=completed)


# ── DOWNLOAD DE MATERIAL ──

@app.route('/download/<int:material_id>')
def download_material(material_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    materials = get_materials()
    mat = next((m for m in materials if m['id'] == material_id), None)
    if not mat or not mat.get('filename'):
        return "Material nao encontrado", 404

    return send_from_directory(UPLOAD_FOLDER, mat['filename'], as_attachment=True)


# ── PROGRESSO TOGGLE ──

@app.route('/toggle/<int:material_id>')
def toggle_progress(material_id):
    if 'user' not in session:
        return redirect(url_for('login'))
    user_id = session['user']['id']
    toggle_material_progress(user_id, material_id)
    return redirect(url_for('painel'))


# ── CERTIFICADO ──

@app.route('/certificado')
def certificado():
    if 'user' not in session:
        return redirect(url_for('login'))
    user = session['user']
    progress = get_user_progress(user['id'])
    return render_template('certificado.html', user=user, progress=progress)


# ── ADMIN DASHBOARD ──

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    stats = get_admin_stats()
    return render_template('dashboard.html', stats=stats)


# ── ADMIN ──

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if 'password' in request.form:
            pwd = request.form.get('password')
            if pwd == ADMIN_PASSWORD:
                session['admin'] = True
            else:
                return render_template('admin_login.html', error='Senha incorreta')
        elif session.get('admin'):
            # Upload material
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            plan_level = request.form.get('plan_level', 'todos')
            file_type = request.form.get('file_type', 'pdf')
            user_id_str = request.form.get('user_id', '')
            user_id = int(user_id_str) if user_id_str else None
            file = request.files.get('file')

            if title and file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                add_material(title, description, filename, file_type, plan_level, user_id)
                return redirect(url_for('admin'))

        # Delete material
        delete_id = request.form.get('delete_id')
        if delete_id and session.get('admin'):
            delete_material(int(delete_id))
            return redirect(url_for('admin'))

    if not session.get('admin'):
        return render_template('admin_login.html')

    users = get_all_users()
    materials = get_materials()
    # Resolve user names for materials
    users_by_id = {u['id']: u['name'] for u in users}
    for m in materials:
        m['assigned_to'] = users_by_id.get(m.get('user_id')) if m.get('user_id') else None
    return render_template('admin.html', materials=materials, users=users)


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))


# ── API PARA O BOT ──

@app.route('/api/create-user', methods=['POST'])
def api_create_user():
    """Bot chama esta rota quando pagamento é confirmado."""
    data = request.get_json()
    telegram_id = data.get('telegram_id')
    name = data.get('name')
    plan = data.get('plan')

    if not telegram_id or not plan:
        return jsonify({'error': 'Campos obrigatorios ausentes'}), 400

    existing = get_user_by_telegram_id(telegram_id)
    if existing:
        return jsonify({'access_code': existing['access_code'], 'exists': True})

    user = create_user(telegram_id, name, plan)
    if user:
        return jsonify({'access_code': user['access_code'], 'exists': False})
    return jsonify({'error': 'Falha ao criar usuario'}), 500


@app.route('/api/users')
def api_users():
    """Lista usuarios (admin only via token)."""
    token = request.args.get('token')
    if token != ADMIN_PASSWORD:
        return jsonify({'error': 'Nao autorizado'}), 403

    from database import get_db
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── ERROR HANDLERS ──

@app.errorhandler(404)
def not_found(e):
    return send_from_directory(BASE_DIR, '404.html'), 404


# ── MAIN ──

if __name__ == '__main__':
    print("[EnglishFlow Server] Iniciando em http://localhost:5000")
    print("[EnglishFlow Server] Login: http://localhost:5000/login")
    print("[EnglishFlow Server] Admin: http://localhost:5000/admin")
    app.run(host='0.0.0.0', port=5000, debug=False)
