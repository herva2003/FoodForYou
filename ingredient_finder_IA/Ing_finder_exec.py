import spacy
from fuzzywuzzy import fuzz
from mongoDB.MongoDb import ingredientes

# Load the trained model
model_path = '../models/ingredient_ner'
nlp = spacy.load(model_path)

# New text to process
text_to_process = ("1 baked pie shell"", ""1 qt. cleaned strawberries"", ""1 1/2 c. water"","
                   " ""4 Tbsp. cornstarch"", ""1 c. sugar"", ""1/8 tsp. salt"", ""4 Tbsp. strawberry jello")

text_to_process = "1 Tbsp " + text_to_process

text_to_process = (text_to_process
                   .replace(',', ', 1 Tbsp ')
                   .replace('and', ' 1 Tbsp ')
                   .replace('chopped', ' 1 Tbsp ')
                   .replace('in', ' 1 Tbsp ')
                   )

# Process the text
doc = nlp(text_to_process)

ing_found = set()

# Display the entities
for ent in doc.ents:
    ing_found.add(ent.text)  # Add the text of the entity
    print(f"{ent.text}")

print(ing_found)


def encontrar_ingrediente(data, nome_ingrediente):
    melhor_pontuacao = 0
    melhor_diferenca_tamanho = float('inf')  # inicializa com um valor grande
    melhor_item = None
    for item in data:
        pontuacao = fuzz.token_set_ratio(item["Descrip"].lower(), nome_ingrediente.lower())
        diferenca_tamanho = abs(len(item["Descrip"]) - len(nome_ingrediente))
        if pontuacao > melhor_pontuacao or (
                pontuacao == melhor_pontuacao and diferenca_tamanho < melhor_diferenca_tamanho):
            melhor_pontuacao = pontuacao
            melhor_diferenca_tamanho = diferenca_tamanho
            melhor_item = item
    return melhor_item if melhor_pontuacao > 80 else "NONE"


def obter_informacoes_ingredientes(nome_ingrediente):
    data = ingredientes.find()
    ingrediente_encontrado = encontrar_ingrediente(data, nome_ingrediente)
    if ingrediente_encontrado:
        return ingrediente_encontrado
    else:
        return None


def obter_informacoes_todos_ingredientes():
    informacoes_ingredientes = []
    for ingrediente in ing_found:
        info = obter_informacoes_ingredientes(ingrediente)
        if info is not None:
            informacoes_ingredientes.append(info)
    return informacoes_ingredientes


informacoes = obter_informacoes_todos_ingredientes()
print(informacoes)

for info in informacoes:
    if isinstance(info, dict):
        print(info['Descrip'])
    else:
        print(info)

print(ing_found)
