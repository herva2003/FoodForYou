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

# ------ DADOS PARA RECEBER DO SERVIDOR ----- #
# ID DO USUARIO
user_id = ObjectId('6654e20af9b8567d917ad516')

# TIPO REFEIÇÃO
tipo_refeicao = ""

# OBSERVAÇÕES
observacao = ""
# ------------------------------------------- #

user_data = users.find_one({'_id': user_id})

ingredientes_ids = user_data.get('ingredients', [])
restricoes_alim = user_data.get('restricoes_alim', [])

# Buscar os ingredientes pelo ID
ingredientes_usuario = [ingredientes.find_one({'_id': ObjectId(id)}) for id in ingredientes_ids]


@app.route('/')
def get_recipes():
    messages = [
        {
            "role": "system",
            "content": "Você é um assistente de culinária profissional. Crie receitas usando apenas os ingredientes fornecidos. "
                       "Não adicione ingredientes extras. Não é obrigatório usar todos os ingredientes."
        },
        {
            "role": "user",
            "content": (
                "Crie apenas 1 receita em inglês, considerando as seguintes informações:\n"
                f"- Ingredientes disponíveis: {ingredientes_usuario}\n"
                f"- Restrições alimentares: {restricoes_alim}\n"
                f"- Tipo de refeição: {tipo_refeicao}\n"
                f"- Observações: {observacao}\n"
                "Apresente as receitas em formato JSON, sem comentários. Agrupe os objetos JSON de cada receita "
                "em um objeto maior chamado 'recipes'. Cada objeto de receita deve conter os campos: "
                "'nome_receita', 'ingredients', 'ingredients_quantity', 'modo_preparo', 'tempo_preparo', "
                "todos como arrays. Os ingredientes devem ser listados com o nome exato fornecido e as quantidades "
                "devem ser especificadas em números inteiros ou decimais, representando a quantidade em gramas, "
                "partindo de uma base de 100 gramas para cada ingrediente."
            )
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
