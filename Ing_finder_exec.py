import spacy

# Load the trained model
model_path = 'models/ingredient_ner_2'
nlp = spacy.load(model_path)

# New text to process
text_to_process = ("cabbage, onion, green pepper and sugar, sugar, salt, celery seed, mustard, water, vinegar and oil.")

text_to_process = "1 Tbsp " + text_to_process

text_to_process = (text_to_process
                   .replace(',', ', 1 Tbsp ')
                   .replace('and', ' 1 Tbsp ')
                   )

# Process the text
doc = nlp(text_to_process)

# Display the entities
for ent in doc.ents:
    print(f"{ent.text}")
