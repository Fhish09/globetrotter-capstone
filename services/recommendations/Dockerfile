FROM python:3.9-slim
WORKDIR /service
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/shared/http_client.py /service/http_client.py
COPY services/recommendations/ .
EXPOSE 5003
CMD ["python", "app.py"]
