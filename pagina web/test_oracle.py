import os
import oracledb
from dotenv import load_dotenv # <-- NUEVO IMPORT

# Cargar variables del archivo .env
load_dotenv() # <-- NUEVA LÍNEA: Esto carga las variables en os.environ

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
    Asegúrate de que la carpeta 'Wallet_LACTEOSDB' exista en la misma ubicación que test_oracle.py.
    """)


# 🔥 MUY IMPORTANTE: limpiar influencia del Oracle local
if "ORACLE_HOME" in os.environ:
    del os.environ["ORACLE_HOME"]

if "TNS_ADMIN" in os.environ:
    del os.environ["TNS_ADMIN"]

# Ahora forzamos el wallet
os.environ["TNS_ADMIN"] = WALLET_DIR

# Importar oracledb DESPUÉS de setear TNS_ADMIN (tu lógica original, mantenida)
# En este caso, como lo importamos al principio, TNS_ADMIN ya está seteado.
# La instrucción "importar DESPUÉS" es más crítica si se llama a oracledb.init_oracle_client()
# o si hubiera múltiples configuraciones de TNS_ADMIN.
# Para este script simple, dejarlo al principio está bien.

print("Usando TNS_ADMIN:", os.environ.get("TNS_ADMIN"))
print(f"Intentando conectar como usuario: {DB_USER} al servicio: {DB_SERVICE_NAME}")


try:
    conn = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=DB_SERVICE_NAME,  # Usamos el service name del tnsnames.ora
        config_dir=WALLET_DIR,
        wallet_location=WALLET_DIR,
        wallet_password=DB_WALLET_PASSWORD
    )

    print("✅ CONEXIÓN EXITOSA A ORACLE CLOUD")
    conn.close()

except oracledb.DatabaseError as e:
    error_obj, = e.args
    print("❌ Error de conexión:")
    print("Código:", error_obj.code)
    print("Mensaje:", error_obj.message)

except Exception as e:
    print("❌ Error general:", repr(e))