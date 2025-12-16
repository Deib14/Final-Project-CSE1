from flask import Flask, request, jsonify, make_response
from db import mysql, init_db
import xml.etree.ElementTree as ET
import config

app = Flask(__name__)
app.config.from_object(config)
init_db(app)

API_KEY = "CSE1-SECURE-KEY"

@app.route('/')
def home():
    return "API is running"

def authorized():
    return request.headers.get('Authorization') == API_KEY

def to_xml(data):
    root = ET.Element("employees")
    for row in data:
        emp = ET.SubElement(root, "employee")
        for k, v in row.items():
            ET.SubElement(emp, k).text = str(v)
    return ET.tostring(root)

@app.route('/employees/search')
def search_employee():
    if not authorized():
        return jsonify({'error': 'Unauthorized'}), 401

    role = request.args.get('role')
    cur = mysql.connection.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees WHERE role=%s", (role,))
    return jsonify(cur.fetchall())

@app.route('/employees')
def get_employees():
    if not authorized():
        return jsonify({'error': 'Unauthorized'}), 401

    cur = mysql.connection.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees")
    data = cur.fetchall()

    if request.args.get('format') == 'xml':
        return make_response(to_xml(data), 200,
                             {'Content-Type': 'application/xml'})
    return jsonify(data)

@app.route('/employees', methods=['POST'])
def add_employee():
    if not authorized():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data or not data.get('email'):
        return jsonify({'error': 'Email required'}), 400

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO employees
        (first_name, last_name, email, role, salary)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        data['first_name'],
        data['last_name'],
        data['email'],
        data.get('role'),
        data.get('salary')
    ))
    mysql.connection.commit()
    return jsonify({'message': 'Employee added'}), 201

@app.route('/employees/<int:id>', methods=['PUT'])
def update_employee(id):
    if not authorized():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE employees
        SET role=%s, salary=%s
        WHERE id=%s
    """, (data.get('role'), data.get('salary'), id))
    mysql.connection.commit()
    return jsonify({'message': 'Employee updated'})

@app.route('/employees/<int:id>', methods=['DELETE'])
def delete_employee(id):
    if not authorized():
        return jsonify({'error': 'Unauthorized'}), 401

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM employees WHERE id=%s", (id,))
    mysql.connection.commit()
    return jsonify({'message': 'Employee deleted'})

if __name__ == '__main__':
    app.run(debug=True)
