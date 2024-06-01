import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import random
import pandas as pd
import ast
import logging
import os

# Função para configurar o sistema de logging
def setup_logging():
    """
    Configura o sistema de logging para o nível INFO.
    """
    logging.basicConfig(level=logging.INFO)

# Verificação se o script está sendo executado diretamente
if __name__ == "__main__":
    setup_logging()  # Configura o logging se o script estiver sendo executado diretamente

# Carrega um modelo pré-existente do spaCy (neste caso, o modelo em inglês)
nlp = spacy.load('en_core_web_sm')

# Verifica se 'INGREDIENT' é um tipo de entidade reconhecido no modelo carregado
if 'INGREDIENT' not in nlp.pipe_labels['ner']:
    # Adiciona o rótulo 'INGREDIENT' ao componente NER (Named Entity Recognition) do modelo
    ner = nlp.get_pipe('ner')
    ner.add_label('INGREDIENT')

# Função para remover entidades sobrepostas
def remove_overlapping_entities(entities):
    """
    Remove entidades sobrepostas em uma lista de entidades.

    Args:
    entities (list): Lista de tuplas contendo (start_index, end_index, label).

    Returns:
    list: Lista de entidades sem sobreposições.
    """
    # Ordena as entidades pelo índice inicial
    entities = sorted(entities, key=lambda x: x[0])
    non_overlapping_entities = []
    last_end_index = -1  # Inicializa o índice final da última entidade adicionada
    for entity in entities:
        # Adiciona a entidade se ela não se sobrepõe com a última entidade adicionada
        if entity[0] > last_end_index:
            non_overlapping_entities.append(entity)
            last_end_index = entity[1]  # Atualiza o índice final da última entidade adicionada
    return non_overlapping_entities

# Função para preparar os dados de treinamento a partir de um DataFrame
def prepare_data(df):
    """
    Prepara os dados de treinamento a partir de um DataFrame.

    Args:
    df (DataFrame): DataFrame contendo textos e anotações de entidades.

    Returns:
    list: Lista de tuplas contendo (texto, anotações) prontas para treinamento.
    """
    TRAIN_DATA = []
    for index, row in df.iterrows():
        entities = []
        ingredients_text = row['ingredients'].lower()  # Converte o texto dos ingredientes para minúsculas
        for ing in ast.literal_eval(row['NER']):
            ing_lower = ing.lower()  # Converte o nome do ingrediente para minúsculas
            # Encontra todas as ocorrências da entidade no texto dos ingredientes
            start_index = ingredients_text.find(ing_lower)
            while start_index != -1:  # Continua encontrando enquanto houverem ocorrências
                end_index = start_index + len(ing_lower)
                entities.append((start_index, end_index, 'INGREDIENT'))  # Adiciona a entidade à lista
                start_index = ingredients_text.find(ing_lower, start_index + 1)  # Procura a próxima ocorrência
        # Remove entidades sobrepostas para evitar conflitos
        entities = remove_overlapping_entities(entities)
        # Adiciona o texto dos ingredientes e suas entidades ao conjunto de dados de treinamento
        TRAIN_DATA.append((row['ingredients'], {'entities': entities}))

    # Filtra entidades desalinhadas para garantir a qualidade dos dados de treinamento
    TRAIN_DATA = [data for data in TRAIN_DATA if not misaligned_entities(data, nlp)]
    return TRAIN_DATA

# Função para verificar se há entidades desalinhadas nos dados de treinamento
def misaligned_entities(data, nlp):
    """
    Verifica se há entidades desalinhadas nos dados de treinamento.

    Args:
    data (tuple): Tupla contendo (texto, anotações).
    nlp (Language): Modelo spaCy carregado.

    Returns:
    bool: True se há entidades desalinhadas, False caso contrário.
    """
    text, annotations = data
    doc = nlp.make_doc(text)  # Cria um documento spaCy a partir do texto
    tags = spacy.training.offsets_to_biluo_tags(doc, annotations['entities'])  # Converte entidades para tags BILUO
    if '-' in tags:  # Verifica se há tags desalinhadas
        logging.error(f"Misaligned entity in text: {text}, entities: {annotations['entities']}")  # Registra um erro
        return True
    return False

# Função para treinar o modelo NER
def train_ner(nlp, TRAIN_DATA, num_iterations=2):
    """
    Treina o modelo NER com os dados de treinamento fornecidos.

    Args:
    nlp (Language): Modelo spaCy carregado.
    TRAIN_DATA (list): Lista de dados de treinamento.
    num_iterations (int): Número de iterações de treinamento.
    """
    for itn in range(num_iterations):
        random.shuffle(TRAIN_DATA)  # Embaralha os dados de treinamento a cada iteração
        losses = {}  # Dicionário para armazenar as perdas
        # Cria lotes de dados de treinamento usando um gerador de minibatches
        batches = minibatch(TRAIN_DATA, size=compounding(4.0, 32.0, 1.001))
        for batch in batches:
            for text, annotations in batch:
                doc = nlp.make_doc(text)  # Cria um documento spaCy a partir do texto
                example = Example.from_dict(doc, annotations)  # Cria um exemplo de treinamento a partir do documento e das anotações
                # Atualiza o modelo com os exemplos de treinamento
                nlp.update([example], drop=0.5, losses=losses)
        # Registra as perdas a cada iteração
        logging.info(f"Losses at iteration {itn}: {losses}")

# Lê o arquivo CSV usando um gerenciador de contexto
try:
    df = pd.read_csv('../ner.csv')  # Tenta ler o arquivo CSV com os dados de treinamento
except FileNotFoundError:
    logging.error('File ner.csv not found.')  # Registra um erro se o arquivo não for encontrado
    exit()  # Encerra o script

# Prepara os dados de treinamento a partir do DataFrame
TRAIN_DATA = prepare_data(df)

# Desativa outros componentes do pipeline para treinar apenas o NER
with nlp.disable_pipes(*[pipe for pipe in nlp.pipe_names if pipe != 'ner']):
    train_ner(nlp, TRAIN_DATA)  # Treina o modelo NER

# Salva o modelo treinado no disco
model_path = os.path.join('../models', 'ingredient_ner')  # Define o caminho para salvar o modelo
if not os.path.exists(model_path):
    os.makedirs(model_path)  # Cria o diretório se ele não existir
nlp.to_disk(model_path)  # Salva o modelo no disco
logging.info(f'Model saved to {model_path}')  # Registra uma mensagem informativa indicando que o modelo foi salvo