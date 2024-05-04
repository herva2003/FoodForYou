from flask import Flask
from openai import OpenAI
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

client = OpenAI(
    api_key="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",
)

@app.route('/')
def get_recipes():
    ingredients = [
        "frango", "cebola", "alho", "tomate", "pimentão", "sal", "pimenta-do-reino",
        "orégano", "manjericão", "alecrim", "tomilho", "salsa", "cebolinha", "coentro",
        "cominho", "páprica", "curry", "gengibre", "canela", "noz-moscada", "louro",
        "azeite de oliva", "vinagre balsâmico", "molho de soja", "mel", "mostarda", "ketchup",
        "maionese", "queijo ralado", "creme de leite", "carne", "arroz", "batata", "feijão", "milho",
        "ervilha", "cenoura", "beterraba", "abóbora", "espinafre", "brócolis", "couve-flor", "abobrinha",
        "berinjela", "pepino", "alface", "rúcula", "chuchu", "quiabo", "lentilha", "grão de bico"
    ]

    prompt = (
        f"Eu gostaria de preparar uma receita com os seguintes ingredientes: {', '.join(ingredients)}"
        "Para o valor nutricional, forneça valores aproximados para cada valor. Exemplo: valores_nutricionais: ['proteina: 8', 'carboidrato: 12', etc] "
        "quero o resultado em json, onde: titulo é um array, modo_preparo é um array, "
        "ingredientes é um array, valores_nutricionais é um array"
        "Exemplo de resposta:"
        "receitas: [{titulo: ['........'], modo_preparo: ['........'], ingredientes: ['........'], valores_nutricionais: ['........']}]"

    )

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=[
            {
                "role": "system",
                "content": "You are a cooker assistant, i give you ingredients and you give me recipes."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return completion.choices[0].message.content


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
