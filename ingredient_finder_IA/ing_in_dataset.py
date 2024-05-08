import json


def carregar_dados_arquivo(nome_arquivo):
    with open(nome_arquivo, 'r') as json_file:
        return json.load(json_file)


def obter_dados_ingrediente(data, nome_ingrediente):
    for item in data:
        if nome_ingrediente.lower() == item["Descrip"].lower():
            return item
    return None


# Carregar os dados
data = carregar_dados_arquivo('../ingredientes.json')

# Obter os dados de "salt"
dados_salt = obter_dados_ingrediente(data, "cheese cottage crmd wfruit")

if dados_salt is not None:
    print("Dados de 'salt' em ingredientes.json:")
    print(dados_salt)
else:
    print("'Salt' não foi encontrado em ingredientes.json.")
