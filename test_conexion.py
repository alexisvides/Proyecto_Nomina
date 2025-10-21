"""
Script de prueba para verificar la conexión a SQL Server
"""
from db import get_connection

try:
    print("🔄 Intentando conectar a SQL Server...")
    conn = get_connection()
    print("✅ ¡Conexión exitosa!")
    
    # Probar una consulta simple
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION as version")
    row = cursor.fetchone()
    print(f"\n📊 Versión de SQL Server:")
    print(f"   {row[0][:100]}...")
    
    # Verificar la base de datos
    cursor.execute("SELECT DB_NAME() as database_name")
    db_name = cursor.fetchone()[0]
    print(f"\n💾 Base de datos actual: {db_name}")
    
    # Listar tablas
    cursor.execute("""
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """)
    
    tablas = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 Tablas en la base de datos ({len(tablas)}):")
    for tabla in tablas:
        print(f"   - {tabla}")
    
    cursor.close()
    conn.close()
    print("\n✅ Conexión cerrada correctamente")
    
except Exception as e:
    print(f"\n❌ Error de conexión:")
    print(f"   {e}")
    print("\n💡 Posibles soluciones:")
    print("   1. Verifica que SQL Server esté corriendo")
    print("   2. Verifica el nombre de usuario y contraseña")
    print("   3. Verifica que la base de datos 'proyecto' exista")
    print("   4. Verifica que el protocolo TCP/IP esté habilitado")
