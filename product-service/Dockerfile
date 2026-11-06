FROM python:3.9-slim as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt --prefix=/install

#production stage

FROM python:3.9-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

RUN useradd -m appuser && chown -R appuser:appuser /app

USER appuser

EXPOSE 8001

CMD ["gunicorn", "--bind", "0.0.0.0:8001", "wsgi:app"]