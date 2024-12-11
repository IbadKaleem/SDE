from flask import Flask, render_template, send_from_directory, jsonify
from routes.user_routes import user_routes
from routes.admin_routes import admin_routes
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from config import JWT_SECRET_KEY

app = Flask(__name__, static_folder="assets", template_folder="templates")
app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
jwt = JWTManager(app)

blacklisted_tokens = set()

# Register Blueprints
app.register_blueprint(user_routes, url_prefix='/api')
app.register_blueprint(admin_routes, url_prefix='/api/admin')

@app.route("/")
def home():
    return render_template("index.html")

# Route for the login page
@app.route("/login")
def login():
    return render_template("login.html")

# Route for the register page
@app.route("/register")
def register():
    return render_template("register.html")

# Route for the dashboard
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/admin_dashboard")
def admin_dashboard():
    return render_template("admin_dashboard.html")

# Route for booking details
@app.route("/bookings")
def bookings():
    return render_template("bookings.html")

# Serve static files (CSS, JS, Images)
@app.route("/assets/<path:path>")
def static_files(path):
    return send_from_directory("assets", path)

@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in blacklisted_tokens


@app.route('/current_user', methods=['GET'])
@jwt_required()
def current_user():
    identity = get_jwt_identity()  # Extract user ID from token
    # Fetch additional details from JWT claims or the database
    return jsonify(identity), 200

if __name__ == "__main__":
    app.run(debug=True)