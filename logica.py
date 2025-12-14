import re
import uuid
from datetime import datetime
from dateutil import parser # NOTA: Asegúrate de tener 'pip install python-dateutil'

# --- FUNCIÓN: SIMULACIÓN DE ENVÍO DE EMAIL ---
def send_email_notification(to_email, subject, body):
    """
    Simula el envío de un correo electrónico. 
    """
    print(f"\n--- SIMULACIÓN DE EMAIL ENVIADO ---")
    print(f"Para: {to_email}")
    print(f"Asunto: {subject}")
    print(f"Cuerpo: {body}")
    print(f"-----------------------------------\n")
    return True

# =======================================================
# CLASES DE GESTIÓN 
# =======================================================

class Login:
    """Clase para manejar la autenticación de usuarios."""

    def __init__(self, correo, contrasena, db_executor):
        self.correo = correo
        self.contrasena = contrasena
        self.execute_query = db_executor 

    def validar_correo(self):
        patron = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        return re.match(patron, self.correo) is not None

    def autenticar(self):
        if not self.validar_correo():
            return {"success": False, "message": "Correo inválido."}

        query = """
            SELECT id, name, password, role, email, firstName, lastName, identificationId 
            FROM usuarios 
            WHERE email = %s
        """
        user_data = self.execute_query(query, (self.correo,), fetch_data=True)

        if user_data is None:
            return {"success": False, "message": "El correo no está registrado."}

        db_id, db_name, db_password, db_role, db_email, db_first_name, db_last_name, db_id_number = user_data

        if db_password == self.contrasena:
            is_admin = db_role == 'Administrador'
            is_provider = db_role == 'Proveedor'
            
            return {
                "success": True,
                "username": db_name,
                "userId": db_id,
                "isAdmin": is_admin,
                "isProvider": is_provider,
                "email": db_email,
                "firstName": db_first_name,
                "lastName": db_last_name,
                "identificationId": db_id_number,
                "message": "Inicio de sesión exitoso."
            }
        else:
            return {"success": False, "message": "Contraseña incorrecta."}

#REVISION CLASE USUARIO
class Usuario:
    """Clase para manejar el registro de nuevos usuarios."""

    def __init__(self, data, db_executor):
        self.data = data
        self.execute_query = db_executor
        self.correo = data.get('email')
        self.contrasena = data.get('password')
        self.firstName = data.get('firstName', '')
        self.lastName = data.get('lastName', '')
        self.identificationId = data.get('identificationId', '')

    def validar_correo(self):
        patron = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
        return re.match(patron, self.correo) is not None

    def existe_en_bd(self):
        query = "SELECT id FROM usuarios WHERE email = %s"
        return self.execute_query(query, (self.correo,), fetch_data=True) is not None

    def registrar(self):
        if not self.validar_correo():
            return {"success": False, "message": "Correo inválido."}

        if self.existe_en_bd():
            return {"success": False, "message": "Este correo ya está registrado."}

        if not self.contrasena or len(self.contrasena) < 6:
            return {"success": False, "message": "La contraseña es demasiado corta."}

        user_id = str(uuid.uuid4())[:50] 
        name = f"{self.firstName} {self.lastName}"

        query = """
            INSERT INTO usuarios (id, email, password, name, role, firstName, lastName, identificationId, status)
            VALUES (%s, %s, %s, %s, 'Cliente', %s, %s, %s, 'Activo')
        """
        params = (user_id, self.correo, self.contrasena, name, self.firstName, self.lastName, self.identificationId)

        if self.execute_query(query, params) is None:
             return {"success": False, "message": "Error CRÍTICO al guardar el usuario en la base de datos."}

        send_email_notification(
            to_email=self.correo,
            subject="Bienvenido a AgendaPro",
            body=f"Hola {name},\n\nTu cuenta ha sido creada exitosamente. ¡Ya puedes reservar tus servicios!"
        )

        return {
            "success": True,
            "message": "Usuario registrado correctamente.",
            "username": name,
            "userId": user_id,
            "isAdmin": False,
            "isProvider": False
        }

