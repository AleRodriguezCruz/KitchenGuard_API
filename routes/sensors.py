from flask import Blueprint, request, jsonify
from database import get_connection

sensors_bp = Blueprint("sensors", __name__)
# Último valor en memoria (no se guarda en BD)
ultimo_valor = {}

COOLDOWN_SEGUNDOS = 180  # 3 minutos

OPC_VALIDAS = ["solo_alertas", "cada_5min", "cada_30min", "cada_hora", "cada_24h"]
INTERVALO_OPC = {
    "cada_5min":  5 * 60,
    "cada_30min": 30 * 60,
    "cada_hora":  60 * 60,
    "cada_24h":   24 * 60 * 60,
}

def guardar_lectura(conn, sensor_type, opc):
    intervalo = INTERVALO_OPC.get(opc)
    if not intervalo:
        return True  
    
    ultima = conn.execute(
        "SELECT timestamp FROM sensor_events WHERE type=? AND alert=0 ORDER BY timestamp DESC LIMIT 1",
        (sensor_type,)
    ).fetchone()
    
    if not ultima:
        return True  # primera lectura, guardar siempre
    
    segundos_actuales = int(conn.execute("SELECT strftime('%s','now')").fetchone()[0])
    segundos_ultima   = int(conn.execute(
        "SELECT strftime('%s', ?)", (ultima["timestamp"],)
    ).fetchone()[0])
    
    return (segundos_actuales - segundos_ultima) >= intervalo

def get_modo_actual():
    conn = get_connection()
    row = conn.execute("SELECT value FROM config WHERE key = 'modo'").fetchone()
    conn.close()
    return row["value"] if row else "solo_alertas"

def en_cooldown(conn, sensor_type):
    row = conn.execute(
        "SELECT value FROM config WHERE key=?",
        (f"cooldown_{sensor_type}",)
    ).fetchone()
    if not row:
        return False
    segundos_actuales = int(conn.execute("SELECT strftime('%s','now')").fetchone()[0])
    return (segundos_actuales - int(row["value"])) < COOLDOWN_SEGUNDOS

@sensors_bp.route("/api/sensor", methods=["POST"])
def receive_sensor():
    data = request.get_json()
    if not data or "type" not in data or "value" not in data:
        return jsonify({"error": "Faltan campos: type y value"}), 400

    sensor_type = data["type"]
    value       = data["value"]
    alert       = data.get("alert", 0)

    if get_modo_actual() == "solo_alertas" and alert == 0:
        return jsonify({"message": "Dato ignorado"}), 200

    conn = get_connection()

    # ─── Lógica de alertas_eventos ────
    evento_activo = conn.execute(
        "SELECT * FROM alertas_eventos WHERE type=? AND activa=1 ORDER BY timestamp_inicio DESC LIMIT 1",
        (sensor_type,)
    ).fetchone()

    if alert == 1:
        if not evento_activo:
            # verificar cooldown antes de otro evento
            if not en_cooldown(conn, sensor_type):
                conn.execute(
                    "INSERT INTO sensor_events (type, value, alert) VALUES (?, ?, ?)",
                    (sensor_type, value, alert)
                )
                conn.execute(
                    "INSERT INTO alertas_eventos (type, valor_inicio, valor_pico) VALUES (?, ?, ?)",
                    (sensor_type, value, value)
                )
        else:
            # Evento activo: solo actualizar pico
            if value > evento_activo["valor_pico"]:
                conn.execute(
                    "UPDATE alertas_eventos SET valor_pico=? WHERE id=?",
                    (value, evento_activo["id"])
                )
    elif alert == 0:
        if evento_activo:
            conn.execute(
                "UPDATE alertas_eventos SET activa=0, timestamp_fin=CURRENT_TIMESTAMP WHERE id=?",
                (evento_activo["id"],)
            )
            # Siempre guardar lectura de normalización aunque sea solo_alertas
            conn.execute(
                "INSERT INTO sensor_events (type, value, alert) VALUES (?, ?, 0)",
                (sensor_type, value)
            )
        else:
            modo = get_modo_actual()
            if modo != "solo_alertas":
                # Obtener la ultima lectura guardada para comparar
                ultima = conn.execute(
                    "SELECT value FROM sensor_events WHERE type=? ORDER BY timestamp DESC LIMIT 1",
                    (sensor_type,)
                ).fetchone()
                
                # Si la diferencia con la ultima lectura es >= 5%, guardar aunque no haya pasado el intervalo
                cambio_significativo = False
                if ultima:
                    diferencia = abs(value - float(ultima["value"]))
                    cambio_significativo = diferencia >= 5.0
                
                # Guardar si hubo cambio significativo O si pasó el intervalo configurado
                if cambio_significativo or guardar_lectura(conn, sensor_type, modo):
                    conn.execute(
                        "INSERT INTO sensor_events (type, value, alert) VALUES (?, ?, ?)",
                        (sensor_type, value, alert)
                    )
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Lectura guardada",
        "type":    sensor_type,
        "value":   value,
        "alert":   alert
    }), 201

