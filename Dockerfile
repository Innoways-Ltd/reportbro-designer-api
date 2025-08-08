FROM python:3.8-slim

ARG NODE_ENV=dev
ENV NODE_ENV=${NODE_ENV}
ENV PORT=80

EXPOSE $PORT

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY ./reportbro_designer_api /app/reportbro_designer_api
COPY ./reportbro-lib /app/reportbro-lib
COPY .env.* /app/
RUN python -m pip install /app/reportbro-lib

# Removed non-root user setup
COPY logging.conf /app/logging.conf

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --timeout=600 --log-config=logging.conf -k uvicorn.workers.UvicornWorker reportbro_designer_api.main:app"]