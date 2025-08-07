FROM python:3.8-slim

ARG NODE_ENV=dev
ENV NODE_ENV=${NODE_ENV}

EXPOSE 80

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

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--timeout=600", "--log-config=logging.conf", "-k", "uvicorn.workers.UvicornWorker", "reportbro_designer_api.main:app"]