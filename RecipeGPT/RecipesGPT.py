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
user_id = ObjectId('66301a37bf601725aecf353b')
# ------------------------------------------- #

user_data = users.find_one({'_id': user_id})
ingredientes_ids = user_data.get('ingredientes', [])

# Buscar os ingredientes pelo ID
ingredientes_usuario = [ingredientes.find_one({'_id': ObjectId(id)}) for id in ingredientes_ids]


@app.route('/')
def get_recipes():
    messages = [
        {"role": "system",
         "content": "Você é um assistente de culinária profissional, que cria receitas apenas com os "
                    "ingredientes que você recebe, mas você não precisa utilizar todos os ingredientes "
                    "que você recebe, use apenas o necessário para que a receita fique gostosa."},
        {"role": "user",
         "content": f"Eu tenho apenas estes ingredientes: {ingredientes_usuario}, "
                    f"você É PROIBIDO de usar algum outro ingrediente que eu não possua. "
                    f"Coloque a receita em um json que possua os seguintes campos, sendo que eles são arrays: "
                    f"nome_receita, ingredientes, ingredientes_quantidade, modo_preparo, tempo_preparo"
                    f"ingredientes_quantidade deve ser retornado sempre em gramas e numero inteiro ou float"}
    ]

    response = client_openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    # Imprimir a resposta
    print(response.choices[0].message.content)

    resultado_chat_str = response.choices[0].message.content

    resultado_chat = json.loads(resultado_chat_str)

    ingredientes_nomes = resultado_chat['ingredientes']
    ingredientes_quantidades = resultado_chat['ingredientes_quantidade']

    ingredientes_list = [ingredientes.find_one({'Descrip': nome_ingrediente}) for nome_ingrediente in ingredientes_nomes]

    valores_nutricionais = calcular_valores_nutricionais(ingredientes_list, ingredientes_quantidades)

    print(valores_nutricionais)

    resposta = {
        'receita': resultado_chat,
        'valores_nutricionais': valores_nutricionais
    }

    return jsonify(resposta)


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
