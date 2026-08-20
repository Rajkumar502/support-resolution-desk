.PHONY: install run test eval ui benchmark evaluate docker-build docker-up docker-down docker-logs clean

# Automatically detect if venv exists; otherwise fallback to global python3 (ideal for CI/CD)
ifeq ($(wildcard venv/bin/python3),)
    PYTHON = python3
else
    PYTHON = ./venv/bin/python3
endif

install:
	python3 -m venv venv
	./venv/bin/python3 -m pip install --upgrade pip
	./venv/bin/python3 -m pip install -r requirements.txt

run:
	$(PYTHON) -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(PYTHON) -m pytest tests/test_classifier.py tests/test_graph.py tests/test_graph_governance.py tests/test_api.py -v -p no:phoenix

eval:
	$(PYTHON) tests/evaluate.py

ui:
	$(PYTHON) -m streamlit run app_ui.py

benchmark:
	$(PYTHON) benchmark.py

evaluate:
	$(PYTHON) evaluate_rag.py

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete