.PHONY: init-dev run shell test destroy migrate mysql

init-dev:
	cp settings.example.py settings.py
	cp celeryconfig.example.py celeryconfig.py
	mkdir -p mounts/mysql mounts/logs mounts/fakes3 mounts/uploaded

run:
	docker-compose up -d

stop:
	docker-compose down

build:
	docker build -t mltshp/mltshp-web:latest .

shell:
	docker exec -it mltshp_mltshp_1 bash

test:
	docker exec -it mltshp_mltshp_1 su ubuntu -c "cd /srv/mltshp.com/mltshp; python test.py $(TEST)"

destroy:
	docker-compose down
	rm -rf mounts

migrate:
	docker exec -it mltshp_mltshp_1 su ubuntu -c "cd /srv/mltshp.com/mltshp; python migrate.py"

mysql:
	docker exec -it mltshp_mltshp_1 su ubuntu -c "cd /srv/mltshp.com/mltshp; mysql -u root --host mysql mltshp"
