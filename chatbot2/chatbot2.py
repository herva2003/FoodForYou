import json
from fuzzywuzzy import fuzz


def carregar_dados_arquivo(nome_arquivo):
    with open(nome_arquivo, 'r') as json_file:
        return json.load(json_file)


def encontrar_ingrediente(data, nome_ingrediente):
    for item in data:
        if fuzz.partial_ratio(item["Descrip"].lower(), nome_ingrediente.lower()) >= 80:
            return item
    return None


def obter_informacoes_ingredientes(nome_ingrediente):
    data = carregar_dados_arquivo('ingredientes.json')
    ingrediente_encontrado = encontrar_ingrediente(data, nome_ingrediente)
    if ingrediente_encontrado:
        return ingrediente_encontrado
    else:
        return None


while True:
    entrada_usuario = input("Digite algo como 'proteínas de butter with salt' (ou 'sair' para encerrar): ")
    if entrada_usuario.lower() == "sair":
        print("Encerrando o programa. Até mais!")
        break

    tokens = entrada_usuario.split()

    # Verifica se o primeiro token é uma tag válida
    tags_validas = {
        "calorias": "Energy_kcal",
        "proteinas": "Protein_g",
        "gordura": "Fat_g",
        "carboidratos": "Carb_g",
        "fibra": "Fiber_g",
        "acucar": "Sugar_g",
        "calcio": "Calcium_mg",
        "ferro": "Iron_mg",
        "magnesio": "Magnesium_mg",
        "fosforo": "Phosphorus_mg",
        "potassio": "Potassium_mg",
        "sodio": "Sodium_mg",
        "zinco": "Zinc_mg",
        "cobre": "Copper_mcg",
        "manganes": "Manganese_mg",
        "selenio": "Selenium_mcg",
        "vitamina_c": "VitC_mg",
        "tiamina": "Thiamin_mg",
        "riboflavina": "Riboflavin_mg",
        "niacina": "Niacin_mg",
        "vitamina_b6": "VitB6_mg",
        "folato": "Folate_mcg",
        "vitamina_b12": "VitB12_mcg",
        "vitamina_a": "VitA_mcg",
        "vitamina_e": "VitE_mg",
        "vitamina_d2": "VitD2_mcg"
    }

    if tokens[0].lower() in tags_validas:
        nome_ingrediente = " ".join(tokens[2:])  # Obtém o nome do ingrediente após a tag
        informacoes = obter_informacoes_ingredientes(nome_ingrediente)
        if informacoes:
            tag = tokens[0].capitalize()
            valor = informacoes.get(tags_validas.get(tokens[0].lower()), "não encontrado")
            print(f"{tag} de {nome_ingrediente}: {valor}")
        else:
            print(f"O ingrediente '{nome_ingrediente}' não foi encontrado.")
    else:
        print("Por favor, inicie sua consulta com uma das tags válidas.")
