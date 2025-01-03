ifneq (,$(wildcard ./.env))
    include .env
    export
endif

install: install-rye install-pre-commit

install-rye:
	curl -sSf https://rye.astral.sh/get | bash

install-pre-commit:
	rye sync
	source .venv/bin/activate
	pre-commit install

local-run:
	gunicorn -w 1 -b 0.0.0.0:8000 "pms:create_app()"

linux-local-run:
	rye run gunicorn -w 4 -b 0.0.0.0:8000 "pms:create_app()"

docker-build:
	docker build -t pms -f ./docker/Dockerfile .

docker-run:
	docker compose up -d

db-init:
	docker compose up -d db

docker-down:
	docker compose down

docker-clean:
	docker compose down --volumes --remove-orphans

restart:
	docker compose down
	docker compose down --volumes --remove-orphans
	docker compose up -d db
	gunicorn -w 4 -b 0.0.0.0:8000 "pms:create_app()"
