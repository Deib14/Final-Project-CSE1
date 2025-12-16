from flask import Flask, request, jsonify, make_response
import mysql.connector
import xml.etree.ElementTree as ET
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required
)
import config

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
jwt = JWTManager(app)


def get_db():
    return mysql.connector.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
        auth_plugin="mysql_native_password"
    )

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

    token = create_access_token(identity="admin")
    return jsonify(access_token=token), 200


@app.route("/employees")
@jwt_required()
def get_employees():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM employees")
    data = cur.fetchall()

    cur.close()
    conn.close()

    if not data:
        return jsonify({"error": "No employees found"}), 404

    if request.args.get("format") == "xml":
        return make_response(
            to_xml(data),
            200,
            {"Content-Type": "application/xml"}
        )

    return jsonify(data), 200



@app.route("/employees/search")
@jwt_required()
def search_employee():
    role = request.args.get("role")
    if not role:
        return jsonify({"error": "Role parameter required"}), 400

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM employees WHERE role=%s", (role,))
    data = cur.fetchall()

    cur.close()
    conn.close()

    if not data:
        return jsonify({"error": "No matching employees found"}), 404

    return jsonify(data), 200

@app.route("/employees", methods=["POST"])
@jwt_required()
def add_employee():
    data = request.get_json()

    required_fields = ["first_name", "last_name", "email"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db()
    cur = conn.cursor()

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

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Employee added"}), 201

@app.route("/employees/<int:id>", methods=["PUT"])
@jwt_required()
def update_employee(id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE employees
        SET role=%s, salary=%s
        WHERE id=%s
    """, (
        data.get("role"),
        data.get("salary"),
        id
    ))

    conn.commit()
    affected = cur.rowcount

    cur.close()
    conn.close()

    if affected == 0:
        return jsonify({"error": "Employee not found"}), 404

    return jsonify({"message": "Employee updated"}), 200

@app.route("/employees/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_employee(id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM employees WHERE id=%s", (id,))
    conn.commit()
    affected = cur.rowcount

    cur.close()
    conn.close()

    if affected == 0:
        return jsonify({"error": "Employee not found"}), 404

    return jsonify({"message": "Employee deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True)
