from flask import Flask, jsonify, make_response
from flask_cors import CORS
import json

app = Flask(__name__)

# Permitir CORS para uma origem específica (localhost:3000)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

@app.route('/api/hostgroups', methods=['GET'])
def get_hostgroups():
    # Aqui você implementa a lógica para retornar os dados do Zabbix
    try:
        # Realizando a consulta ao Zabbix
        from pyzabbix import ZabbixAPI
        config = configparser.ConfigParser()
        config.read("config.ini")
        user = config.get('zabbix', 'user')
        password = config.get('zabbix', 'password')
        server = config.get('zabbix', 'server')

        zapi = ZabbixAPI(server)
        zapi.login(user, password)

        # Consulta os grupos de hosts, excluindo os grupos que contém 'Templates'
        hostgroups = zapi.hostgroup.get(
            output='extend',
            excludeSearch=True,
            search={'name': 'Templates'}
        )
        zapi.user.logout()  # Finaliza a sessão

        return jsonify(hostgroups)
    except Exception as e:
        return make_response(jsonify({"error": str(e)}), 500)

if __name__ == "__main__":
    app.run(debug=True)
