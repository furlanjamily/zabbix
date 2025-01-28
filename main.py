from pyzabbix import ZabbixAPI
import configparser

def test_connection():
    config = configparser.ConfigParser()
    config.read("config.ini")

    user = config.get('zabbix', 'user')
    password = config.get('zabbix', 'password')
    server = config.get('zabbix', 'server')

    print(f"Tentando conectar ao servidor Zabbix: {server} com user='{user}'")

    try:
        zapi = ZabbixAPI(server)
        zapi.login(user, password)  # Assíncrono em versões mais novas
        print("Conexão bem-sucedida!")
    except Exception as e:
        print(f"Erro: {e}")

test_connection()
