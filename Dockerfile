# Single container serving both the API and the pre-built SPA on one
# origin (api/app.py mounts web/dist) — no separate frontend host, no CORS.
# Local open-weights embeddings (bge-small/bge-large) are why this can't be
# a Vercel serverless function; a persistent Python process is required
# regardless, so the frontend rides along in the same image.

FROM node:22-slim AS frontend
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.13-slim AS runtime
WORKDIR /app

# build-essential: requirements.txt is the one flat file for the whole
# project (runtime + eval + dev), and ir_measures' pytrec_eval_terrier
# needs a C compiler to build. Simpler and less drift-prone than
# maintaining a hand-split runtime-only requirements file.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch: the default PyPI wheel bundles CUDA libraries this
# container never uses (GPU inference isn't part of this architecture),
# inflating the image by ~2GB for nothing.
COPY requirements.txt .
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.13.0 \
    && pip install --no-cache-dir -r requirements.txt

# api/ is the served product; pipeline/ is included only because
# api/extract_idea.py reuses pipeline.extract_facets's MODEL/SYSTEM_PROMPT
# so query-time and corpus extraction stay in sync — eval/ (the harness)
# and tests/ are dev-only and never imported by the running app.
COPY api/ api/
COPY pipeline/ pipeline/
COPY data/ data/
COPY --from=frontend /web/dist web/dist

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
