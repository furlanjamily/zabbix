import os
import time
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configurações do Zabbix
ZABBIX_URL = os.getenv("ZABBIX_URL", "http://seu-zabbix.com/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "Admin")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "zabbix")

# Cache para armazenar os dados temporariamente
cached_data = {"timestamp": 0, "data": {}}
CACHE_TIMEOUT = 60  # Tempo de cache em segundos

def get_zabbix_token():
    """Autentica no Zabbix e retorna o token de sessão."""
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "user": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1,
        "auth": None
    }
    response = requests.post(ZABBIX_URL, json=payload)
    data = response.json()
    
    if "result" in data:
        return data["result"]
    else:
        raise Exception(f"Erro ao autenticar no Zabbix: {data}")

def get_hosts_from_zabbix():
    """Consulta a API do Zabbix para obter os hosts monitorados."""
    try:
        token = get_zabbix_token()
        
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid", "host", "name"],
                "selectInterfaces": ["ip"]
            },
            "id": 2,
            "auth": token
        }
        response = requests.post(ZABBIX_URL, json=payload)
        data = response.json()
        
        if "result" in data:
            hosts = []
            for host in data["result"]:
                ip = host["interfaces"][0]["ip"] if host["interfaces"] else "Desconhecido"
                hosts.append({
                    "id": host["hostid"],
                    "name": host["name"],
                    "ip": ip,
                    "status": "online"  # Para status real, precisaríamos consultar o ping
                })
            return hosts
        else:
            raise Exception(f"Erro ao buscar hosts: {data}")

    except Exception as e:
        print(f"Erro ao obter hosts do Zabbix: {e}")
        return []

@app.route("/api/hosts", methods=["GET"])
def api_hosts():
    """Endpoint para listar os hosts monitorados pelo Zabbix."""
    global cached_data  

    # Retorna do cache se ainda estiver válido
    if time.time() - cached_data["timestamp"] < CACHE_TIMEOUT:
        return jsonify(cached_data["data"])

    # Obtém hosts do Zabbix
    hosts = get_hosts_from_zabbix()

    # Atualiza cache
    cached_data = {
        "timestamp": time.time(),
        "data": hosts
    }

    return jsonify(hosts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
