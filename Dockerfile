FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY app ./app

EXPOSE 8000
VOLUME /data

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]