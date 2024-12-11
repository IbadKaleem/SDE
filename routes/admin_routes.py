from flask import Blueprint, request, jsonify
import mysql.connector
from config import DB_CONFIG, API_KEY
from flask_jwt_extended import jwt_required, get_jwt
from utils.role_check import admin_required


admin_routes = Blueprint('admin_routes', __name__)


@admin_routes.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    jwt_data = get_jwt()
    username = jwt_data.get("username")
    role = jwt_data.get("role")
    return jsonify({"username": username, "role": role}), 200

@admin_routes.route('/add_train', methods=['POST'])
@jwt_required()
def add_train():
    # Check if the current user is an admin
    role_check = admin_required()
    if role_check:
        return role_check

    try:
        data = request.get_json()
        train_name = data.get('train_name')
        source = data.get('source')
        destination = data.get('destination')
        total_seats = data.get('total_seats')

        if not all([train_name, source, destination, total_seats]):
            return jsonify({'error': 'All fields are required'}), 400

        # Set available seats equal to total seats initially
        available_seats = total_seats

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Insert the train into the database
        query = """
            INSERT INTO trains (train_name, source, destination, total_seats, available_seats)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (train_name, source, destination, total_seats, available_seats))
        connection.commit()

        return jsonify({'message': 'Train added successfully'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()