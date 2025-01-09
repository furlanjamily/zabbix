import apizabbix




api = apizabbix.connect() # Realiza a conexao com o servidor

# Realiza consulta  e armazena na variavel, elimina os grupos que contem o nome Templates
hostgroups = api.hostgroup.get(
    output='extend',
    excludeSearch=True,
    search={
        'name': 'Templates'
    },
    selectHosts=[
        'name',
        'host',
        'id'
    ]
)

apizabbix.processa_dados_api(hostgroups)

#hostgroups = api.hostgroup.get() # Coleta os hostgroups existentes no servidor

for hostgroup in hostgroups:
    print(" Grupo "+ hostgroup['name'])

    for host in hostgroup['hosts']:
        print("    Host: " + host['name'] + ": " + host['host'])


#apizabbix.processa_dados_api(hostgroups)


api.user.logout() # fecha a conexão