# 🆕 Ruta para el historial (GET)
@sensors_bp.route("/api/sensor", methods=["GET"])
def get_sensors():
    sensor_type = request.args.get("type")
    conn = get_connection()
    if sensor_type:
        rows = conn.execute(
            "SELECT * FROM sensor_events WHERE type=? ORDER BY timestamp DESC LIMIT 500",
            (sensor_type,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM sensor_events ORDER BY timestamp DESC LIMIT 500"
        ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200

@sensors_bp.route("/api/sensor/latest", methods=["GET"])
def get_latest():
    conn = get_connection()
    temp = conn.execute(
        "SELECT value FROM sensor_events WHERE type='temperatura' ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    gas = conn.execute(
        "SELECT value, alert FROM sensor_events WHERE type='gas' ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    gas_evento = conn.execute(
        "SELECT timestamp_inicio FROM alertas_eventos WHERE type='gas' AND activa=1 ORDER BY timestamp_inicio DESC LIMIT 1"
    ).fetchone()
    temp_evento = conn.execute(
        "SELECT timestamp_inicio FROM alertas_eventos WHERE type='temperatura' AND activa=1 ORDER BY timestamp_inicio DESC LIMIT 1"
    ).fetchone()
    panic = conn.execute(
        "SELECT timestamp FROM panic_events WHERE atendido=0 ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return jsonify({
        "temperature": float(temp["value"]) if temp else 0,
        "humidity": 55,
        "gas_level": float(gas["value"])  if gas  else 0,
        "stove_on":      gas_evento is not None,
        "gas_alert_at":  gas_evento["timestamp_inicio"]    if gas_evento  else None,
        "temp_alert_at": temp_evento["timestamp_inicio"] if temp_evento else None,
        "panic_at": panic["timestamp"]  if panic        else None,
        "panic": False
    }), 200

@sensors_bp.route("/api/sensor/live", methods=["POST"])
def sensor_live():
    data = request.get_json()
    if not data or "type" not in data or "value" not in data:
        return jsonify({"error": "Faltan campos"}), 400
    ultimo_valor[data["type"]] = data["value"]
    return jsonify({"message": "OK"}), 200

@sensors_bp.route("/api/sensor/live", methods=["GET"])
def get_sensor_live():
    return jsonify(ultimo_valor), 200

@sensors_bp.route("/api/sensor/histograma", methods=["GET"])
def get_histograma():
    tipo = request.args.get("type")  # gas o temperatura
    fecha = request.args.get("fecha")  # formato YYYY-MM-DD
    
    if not tipo or not fecha:
        return jsonify({"error": "Faltan parametros type y fecha"}), 400
    
    conn = get_connection()
    rows = conn.execute("""
        SELECT 
            strftime('%H', timestamp) as hora,
            AVG(value) as promedio,
            MAX(value) as maximo,
            MIN(value) as minimo,
            COUNT(*) as lecturas
        FROM sensor_events
        WHERE type = ?
          AND date(datetime(timestamp, '-7 hours')) = ?
          AND alert = 0
        GROUP BY strftime('%H', datetime(timestamp, '-7 hours'))
        ORDER BY hora ASC
    """, (tipo, fecha)).fetchall()

    alertas = conn.execute("""
        SELECT 
            strftime('%H', timestamp) as hora,
            value,
            timestamp
        FROM sensor_events
        WHERE type = ?
          AND date(datetime(timestamp, '-7 hours')) = ?
          AND alert = 1
        ORDER BY timestamp ASC
    """, (tipo, fecha)).fetchall()
    
    conn.close()
    return jsonify({
        "lecturas": [dict(row) for row in rows],
        "alertas":  [dict(row) for row in alertas]
        }), 200

@sensors_bp.route("/api/test/hora", methods=["GET"])
def test_hora():
    conn = get_connection()
    row = conn.execute("SELECT datetime('now') as utc, datetime('now', '-7 hours') as ensenada").fetchone()
    conn.close()
    return jsonify(dict(row)), 200

# ─── Config: modo historial ──────────────────────────────────
@sensors_bp.route("/api/config/modo", methods=["GET"])
def get_modo():
    return jsonify({"modo": get_modo_actual()}), 200

@sensors_bp.route("/api/config/modo", methods=["POST"])
def set_modo():
    data = request.get_json()
    if not data or "modo" not in data:
        return jsonify({"error": "Falta campo modo"}), 400
    if data["modo"] not in OPC_VALIDAS:
        return jsonify({"error": "Modo inválido"}), 400
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('modo', ?)",
        (data["modo"],)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Modo actualizado", "modo": data["modo"]}), 200

# Entrar al historial, el frontend consula que tab habia seleccionado y lo restaura
@sensors_bp.route("/api/config/tab", methods=["GET"])
def get_tab():
    conn = get_connection()
    row = conn.execute("SELECT value FROM config WHERE key = 'tab_historial'").fetchone()
    conn.close()
    return jsonify({"tab": row["value"] if row else "sensores"}), 200

# Si cambias de tab (sensores, panico, todos) el frontend guarda lo seleccionado en el backend
@sensors_bp.route("/api/config/tab", methods=["POST"])
def set_tab():
    data = request.get_json()
    if not data or "tab" not in data:
        return jsonify({"error": "Falta tab"}), 400
    if data["tab"] not in ["sensores", "panico", "todos"]:
        return jsonify({"error": "Tab inválido"}), 400
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('tab_historial', ?)",
        (data["tab"],)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Tab actualizado", "tab": data["tab"]}), 200

@sensors_bp.route("/api/alertas/eventos", methods=["GET"])
def get_alertas_eventos():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM alertas_eventos ORDER BY timestamp_inicio DESC LIMIT 500"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200

#consultar si hay alerta activa
@sensors_bp.route("/api/alertas/activa/<string:tipo>", methods=["GET"])
def get_alerta_activa(tipo):
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM alertas_eventos WHERE type=? AND activa=1 LIMIT 1",
        (tipo,)
    ).fetchone()
    conn.close()
    return jsonify(row is not None), 200

