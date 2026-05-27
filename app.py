from flask import Flask, request, jsonify, make_response
from flask_mysqldb import MySQL
import xml.etree.ElementTree as ET
from itsdangerous import URLSafeTimedSerializer
from functools import wraps
import config

app = Flask(__name__)

app.config["MYSQL_HOST"] = config.MYSQL_HOST
app.config["MYSQL_USER"] = config.MYSQL_USER
app.config["MYSQL_PASSWORD"] = config.MYSQL_PASSWORD
app.config["MYSQL_DB"] = config.MYSQL_DB
app.config["SECRET_KEY"] = config.JWT_SECRET_KEY

mysql = MySQL(app)
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

def rows_to_dict(cursor, rows):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in rows]

def generate_token(username):
    return serializer.dumps(username)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"error": "Token missing"}), 401
        try:
            serializer.loads(token, max_age=3600)
        except:
            return jsonify({"error": "Invalid or expired token"}), 401
        return f(*args, **kwargs)
    return decorated

def to_xml(data):
    root = ET.Element("employees")
    for row in data:
        emp = ET.SubElement(root, "employee")
        for k, v in row.items():
            ET.SubElement(emp, k).text = str(v)
    return ET.tostring(root)

@app.route("/")
def home():
    return "CSE1 Employee API is running"

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or data.get("username") != "admin" or data.get("password") != "password":
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token("admin")
    return jsonify({"access_token": token}), 200

"""
{
            "username": "admin",
            "password": "password"
}
"""

@app.route("/employees", methods=["GET"])
@token_required
def get_employees():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()

    if not rows:
        cur.close()
        return jsonify({"error": "No employees found"}), 404

    data = rows_to_dict(cur, rows)
    cur.close()

    if request.args.get("format") == "xml":
        return make_response(to_xml(data), 200, {"Content-Type": "application/xml"})

    return jsonify(data), 200

@app.route("/employees/search", methods=["GET"])
@token_required
def search_employee():
    role = request.args.get("role")
    if not role:
        return jsonify({"error": "Role parameter required"}), 400

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees WHERE role=%s", (role,))
    rows = cur.fetchall()

    if not rows:
        cur.close()
        return jsonify({"error": "No matching employees found"}), 404

    data = rows_to_dict(cur, rows)
    cur.close()

    return jsonify(data), 200

@app.route("/employees", methods=["POST"])
@token_required
def add_employee():
    data = request.get_json()
    required_fields = ["first_name", "last_name", "email"]

    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO employees (first_name, last_name, email, role, salary)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        data["first_name"],
        data["last_name"],
        data["email"],
        data.get("role"),
        data.get("salary")
    ))
    mysql.connection.commit()
    cur.close()

    return jsonify({"message": "Employee added"}), 201

@app.route("/employees/<int:id>", methods=["PUT"])
@token_required
def update_employee(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE employees
        SET role=%s, salary=%s
        WHERE id=%s
    """, (
        data.get("role"),
        data.get("salary"),
        id
    ))
    mysql.connection.commit()
    affected = cur.rowcount
    cur.close()

    if affected == 0:
        return jsonify({"error": "Employee not found"}), 404

    return jsonify({"message": "Employee updated"}), 200

@app.route("/employees/<int:id>", methods=["DELETE"])
@token_required
def delete_employee(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM employees WHERE id=%s", (id,))
    mysql.connection.commit()
    affected = cur.rowcount
    cur.close()

    if affected == 0:
        return jsonify({"error": "Employee not found"}), 404

    return jsonify({"message": "Employee deleted"}), 200

if __name__ == "__main__":
    app.run(debug=True)
