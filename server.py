# -*- coding: utf-8 -*- 
from flask import Flask, request, jsonify, render_template 
from flask_cors import CORS

# Importamos la configuración y funciones auxiliares de BD
from configuracion_db import execute_query 
# Importamos las clases de lógica de negocio (de logica.py)
from logica import Login, Usuario, HistorialReservas, Pago, Servicio, Reserva 

import psycopg2 
import re
import uuid

# --- CONFIGURACIÓN DE FLASK ---
app = Flask(__name__)
CORS(app) 

# =======================================================
# ENDPOINT PRINCIPAL (SIRVE EL HTML)
# =======================================================
#REVISION DE ENDPOINTS
@app.route("/")
def serve_frontend():
    """Sirve el archivo index.html cuando se accede a la raíz del servidor."""
    # NOTA: index.html debe estar en la carpeta 'templates'
    return render_template("index.html")

# =======================================================
# ENDPOINTS DE AUTENTICACIÓN
# =======================================================

@app.route('/api/register', methods=['POST'])
def handle_register():
    """Endpoint para registrar un nuevo usuario (Cliente)."""
    data = request.json
    
    user_logic = Usuario(data, execute_query)
    result = user_logic.registrar()

    if result.get("success", False):
        return jsonify(result), 201
    else:
        return jsonify({"message": result.get("message", "Error de registro desconocido.")}), 400


@app.route('/api/login', methods=['POST'])
def handle_login():
    """Endpoint para el inicio de sesión."""
    data = request.json
    
    login_logic = Login(data.get('email'), data.get('password'), execute_query)
    result = login_logic.autenticar()

    if result.get("success", False):
        is_admin = result.get('isAdmin', False)
        is_provider = result.get('isProvider', False)
        result['destinationView'] = 'admin' if is_admin else ('provider_panel' if is_provider else 'services')
        return jsonify(result), 200
    else:
        return jsonify(result), 401

# =======================================================
# ENDPOINTS DE SERVICIOS (CRUD)
# =======================================================
#REVISION ENDPOINTS
@app.route('/api/services', methods=['GET'])
def get_all_services():
    """Endpoint para obtener todo el catálogo de servicios."""
    service_logic = Servicio(None, execute_query) 
    result = service_logic.obtener_todos()
    
    if result.get("success", False):
        return jsonify(result["data"]), 200
    else:
        return jsonify({"message": result.get("message", "Error interno al cargar servicios.")}), 400

@app.route('/api/service', methods=['POST'])
def create_service():
    """Endpoint para que el Admin/Proveedor cree un nuevo servicio."""
    data = request.json
    service_logic = Servicio(data, execute_query)
    result = service_logic.crear()

    if result.get("success", False):
        return jsonify(result), 201
    else:
        return jsonify({"message": result.get("message", "Error al crear servicio.")}), 400


# =======================================================
# ENDPOINTS DE RESERVAS Y PAGOS
# =======================================================
#REVISION ENDPOINTS
@app.route('/api/reservation', methods=['POST'])
def create_reservation():
    """Endpoint para que el Cliente cree una nueva reserva."""
    data = request.json
    reserva_logic = Reserva(data, execute_query)
    result = reserva_logic.crear_reserva()

    if result.get("success", False):
        return jsonify(result), 201
    else:
        return jsonify({"message": result.get("message", "Error al crear reserva.")}), 400


# ENDPOINT DE HISTORIAL (AJUSTADO PARA RECIBIR STATUS DEL MANAGER)
@app.route('/api/history/<string:user_id>/<string:role>', methods=['GET'])
def get_user_history(user_id, role):
    """Endpoint para obtener el historial, filtrado por usuario o todos si es manager."""
    
    is_manager = role in ['Administrador', 'Proveedor']
    
    data_payload = {
        'usuario_id': user_id,
        'is_manager': is_manager
    }
    
    history_logic = HistorialReservas(data_payload, execute_query)
    result = history_logic.obtener_historial()

    if result.get("success", False):
        return jsonify(result["data"]), 200
    else:
        return jsonify({"message": result.get("message", "Error al cargar historial.")}), 400


@app.route('/api/process_payment', methods=['POST'])
def process_reservation_payment():
    """Simulación de procesamiento de pago para una reserva."""
    data = request.json
    
    payment_logic = Pago(data, execute_query)
    result = payment_logic.procesar_pago()

    if result.get("success", False):
        return jsonify(result), 200
    else:
        return jsonify({"message": result.get("message", "Error al procesar el pago.")}), 400


if __name__ == '__main__':
    print("Servidor Flask corriendo en http://0.0.0.0:5000/ (Accesible en la red local)")
    app.run(debug=True, port=5000, host='0.0.0.0')
