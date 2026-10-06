FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Environment configurations driven by Cloud Run
ENV PORT=8080
ENV LOG_LEVEL=INFO

# Uvicorn serves FastAPI
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
