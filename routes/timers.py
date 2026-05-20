from flask import Blueprint, request, jsonify
from database import get_connection

timers_bp = Blueprint("timers", __name__)

@timers_bp.route("/api/timers", methods=["POST"])
def create_timer():
    data = request.get_json()
    if not data or "label" not in data or "duration" not in data:
        return jsonify({"error": "Faltan campos: label y duration"}), 400

    label    = data["label"]
    duration = data["duration"]

    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO timers (label, duration) VALUES (?, ?)",
        (label, duration)
    )
    conn.commit()
    timer_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message":  "Temporizador creado",
        "id":       timer_id,
        "label":    label,
        "duration": duration
    }), 201

@timers_bp.route("/api/timers", methods=["GET"])
def get_timers():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM timers WHERE active=1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200

# Devolver el timer mas antiguo
@timers_bp.route("/api/timers/siguiente", methods=["GET"])
def get_siguiente_timer():
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM timers WHERE active=1 ORDER BY created_at ASC LIMIT 1"
    ).fetchone()
    conn.close()
    if row is None:
        return jsonify(None), 200
    return jsonify(dict(row)), 200

@timers_bp.route("/api/timers/<int:timer_id>", methods=["DELETE"])
def delete_timer(timer_id):
    conn = get_connection()
    conn.execute(
        "UPDATE timers SET active=0 WHERE id=?",
        (timer_id,)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Temporizador eliminado", "id": timer_id}), 200
