import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import random
import pandas as pd
import ast
import logging
import os


def setup_logging():
    logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    setup_logging()

# Load a pre-existing spaCy model
nlp = spacy.load('en_core_web_sm')

# Check if 'INGREDIENT' is a recognized entity type in the model
if 'INGREDIENT' not in nlp.pipe_labels['ner']:
    ner = nlp.get_pipe('ner')
    ner.add_label('INGREDIENT')


def remove_overlapping_entities(entities):
    entities = sorted(entities, key=lambda x: x[0])
    non_overlapping_entities = []
    last_end_index = -1
    for entity in entities:
        if entity[0] > last_end_index:
            non_overlapping_entities.append(entity)
            last_end_index = entity[1]
    return non_overlapping_entities


def prepare_data(df):
    TRAIN_DATA = []
    for index, row in df.iterrows():
        entities = []
        ingredients_text = row['ingredients'].lower()
        for ing in ast.literal_eval(row['NER']):
            ing_lower = ing.lower()
            start_index = ingredients_text.find(ing_lower)
            while start_index != -1:
                end_index = start_index + len(ing_lower)
                entities.append((start_index, end_index, 'INGREDIENT'))
                start_index = ingredients_text.find(ing_lower, start_index + 1)
        entities = remove_overlapping_entities(entities)
        TRAIN_DATA.append((row['ingredients'], {'entities': entities}))

    # Filter out misaligned entities
    TRAIN_DATA = [data for data in TRAIN_DATA if not misaligned_entities(data, nlp)]
    return TRAIN_DATA


def misaligned_entities(data, nlp):
    text, annotations = data
    doc = nlp.make_doc(text)
    tags = spacy.training.offsets_to_biluo_tags(doc, annotations['entities'])
    if '-' in tags:
        logging.error(f"Misaligned entity in text: {text}, entities: {annotations['entities']}")
        return True
    return False


def train_ner(nlp, TRAIN_DATA, num_iterations=2):
    for itn in range(num_iterations):
        random.shuffle(TRAIN_DATA)
        losses = {}
        batches = minibatch(TRAIN_DATA, size=compounding(4., 32., 1.001))
        for batch in batches:
            for text, annotations in batch:
                doc = nlp.make_doc(text)
                example = Example.from_dict(doc, annotations)
                nlp.update([example], drop=0.5, losses=losses)
        logging.info(f"Losses at iteration {itn}: {losses}")


# Read the CSV file using a context manager
try:
    df = pd.read_csv('ner.csv')
except FileNotFoundError:
    logging.error('File ner.csv not found.')
    exit()

TRAIN_DATA = prepare_data(df)


# Disable other pipes to only train NER
with nlp.disable_pipes(*[pipe for pipe in nlp.pipe_names if pipe != 'ner']):
    train_ner(nlp, TRAIN_DATA)

# Save the model to disk
model_path = os.path.join('models', 'ingredient_ner')
if not os.path.exists(model_path):
    os.makedirs(model_path)
nlp.to_disk(model_path)
logging.info(f'Model saved to {model_path}')













