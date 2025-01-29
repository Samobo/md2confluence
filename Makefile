.EXPORT_ALL_VARIABLES:
MD2CONFLUENCE_VERSION = 1.0.1

.PHONY: build publish

build:
	docker buildx bake --load

publish:
	docker buildx bake --set *.platform=linux/amd64 --push

release:
	docker buildx bake release --set *.platform=linux/amd64 --push