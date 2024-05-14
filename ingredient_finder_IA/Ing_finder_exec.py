import spacy
from fuzzywuzzy import fuzz
from mongoDB.MongoDb import ingredientes
from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import ObjectId


app = Flask(__name__)
CORS(app, resources={r"/process_text": {"origins": "*"}})
CORS(app, resources={r"/send_quantities": {"origins": "*"}})

# Load the trained model
model_path = '../models/ingredient_ner'
nlp = spacy.load(model_path)


@app.route('/process_text', methods=['POST'])
def process_text():
    # New text to process
    text_to_process = request.data.decode('utf-8')
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
            ingrediente_encontrado['_id'] = str(ingrediente_encontrado['_id'])  # Convert ObjectId to string
            ingrediente_encontrado['nome_ingrediente'] = nome_ingrediente  # Add ingredient name
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
    results = []
    for info in informacoes:
        if isinstance(info, dict):
            results.append({'_id': info['_id'], 'Descrip': info['Descrip']})
        else:
            results.append(info)

    return jsonify(results)


@app.route('/send_quantities', methods=['POST'])
def send_quantities():
    quantities = request.get_json()
    print('Received quantities:', quantities)

    def calcular_valores_nutricionais(quantidades):
        valores_nutricionais_totais = {}

        for item in quantidades:
            _id = item['_id']
            quantidade = item['quantity']

            # Busca os detalhes do ingrediente no MongoDB usando o _id
            ingrediente_detalhes = ingredientes.find_one({'_id': ObjectId(_id)})
            print(ingrediente_detalhes)

            if ingrediente_detalhes:
                # Calcula os valores nutricionais proporcionais
                for chave, valor in ingrediente_detalhes.items():
                    if chave not in ['_id', 'NDB_No', 'Descrip']:
                        valor_nutricional = (valor / 100) * quantidade

                        if chave in valores_nutricionais_totais:
                            valores_nutricionais_totais[chave] += valor_nutricional
                        else:
                            valores_nutricionais_totais[chave] = valor_nutricional
            print(valores_nutricionais_totais)

        return valores_nutricionais_totais

    # Calcula os valores nutricionais totais com base nas quantidades recebidas
    valores_nutricionais = calcular_valores_nutricionais(quantities)

    return jsonify({'message': 'Quantities received successfully', 'nutritional_values': valores_nutricionais})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
