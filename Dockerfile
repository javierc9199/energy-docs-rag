FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    EMBEDDING_BACKEND=tfidf \
    LLM_BACKEND=extractive

WORKDIR /app

COPY requirements.txt requirements-optional.txt ./
RUN pip install --no-cache-dir -r requirements.txt langchain-google-genai

COPY pyproject.toml ./
COPY src/ ./src/
COPY config/ ./config/
COPY corpus/ ./corpus/
COPY eval/ ./eval/
RUN pip install --no-cache-dir -e .

# Build an offline index of the synthetic corpus at image build time, so the container
# answers questions out of the box. No credentials are available (or wanted) at build
# time; for the Vertex AI stack, pass .env and gcloud credentials at run time and
# re-run `energy-rag ingest`. Private documents are never baked into the image.
RUN EMBEDDING_BACKEND=tfidf energy-rag ingest --collection plant-docs

EXPOSE 8000
CMD ["uvicorn", "energy_rag.api:app", "--host", "0.0.0.0", "--port", "8000"]
