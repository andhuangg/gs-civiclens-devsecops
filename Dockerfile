FROM python:3.14.10-alpine3.24 AS builder

WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y pip

FROM python:3.14.10-alpine3.24

ARG APP_VERSION=dev
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}

LABEL org.opencontainers.image.title="civiclens-lite" \
      org.opencontainers.image.source="https://github.com/andhuangg/gs-civiclens-devsecops" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.revision="${APP_VERSION}"

RUN apk upgrade --no-cache \
    && addgroup -S app && adduser -S -G app -H -s /sbin/nologin app \
    && pip uninstall -y pip

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app ./app

USER app
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
