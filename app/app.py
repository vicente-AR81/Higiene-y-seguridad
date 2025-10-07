import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://us3nqfawfptvkb6y:xEQCWJCnlS8JQSgNWUFm@balklvwchlpbnxgbnmai-mysql.services.clever-cloud.com:3306/balklvwchlpbnxgbnmai'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(120), unique=True, nullable=False)
    legajo = db.Column(db.String(20), unique=True, nullable=False)
    es_admin = db.Column(db.Boolean, default=False)

class Incidente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    x = db.Column(db.Integer)
    y = db.Column(db.Integer)
    foto = db.Column(db.String(255))
    tipo_riesgo = db.Column(db.String(50))
    resuelto = db.Column(db.Boolean, default=False)


@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    mail = request.form['mail']
    legajo = request.form['legajo']

    usuario = Usuario.query.filter_by(mail=mail, legajo=legajo).first()
    if usuario:
        session['usuario'] = {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "mail": usuario.mail,
            "es_admin": usuario.es_admin
        }
        return redirect(url_for('index'))
    else:
        flash("Datos incorrectos o usuario no registrado")
        return redirect(url_for('login'))


@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/registro', methods=['POST'])
def registro_post():
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    mail = request.form['mail']
    legajo = request.form['legajo']

    if Usuario.query.filter_by(mail=mail).first():
        flash("El mail ya está registrado.")
        return redirect(url_for('registro'))

    nuevo_usuario = Usuario(nombre=nombre, apellido=apellido, mail=mail, legajo=legajo)
    db.session.add(nuevo_usuario)
    db.session.commit()
    flash("Registro exitoso. Iniciá sesión.")
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'usuario' in session:
        incidentes = Incidente.query.all()

        incidentes_json = []
        for inc in incidentes:
            incidentes_json.append({
                "descripcion": inc.descripcion,
                "sector": inc.sector,
                "tipo_riesgo": inc.tipo_riesgo,
                "nombre": inc.nombre,
                "apellido": inc.apellido,
                "mail": inc.mail,
                "fecha": inc.fecha.strftime("%Y-%m-%d %H:%M"),
                "x": inc.x or 100,   # fallback
                "y": inc.y or 100,    # fallback
                "foto": url_for('static', filename=f"uploads/{inc.foto}") if inc.foto else None
            })

        return render_template('index.html', usuario=session['usuario'], incidentes=incidentes, incidentes_json=json.dumps(incidentes_json))
    else:
        return redirect(url_for('login'))
    
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/form', methods=['GET', 'POST'])
def form():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        descripcion = request.form['descripcion']
        sector = request.form['sector']
        tipo_riesgo = request.form.get('tipo_riesgo')  
        x = request.form.get('x', None)
        y = request.form.get('y', None)

        usuario = session['usuario']

        nuevo_incidente = Incidente(
            descripcion=descripcion,
            sector=sector,
            tipo_riesgo=tipo_riesgo,  
            nombre=usuario['nombre'],
            apellido=usuario['apellido'],
            mail=usuario['mail'],
            x=int(x) if x else None,
            y=int(y) if y else None
        )

        # Guardar foto si existe
        if 'foto' in request.files:
            foto = request.files['foto']
            if foto and foto.filename != '':
                filename = secure_filename(foto.filename)
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                foto.save(os.path.join(upload_folder, filename))
                nuevo_incidente.foto = filename

        db.session.add(nuevo_incidente)
        db.session.commit()
        flash("Incidente reportado con éxito.")
        return redirect(url_for('index'))

    tipos_riesgo = [
        "Eléctrico", "Físico", "Químico", "Biológico",
        "Ergonómico", "Mecánico", "Ambiental", "Estructural"
    ]
    return render_template('form.html', tipos_riesgo=tipos_riesgo)


@app.route('/actualizar_resuelto/<int:id>', methods=['POST'])
def actualizar_resuelto(id):
    if 'usuario' not in session or not session['usuario'].get('es_admin'):
        return jsonify({"error": "No autorizado"}), 403

    data = request.get_json()
    estado = data.get('resuelto', False)

    incidente = Incidente.query.get_or_404(id)
    incidente.resuelto = estado
    db.session.commit()

    return jsonify({"success": True})

with app.app_context():
    db.create_all()
    
if __name__ == '__main__':
    app.run(debug=True, port=3000)
