.PHONY: init-dev run shell test destroy migrate mysql sass-watch sass-compile build

init-dev:
	cp settings.example.py settings.py
	cp celeryconfig.example.py celeryconfig.py
	mkdir -p mounts/mysql mounts/logs mounts/fakes3 mounts/uploaded

sass-compile:
	sass --update --stop-on-error --style compressed static/sass:static/css

sass-watch:
	sass --watch --stop-on-error --style compressed static/sass:static/css

run: sass-compile
	docker-compose up -d

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
