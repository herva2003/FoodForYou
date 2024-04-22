import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import random
import pandas as pd
import ast
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)

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
        for ing in ast.literal_eval(row['NER']):
            # Split the ingredients string into individual ingredients
            ingredients = row['ingredients'].replace('",', ', ').split(', ')
            for ingredient in ingredients:
                # Check if the current ingredient contains the target ingredient
                if ing.lower() in ingredient.lower():
                    # Calculate the start and end index of the ingredient in the current ingredient
                    start_index = ingredient.lower().find(ing.lower())
                    end_index = start_index + len(ing)
                    # Adjust the start and end index to the ingredients string
                    start_index += row['ingredients'].lower().find(ingredient.lower())
                    end_index += row['ingredients'].lower().find(ingredient.lower())
                    entities.append((start_index, end_index, 'INGREDIENT'))
        if entities:
            # Remove overlapping entities
            entities = remove_overlapping_entities(entities)
            TRAIN_DATA.append((row['ingredients'], {'entities': entities}))

        # Check alignment of entities
        for text, annotations in TRAIN_DATA:
            doc = nlp.make_doc(text)
            tags = spacy.training.offsets_to_biluo_tags(doc, annotations['entities'])
            if '-' in tags:  # Misaligned entity found
                logging.error(f"Misaligned entity in text: {text}, entities: {annotations['entities']}")
                TRAIN_DATA.remove((text, annotations))  # Remove misaligned data from training data
    return TRAIN_DATA


def train_ner(nlp, TRAIN_DATA):
    for itn in range(10):  # Number of training iterations
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
    with open('ner.csv', 'r') as file:
        df = pd.read_csv(file)
except FileNotFoundError:
    logging.error('File ner.csv not found.')
    exit()

TRAIN_DATA = prepare_data(df)
if TRAIN_DATA is None:  # If misaligned entity found, stop the script
    exit()

# Disable other pipes to only train NER
with nlp.disable_pipes(*[pipe for pipe in nlp.pipe_names if pipe != 'ner']):
    train_ner(nlp, TRAIN_DATA)

# Save the model to disk
model_path = os.path.join('models', 'ingredient_ner')
if not os.path.exists(model_path):
    os.makedirs(model_path)
nlp.to_disk(model_path)
logging.info(f'Model saved to {model_path}')
