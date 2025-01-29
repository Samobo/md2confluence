.EXPORT_ALL_VARIABLES:
MD2CONFLUENCE_VERSION = 1.0.0

.PHONY: build publish

build:
	docker buildx bake --load

publish:
	docker buildx bake --set *.platform=linux/arm64 --set *.platform=linux/amd64 --push