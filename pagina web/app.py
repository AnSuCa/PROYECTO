from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import os
import oracledb
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

# Evitar que el navegador cachee páginas protegidas (para que "Atrás" no muestre el dashboard tras logout)
@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# --- Configuración de Conexión a Oracle Cloud ---
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_SERVICE_NAME = os.environ.get("DB_SERVICE_NAME")
DB_WALLET_PASSWORD = os.environ.get("DB_WALLET_PASSWORD")

# --- CALCULAR RUTA DEL WALLET RELATIVA AL PROYECTO ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_DIR = os.path.join(BASE_DIR, "Wallet_LACTEOSDB")

# Verificar que todas las variables estén configuradas
if not all([DB_USER, DB_PASSWORD, DB_SERVICE_NAME, DB_WALLET_PASSWORD]):
    raise ValueError("""
    ¡ERROR DE CONFIGURACIÓN!
    Por favor, asegúrate de configurar las siguientes variables en tu archivo .env
    (ubicado en la misma carpeta que app.py):
    DB_USER, DB_PASSWORD, DB_SERVICE_NAME, DB_WALLET_PASSWORD
    """)

# Verificar si la carpeta del wallet existe
if not os.path.isdir(WALLET_DIR):
    raise FileNotFoundError(f"""
    ¡ERROR: La carpeta del Wallet no se encuentra!
    Se esperaba en: {WALLET_DIR}
    Asegúrate de que la carpeta 'Wallet_LACTEOSDB' exista en la misma ubicación que app.py.
    """)

# Limpiar posibles influencias de Oracle local
if "ORACLE_HOME" in os.environ:
    del os.environ["ORACLE_HOME"]
if "TNS_ADMIN" in os.environ:
    del os.environ["TNS_ADMIN"]

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
        raise

# Página principal
@app.route('/')
def home():
    if 'idusuario' in session:
        return redirect(url_for('user'))
    return render_template('index.html')


# Dashboard de usuario
@app.route('/user')
def user():
    if 'idusuario' not in session:
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Productos + unidad de medida
        cursor.execute("""
            SELECT 
                P.IDPRODUCTO,      -- 0
                P.NOMBRE,          -- 1
                P.DESCRIPCION,     -- 2
                P.ACTIVO,          -- 3
                P.CANTIDAD,        -- 4
                U.NOMBRE,          -- 5 nombre unidad
                U.SIMBOLO,         -- 6 símbolo unidad
                P.IDUNIDAD         -- 7 idunidad
            FROM PRODUCTO P
            JOIN UNIDADMEDIDA U
                ON P.IDUNIDAD = U.IDUNIDAD
            ORDER BY P.IDPRODUCTO
        """)
        productos = cursor.fetchall()

        # Categorías
        cursor.execute("""
            SELECT IDCATEGORIA, NOMBRE
            FROM CATEGORIAPRODUCTO
            ORDER BY NOMBRE
        """)
        categorias = cursor.fetchall()

        # Unidades (para los selects)
        cursor.execute("""
            SELECT IDUNIDAD, NOMBRE, SIMBOLO
            FROM UNIDADMEDIDA
            ORDER BY NOMBRE
        """)
        unidades = cursor.fetchall()

        cursor.close()
        conn.close()

    except oracledb.Error as e:
        print("Error Oracle al listar datos:", e)
        productos = []
        categorias = []
        unidades = []
    except Exception as e:
        print("Error general:", e)
        productos = []
        categorias = []
        unidades = []

    return render_template(
        'dashboar.html',
        productos=productos,
        categorias=categorias,
        unidades=unidades,
        nombre=session.get('nombre')
    )


