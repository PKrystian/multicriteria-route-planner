FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY src ./src
RUN pip install --no-cache-dir -e .

COPY config ./config
COPY scripts ./scripts
COPY frontend ./frontend
COPY docker ./docker

EXPOSE 8000

ENTRYPOINT ["sh", "docker/entrypoint.sh"]
