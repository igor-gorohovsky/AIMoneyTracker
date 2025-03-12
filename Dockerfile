FROM python:3.12-slim

RUN apt update && apt install -y build-essential python3-dev libpq-dev

COPY ./pyproject.toml /tmp/pyproject.toml
COPY ./poetry.lock /tmp/poetry.lock

WORKDIR /tmp
RUN pip install poetry==2.1.1
RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

COPY ./src /src

WORKDIR /src

CMD ["python3", "main.py"]
