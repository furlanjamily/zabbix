import apizabbix

api = apizabbix.connect() # Realiza a conexao com o servidor

# Consulta elimina os grupos que contem o nome Templates
hostgroups = api.hostgroup.get(
    output='extend',
    excludeSearch=True,
    search={
        'name': 'Templates'
    }
)

#hostgroups = api.hostgroup.get() # Coleta os hostgroups existentes no servidor

for hostgroup in hostgroups:
    print(
        hostgroup['name']
    )

#apizabbix.processa_dados_api(hostgroups)


api.user.logout() # fecha a conexão