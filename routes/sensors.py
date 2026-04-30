from flask import Blueprint, request, jsonify
from database import get_connection

sensors_bp = Blueprint("sensors", __name__)

@sensors_bp.route("/api/sensor", methods=["POST"])
def receive_sensor():
    data = request.get_json()
    if not data or "type" not in data or "value" not in data:
        return jsonify({"error": "Faltan campos: type y value"}), 400

    sensor_type = data["type"]
    value = float(data["value"])
    alert = int(data.get("alert", 0))

    supabase = get_connection()
    result = supabase.table("sensor_events").insert({
        "type": sensor_type,
        "value": value,
        "alert": alert
    }).execute()

    return jsonify({
        "message": "Lectura guardada",
        "type": sensor_type,
        "value": value,
        "alert": alert
    }), 201

@sensors_bp.route("/api/sensor", methods=["GET"])
def get_sensors():
    sensor_type = request.args.get("type")
    supabase = get_connection()
    
    query = supabase.table("sensor_events").select("*").order("timestamp", desc=True).limit(50)
    
    if sensor_type:
        query = query.eq("type", sensor_type)
    
    result = query.execute()
    return jsonify(result.data), 200