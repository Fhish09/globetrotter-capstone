FROM python:3.9-slim
WORKDIR /service
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/shared/http_client.py /service/http_client.py
COPY services/shared/circuit_breaker.py /service/circuit_breaker.py
COPY services/shared/cache.py /service/cache.py
COPY services/shared/observability.py /service/observability.py
COPY services/recommendations/ .
EXPOSE 5003
CMD ["python", "app.py"]
