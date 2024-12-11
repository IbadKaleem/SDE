import bcrypt
import jwt
import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token,get_jwt
import mysql.connector
from config import DB_CONFIG

user_routes = Blueprint('user_routes', __name__)

SECRET_KEY = "8f934a0c2b5e8f1a4c9b7d6e3f2a8b5c4a7d2e1c9f3b8a6d5e4c2f1a7b9d6e3"

blacklisted_tokens = set()

@user_routes.route('/current_user', methods=['GET'])
@jwt_required()
def current_user():
    jwt_data = get_jwt()
    user_id = jwt_data.get("user_id")
    username = jwt_data.get("username")
    role = jwt_data.get("role")
    return jsonify({"user_id": user_id, "username": username, "role": role}), 200

@user_routes.route('/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'user')  # Default to 'user'

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Insert the new user
        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hashed_password.decode('utf-8'), role))
        connection.commit()

        return jsonify({'message': 'User registered successfully'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


@user_routes.route('/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Fetch the user from the database
        query = "SELECT * FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401

        # Check the password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Invalid username or password'}), 401

        # Generate JWT token
        access_token = create_access_token(
            identity=str(user['id']),  # This sets the `sub` claim
            additional_claims={
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role']
            }
        )
        return jsonify({'message': 'Login successful', 'token': access_token, 'role': user['role']}), 200

    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()



@user_routes.route('/seat_availability', methods=['GET'])
def get_seat_availability():
    try:
        source = request.args.get('source')
        destination = request.args.get('destination')
        page = int(request.args.get('page', 1))  # Default to page 1
        per_page = int(request.args.get('per_page', 10))  # Default to 10 results per page

        if not source or not destination:
            return jsonify({'error': 'Source and destination are required'}), 400

        offset = (page - 1) * per_page

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Query trains with pagination
        query = """
            SELECT train_name, source, destination, available_seats
            FROM trains
            WHERE source = %s AND destination = %s
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (source, destination, per_page, offset))
        trains = cursor.fetchall()

        if not trains:
            return jsonify({'message': 'No trains found between the given stations'}), 404

        return jsonify({'trains': trains, 'page': page, 'per_page': per_page}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@user_routes.route('/book_seat', methods=['POST'])
@jwt_required()
def book_seat():
    try:
        # Extract `user_id` from the token claims
        user_id = get_jwt_identity()  # This is the `sub` claim
        data = request.get_json()
        train_id = data.get('train_id')

        if not train_id:
            return jsonify({'error': 'Train ID is required'}), 400

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Start a transaction
        connection.start_transaction()

        # Check seat availability
        check_query = "SELECT available_seats FROM trains WHERE id = %s FOR UPDATE"
        cursor.execute(check_query, (train_id,))
        train = cursor.fetchone()

        if not train:
            return jsonify({'error': 'Train not found'}), 404

        available_seats = train[0]
        if available_seats <= 0:
            return jsonify({'error': 'No seats available'}), 400

        # Deduct one seat
        update_query = "UPDATE trains SET available_seats = available_seats - 1 WHERE id = %s"
        cursor.execute(update_query, (train_id,))

        # Record the booking
        insert_query = "INSERT INTO bookings (user_id, train_id) VALUES (%s, %s)"
        cursor.execute(insert_query, (user_id, train_id))

        # Commit the transaction
        connection.commit()

        return jsonify({'message': 'Seat booked successfully'}), 200
    except mysql.connector.Error as err:
        connection.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()

@user_routes.route('/booking_details', methods=['GET'])
@jwt_required()
def get_booking_details():
    try:
        user_id = get_jwt_identity()  # This is the `sub` claim
        page = int(request.args.get('page', 1))  # Default to page 1
        per_page = int(request.args.get('per_page', 10))  # Default to 10 results per page
        offset = (page - 1) * per_page

        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor(dictionary=True)

        # Fetch bookings with pagination
        query = """
            SELECT b.id AS booking_id, t.train_name, t.source, t.destination, b.booking_time
            FROM bookings b
            INNER JOIN trains t ON b.train_id = t.id
            WHERE b.user_id = %s
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (user_id, per_page, offset))
        bookings = cursor.fetchall()

        if not bookings:
            return jsonify({'message': 'No bookings found for this user'}), 404

        return jsonify({'bookings': bookings, 'page': page, 'per_page': per_page}), 200
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()


@user_routes.route('/logout', methods=['POST'])
@jwt_required()
def logout_user():
    jti = get_jwt()["jti"]  # JWT ID, a unique identifier for the token
    blacklisted_tokens.add(jti)
    return jsonify({"message": "Successfully logged out"}), 200
