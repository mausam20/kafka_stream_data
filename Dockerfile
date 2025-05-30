FROM python:3.9.1

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

ENV environment=production

CMD ["python", "bquery_ingest_data.py"]
