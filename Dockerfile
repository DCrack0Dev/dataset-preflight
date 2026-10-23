FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY examples ./examples

RUN python -m pip install --no-cache-dir .

ENV PYTHONPATH=/app/src
EXPOSE 8080

USER nobody
CMD ["python", "-m", "dataset_preflight", "serve", "--host", "0.0.0.0", "--port", "8080"]
