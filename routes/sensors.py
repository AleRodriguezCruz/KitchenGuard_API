from flask import Blueprint, request, jsonify
from database import get_connection

sensors_bp = Blueprint("sensors", __name__)

@sensors_bp.route("/api/sensor", methods=["POST"])
def receive_sensor():
    data = request.get_json()
    if not data or "type" not in data or "value" not in data:
        return jsonify({"error": "Faltan campos: type y value"}), 400

    sensor_type = data["type"]
    value       = data["value"]
    alert       = data.get("alert", 0)

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
        "SELECT value, alert FROM sensor_events WHERE type='gas' ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return jsonify({
        "temperature": float(temp["value"]) if temp else 0,
        "humidity":    55,
        "gas_level":   float(gas["value"])  if gas  else 0,
        "stove_on":    bool(gas["alert"])   if gas  else False,
        "panic":       False
    }), 200
