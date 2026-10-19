FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt

COPY backend ./backend
COPY data ./data

WORKDIR /app/backend
RUN chmod +x entrypoint.sh

ENTRYPOINT ["/app/backend/entrypoint.sh"]

CMD ["gunicorn", "config.wsgi", "-w", "4", "-t", "120", "-b", "0.0.0.0:9000"]
