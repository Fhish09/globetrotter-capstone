FROM python:3.9-slim
WORKDIR /service
COPY services/shared/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/auth/ .
EXPOSE 5001
CMD ["python", "app.py"]
