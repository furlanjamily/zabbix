from flask import Flask, jsonify, make_response
from flask_cors import CORS
from pyzabbix import ZabbixAPI
import configparser

app = Flask(__name__)

# Permitir CORS para uma origem específica (localhost:5173)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Função para conectar ao Zabbix
def connect():
    config = configparser.ConfigParser()
    config.read("config.ini")  # Pega os dados de acesso do arquivo config.ini
    
    user = config.get('zabbix', 'user')
    password = config.get('zabbix', 'password')
    server = config.get('zabbix', 'server')
    
    zapi = ZabbixAPI(server)
    zapi.login(user, password)
    return zapi

# Rota para obter os grupos de hosts, excluindo aqueles que contêm "Templates"
@app.route('/api/hostgroups', methods=['GET'])
def get_hostgroups():
    try:
        # Conectar ao servidor Zabbix
        zapi = connect()

        # Consulta os grupos de hosts, excluindo os grupos que contêm "Templates"
        hostgroups = zapi.hostgroup.get(
            output='extend',
            excludeSearch=True,
            search={'name': 'Templates'}
        )

        # Fechar a sessão com o Zabbix
        zapi.user.logout()

        # Retornar os dados como JSON
        return jsonify(hostgroups)

    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

if __name__ == "__main__":
    app.run(debug=True)