#REVISION CLASE SERVICIO
class Servicio:
    """Clase para manejar el CRUD de servicios y consultas al catálogo."""

    def __init__(self, data, db_executor):
        self.data = data if data is not None else {}
        self.execute_query = db_executor
        self.service_id = self.data.get('id')

    def obtener_todos(self):
        """Consulta todos los servicios disponibles."""
        query = """
             SELECT id, provider_id, expert_name, name, price, duration, capacity, modality, description, image_url, category
             FROM servicios
             ORDER BY name ASC
        """
        resultados = self.execute_query(query, fetch_all=True)

        if resultados is None:
             return {"success": True, "data": []}
             
        servicios_list = []
        for fila in resultados:
            servicio = {
                "id": fila[0],
                "providerId": fila[1],
                "expertName": fila[2],
                "name": fila[3],
                "price": float(fila[4]),
                "duration": fila[5],
                "capacity": fila[6],
                "modality": fila[7],
                "desc": fila[8],
                "image": fila[9],
                "category": fila[10]
            }
            servicios_list.append(servicio)

        return {"success": True, "data": servicios_list}


    def crear(self):
        """Crea un nuevo servicio en la base de datos."""
        
        required_fields = ['providerId', 'expertName', 'name', 'price', 'duration', 'capacity', 'modality', 'desc']
        if not all(self.data.get(field) for field in required_fields):
            return {"success": False, "message": "Faltan campos obligatorios para el servicio."}

        new_service_id = str(uuid.uuid4())[:50]
        
        query = """
            INSERT INTO servicios (id, provider_id, expert_name, name, price, duration, capacity, modality, description, image_url, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            new_service_id, 
            self.data['providerId'], 
            self.data['expertName'], 
            self.data['name'], 
            self.data['price'], 
            self.data['duration'], 
            self.data['capacity'], 
            self.data['modality'], 
            self.data['desc'], 
            self.data.get('image', 'https://placehold.co/100x100/9400D3/ffffff?text=Service'), 
            self.data.get('category', 'Sin Categoría')
        )

        if self.execute_query(query, params) is None:
             return {"success": False, "message": "Error CRÍTICO al crear el servicio en la BD."}

        return {"success": True, "message": "Servicio creado correctamente.", "id": new_service_id}

#REVISION CLASE HISTORIALRESERVAS
class HistorialReservas:
    """Clase para obtener historial completo de reservas (incluyendo canceladas)."""

    def __init__(self, data, db_executor):
        self.usuario_id = data.get('usuario_id')
        self.is_manager = data.get('is_manager', False)
        self.execute_query = db_executor

    def obtener_historial(self):
        # El administrador/proveedor ve TODAS las citas
        if self.is_manager:
            query = """
                 SELECT 
                    r.id, s.name, r.slot_time, r.status, 
                    p.amount, p.payment_method, p.status AS payment_status, 
                    u.name AS username, u.id AS user_id
                 FROM reservas r
                 JOIN servicios s ON r.service_id = s.id
                 JOIN usuarios u ON r.usuario_id = u.id 
                 LEFT JOIN pagos p ON r.id = p.reservation_id
                 ORDER BY r.slot_time DESC
            """
            params = None
        else:
            # Cliente ve SOLO sus citas
            query = """
                 SELECT 
                    r.id, s.name, r.slot_time, r.status, 
                    p.amount, p.payment_method, p.status AS payment_status,
                    u.name AS username, u.id AS user_id
                 FROM reservas r
                 JOIN servicios s ON r.service_id = s.id
                 JOIN usuarios u ON r.usuario_id = u.id
                 LEFT JOIN pagos p ON r.id = p.reservation_id
                 WHERE r.usuario_id = %s
                 ORDER BY r.slot_time DESC
            """
            params = (self.usuario_id,)

        resultados = self.execute_query(query, params, fetch_all=True)

        if resultados is None:
             return {"success": True, "data": []}
             
        historial = []
        for fila in resultados:
            slot_time_dt = fila[2]
            slot_time_str = slot_time_dt.strftime("%Y-%m-%d %H:%M:%S") if isinstance(slot_time_dt, datetime) else str(fila[2])
            
            reserva = {
                "id_reserva": fila[0],
                "tipo_consulta": fila[1],
                "slot_time": slot_time_str,
                "estado_reserva": fila[3],
                "monto_pago": float(fila[4]) if fila[4] else None,
                "metodo_pago": fila[5],
                "estado_pago": fila[6],
                "username": fila[7],
                "user_id": fila[8],
            }
            historial.append(reserva)

        return {"success": True, "data": historial}

#REVISION CLASE RESERVA
class Reserva:
    """Clase para manejar la creación de nuevas reservas."""

    def __init__(self, data, db_executor):
        self.data = data
        self.execute_query = db_executor

    def crear_reserva(self):
        
        required_fields = ['usuarioId', 'serviceId', 'slotTime', 'status', 'userEmail', 'serviceName']
        if not all(self.data.get(field) for field in required_fields):
            return {"success": False, "message": "Faltan campos obligatorios para la reserva."}

        reserva_id = str(uuid.uuid4())[:50]
        
        try:
            slot_time_dt = parser.parse(self.data['slotTime']) 
        except Exception as e:
            return {"success": False, "message": f"Formato de fecha u hora inválido: {e}"}

        query = """
            INSERT INTO reservas (id, usuario_id, service_id, slot_time, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        params = (
            reserva_id, 
            self.data['usuarioId'], 
            self.data['serviceId'], 
            slot_time_dt, 
            self.data['status']
        )
        
        if self.execute_query(query, params) is None:
            return {"success": False, "message": "Error CRÍTICO al guardar la reserva en la base de datos."}
        
        send_email_notification(
            to_email=self.data['userEmail'],
            subject=f"Reserva Confirmada: {self.data['serviceName']}",
            body=f"Su reserva para el servicio '{self.data['serviceName']}' ha sido creada exitosamente para la fecha y hora: {self.data['slotTime']}."
        )
        
        return {"success": True, "message": "Reserva creada exitosamente.", "reservaId": reserva_id}

#REVISION CLASE PAGO
class Pago:
    """Clase para manejar y procesar pagos."""

    def __init__(self, data, db_executor):
        self.data = data
        self.execute_query = db_executor

    def validar_metodo(self):
        metodo = self.data.get('metodo', '').lower()
        metodos_validos = ["online", "pagar en sitio", "tarjeta guardada"]
        return metodo in metodos_validos

    def procesar_pago(self):
        metodo = self.data.get('metodo', '').lower()
        monto = self.data.get('monto', 0)
        reserva_id = self.data.get('reserva_id') 
        
        if not self.validar_metodo():
            return {"success": False, "message": f"Método de pago inválido: {metodo}"}

        if monto <= 0:
            return {"success": False, "message": "El monto debe ser mayor a 0."}
        
        if not reserva_id:
             return {"success": False, "message": "ID de reserva requerido para el pago."}

        if metodo == "pagar en sitio":
            estado_pago = "PENDIENTE"
            mensaje = "Pago contraentrega registrado."
        else:
            estado_pago = "APROBADO"
            mensaje = "Pago procesado con éxito."

        # Guardar en tabla pagos
        pago_id = str(uuid.uuid4())[:50]
        query = """
             INSERT INTO pagos (id, reservation_id, amount, payment_method, status)
             VALUES (%s, %s, %s, %s, %s)
        """
        params = (pago_id, reserva_id, monto, metodo, estado_pago)
        
        if self.execute_query(query, params) is None:
             return {"success": False, "message": "Error CRÍTICO al procesar y guardar el pago."}

        return {"success": True, "estado_pago": estado_pago, "message": mensaje}
