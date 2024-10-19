import spacy
from fuzzywuzzy import fuzz
from mongoDB.MongoDb import ingredientes
from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import ObjectId

# Criação da aplicação Flask
app = Flask(__name__)

# Configuração do CORS (Cross-Origin Resource Sharing) para permitir requisições de qualquer origem
# nos endpoints especificados, possibilitando a comunicação entre diferentes domínios
CORS(app, resources={r"/process_text": {"origins": "*"}})
CORS(app, resources={r"/send_quantities": {"origins": "*"}})
CORS(app, resources={r"/process_ingredients": {"origins": "*"}})

# Carregamento do modelo treinado de reconhecimento de entidades nomeadas (NER) do spaCy
model_path = '../models/ingredient_ner'
nlp = spacy.load(model_path)

@app.route('/process_ingredients', methods=['POST'])
def process_ingredients():
    """
    Endpoint para processar ingredientes e quantidades enviados via POST e calcular valores nutricionais.
    """
    ingredients_data = request.get_json()
    print('Received ingredients data:', ingredients_data)

    def calcular_valores_nutricionais(ingredients_data):
        """
        Função para calcular os valores nutricionais totais com base nas quantidades recebidas.

        Args:
        ingredients_data (list): Lista de dicionários contendo '_id' do ingrediente e 'quantity' a ser calculada.

        Returns:
        dict: Dicionário contendo os valores nutricionais totais calculados.
        """
        valores_nutricionais_totais = {}

        for item in ingredients_data:
            _id = item['_id']
            quantidade = item['quantity']

            # Busca os detalhes do ingrediente no MongoDB usando o _id
            ingrediente_detalhes = ingredientes.find_one({'_id': ObjectId(_id)})
            print(ingrediente_detalhes)

            if ingrediente_detalhes:
                # Calcula os valores nutricionais proporcionais com base na quantidade
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
    valores_nutricionais = calcular_valores_nutricionais(ingredients_data)

    # Retorna os valores nutricionais totais em formato JSON
    return jsonify({'nutritional_values': valores_nutricionais})

