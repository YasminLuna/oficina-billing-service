FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN mkdir -p /tmp && chmod 1777 /tmp
USER 65532:65532
EXPOSE 8080
CMD ["uvicorn", "app.persistent_api:app", "--host", "0.0.0.0", "--port", "8080"]
