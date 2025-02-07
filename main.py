from flask import Flask, jsonify, make_response
from flask_cors import CORS
from pyzabbix import ZabbixAPI
from ping3 import ping
import configparser
import time
from flask_limiter import Limiter

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})

# Configuração do Limiter
limiter = Limiter(app)

# Função para conectar ao Zabbix
def connect_zabbix():
    config = configparser.ConfigParser()
    config.read("config.ini")
    user = config.get('zabbix', 'user')
    password = config.get('zabbix', 'password')
    server = config.get('zabbix', 'server')

    print(f"🔌 Conectando ao Zabbix em {server}...")
    zapi = ZabbixAPI(server)
    zapi.login(user, password)
    return zapi

# Função para processar os dados da API
def processa_dados_api(hostgroups):
    for hostgroup in hostgroups:
        print(f"🖥️ Grupo: {hostgroup['name']}")
        for host in hostgroup.get('hosts', []):
            print(f"   - Host: {host['name']} ({host['host']})")

# Limita o número de requisições para 15 por minuto
@app.route('/api/hostgroups', methods=['GET'])
@limiter.limit("15 per minute")  # Limita a 15 requisições por minuto
def get_hostgroups():
    start_time = time.time()
    try:
        zapi = connect_zabbix()

        print("📡 Buscando grupos de hosts...")
        hostgroups = zapi.hostgroup.get(
            output=['groupid', 'name'],
            excludeSearch=True,
            search={'name': 'Templates'},
            selectHosts=['hostid', 'name', 'host']
        )

        if not hostgroups:
            print("⚠️ Nenhum grupo encontrado.")
            return jsonify([])

        print(f"✅ {len(hostgroups)} grupos encontrados.")

        # Remover o ping para melhorar a performance
        # Você pode reintroduzi-lo de forma assíncrona ou em uma segunda chamada, se necessário

        # Processa os dados coletados
        processa_dados_api(hostgroups)

        zapi.user.logout()
        execution_time = time.time() - start_time
        print(f"✅ Resposta gerada em {execution_time:.2f} segundos.")

        return jsonify(hostgroups)

    except Exception as e:
        print(f"❌ Erro no servidor: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 500)

# Rodar o servidor
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
