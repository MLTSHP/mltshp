.PHONY: init-dev run shell test destroy migrate mysql

init-dev:
	cp settings.example.py settings.py
	cp celeryconfig.example.py celeryconfig.py
	mkdir -p mounts/mysql mounts/logs mounts/fakes3 mounts/uploaded

run:
	docker-compose --env-file .env up -d

stop:
	docker-compose --env-file .env down

build:
	docker build -t mltshp/mltshp-web:latest .

shell:
	docker-compose --env-file .env exec mltshp bash

test:
	docker-compose --env-file .env exec mltshp su ubuntu -c "cd /srv/mltshp.com/mltshp; python test.py $(TEST)"

destroy:
	docker-compose down
	rm -rf mounts

migrate:
	docker-compose --env-file .env exec mltshp su ubuntu -c "cd /srv/mltshp.com/mltshp; python migrate.py"

mysql:
	docker-compose --env-file .env exec mltshp su ubuntu -c "cd /srv/mltshp.com/mltshp; mysql -u root --host mysql mltshp"
