from flask import Flask, jsonify
from flask_cors import CORS
import requests
import socket
import time
import warnings

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

ZABBIX_URL = "https://nocadm.quintadabaroneza.com.br/api_jsonrpc.php"
ZABBIX_USER = "api"
ZABBIX_PASSWORD = "123mudar@"  # ⚠️ Armazene credenciais com segurança.

CACHE_TIMEOUT = 30  # Cache de 30 segundos
cached_data = {"timestamp": 0, "data": {}}

def get_auth_token():
    """Obtém o token de autenticação do Zabbix."""
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
        "id": 1,
        "auth": None
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, verify=False, timeout=5)
        response.raise_for_status()
        return response.json().get("result")
    except requests.exceptions.RequestException as e:
        print(f"Erro na autenticação: {e}")
        return None

def get_hosts(auth_token):
    """Obtém a lista de hosts cadastrados no Zabbix."""
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["host", "name"],
            "selectInterfaces": ["ip"],
            "selectGroups": ["name"]
        },
        "auth": auth_token,
        "id": 2
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, verify=False, timeout=5)
        response.raise_for_status()
        return response.json().get("result", [])
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter hosts: {e}")
        return []

def check_host_status(ip, port=80, timeout=2):
    """Verifica a conectividade de um host usando socket."""
    try:
        socket.create_connection((ip, port), timeout)
        return "Online"
    except (socket.timeout, socket.error):
        return "Offline"

@app.route("/api/hosts", methods=["GET"])
def api_hosts():
    """Endpoint que retorna o status dos hosts do Zabbix."""
    global cached_data

    # Verifica se os dados no cache ainda são válidos
    if time.time() - cached_data["timestamp"] < CACHE_TIMEOUT:
        return jsonify(cached_data["data"])

    auth_token = get_auth_token()
    if not auth_token:
        return jsonify({"error": "Falha na autenticação do Zabbix"}), 500

    hosts = get_hosts(auth_token)
    grouped_hosts = {}

    for host in hosts:
        hostgroups = host.get("groups", [])
        ip = host["interfaces"][0]["ip"] if "interfaces" in host and host["interfaces"] else ""
        status = check_host_status(ip)

        for group in hostgroups:
            group_name = group.get("name", "Unknown Group")
            if group_name not in grouped_hosts:
                grouped_hosts[group_name] = []
            grouped_hosts[group_name].append({
                "host": host["host"],
                "name": host.get("name", "Unknown"),
                "ip": ip,
                "status": status
            })

    cached_data = {"timestamp": time.time(), "data": grouped_hosts}

    return jsonify(grouped_hosts)

if __name__ == "__main__":
    warnings.simplefilter("ignore")  # Oculta avisos de SSL sem verificação
    app.run(debug=True, host="0.0.0.0", port=5000)
