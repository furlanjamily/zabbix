import threading
import asyncio
import socket
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os
import requests
from ping3 import ping

# 🔹 Configuração do Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para evitar problemas com o frontend

# 🔹 Inicializa o SocketIO para WebSockets
socketio = SocketIO(app, cors_allowed_origins="*")

# 🔹 Configurações do Zabbix
ZABBIX_URL = os.getenv("ZABBIX_URL", "http://nocadm.quintadabaroneza.com.br/api_jsonrpc.php")
ZABBIX_USER = os.getenv("ZABBIX_USER", "api")
ZABBIX_PASSWORD = os.getenv("ZABBIX_PASSWORD", "123mudar@")

def check_ping(host_ip):
    """Verifica se o host responde ao ping usando socket."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)  # Timeout de 2 segundos
            result = s.connect_ex((host_ip, 80))  # Testa a conexão na porta 80
            return "online" if result == 0 else "offline"
    except Exception as e:
        print(f"⚠️ Erro ao verificar ping para {host_ip}: {e}")
        return "offline"

def get_zabbix_token():
    """Autentica no Zabbix e retorna o token de sessão."""
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
        "id": 1,
        "auth": None
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(ZABBIX_URL, json=payload, headers=headers)
    data = response.json()

    if "result" in data:
        return data["result"]
    raise Exception(f"Erro ao autenticar no Zabbix: {data}")

def get_hostgroups_from_zabbix():
    """Obtém os grupos de hosts e verifica o status via socket."""
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
        headers = {"Content-Type": "application/json"}
        response = requests.post(ZABBIX_URL, json=payload, headers=headers)
        data = response.json()

        if "result" not in data:
            raise Exception(f"Erro ao buscar grupos de hosts: {data}")

        hostgroups = []
        for group in data["result"]:
            group_hosts = []
            for host in group["hosts"]:
                ip = host["interfaces"][0].get("ip", "Desconhecido") if host.get("interfaces") else "Desconhecido"
                status = check_ping(ip)  # Verifica o status usando socket
                group_hosts.append({
                    "hostid": host["hostid"],
                    "name": host["name"],
                    "host": host["host"],
                    "ip": ip,
                    "status": status
                })
            hostgroups.append({
                "hostgroupid": group["groupid"],
                "name": group["name"],
                "hosts": group_hosts
            })
        return hostgroups
    except Exception as e:
        print(f"❌ Erro ao obter grupos de hosts do Zabbix: {e}")
        return []

@socketio.on("connect")
def handle_connect():
    """Evento chamado quando um cliente se conecta via WebSocket."""
    print("✅ Cliente conectado via WebSocket!")

def start_monitoring_task():
    """Inicia a atualização contínua dos dados."""
    while True:
        data = get_hostgroups_from_zabbix()
        socketio.emit("update_data", data)
        socketio.sleep(10)  # Atualiza os dados a cada 10 segundos

@socketio.on("start_monitoring")
def start_monitoring():
    """Inicia a transmissão contínua de dados para os clientes."""
    print("📡 Iniciando monitoramento dos hosts...")
    threading.Thread(target=start_monitoring_task, daemon=True).start()

# 🔹 Executa a aplicação Flask com WebSockets
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
