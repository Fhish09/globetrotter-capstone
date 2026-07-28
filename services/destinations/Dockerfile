FROM python:3.9-slim
WORKDIR /service
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/destinations/ .
COPY data/destinations.json /service/data/destinations.json
EXPOSE 5002
CMD ["python", "app.py"]
