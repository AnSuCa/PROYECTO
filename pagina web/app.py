from flask import Flask,app, render_template, request, redirect, session, url_for
from werkzeug.security import  generate_password_hash, check_password_hash # Importar check_password_hash si lo usas para login
import os
import oracledb
from dotenv import load_dotenv # <-- NUEVO IMPORT

# Cargar variables del archivo .env
load_dotenv() # <-- NUEVA LÍNEA: Esto carga las variables en os.environ
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# --- Configuración de Conexión a Oracle Cloud ---
# Obtener credenciales del entorno (ahora provienen del .env cargado)
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_SERVICE_NAME = os.environ.get("DB_SERVICE_NAME")
DB_WALLET_PASSWORD = os.environ.get("DB_WALLET_PASSWORD")

# ... (el resto del código sigue igual) ...

# --- CALCULAR RUTA DEL WALLET RELATIVA AL PROYECTO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_DIR = os.path.join(BASE_DIR, "Wallet_LACTEOSDB")

# Verificar que todas las variables estén configuradas (ahora incluyendo el mensaje de .env)
if not all([DB_USER, DB_PASSWORD, DB_SERVICE_NAME, DB_WALLET_PASSWORD]):
    raise ValueError("""
    ¡ERROR DE CONFIGURACIÓN!
    Por favor, asegúrate de configurar las siguientes variables en tu archivo .env
    (ubicado en la misma carpeta que test_oracle.py):
    DB_USER, DB_PASSWORD, DB_SERVICE_NAME, DB_WALLET_PASSWORD
    Y también el archivo .env debe ser cargado al inicio del script.
    """)

# ... (el resto del código es idéntico a la versión anterior) ...

# Verificar si la carpeta del wallet existe
if not os.path.isdir(WALLET_DIR):
    raise FileNotFoundError(f"""
    ¡ERROR: La carpeta del Wallet no se encuentra!
    Se esperaba en: {WALLET_DIR}
    Asegúrate de que la carpeta 'Wallet_LACTEOSDB' exista en la misma ubicación que app.py.
    """)

# Limpiar posibles influencias de Oracle local (tu código original)
if "ORACLE_HOME" in os.environ: del os.environ["ORACLE_HOME"]
if "TNS_ADMIN" in os.environ: del os.environ["TNS_ADMIN"]

# Forzar TNS_ADMIN para que el driver sepa dónde buscar el tnsnames.ora
os.environ["TNS_ADMIN"] = WALLET_DIR

# --- Función de Conexión a la base de datos Oracle ---
def get_db_connection():
    try:
        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            dsn=DB_SERVICE_NAME,
            config_dir=WALLET_DIR,
            wallet_location=WALLET_DIR,
            wallet_password=DB_WALLET_PASSWORD
        )
        return conn
    except oracledb.DatabaseError as e:
        error_obj, = e.args
        print(f"❌ Error de conexión a la base de datos: Código {error_obj.code}, Mensaje: {error_obj.message}")
        raise # Relanzar el error para que Flask lo capture y muestre un 500

# --- Rutas de tu aplicación Flask (el resto del código sigue igual) ---
# ... (todo tu código de Flask register, login, admin, etc.) ...

# Página principal
@app.route('/')
def home():
    return render_template('index.html')
#Registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')

        if not nombre or not email or not password:
            return render_template('register.html', error="Completa todos los campos")

        # Encriptamos la contraseña
        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO Usuario (Nombre, Email, PasswordHash)
                VALUES (:1, :2, :3)
            """, (nombre, email, password_hash))

            conn.commit()
            cursor.close()
            conn.close()

            # Muestra mensaje en la misma página
            return render_template('register.html', mensaje="Usuario registrado exitosamente ✅")

        except oracledb.IntegrityError:
            # Por ejemplo, si Email es UNIQUE
            return render_template('register.html', error="El correo ya está registrado")

        except oracledb.Error as e:
            print("Error Oracle en registro:", e)
            return render_template('register.html', error=f"Error al registrar usuario: {e}")
        except Exception as e:
            print("Error general en registro:", e)
            return render_template('register.html', error=f"Error inesperado: {e}")

    # GET
    return render_template('register.html')


# Inicio de sesión
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_form = request.form.get('usuario')
        password_form = request.form.get('password')

        # DEBUG opcional:
        print("DEBUG login email:", email_form)
        print("DEBUG login pass:", password_form)

        if not email_form or not password_form:
            return render_template('login.html', error="Completa todos los campos")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT IDUSUARIO, NOMBRE, PASSWORDHASH, ACTIVO
                FROM USUARIO
                WHERE EMAIL = :1
                """,
                (email_form,)
            )
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            print("DEBUG row:", row)  # para ver qué trae

            if row:
                idusuario, nombre, password_db, activo = row

                if check_password_hash(password_db, password_form):
                    session.clear()
                    session['idusuario'] = idusuario
                    session['nombre'] = nombre
                    session['activo'] = activo
                    session['categoria'] = 'usuario'

                    print("DEBUG: login OK, redirigiendo a /user")
                    return redirect(url_for('user'))
                else:
                    print("DEBUG: contraseña incorrecta")
                    return render_template('login.html', error="Usuario o contraseña incorrectos")
            else:
                print("DEBUG: no se encontró usuario")
                return render_template('login.html', error="Usuario o contraseña incorrectos")

        except oracledb.Error as e:
            print("Error Oracle en login:", e)
            return render_template('login.html', error=f"Error al iniciar sesión: {e}")
        except Exception as e:
            print("Error general en login:", e)
            return render_template('login.html', error=f"Error inesperado: {e}")
    else:
        return render_template('login.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('categoria') != 'admin':
        return "Acceso denegado"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            nombre = request.form['name']
            descp = request.form['description']
            id_item = request.form['id']

            cursor.execute(
                """
                INSERT INTO items (nombre, descripcion, id)
                VALUES (:1, :2, :3)
                """,
                (nombre, descp, id_item)
            )
            conn.commit()

        cursor.execute("SELECT * FROM producto")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_temp.html', items=items)

    except oracledb.Error as e:
        print("Error Oracle en admin:", e)
        return f"Error en la sección de administración: {e}"
    except Exception as e:
        print("Error general en admin:", e)
        return f"Error inesperado en administración: {e}"


@app.route('/user')
def user():
    if 'idusuario' not in session:
        return redirect(url_for('login'))

    if session.get('categoria') != 'usuario':
        return "Acceso denegado"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM producto")
        items = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('dashboar.html', 
                               items=items, 
                               nombre=session.get('nombre'))
    except oracledb.Error as e:
        print("Error Oracle en user:", e)
        return f"Error en la sección de usuario: {e}"
    except Exception as e:
        print("Error general en user:", e)
        return f"Error inesperado en usuario: {e}"



@app.route('/delete', methods=['GET', 'POST'])
def delete():
    if session.get('categoria') != 'admin': 
        return "Acceso denegado"

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            ide = request.form['llav']
            cursor.execute("DELETE FROM producto WHERE id = :1", (ide,))
            conn.commit()

        cursor.execute("SELECT * FROM producto")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_temp.html', items=items)

    except oracledb.Error as e:
        print("Error Oracle en delete:", e)
        return f"Error al eliminar: {e}"
    except Exception as e:
        print("Error general en delete:", e)
        return f"Error inesperado al eliminar: {e}"

@app.route('/update', methods=['POST'])
def update():
    if session.get('categoria') != 'admin': 
        return "Acceso denegado"

    try:
        nombre = request.form['nname']
        desc = request.form['ndesc']
        id_item = request.form['llave']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE producto
            SET nombre = :1, descripcion = :2
            WHERE id = :3
            """,
            (nombre, desc, id_item)
        )
        conn.commit()

        cursor.execute("SELECT * FROM items")
        items = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin_temp.html', items=items)

    except oracledb.Error as e:
        print("Error Oracle en update:", e)
        return f"Error al actualizar: {e}"
    except Exception as e:
        print("Error general en update:", e)
        return f"Error inesperado al actualizar: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/search')
def search():
    return render_template('buscar.html')

@app.route('/updat')
def updat():
    return render_template('update.html')

if __name__ == '__main__':
    app.run(debug=True)