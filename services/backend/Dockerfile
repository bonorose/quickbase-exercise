FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY src/ ./src/

EXPOSE 5000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "5000"]
