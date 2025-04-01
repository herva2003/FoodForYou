FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=ingredient_finder_IA/ing_finder2.py
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["python3", "ingredient_finder_IA/ing_finder2.py"]