from flask import Blueprint, request, jsonify
from database import get_connection

sensors_bp = Blueprint("sensors", __name__)

def get_modo_actual():
    conn = get_connection()
    row = conn.execute("SELECT value FROM config WHERE key = 'modo'").fetchone()
    conn.close()
    return row["value"] if row else "todo"

@sensors_bp.route("/api/sensor", methods=["POST"])
def receive_sensor():
    data = request.get_json()
    if not data or "type" not in data or "value" not in data:
        return jsonify({"error": "Faltan campos: type y value"}), 400

    sensor_type = data["type"]
    value       = data["value"]
    alert       = data.get("alert", 0)

    if get_modo_actual() == "solo_alertas" and alert == 0:
        return jsonify({"message": "Dato ignorado por modo solo_alertas"}), 200

    conn = get_connection()
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
            "SELECT * FROM sensor_events WHERE type=? ORDER BY timestamp DESC LIMIT 50",
            (sensor_type,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM sensor_events ORDER BY timestamp DESC LIMIT 50"
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
        "SELECT value, alert, timestamp FROM sensor_events WHERE type='gas' ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    temp_alert = conn.execute(
        "SELECT timestamp FROM sensor_events WHERE type='temperatura' AND alert=1 ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    panic = conn.execute(
        "SELECT timestamp FROM panic_events WHERE atendido=0 ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return jsonify({
        "temperature": float(temp["value"]) if temp else 0,
        "humidity":    55,
        "gas_level":   float(gas["value"])  if gas  else 0,
        "stove_on":    bool(gas["alert"])   if gas  else False,
        "gas_alert_at":  gas["timestamp"]        if gas and gas["alert"] else None,
        "temp_alert_at": temp_alert["timestamp"] if temp_alert else None,
        "panic_at":      panic["timestamp"]      if panic      else None,
        "panic":       False
    }), 200

# ─── Config: modo historial ──────────────────────────────────
@sensors_bp.route("/api/config/modo", methods=["GET"])
def get_modo():
    return jsonify({"modo": get_modo_actual()}), 200

@sensors_bp.route("/api/config/modo", methods=["POST"])
def set_modo():
    data = request.get_json()
    if not data or "modo" not in data:
        return jsonify({"error": "Falta campo modo"}), 400
    if data["modo"] not in ["todo", "solo_alertas"]:
        return jsonify({"error": "Modo inválido"}), 400
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES ('modo', ?)",
        (data["modo"],)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Modo actualizado", "modo": data["modo"]}), 200
