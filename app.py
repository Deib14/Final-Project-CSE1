from flask import Flask, request, jsonify, make_response
from db import mysql, init_db
from auth import generate_token, token_required
import xml.etree.ElementTree as ET
import config

app = Flask(__name__)
app.config.from_object(config)
init_db(app)

def to_xml(data, root_name='employees'):
    root = ET.Element(root_name)
    for row in data:
        emp = ET.SubElement(root, 'employee')
        for k, v in row.items():
            ET.SubElement(emp, k).text = str(v)
    return ET.tostring(root)