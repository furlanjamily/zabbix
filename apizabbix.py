from flask import Flask, request, jsonify
from pyzabbix import ZabbixAPI
import configparser
import json
from datetime import datetime
import time

app = Flask(__name__)

# Função que realiza a conexão e autenticação no servidor Zabbix
def connect():
    config = configparser.ConfigParser()
    config.read("config.ini")  # pega os dados de acesso do arquivo config.ini

    user = config.get('zabbix', 'user')
    password = config.get('zabbix', 'password')
    server = config.get('zabbix', 'server')

    zapi = ZabbixAPI(server)
    zapi.login(user, password)

    return zapi

# Inicializa a conexão global
zapi = connect()

# Endpoint para consultar histórico
@app.route('/api/zabbix/history', methods=['POST'])
def get_history():
    try:
        # Dados do cliente
        data = request.json
        item_id = data.get('item_id')
        time_from = data.get('time_from')
        time_till = data.get('time_till')

        # Validação básica
        if not item_id or not time_from or not time_till:
            return jsonify({"error": "Parâmetros inválidos"}), 400

        # Consulta histórico
        history = consulta_historico_item(time_from, time_till, item_id, zapi)

        # Processa os dados para JSON
        processed_history = []
        for point in history:
            valor, unidade = converte_mb(point["value"])
            processed_history.append({
                "timestamp": datetime.fromtimestamp(int(point["clock"])).strftime("%Y-%m-%d %H:%M:%S"),
                "value": round(valor, 2),
                "unit": unidade
            })

        return jsonify(processed_history)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Consulta histórico de dados do Zabbix
def consulta_historico_item(time_from, time_till, itemid, api):
    history = api.history.get(
        itemids=itemid,
        time_from=int(time_from),
        time_till=int(time_till),
        output="extend",
        limit="5000",
    )
    return history

# Converte valores para MB
def converte_mb(valor):
    valor = int(valor)
    unidade = "Mb"
    valor = valor / 1000 / 1000
    return valor, unidade

# Iniciar o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
