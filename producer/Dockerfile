FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DOMAIN=infra
ENV EVENTS_PER_SECOND=5.0

CMD ["python", "-m", "producer.main"]
