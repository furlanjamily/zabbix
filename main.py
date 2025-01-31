from flask import Flask, jsonify, make_response
from flask_cors import CORS
from pyzabbix import ZabbixAPI
from ping3 import ping  # Para realizar o ping
import configparser

# Criação da aplicação Flask
app = Flask(__name__)

# Permitir CORS para uma origem específica (localhost:5173)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

@app.route('/api/hostgroups', methods=['GET'])
def get_hostgroups():
    try:
        print("Iniciando requisição...")
        config = configparser.ConfigParser()
        config.read("config.ini")  # Lê o arquivo de configuração
        user = config.get('zabbix', 'user')
        password = config.get('zabbix', 'password')
        server = config.get('zabbix', 'server')

        # Conectando ao Zabbix
        print(f"Conectando ao Zabbix em {server}...")
        zapi = ZabbixAPI(server)
        zapi.login(user, password)

        # Consulta os grupos de hosts, excluindo os grupos que contêm 'Templates'
        print("Consultando grupos de hosts...")
        hostgroups = zapi.hostgroup.get(
            output='extend',
            excludeSearch=True,
            search={'name': 'Templates'},
            selectHosts=['name', 'host', 'id']
        )

        print(f"Hostgroups encontrados: {len(hostgroups)}")
        
        # Verifica o status de cada host (ping)
        for hostgroup in hostgroups:
            for host in hostgroup['hosts']:
                host_ip = host['host']  # IP ou nome do host
                response_time = ping(host_ip)
                host['ping_status'] = 'online' if response_time is not None else 'offline'

        zapi.user.logout()  # Finaliza a sessão do Zabbix

        # Retorna os hostgroups com o status de ping dos hosts
        return jsonify(hostgroups)
    
    except Exception as e:
        print(f"Erro ao processar: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 500)

# Rodar a aplicação
if __name__ == "__main__":
    app.run(debug=True)
