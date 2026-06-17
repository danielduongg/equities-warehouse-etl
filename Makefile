.PHONY: install run analytics test docker
install:
	pip install -r requirements.txt
run:
	python run_pipeline.py --full-refresh
analytics:
	python analytics.py
test:
	pytest -q
docker:
	docker build -t equities-warehouse-etl . && docker run --rm equities-warehouse-etl