@sensors_bp.route("/api/alertas/eventos/cerrar-activo", methods=["POST"])
def cerrar_evento_activo():
    data = request.get_json()
    if not data or "type" not in data:
        return jsonify({"error": "Falta type"}), 400
    conn = get_connection()
    
    # Obtener valor pico del evento antes de cerrarlo
    evento = conn.execute(
        "SELECT valor_pico FROM alertas_eventos WHERE type=? AND activa=1",
        (data["type"],)
    ).fetchone()

    conn.execute(
        "UPDATE alertas_eventos SET activa=0, timestamp_fin=CURRENT_TIMESTAMP WHERE type=? AND activa=1",
        (data["type"],)
    )

     # Guardar lectura actual con el valor real
    if evento:
        conn.execute(
            "INSERT INTO sensor_events (type, value, alert) VALUES (?, ?, 0)",
            (data["type"], evento["valor_pico"])
        )

    # Guardar cooldown en config
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, strftime('%s','now'))",
        (f"cooldown_{data['type']}",)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Evento cerrado"}), 200

# Eliminar registros seleccionasdos de sensor_events
@sensors_bp.route("/api/sensor/eliminar", methods=["POST"])
def eliminar_sensores():
    data = request.get_json()
    if not data or "ids" not in data:
        return jsonify({"error": "Faltan ids"}), 400
    conn = get_connection()

    # Obtener tipos con alerta antes de eliminar
    placeholders = ','.join('?' * len(data["ids"]))
    rows = conn.execute(
        f"SELECT type FROM sensor_events WHERE id IN ({placeholders}) AND alert=1",
        data["ids"]
    ).fetchall()

    # Cerrar alertas_eventos activos de esos tipos
    tipos_con_alerta = set(row["type"] for row in rows)
    for tipo in tipos_con_alerta:
        conn.execute(
            "UPDATE alertas_eventos SET activa=0, timestamp_fin=CURRENT_TIMESTAMP WHERE type=? AND activa=1",
            (tipo,)
        )
    
    # Eliminar los registros
    conn.executemany(
        "DELETE FROM sensor_events WHERE id = ?",
        [(id,) for id in data["ids"]]
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Eliminados"}), 200