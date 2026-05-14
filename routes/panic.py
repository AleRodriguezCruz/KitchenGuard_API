from flask import Blueprint, jsonify
from database import get_connection

panic_bp = Blueprint("panic", __name__)

@panic_bp.route("/api/panic", methods=["POST"])
def panic_button():
    conn = get_connection()
    cursor = conn.execute("INSERT INTO panic_events DEFAULT VALUES")
    conn.commit()
    event_id = cursor.lastrowid
    conn.close()
    print("BOTON DE PANICO ACTIVADO")
    return jsonify({
        "message": "Alerta de panico registrada",
        "id":      event_id
    }), 201

@panic_bp.route("/api/panic", methods=["GET"])
def get_panic_events():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM panic_events ORDER BY timestamp DESC LIMIT 20"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200

@panic_bp.route("/api/panic/activo", methods=["GET"])
def get_panic_activo():
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM panic_events WHERE atendido = 0 ORDER BY timestamp DESC LIMIT 1"
    ).fetchone()
    if not row:
        conn.close()
        return jsonify(None), 200
    
    count = conn.execute(
        "SELECT COUNT(*) as total FROM panic_events WHERE atendido = 0"
    ).fetchone()
    conn.close()
    
    result = dict(row)
    result['intentos'] = count['total']
    return jsonify(result), 200

@panic_bp.route("/api/panic/<int:event_id>/atender", methods=["POST"])
def atender_panico(event_id):
    conn = get_connection()
    conn.execute(
        "UPDATE panic_events SET atendido = 1 WHERE id = ?",
        (event_id,)
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Evento atendido", "id": event_id}), 200
