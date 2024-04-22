import spacy

# Load the trained model
model_path = 'models/ingredient_ner'
nlp = spacy.load(model_path)

# New text to process
text_to_process = ("1 c. firmly packed brown sugar, 1/2 c. evaporated milk, 1/2 tsp. vanilla, 1/2 c. broken nuts (pecans), "
                   "2 Tbsp. butter or margarine, 3 1/2 c. bite size shredded rice biscuits")

# Process the text
doc = nlp(text_to_process)

# Display the entities
for ent in doc.ents:
    print(f"Entity: {ent.text}, Label: {ent.label_}")