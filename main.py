from flask import Flask, jsonify
from flask_cors import CORS
import requests
import asyncio
import aioping

app = Flask(__name__)

CORS(app, resources={r"/api/*": {"origins": "https://monitoramento-baroneza.vercel.app"}})

ZABBIX_URL = "https://nocadm.quintadabaroneza.com.br/api_jsonrpc.php"
ZABBIX_USER = "api"
ZABBIX_PASSWORD = "123mudar@"

MAX_CONCURRENT_PINGS = 10

def get_auth_token():
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

async def check_host_status(ip, semaphore):
    async with semaphore:
        try:
            await aioping.ping(ip, timeout=1)
            return {"ip": ip, "status": "Online"}
        except TimeoutError:
            return {"ip": ip, "status": "Offline"}
        except Exception as e:
            return {"ip": ip, "status": f"Erro ({e})"}

async def check_all_hosts(ips):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_PINGS)
    tasks = [check_host_status(ip, semaphore) for ip in ips]
    return await asyncio.gather(*tasks)

@app.route("/api/hosts", methods=["GET"])
def api_hosts():
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
