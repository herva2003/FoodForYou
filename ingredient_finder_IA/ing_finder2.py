import re
import ast
import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import ObjectId
from fuzzywuzzy import fuzz
import logging
from pymongo import MongoClient
import json

client_mongo = MongoClient('mongodb+srv://gvghervatin:123456qwerty@cluster0.b4m0rm3.mongodb.net/')

db = client_mongo['PI5']
users = db['users']
ingredientes = db['ingredientes']

# Configuração do logging
logging.basicConfig(level=logging.INFO)

# Criação da aplicação Flask
app = Flask(__name__)
CORS(app, resources={r"/process_text": {"origins": "*"}})
CORS(app, resources={r"/send_quantities": {"origins": "*"}})
CORS(app, resources={r"/process_ingredients": {"origins": "*"}})

# Carregar CSV e extrair lista de ingredientes da coluna 'NER'
def carregar_ingredientes(csv_path):
    try:
        df = pd.read_csv(csv_path)
        ingredientes_set = set()
        for ner_list in df['NER']:
            ingredientes = ast.literal_eval(ner_list)  # Converte a string da lista em uma lista real
            for ing in ingredientes:
                ingredientes_set.add(ing.lower().strip())  # Adiciona cada ingrediente ao conjunto em minúsculas
        return list(ingredientes_set)
    except FileNotFoundError:
        logging.error('File ner.csv not found.')
        return []

ingredientes_list = carregar_ingredientes('/app/ingredient_finder_IA/ner.csv')
    
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
    raw_data = request.data.decode('utf-8')
    
    # Parse the raw JSON string to a dictionary
    data_dict = json.loads(raw_data)
    
    # Extract the actual text to process
    text_to_process = data_dict.get("text_to_process", "")

    # Remove caracteres especiais e números do texto
    text_to_process = re.sub(r'[^a-zA-Z\s]', '', text_to_process).lower()

    # Inicializa um conjunto para armazenar ingredientes encontrados
    ing_found = set()

    # Divide o texto em palavras
    words = text_to_process.split()

    # Função para identificar ingredientes compostos no texto
    def identificar_ingredientes(text, ingredientes_list):
        found_ingredients = set()
        words = text.split()
        n = len(words)

        # Tentar identificar ingredientes compostos, começando pelos maiores
        for length in range(n, 0, -1):
            for i in range(n - length + 1):
                possible_ingredient = ' '.join(words[i:i + length])
                if possible_ingredient in ingredientes_list:
                    found_ingredients.add(possible_ingredient)
                    # Marcar as palavras como usadas
                    for j in range(i, i + length):
                        words[j] = ''
        return found_ingredients

    # Identifica os ingredientes no texto
    ing_found = identificar_ingredientes(text_to_process, ingredientes_list)
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
    app.run(host='0.0.0.0', port=5000, debug=True)