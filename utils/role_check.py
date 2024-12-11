from flask import jsonify
from flask_jwt_extended import get_jwt

def admin_required():
    jwt_data = get_jwt()
    role = jwt_data.get('role', None)
    if role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
