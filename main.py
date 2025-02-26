<<<<<<< HEAD
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import asyncio

app = Flask(__name__)

# Permite requisições de uma origem específica
CORS(app)


# Configurações do Zabbix
ZABBIX_URL = "https://nocadm.quintadabaroneza.com.br/api_jsonrpc.php"
ZABBIX_USER = "api"
ZABBIX_PASSWORD = "123mudar@"  

MAX_CONCURRENT_CHECKS = 10  # Limite de conexões simultâneas

MAX_THREADS = 10  # Limite de threads para paralelizar o ping

def get_auth_token():
    """Autentica no Zabbix e retorna o token"""
=======
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
>>>>>>> 47e2a19 (TesteAjustData)
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
    
    if "result" in data:
        return data["result"]
    else:
        raise Exception(f"Erro ao autenticar no Zabbix: {data}")

<<<<<<< HEAD
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
=======
def get_hosts_from_zabbix():
    """Consulta a API do Zabbix para obter os hosts monitorados."""
>>>>>>> 47e2a19 (TesteAjustData)
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

async def check_all_hosts(ips):
    """Verifica a conectividade de todos os hosts em paralelo"""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_CHECKS)

    async def limited_check(ip):
        async with semaphore:
            return await check_host_status(ip, port=80)

    tasks = [limited_check(ip) for ip in ips]
    return await asyncio.gather(*tasks)

@app.route("/api/hosts", methods=["GET"])
def api_hosts():
    """Endpoint para retornar os hosts e seus status com paginação"""
    # Obter parâmetros de página e limite
    page = int(request.args.get('page', 1))  # Página atual
    limit = int(request.args.get('limit', 10))  # Número de hosts por página
    
    auth_token = get_auth_token()
    if not auth_token:
        return jsonify({"error": "Falha na autenticação do Zabbix"}), 500

    hosts = get_hosts(auth_token)
    if not hosts:
        return jsonify({"error": "Nenhum host encontrado"}), 500

    # Paginação: obter somente os hosts da página solicitada
    start = (page - 1) * limit
    end = start + limit
    paginated_hosts = hosts[start:end]

    ips = {host["interfaces"][0]["ip"] for host in paginated_hosts if "interfaces" in host and host["interfaces"]}

    # Correção: Usar asyncio.create_task() para rodar a verificação assíncrona sem travar Flask
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(check_all_hosts(list(ips)))

    grouped_hosts = {}

    for host in paginated_hosts:
        hostgroups = host.get("groups", [])
        ip = host["interfaces"][0]["ip"] if "interfaces" in host and host["interfaces"] else ""
        status = status_dict.get(ip, "Offline")

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
>>>>>>> 47e2a19 (TesteAjustData)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
