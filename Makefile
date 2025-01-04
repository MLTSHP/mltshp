.PHONY: init start stop custom-build build shell test destroy migrate mysql

init:
	cp settings.example.py settings.py
	cp celeryconfig.example.py celeryconfig.py
	mkdir -p mounts/mysql mounts/logs mounts/fakes3 mounts/uploaded

start:
	docker compose up -d

stop:
	docker compose down

custom-build:
	@read -p "build tag (default is 'latest'): " build_tag; \
	docker build -t mltshp/mltshp-web:$${build_tag:-latest}

build:
	docker build -t mltshp/mltshp-web:latest .

shell:
	docker compose exec mltshp bash

test:
	docker compose exec mltshp su ubuntu -c "cd /srv/mltshp.com/mltshp; python3 -u test.py $(TEST)"

destroy:
	docker compose down && rm -rf mounts

migrate:
	docker compose exec mltshp su ubuntu -c "cd /srv/mltshp.com/mltshp; python3 migrate.py"

mysql:
	docker compose exec mltshp su ubuntu -c "cd /srv/mltshp.com/mltshp; mysql -u root --host mysql mltshp"
