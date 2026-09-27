.PHONY: setup test-mock test-live run lint clean docker-build docker-run

setup:
	python -m venv venv
	./venv/bin/pip install --upgrade pip
	./venv/bin/pip install -r requirements.txt
	cp -n .env.example .env || true

test-mock:
	python test_pipeline.py --mode mock

test-live:
	python test_pipeline.py --mode live

run:
	streamlit run app.py

lint:
	pip install ruff bandit
	ruff check .
	bandit -r services/

docker-build:
	docker build -t pocketsmart-ai:v1.0.0 .

docker-run:
	docker run -p 8080:8080 -e PORT=8080 --env-file .env pocketsmart-ai:v1.0.0

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
