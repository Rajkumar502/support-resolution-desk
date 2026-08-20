.PHONY: virt-install run test eval clean

install:
	python3 -m venv venv
	./venv/bin/python3 -m pip install --upgrade pip
	./venv/bin/python3 -m pip install -r requirements.txt

run:
	./venv/bin/uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000


test:
	./venv/bin/python3 -m pytest tests/test_classifier.py tests/test_graph.py tests/test_graph_governance.py tests/test_api.py -v -p no:phoenix

eval:
	./venv/bin/python3 tests/evaluate.py

ui:
	./venv/bin/streamlit run app_ui.py

benchmark:
	./venv/bin/python3 benchmark.py

evaluate:
	./venv/bin/python3 evaluate_rag.py

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