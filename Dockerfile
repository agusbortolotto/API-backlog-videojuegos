FROM python:3.13.16-slim-bookworm AS builder

WORKDIR /build

RUN python -m venv /opt/venv

COPY requirements.txt .

RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.13.16-slim-bookworm AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --no-create-home app

COPY --from=builder /opt/venv /opt/venv
COPY app/ ./app/
COPY database/schema.sql ./database/schema.sql

RUN chown app:app /app/database

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]