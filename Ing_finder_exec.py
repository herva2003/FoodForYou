import spacy

# Load the trained model
model_path = 'models/ingredient_ner'
nlp = spacy.load(model_path)

# New text to process
text_to_process = ("brown sugar, milk, vanilla, nuts (pecans), "
                   "butter, rice biscuits")

# Process the text
doc = nlp(text_to_process)

# Display the entities
for ent in doc.ents:
    print(f"Entity: {ent.text}, Label: {ent.label_}")