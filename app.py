from flask import Flask, request, jsonify, make_response
from db import mysql, init_db
from auth import generate_token, token_required
import xml.etree.ElementTree as ET
import config
from flask import request

app = Flask(__name__)
app.config.from_object(config)
init_db(app)

API_KEY = "CSE1-SECURE-KEY"

def authorized():
    return request.headers.get('Authorization') == API_KEY

def to_xml(data, root_name='employees'):
    root = ET.Element(root_name)
    for row in data:
        emp = ET.SubElement(root, 'employee')
        for k, v in row.items():
            ET.SubElement(emp, k).text = str(v)
    return ET.tostring(root)

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data['username'] == 'admin' and data['password'] == 'admin':
        return jsonify({'token': generate_token('admin')})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/employees/search')
@token_required
def search_employee():
    role = request.args.get('role')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM employees WHERE role=%s", (role,))
    rows = cur.fetchall()
    return jsonify(rows)

@app.route('/employees')
@token_required
def get_employees():
    fmt = request.args.get('format', 'json')
    cur = mysql.connection.cursor(dictionary=True)
    cur.execute("SELECT * FROM employees")
    data = cur.fetchall()

    if fmt == 'xml':
        return make_response(to_xml(data), 200,
            {'Content-Type': 'application/xml'})
    return jsonify(data)

@app.route('/employees', methods=['POST'])
@token_required
def add_employee():
    data = request.get_json()
    if not data.get('email'):
        return jsonify({'error': 'Email required'}), 400

    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO employees(first_name,last_name,email,role,salary)
        VALUES(%s,%s,%s,%s,%s)
    """, tuple(data.values()))
    mysql.connection.commit()
    return jsonify({'message': 'Employee added'}), 201


@app.route('/employees/<int:id>', methods=['PUT'])
@token_required
def update_employee(id):
    data = request.get_json()
    cur = mysql.connection.cursor()
    cur.execute("""
        UPDATE employees SET role=%s, salary=%s WHERE id=%s
    """, (data['role'], data['salary'], id))
    mysql.connection.commit()
    return jsonify({'message': 'Employee updated'})

@app.route('/employees/<int:id>', methods=['DELETE'])
@token_required
def delete_employee(id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM employees WHERE id=%s", (id,))
    mysql.connection.commit()
    return jsonify({'message': 'Employee deleted'})

if __name__ == '__main__':
    app.run(debug=True)