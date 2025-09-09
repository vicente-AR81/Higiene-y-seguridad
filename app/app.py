from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import json

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://us3nqfawfptvkb6y:xEQCWJCnlS8JQSgNWUFm@balklvwchlpbnxgbnmai-mysql.services.clever-cloud.com:3306/balklvwchlpbnxgbnmai'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(120), unique=True, nullable=False)
    legajo = db.Column(db.String(20), unique=True, nullable=False)

class Incidente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.Text, nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    mail = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.DateTime, default=db.func.current_timestamp())
    x = db.Column(db.Integer)   # nueva columna
    y = db.Column(db.Integer)   # nueva columna


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
            "mail": usuario.mail
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
        return render_template('index.html', usuario=session['usuario'])
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
        x = request.form.get('x', None)
        y = request.form.get('y', None)

        usuario = session['usuario']

        nuevo_incidente = Incidente(
            descripcion=descripcion,
            sector=sector,
            nombre=usuario['nombre'],
            apellido=usuario['apellido'],
            mail=usuario['mail'],
            x=int(x) if x else None,
            y=int(y) if y else None
        )
        db.session.add(nuevo_incidente)
        db.session.commit()
        flash("Incidente reportado con éxito.")
        return redirect(url_for('list'))


    return render_template('form.html')


@app.route('/list')
def list():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    incidentes = Incidente.query.all()
    return render_template('list.html', incidentes=incidentes)

@app.route('/map')
def mapa():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    incidentes = Incidente.query.all()

    incidentes_json = []
    for inc in incidentes:
        incidentes_json.append({
            "descripcion": inc.descripcion,
            "sector": inc.sector,
            "nombre": inc.nombre,
            "apellido": inc.apellido,
            "mail": inc.mail,
            "fecha": inc.fecha.strftime("%Y-%m-%d %H:%M"),
            "x": inc.x or 100,   # fallback
            "y": inc.y or 100    # fallback
        })

    return render_template("map.html", incidentes_json=json.dumps(incidentes_json))


with app.app_context():
    db.create_all()
    
if __name__ == '__main__':
    app.run(debug=True, port=3000)


