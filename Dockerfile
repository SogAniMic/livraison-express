# syntax=docker/dockerfile:1.7
# Build multi-stage (séance 3) :
#   builder -> dépendances d'exécution dans un venv isolé
#   test    -> dépendances de test, lint et tests exécutés pendant le build
#   prod    -> image minimale : venv + code applicatif, utilisateur non-root
ARG PYTHON_VERSION=3.13

# ---------------------------------------------------------------- builder
FROM python:${PYTHON_VERSION}-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
# Compression : on retire du venv ce qui ne sert pas à l'exécution
# (suites de tests des bibliothèques, bytecode, pip/setuptools).
RUN pip install -r requirements.txt \
 && find /opt/venv -depth -type d \( -name tests -o -name __pycache__ \) -exec rm -rf {} + \
 && pip uninstall -y -q pip setuptools 2>/dev/null || true

# ---------------------------------------------------------------- test
FROM python:${PYTHON_VERSION}-slim AS test
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PATH="/opt/venv/bin:$PATH"
RUN python -m venv /opt/venv
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt
COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
ENV PYTHONPATH=/app/src
RUN ruff check src tests && pytest -q -m "not integration"
CMD ["pytest", "-q"]

# ---------------------------------------------------------------- prod
FROM python:${PYTHON_VERSION}-slim AS prod
ARG VERSION=dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="livraison-express" \
      org.opencontainers.image.description="API de prédiction d'éligibilité à la livraison express" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app/src \
    ENVIRONMENT=prod \
    MODEL_PATH=/app/artifacts/express_delivery_model.joblib

# Rootless : un attaquant qui prend la main sur le conteneur n'est pas root.
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
 && mkdir -p /app/artifacts && chown app:app /app/artifacts

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
# Uniquement le code : ni tests, ni .env, ni requirements, ni .git, ni documentation.
COPY --chown=root:root src/livraison_express ./src/livraison_express

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status != 200)"

ENTRYPOINT ["python", "-m", "livraison_express"]
CMD ["serve", "--host", "0.0.0.0", "--port", "8000"]
