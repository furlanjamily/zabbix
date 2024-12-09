# server.py

from flask import Flask, jsonify, request
from flask_cors import CORS  # Para lidar com CORS (Cross-Origin Resource Sharing)
import json
import os
import configparser
from pyzabbix import ZabbixAPI

# Inicialização do Flask
app = Flask(__name__)

# Habilitar CORS para todas as origens
CORS(app)

# Função para conectar ao Zabbix
def connect():
    config = configparser.ConfigParser()
    config.read('config.ini')

    user = config.get('zabbix', 'user')
    password = config.get('zabbix', 'password')
    server = config.get('zabbix', 'server')

    zapi = ZabbixAPI(server)
    zapi.login(user, password)

    return zapi

# Rota para obter os dados dos grupos de hosts
@app.route('/api/hostgroups', methods=['GET'])
def get_hostgroups():
    try:
        # Conectar ao Zabbix API
        api = connect()

        # Obter os grupos de hosts, excluindo aqueles com o nome "Templates"
        hostgroups = api.hostgroup.get(
            output='extend',
            excludeSearch=True,
            search={'name': 'Templates'},
            selectHosts=['name', 'host', 'status']
        )

        # Estruturar os dados para enviar ao frontend
        formatted_data = []
        for group in hostgroups:
            group_data = {
                "name": group['name'],
                "hosts": [
                    {
                        "name": host['name'],
                        "host": host['host'],
                        "status": host['status']
                    }
                    for host in group['hosts']
                ]
            }
            formatted_data.append(group_data)

        return jsonify(formatted_data)

    except Exception as e:
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
