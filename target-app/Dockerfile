FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
