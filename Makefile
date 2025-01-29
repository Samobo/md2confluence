.EXPORT_ALL_VARIABLES:
MD2CONFLUENCE_VERSION = $(shell git describe --tags --always --dirty)

.PHONY: build publish release

build:
	docker buildx bake --load

publish:
	docker buildx bake --set *.platform=linux/amd64 --push

release:
	docker buildx bake release --set *.platform=linux/amd64 --push