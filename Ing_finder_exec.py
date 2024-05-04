import spacy

# Load the trained model
model_path = 'models/ingredient_ner_2'
nlp = spacy.load(model_path)

# New text to process
text_to_process = ("Combine cabbage, onion, green pepper and sugar."", ""In saucepan, combine 1 tablespoon sugar"
                   ", salt, celery seed, dry mustard, water, vinegar and oil."", ""Bring to a boil;"
                   " pour over vegetables."", ""Cool in refrigerator for 24 hours."", ""Keeps for 3 weeks.")

text_to_process = (text_to_process
                   .replace(', ', ', c. 1 Tbsp oz ')
                   .replace('or ', 'c. 1 Tbsp oz ')
                   .replace('and ', 'c. 1 Tbsp oz ')
                   .replace('in ', 'c. 1 Tbsp oz ')
                   .replace('In ', 'In c. 1 Tbsp oz ')
                   .replace('whole', 'c. 1 Tbsp oz ')
                   .replace('combine', 'c. 1 Tbsp oz ')
                   )

# Process the text
doc = nlp(text_to_process)

# Display the entities
for ent in doc.ents:
    print(f"{ent.text}")