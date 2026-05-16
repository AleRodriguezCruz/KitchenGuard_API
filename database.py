import sqlite3

DB_NAME = "kitchenguard.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sensor_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            type      TEXT NOT NULL,
            value     REAL NOT NULL,
            alert     INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS timers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            label      TEXT NOT NULL,
            duration   INTEGER NOT NULL,
            active     INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS panic_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
             atendido  INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alertas_eventos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            type          TEXT NOT NULL,
            valor_inicio  REAL NOT NULL,
            valor_pico    REAL DEFAULT 0,
            timestamp_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
            timestamp_fin    DATETIME DEFAULT NULL,
            activa        INTEGER DEFAULT 1
        );
    """)
    conn.commit()


    # Migración segura: si la tabla ya existía sin la columna, la agrega
    try:
        cursor.execute("ALTER TABLE panic_events ADD COLUMN atendido INTEGER DEFAULT 0")
        conn.commit()
        print("✅ Migración: columna 'atendido' agregada")
    except sqlite3.OperationalError:
        pass  # La columna ya existe, no hay nada que hacer

    # Valor por defecto del modo
    try:
        cursor.execute("INSERT OR IGNORE INTO config (key, value) VALUES ('modo', 'todo')")
        conn.commit()
        print("✅ Config: modo inicial insertado")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alertas_eventos (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                type             TEXT NOT NULL,
                valor_inicio     REAL NOT NULL,
                valor_pico       REAL DEFAULT 0,
                timestamp_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
                timestamp_fin    DATETIME DEFAULT NULL,
                activa           INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        print("✅ Tabla alertas_eventos creada")
    except sqlite3.OperationalError:
        pass
    conn.close()
