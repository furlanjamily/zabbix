from flask import Flask, jsonify
from flask_cors import CORS
import requests
import asyncio
import socket

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "https://monitoramento-baroneza.vercel.app"}})

ZABBIX_URL = "https://nocadm.quintadabaroneza.com.br/api_jsonrpc.php"
ZABBIX_USER = "api"
ZABBIX_PASSWORD = "123mudar@"

MAX_CONCURRENT_CHECKS = 10  # Limite de conexões simultâneas

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
        return response.json().get("result")
    except requests.exceptions.RequestException as e:
        print(f"Erro na autenticação: {e}")
        return None

def get_hosts(auth_token):
    """Obtém os hosts e seus status diretamente da API do Zabbix"""
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
        response = requests.post(ZABBIX_URL, json=payload, headers=headers, verify=False)
        response.raise_for_status()
        return response.json().get("result", [])
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter hosts: {e}")
        return []

async def check_host_status(ip, port=80, timeout=1):
    """Tenta conectar ao host via TCP na porta especificada"""
    try:
        reader, writer = await asyncio.open_connection(ip, port)
        writer.close()
        await writer.wait_closed()
        return {"ip": ip, "status": "Online"}
    except Exception:
        return {"ip": ip, "status": "Offline"}

async def check_all_hosts(ips):
    """Verifica a conectividade de todos os hosts em paralelo"""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)
    
    async def limited_check(ip):
        async with semaphore:
            return await check_host_status(ip, port=80)  # Porta 80 (HTTP)

    tasks = [limited_check(ip) for ip in ips]
    return await asyncio.gather(*tasks)

@app.route("/api/hosts", methods=["GET"])
def api_hosts():
    """Endpoint para retornar os hosts e seus status"""
    auth_token = get_auth_token()
    if not auth_token:
        return jsonify({"error": "Falha na autenticação do Zabbix"}), 500

    hosts = get_hosts(auth_token)
    ips = {host["interfaces"][0]["ip"] for host in hosts if "interfaces" in host and host["interfaces"]}
    
    results = asyncio.run(check_all_hosts(list(ips)))

    grouped_hosts = {}
    for host in hosts:
        hostgroups = host.get("groups", [])
        ip = host["interfaces"][0]["ip"] if "interfaces" in host and host["interfaces"] else ""
        status = next((result["status"] for result in results if result["ip"] == ip), "Offline")
        
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
