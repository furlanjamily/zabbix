from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import time
import requests
import asyncio
from ping3 import ping

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # Habilita WebSocket

# Configurações do Zabbix
ZABBIX_URL = os.getenv("ZABBIX_URL", "http://nocadm.quintadabaroneza.com.br/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "api")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "123mudar@")

async def check_ping(host_ip):
    """Verifica o status de conectividade (ping) do host de forma assíncrona."""
    try:
        response = await asyncio.to_thread(ping, host_ip, timeout=2)
        return "online" if response is not None else "offline"
    except Exception as e:
        print(f"⚠️ Erro ao verificar ping para {host_ip}: {e}")
        return "offline"

async def get_hostgroups_from_zabbix():
    """Consulta a API do Zabbix e obtém os grupos de hosts com status atualizado."""
    try:
        token = get_zabbix_token()
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

def get_zabbix_token():
    """Autentica no Zabbix e retorna o token de sessão."""
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
        "id": 1,
        "auth": None
    }
    response = requests.post(ZABBIX_URL, json=payload)
    data = response.json()
    if "result" in data:
        return data["result"]
    raise Exception(f"Erro ao autenticar no Zabbix: {data}")

@socketio.on("connect")
def handle_connect():
    print("Cliente conectado via WebSocket!")

async def broadcast_data():
    """Atualiza os dados a cada 10s e envia para os clientes via WebSocket."""
    while True:
        data = await get_hostgroups_from_zabbix()
        socketio.emit("update_data", data)
        await asyncio.sleep(10)

# Inicia a atualização automática
@socketio.on("start_monitoring")
def start_monitoring():
    asyncio.create_task(broadcast_data())

if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
