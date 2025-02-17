.PHONY: init start stop custom-build build shell test destroy migrate mysql straw

init:
	cp web/settings.example.py web/settings.py
	cp web/celeryconfig.example.py web/celeryconfig.py
	mkdir -p mounts/mysql mounts/logs mounts/fakes3 mounts/uploaded \
		mounts/tmpuploads/0 mounts/tmpuploads/1 mounts/tmpuploads/2 \
		mounts/tmpuploads/3 mounts/tmpuploads/4 mounts/tmpuploads/5 \
		mounts/tmpuploads/6 mounts/tmpuploads/7 mounts/tmpuploads/8 \
		mounts/tmpuploads/9

start:
	docker compose -f setup/web/docker-compose.dev.yml --project-directory=. up -d

stop:
	docker compose -f setup/web/docker-compose.dev.yml --project-directory=. down

custom-build:
	@read -p "build tag (default is 'latest'): " build_tag; \
	docker build -f setup/web/Dockerfile -t mltshp/mltshp-web:$${build_tag:-latest}

build:
	docker build -f setup/web/Dockerfile -t mltshp/mltshp-web:latest .

shell:
	docker compose -f setup/web/docker-compose.dev.yml --project-directory=. exec web ash

test:
	docker compose -f setup/test/docker-compose.yml --project-directory=. exec web su mltshp -c "python3 -u test/test.py $(TEST)"

destroy:
	docker compose -f setup/web/docker-compose.dev.yml --project-directory=. down && rm -rf mounts

migrate:
	docker compose -f setup/web/docker-compose.dev.yml --project-directory=. exec web su mltshp -c "cd /srv/mltshp.com/mltshp; python3 migrate.py"

mysql:
	docker compose -f setup/web/docker-compose.dev.yml --project-directory=. exec web su mltshp -c "cd /srv/mltshp.com/mltshp; mysql -u root --host mysql mltshp"

web/static/straw/compact.js: web/static/straw/source.js
	closure-compiler --js web/static/straw/source.js --js_output_file web/static/straw/compact.js || echo "closure-compiler not found"

