from senha import API_KEY
from MongoDb import *
from openai import OpenAI
from bson import ObjectId


# Conexão com a API da OpenAI
API_KEY = API_KEY
client_openai = OpenAI(api_key=API_KEY)


user_id = ObjectId('66301a37bf601725aecf353b')
user_data = users.find_one({'_id': user_id})
ingredientes_usuario = user_data.get('ingredientes', [])


messages = [
    {"role": "system",
     "content": "Você é um assistente de culinária profissional, que cria receitas apenas com os "
                "ingredientes que você recebe, mas você não precisa utilizar todos os ingredientes "
                "que você recebe, use apenas o necessário para que a receita fique gostosa."},
    {"role": "user",
     "content": f"Eu tenho apenas estes ingredientes: {ingredientes_usuario}, "
                f"você É PROIBIDO de usar algum outro ingrediente que eu não possua. "
                f"Coloque a receita em um json que possua os seguintes campos, sendo que eles são arrays: "
                f"nome_receita, ingredientes, modo_preparo, tempo_preparo"}
]

response = client_openai.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=messages
)

# Imprimir a resposta
print(response.choices[0].message.content)

