from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# ⚠️ Pegando credenciais de variáveis de ambiente
ZABBIX_URL = os.getenv("ZABBIX_URL", "https://nocadm.quintadabaroneza.com.br/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "api")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "123mudar@")  # ⚠️ Mude isso e use variáveis de ambiente

def get_auth_token():
    """Autentica no Zabbix e retorna o token"""
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
        "id": 1,
        "auth": None
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        return data.get("result")
    except requests.exceptions.RequestException as e:
        print(f"Erro na autenticação: {e}")
        return None

def get_hosts(auth_token):
    """Obtém os hosts e seus status diretamente da API do Zabbix"""
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": ["host", "name", "status"],
            "selectInterfaces": ["ip"],
            "selectGroups": ["name"]
        },
        "auth": auth_token,
        "id": 2
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        return data.get("result", [])
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter hosts: {e}")
        return []

@app.route("/api/hosts", methods=["GET"])
def api_hosts():
    """Endpoint para retornar os hosts e seus status"""
    auth_token = get_auth_token()
    if not auth_token:
        return jsonify({"error": "Falha na autenticação do Zabbix"}), 500

    hosts = get_hosts(auth_token)

    grouped_hosts = {}
    for host in hosts:
        hostgroups = host.get("groups", [])
        ip = host["interfaces"][0]["ip"] if host.get("interfaces") and len(host["interfaces"]) > 0 else "Sem IP"
        status = "Online" if host["status"] == "0" else "Offline"

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

    return jsonify(grouped_hosts)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
