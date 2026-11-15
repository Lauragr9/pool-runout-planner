FROM python:3.12-slim

RUN groupadd --system app && useradd --system --gid app --no-create-home app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py engine.py geometry.py results_repository.py client.py ./

RUN mkdir -p /app/data && chown -R app:app /app

USER app

ENV PORT=8001
ENV DATA_DIR=/app/data
EXPOSE 8001

CMD ["python", "app.py"]
