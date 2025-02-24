<<<<<<< HEAD
<<<<<<< HEAD
from flask import Flask, jsonify, request
=======
from flask import Flask, jsonify
>>>>>>> 6eff47e (testePingOff)
from flask_cors import CORS
import requests
import asyncio
import aioping

app = Flask(__name__)
CORS(app)

ZABBIX_URL = "https://nocadm.quintadabaroneza.com.br/api_jsonrpc.php"
ZABBIX_USER = "api"
ZABBIX_PASSWORD = "123mudar@"  

MAX_CONCURRENT_PINGS = 10

MAX_THREADS = 10  # Limite de threads para paralelizar o ping

def get_auth_token():
<<<<<<< HEAD
    """Autentica no Zabbix e retorna o token"""
=======
import os
import time
import requests
import asyncio
from ping3 import ping
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permitir acesso de outros domínios

# Configurações do Zabbix
ZABBIX_URL = os.getenv("ZABBIX_URL", "http://nocadm.quintadabaroneza.com.br/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "api")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "123mudar@")

# Cache para armazenar os dados temporariamente
cached_data = {"timestamp": 0, "data": []}
CACHE_TIMEOUT = 60  # Tempo de cache em segundos

def get_zabbix_token():
    """Autentica no Zabbix e retorna o token de sessão."""
>>>>>>> 47e2a19 (TesteAjustData)
=======
>>>>>>> 6eff47e (testePingOff)
    payload = {
        "method": "user.login",
<<<<<<< HEAD
=======
        "params": {
            "user": ZABBIX_USER,
            "password": ZABBIX_PASSWORD
        },
        "id": 1,
        "auth": None
>>>>>>> 47e2a19 (TesteAjustData)
    }
    response = requests.post(ZABBIX_URL, json=payload)
    data = response.json()

    print("🔑 Token recebido:", data)  # Debug

    if "result" in data:
        return data["result"]
    else:
        raise Exception(f"Erro ao autenticar no Zabbix: {data}")

<<<<<<< HEAD
<<<<<<< HEAD
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
=======
def get_hosts_from_zabbix():
    """Consulta a API do Zabbix para obter os hosts monitorados."""
>>>>>>> 47e2a19 (TesteAjustData)
=======
async def check_ping(host_ip):
    """Verifica o status de conectividade (ping) do host de forma assíncrona."""
    try:
        response = await asyncio.to_thread(ping, host_ip, timeout=2)
        return "online" if response is not None else "offline"
    except Exception as e:
        print(f"⚠️ Erro ao verificar ping para {host_ip}: {e}")
        return "offline"

async def get_hostgroups_from_zabbix():
    """Consulta a API do Zabbix para obter os grupos de hosts e seus hosts associados."""
>>>>>>> b80c220 (TetsepPing3)
    try:
        token = get_zabbix_token()

        # Obtendo os grupos de hosts
        payload = {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": ["groupid", "name"],
                "selectHosts": ["hostid", "name", "host", "interfaces"]
            },
            "id": 2,
            "auth": token
        }
        response = requests.post(ZABBIX_URL, json=payload)
        data = response.json()

        print("📡 Resposta do Zabbix:", data)  # Debug

        if "result" not in data:
            raise Exception(f"Erro ao buscar grupos de hosts: {data}")

        hostgroups = []
        tasks = []

        for group in data["result"]:
            group_hosts = []
            for host in group["hosts"]:
                ip = host["interfaces"][0].get("ip", "Desconhecido") if host.get("interfaces") else "Desconhecido"
                tasks.append(check_ping(ip))  # Adiciona a tarefa de ping
                group_hosts.append({
                    "hostid": host["hostid"],
                    "name": host["name"],
                    "host": host["host"],
                    "ip": ip
                })

            hostgroups.append({
                "hostgroupid": group["groupid"],
                "name": group["name"],
                "hosts": group_hosts
            })

        # Executa todas as tarefas de ping simultaneamente
        ping_results = await asyncio.gather(*tasks)

        # Atribui os resultados do ping aos hosts
        index = 0
        for group in hostgroups:
            for host in group["hosts"]:
                host["status"] = ping_results[index]
                index += 1

        return hostgroups

    except Exception as e:
        print(f"❌ Erro ao obter grupos de hosts do Zabbix: {e}")
        return []

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
async def check_host_status(ip, port=80):
    """Tenta conectar ao host via TCP na porta especificada"""
    try:
        reader, writer = await asyncio.open_connection(ip, port)
        writer.close()
        await writer.wait_closed()
        return {"ip": ip, "status": "Online"}
    except Exception:
        return {"ip": ip, "status": "Offline"}
=======
async def check_host_status(ip, semaphore):
    async with semaphore:
        try:
            await aioping.ping(ip, timeout=1)
            return {"ip": ip, "status": "Online"}
        except TimeoutError:
            return {"ip": ip, "status": "Offline"}
        except Exception as e:
            return {"ip": ip, "status": f"Erro ({e})"}
>>>>>>> 6eff47e (testePingOff)

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
<<<<<<< HEAD
        status = status_dict.get(ip, "Offline")

=======
        status = next((result["status"] for result in results if result["ip"] == ip), "Offline")
        
>>>>>>> 6eff47e (testePingOff)
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
=======
@app.route("/api/hosts", methods=["GET"])
def api_hosts():
    """Endpoint para listar os hosts monitorados pelo Zabbix."""
=======
@app.route("/api/hostgroups", methods=["GET"])
def api_hostgroups():
    """Endpoint para listar os grupos de hosts e seus hosts monitorados pelo Zabbix."""
>>>>>>> b80c220 (TetsepPing3)
    global cached_data  

    # Retorna do cache se ainda estiver válido
    if time.time() - cached_data["timestamp"] < CACHE_TIMEOUT:
        return jsonify(cached_data["data"])

    # Obtém hostgroups do Zabbix de forma assíncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    hostgroups = loop.run_until_complete(get_hostgroups_from_zabbix())

    # Atualiza cache
    cached_data = {
        "timestamp": time.time(),
        "data": hostgroups
    }

<<<<<<< HEAD
    return jsonify(hosts)
>>>>>>> 47e2a19 (TesteAjustData)
=======
    return jsonify(hostgroups)
>>>>>>> b80c220 (TetsepPing3)

if __name__ == "__main__":
<<<<<<< HEAD
    app.run(host="0.0.0.0", port=10000, debug=True)
=======
    app.run(debug=True, host="0.0.0.0", port=5000)
>>>>>>> 6eff47e (testePingOff)
