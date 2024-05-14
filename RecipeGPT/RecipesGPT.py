from senha import API_KEY
from mongoDB.MongoDb import *
from openai import OpenAI
from bson import ObjectId
import json
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Conexão com a API da OpenAI
API_KEY = API_KEY
client_openai = OpenAI(api_key=API_KEY)

# ---------------- MUDAR ISSO --------------- #
user_id = ObjectId('6640e3f34abafb15341e6b03')
# ------------------------------------------- #

user_data = users.find_one({'_id': user_id})
ingredientes_ids = user_data.get('ingredients', [])

# Buscar os ingredientes pelo ID
ingredientes_usuario = [ingredientes.find_one({'_id': ObjectId(id)}) for id in ingredientes_ids]


@app.route('/')
def get_recipes():
    messages = [
        {
            "role": "system",
            "content": "Você é um assistente de culinária profissional, que cria receitas apenas com os ingredientes "
                       "fornecidos. É PROIBIDO usar algum outro ingrediente que não foi fornecido. "
                       "Não é necessário utilizar todos os ingredientes, use apenas o necessário para uma receita boa."
        },
        {
            "role": "user",
            "content": f"Por favor, crie 3 receitas utilizando apenas os seguintes ingredientes: {ingredientes_usuario}. "
                       f"Escreva as receitas em inglês e as apresente em formato JSON. Cada receita deve ser um objeto JSON separado, "
                       f"e todos os objetos de receita devem ser agrupados em um objeto JSON maior chamado 'recipes'. "
                       f"Cada objeto de receita deve ter os seguintes campos: 'nome_receita', 'ingredients', 'ingredients_quantity', "
                       f"'modo_preparo', 'tempo_preparo'. Todos os campos devem ser arrays. "
                       f"Não inclua comentários no JSON. "
                       f"Os ingredientes são sempre fornecidos em quantidades de 100 gramas. Portanto, no campo 'ingredients_quantity', "
                       f"retorne a quantidade necessária como um número inteiro ou float. "
                       f"O campo 'ingredients' deve conter o nome exato do ingrediente fornecido, sem alterações."
        }
    ]

    response = client_openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    # Imprimir a resposta
    print(response.choices[0].message.content)

    resultado_chat_str = response.choices[0].message.content

    resultado_chat = json.loads(resultado_chat_str)

    respostas = []
    for recipe in resultado_chat['recipes']:
        ingredientes_nomes = recipe['ingredients']
        ingredientes_quantidades = recipe['ingredients_quantity']

        ingredientes_list = [ingredientes.find_one({'Descrip': nome_ingrediente}) for nome_ingrediente in
                             ingredientes_nomes]

        valores_nutricionais = calcular_valores_nutricionais(ingredientes_list, ingredientes_quantidades)

        resposta = {
            'receita': recipe,
            'valores_nutricionais': valores_nutricionais
        }
        respostas.append(resposta)

    return jsonify(respostas)


def calcular_valores_nutricionais(ingredientes, quantidades):
    valores_nutricionais_totais = {}

    for ingrediente, quantidade in zip(ingredientes, quantidades):
        for chave, valor in ingrediente.items():
            if chave not in ['_id', 'NDB_No', 'Descrip']:
                valor_nutricional = (valor / 100) * quantidade

                if chave in valores_nutricionais_totais:
                    valores_nutricionais_totais[chave] += valor_nutricional
                else:
                    valores_nutricionais_totais[chave] = valor_nutricional

    return valores_nutricionais_totais


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
