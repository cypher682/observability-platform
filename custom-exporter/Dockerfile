FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY exporter.py .

EXPOSE 9200

CMD ["uvicorn", "exporter:app", "--host", "0.0.0.0", "--port", "9200"]
