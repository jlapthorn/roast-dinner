FROM registry.access.redhat.com/ubi9/python-312:latest

ENV PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    PORT=8080 \
    HOME=/opt/app-root/src

WORKDIR /opt/app-root/src

COPY --chown=1001:0 requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=1001:0 app.py ./
COPY --chown=1001:0 roast_dinner ./roast_dinner
COPY --chown=1001:0 templates ./templates
COPY --chown=1001:0 static ./static

USER 1001

EXPOSE 8080

# Single worker: SQLite does not handle concurrent writers well.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "60", "app:app"]
