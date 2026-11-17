FROM python:3.12-slim

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py repository.py migrate.py ./
COPY migrations ./migrations

RUN chown -R app:app /app

USER app

ENV PORT=8000
EXPOSE 8000

CMD ["python", "app.py"]
