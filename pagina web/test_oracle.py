import os
import oracledb

# --- Configuración de Conexión a Oracle Cloud (¡Usando Variables de Entorno para Seguridad!) ---
# Estas variables deberían configurarse en tu sistema operativo o en tu entorno de despliegue.
# Por ejemplo, en Windows PowerShell:
# $env:DB_USER="ADMIN"
# $env:DB_PASSWORD="Lacteos#2024" # Contraseña del usuario de la DB
# $env:DB_SERVICE_NAME="lacteosdb_high" # El nombre de servicio que usas en el tnsnames.ora
# $env:DB_WALLET_PASSWORD="Lacteos#2024" # Contraseña del wallet (usualmente la misma que la del DB user ADMIN)

# Obtener credenciales del entorno
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_SERVICE_NAME = os.environ.get("DB_SERVICE_NAME")
WALLET_PASSWORD = os.environ.get("DB_WALLET_PASSWORD")

# --- CALCULAR RUTA DEL WALLET RELATIVA AL PROYECTO ---
# Esto hace que la aplicación encuentre el wallet sin importar dónde se clone el proyecto.
# __file__ es la ruta del archivo actual (test_oracle.py)
# os.path.dirname(__file__) obtiene el directorio donde está test_oracle.py ('pagina web')
# os.path.join(...) construye la ruta final: 'pagina web/Wallet_LACTEOSDB'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WALLET_DIR = os.path.join(BASE_DIR, "Wallet_LACTEOSDB")

# Verificar que todas las variables de entorno estén configuradas
if not all([DB_USER, DB_PASSWORD, DB_SERVICE_NAME, WALLET_PASSWORD]):
    raise ValueError("""
    ¡ERROR DE CONFIGURACIÓN!
    Por favor, asegúrate de configurar las siguientes variables de entorno antes de ejecutar:
    DB_USER, DB_PASSWORD, DB_SERVICE_NAME, DB_WALLET_PASSWORD
    Ejemplo para Windows PowerShell:
    $env:DB_USER="ADMIN"
    $env:DB_PASSWORD="Lacteos#2024"
    $env:DB_SERVICE_NAME="lacteosdb_high"
    $env:DB_WALLET_PASSWORD="Lacteos#2024"
    """)

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
        wallet_password=WALLET_PASSWORD
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