@app.route('/process_text', methods=['POST'])
def process_text():
    """
    Endpoint para processar texto enviado via POST, identificar ingredientes e retornar informações sobre eles.
    """

    # Recebe o texto a ser processado da requisição HTTP
    text_to_process = request.data.decode('utf-8')
    text_to_process = "1 Tbsp " + text_to_process

    # Adiciona "1 Tbsp" após certas palavras para normalizar o texto
    text_to_process = (text_to_process
                       .replace(',', ', 1 Tbsp ')
                       .replace('and', ' 1 Tbsp ')
                       .replace('chopped', ' 1 Tbsp ')
                       .replace('in', ' 1 Tbsp ')
                       .replace('the', ' 1 Tbsp ')
                       )

    # Processa o texto usando o modelo NER do spaCy para identificar entidades
    doc = nlp(text_to_process)

    # Conjunto para armazenar os ingredientes encontrados
    ing_found = set()

    # Itera sobre as entidades encontradas no texto processado
    for ent in doc.ents:
        # Adiciona o texto da entidade ao conjunto de ingredientes encontrados
        ing_found.add(ent.text)

        print(ent)
        print(ing_found)

    def encontrar_ingrediente(data, nome_ingrediente):
        """
        Função para encontrar o melhor candidato de ingrediente na base de dados com base na similaridade de texto.

        Args:
        data (list): Lista de dicionários contendo dados dos ingredientes.
        nome_ingrediente (str): Nome do ingrediente a ser encontrado.

        Returns:
        dict or str: O melhor item encontrado ou "NONE" se a pontuação for menor ou igual a 80.
        """
        melhor_pontuacao = 0
        melhor_diferenca_tamanho = float('inf')  # Inicializa com um valor grande
        melhor_item = None
        for item in data:
            # Calcula a similaridade entre descrições usando fuzzy matching
            pontuacao = fuzz.token_set_ratio(item["Descrip"].lower(), nome_ingrediente.lower())
            diferenca_tamanho = abs(len(item["Descrip"]) - len(nome_ingrediente))
            # Atualiza o melhor item com base na pontuação e na diferença de tamanho
            if pontuacao > melhor_pontuacao or (
                    pontuacao == melhor_pontuacao and diferenca_tamanho < melhor_diferenca_tamanho):
                melhor_pontuacao = pontuacao
                melhor_diferenca_tamanho = diferenca_tamanho
                melhor_item = item
        # Retorna o melhor item se a pontuação for maior que 80, caso contrário, retorna "NONE"
        return melhor_item if melhor_pontuacao > 80 else "NONE"

    def obter_informacoes_ingredientes(nome_ingrediente):
        """
        Função para obter informações do ingrediente a partir do banco de dados.

        Args:
        nome_ingrediente (str): Nome do ingrediente a ser pesquisado.

        Returns:
        dict or None: Dicionário contendo informações do ingrediente encontrado, ou None se não encontrado.
        """
        # Busca os dados dos ingredientes no MongoDB
        data = ingredientes.find()
        # Encontra o melhor candidato de ingrediente
        ingrediente_encontrado = encontrar_ingrediente(data, nome_ingrediente)
        if ingrediente_encontrado != "NONE":
            # Converte ObjectId para string e adiciona o nome do ingrediente
            ingrediente_encontrado['_id'] = str(ingrediente_encontrado['_id'])
            ingrediente_encontrado['nome_ingrediente'] = nome_ingrediente
            return ingrediente_encontrado
        else:
            return None

    def obter_informacoes_todos_ingredientes():
        """
        Função para obter informações de todos os ingredientes encontrados no texto.

        Returns:
        list: Lista de dicionários contendo informações dos ingredientes encontrados.
        """
        informacoes_ingredientes = []
        for ingrediente in ing_found:
            # Obtém informações de cada ingrediente encontrado
            info = obter_informacoes_ingredientes(ingrediente)
            if info is not None:
                informacoes_ingredientes.append(info)
        return informacoes_ingredientes

    # Obtém informações de todos os ingredientes identificados no texto
    informacoes = obter_informacoes_todos_ingredientes()
    results = []
    for info in informacoes:
        if isinstance(info, dict):
            # Adiciona informações relevantes ao resultado
            results.append({'_id': info['_id'], 'Descrip': info['Descrip']})
        else:
            results.append(info)

    # Retorna as informações dos ingredientes em formato JSON
    return jsonify(results)


@app.route('/send_quantities', methods=['POST'])
def send_quantities():
    """
    Endpoint para receber quantidades de ingredientes via POST e calcular valores nutricionais totais.
    """
    # Recebe as quantidades dos ingredientes da requisição HTTP
    quantities = request.get_json()
    print('Received quantities:', quantities)

    def calcular_valores_nutricionais(quantidades):
        """
        Função para calcular os valores nutricionais totais com base nas quantidades recebidas.

        Args:
        quantidades (list): Lista de dicionários contendo '_id' do ingrediente e 'quantity' a ser calculada.

        Returns:
        dict: Dicionário contendo os valores nutricionais totais calculados.
        """
        valores_nutricionais_totais = {}

        for item in quantidades:
            _id = item['_id']
            quantidade = item['quantity']

            # Busca os detalhes do ingrediente no MongoDB usando o _id
            ingrediente_detalhes = ingredientes.find_one({'_id': ObjectId(_id)})
            print(ingrediente_detalhes)

            if ingrediente_detalhes:
                # Calcula os valores nutricionais proporcionais com base na quantidade
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

    # Retorna os valores nutricionais totais em formato JSON
    return jsonify({'nutritional_values': valores_nutricionais})


if __name__ == '__main__':
    # Inicia a aplicação Flask
    app.run(host='0.0.0.0', debug=True)