# Registro de usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validación simple
        if not nombre or not email or not password:
            return render_template('register.html', error="Completa todos los campos")

        # Encriptar contraseña
        password_hash = generate_password_hash(password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO USUARIO (NOMBRE, EMAIL, PASSWORDHASH, FECHAREGISTRO, ACTIVO)
                VALUES (:1, :2, :3, SYSTIMESTAMP, 1)
            """, (nombre, email, password_hash))

            conn.commit()
            cursor.close()
            conn.close()

            return render_template('register.html', mensaje="Usuario registrado exitosamente ✅")

        except oracledb.IntegrityError:
            return render_template('register.html', error="El correo ya está registrado")
        except oracledb.Error as e:
            print("Error Oracle en registro:", e)
            return render_template('register.html', error=f"Error al registrar usuario: {e}")
        except Exception as e:
            print("Error general en registro:", e)
            return render_template('register.html', error=f"Error inesperado: {e}")

    return render_template('register.html')

# Panel admin (si lo usas)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'idusuario' not in session or session.get('categoria') != 'admin':
        return redirect(url_for('login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        if request.method == 'POST':
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            idcategoria = request.form.get('idcategoria')
            idunidad = request.form.get('idunidad')

            cursor.execute("""
                INSERT INTO PRODUCTO (NOMBRE, DESCRIPCION, IDCATEGORIA, IDUNIDAD, ACTIVO, IDUSUARIOCREADOR)
                VALUES (:1, :2, :3, :4, 1, :5)
            """, (nombre, descripcion, idcategoria, idunidad, session['idusuario']))
            conn.commit()

        cursor.execute("""
            SELECT IDPRODUCTO, NOMBRE, DESCRIPCION, ACTIVO
            FROM PRODUCTO
            ORDER BY IDPRODUCTO
        """)
        productos = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('admin_temp.html', productos=productos)
    except oracledb.Error as e:
        print("Error Oracle en admin:", e)
        return f"Error en la sección de administración: {e}"
    except Exception as e:
        print("Error general en admin:", e)
        return f"Error inesperado en administración: {e}"

# Eliminar producto (admin)
@app.route('/delete', methods=['POST'])
def delete():
    if 'idusuario' not in session or session.get('categoria') != 'admin':
        return redirect(url_for('login'))

    try:
        idproducto = request.form.get('idproducto')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM PRODUCTO WHERE IDPRODUCTO = :1", (idproducto,))
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('admin'))
    except oracledb.Error as e:
        print("Error Oracle en delete:", e)
        return f"Error al eliminar: {e}"
    except Exception as e:
        print("Error general en delete:", e)
        return f"Error inesperado al eliminar: {e}"

# Actualizar producto (admin)
@app.route('/update', methods=['POST'])
def update():
    if 'idusuario' not in session or session.get('categoria') != 'admin':
        return redirect(url_for('login'))

    try:
        idproducto = request.form.get('llave')
        nombre = request.form.get('nname')
        desc = request.form.get('ndesc')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE PRODUCTO
            SET NOMBRE = :1, DESCRIPCION = :2
            WHERE IDPRODUCTO = :3
        """, (nombre, desc, idproducto))
        conn.commit()

        cursor.close()
        conn.close()
        return redirect(url_for('admin'))
    except oracledb.Error as e:
        print("Error Oracle en update:", e)
        return f"Error al actualizar: {e}"
    except Exception as e:
        print("Error general en update:", e)
        return f"Error inesperado al actualizar: {e}"

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Si ya hay sesión y es solo una visita GET (por ejemplo, el usuario presionó "Atrás"),
    # lo mandamos directo al dashboard
    if request.method == 'GET' and 'idusuario' in session:
        return redirect(url_for('user'))

    if request.method == 'POST':
        email_form = request.form.get('usuario')
        password_form = request.form.get('password')

        if not email_form or not password_form:
            return render_template('login.html', error="Completa todos los campos")

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT IDUSUARIO, NOMBRE, PASSWORDHASH, ACTIVO
                FROM USUARIO
                WHERE EMAIL = :1
            """, (email_form,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row:
                idusuario, nombre, password_db, activo = row

                if check_password_hash(password_db, password_form):
                    session.clear()
                    session['idusuario'] = idusuario
                    session['nombre'] = nombre
                    session['activo'] = activo
                    session['categoria'] = 'usuario'
                    return redirect(url_for('user'))
                else:
                    return render_template('login.html', error="Usuario o contraseña incorrectos")
            else:
                return render_template('login.html', error="Usuario o contraseña incorrectos")

        except oracledb.Error as e:
            print("Error Oracle en login:", e)
            return render_template('login.html', error=f"Error al iniciar sesión: {e}")
        except Exception as e:
            print("Error general en login:", e)
            return render_template('login.html', error=f"Error inesperado: {e}")

    # GET sin sesión → mostrar login
    return render_template('login.html')

# Registrar productos desde el dashboard
@app.route('/registrar_producto', methods=['POST'])
def registrar_producto():
    if 'idusuario' not in session:
        return redirect(url_for('login'))

    try:
        nombre = request.form.get('nombre')
        descripcion = request.form.get('descripcion')
        idcategoria = request.form.get('idcategoria')
        idunidad = request.form.get('idunidad')
        cantidad = request.form.get('cantidad') or 0  # nuevo

        if not (nombre and idcategoria and idunidad):
            return "Faltan datos (nombre, categoría o unidad)"

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO PRODUCTO 
            (NOMBRE, DESCRIPCION, IDCATEGORIA, IDUNIDAD, CANTIDAD, ACTIVO, IDUSUARIOCREADOR)
            VALUES (:1, :2, :3, :4, :5, 1, :6)
        """, (
            nombre,
            descripcion,
            idcategoria,
            idunidad,
            cantidad,
            session['idusuario']
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('user'))

    except Exception as e:
        print("Error registrando producto:", e)
        return f"Error al registrar producto: {e}"


