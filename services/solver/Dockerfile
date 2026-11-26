FROM python:3.12-slim

# Picks up Debian security patches newer than this base image tag was built
# with (found by Trivy scanning the built image, not guessed).
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py engine.py geometry.py results_repository.py client.py migrate.py ./
COPY migrations ./migrations

RUN chown -R app:app /app

USER app

ENV PORT=8001
EXPOSE 8001

CMD ["python", "app.py"]
