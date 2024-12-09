from flask import Flask, jsonify, make_response
from flask_cors import CORS
import json

app = Flask(__name__)

# Permitir CORS para todas as origens ou uma origem específica
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

@app.route('/api/hostgroups', methods=['GET'])
def get_hostgroups():
    # Aqui você implementa a lógica para retornar os dados do Zabbix
    with open("hostgroups.json", "r") as f:
        data = json.load(f)

    # Garantir que a resposta tenha os cabeçalhos CORS corretos
    response = make_response(jsonify(data))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == "__main__":
    app.run(debug=True)
