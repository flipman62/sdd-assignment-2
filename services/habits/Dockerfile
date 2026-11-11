# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PORT=8000
WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY migrations/ ./migrations/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "app.py"]
