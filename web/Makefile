docker:
	docker pull node:20.19.4
install:
	docker run --rm -v $(PWD):/app/ -w /app/ node:20.19.4 npm install
dev:
	docker run --rm -v $(PWD):/app/ -w /app/ -p 127.0.0.1:8081:8081/tcp --name image-tools node:20.19.4 npm run dev
env:
	docker run -it --rm -v $(PWD):/app/ -w /app/ node:20.19.4 /bin/sh
preview:
	docker run --rm -v $(PWD)/dist:/local/web:ro -v $(PWD)/nginx.conf:/etc/nginx/conf.d/default.conf:ro -p 127.0.0.1:8889:80 nginx:1.22-alpine
build:
	docker run --rm -v $(PWD):/app/ -w /app/ --name image-tools-builder node:20.19.4 npm run build
	@echo "Creating zip package..."
	@DATE=$$(date +%Y%m%d-%H%M); \
	cd dist && zip -r ../image-tools-$$DATE.zip . && cd .. && \
	echo "Build completed! Package created: image-tools-$$DATE.zip"
