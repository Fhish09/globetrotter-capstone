FROM python:3.9-slim
WORKDIR /service
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/itineraries/ .
EXPOSE 5004
CMD ["python", "app.py"]