# Actualizar producto desde el dashboard
@app.route('/producto/actualizar', methods=['POST'])
def actualizar_producto():
    if 'idusuario' not in session:
        return redirect(url_for('login'))

    idproducto = request.form.get('idproducto')
    nombre = request.form.get('nombre')
    descripcion = request.form.get('descripcion')
    cantidad = request.form.get('cantidad')
    idunidad = request.form.get('idunidad')  # 👈 nuevo

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE PRODUCTO
            SET NOMBRE = :1,
                DESCRIPCION = :2,
                CANTIDAD = :3,
                IDUNIDAD = :4
            WHERE IDPRODUCTO = :5
        """, (nombre, descripcion, cantidad, idunidad, idproducto))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('user'))
    except Exception as e:
        print("Error actualizando producto:", e)
        return f"Error al actualizar producto: {e}"

# Eliminar producto desde el dashboard
@app.route('/producto/eliminar', methods=['POST'])
def eliminar_producto():
    if 'idusuario' not in session:
        return redirect(url_for('login'))

    idproducto = request.form.get('idproducto')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM PRODUCTO WHERE IDPRODUCTO = :1", (idproducto,))
        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for('user'))
    except Exception as e:
        print("Error eliminando producto:", e)
        return f"Error al eliminar producto: {e}"

# Registrar envío de producto por correo (solo en BD por ahora)
@app.route('/producto/enviar_correo', methods=['POST'])
def enviar_producto_correo():
    if 'idusuario' not in session:
        return redirect(url_for('login'))

    idproducto = request.form.get('idproducto')
    email_destino = request.form.get('email_destino')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtenemos datos del producto
        cursor.execute("""
            SELECT NOMBRE, DESCRIPCION
            FROM PRODUCTO
            WHERE IDPRODUCTO = :1
        """, (idproducto,))
        row = cursor.fetchone()

        if not row:
            cursor.close()
            conn.close()
            return "Producto no encontrado"

        nombre_prod, desc_prod = row

        asunto = f"Información del producto: {nombre_prod}"
        cuerpo = f"Producto: {nombre_prod}\nDescripción: {desc_prod}"

        # Buscamos si el destinatario existe como usuario (opcional)
        cursor.execute("""
            SELECT IDUSUARIO FROM USUARIO WHERE EMAIL = :1
        """, (email_destino,))
        dest_row = cursor.fetchone()
        idusuario_destino = dest_row[0] if dest_row else None

        cursor.execute("""
            INSERT INTO ENVIOCORREO (IDUSUARIODESTINO, ASUNTO, CUERPO, FECHAENVIO, ENVIADO)
            VALUES (:1, :2, :3, SYSTIMESTAMP, 0)
        """, (idusuario_destino, asunto, cuerpo))

        conn.commit()
        cursor.close()
        conn.close()

        # Aquí en el futuro puedes agregar envío real por SMTP
        return redirect(url_for('user'))

    except Exception as e:
        print("Error registrando envío de correo:", e)
        return f"Error al enviar producto por correo: {e}"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/search')
def search():
    return render_template('buscar.html')

@app.route('/updat')
def updat():
    return render_template('update.html')

if __name__ == '__main__':
    app.run(debug=True)
