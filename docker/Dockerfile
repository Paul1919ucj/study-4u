FROM python:3.12

WORKDIR /app

COPY requirements.txt .


RUN pip install --no-cache-dir -r requirements.txt

COPY BACKEND/ .

COPY tests/ ./tests/

EXPOSE 5000

CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "app:app"]