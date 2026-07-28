FROM python:3.9-slim
WORKDIR /service
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/shared/observability.py /service/observability.py
COPY services/gateway/ .
COPY app/templates /service/templates
COPY app/static /service/static
EXPOSE 5000
CMD ["python", "app.py"]
