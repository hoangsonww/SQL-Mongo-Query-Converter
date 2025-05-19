# Makefile for sql_mongo_converter Docker image

# ← our GHCR namespace & repo
IMAGE    ?= ghcr.io/hoangsonww/sql-mongo-converter
REGISTRY ?= ghcr.io
USER     ?= hoangsonww

# ← parse version="x.y.z" from setup.py (portable sed)
VERSION := $(shell sed -nE "s/^[[:space:]]*version[[:space:]]*=[[:space:]]*[\"']([0-9]+\.[0-9]+\.[0-9]+)[\"'].*$$/\1/p" setup.py)

.PHONY: all login build push clean version

all: login build push

version:
	@echo $(VERSION)

login:
	@# ensure we have a token
	@test -n "$(GITHUB_TOKEN)" || (echo "Error: GITHUB_TOKEN not set" && exit 1)
	@echo "🔑 Logging into $(REGISTRY) as $(USER)"
	@echo "$(GITHUB_TOKEN)" | docker login $(REGISTRY) -u $(USER) --password-stdin

build:
	@echo "🔨 Building Docker image $(IMAGE):$(VERSION)"
	@docker build --pull -t $(IMAGE):$(VERSION) -t $(IMAGE):latest .

push:
	@echo "🚀 Pushing $(IMAGE):$(VERSION) and $(IMAGE):latest"
	@docker push $(IMAGE):$(VERSION)
	@docker push $(IMAGE):latest

clean:
	@echo "🗑 Removing images"
	-@docker rmi $(IMAGE):$(VERSION) $(IMAGE):latest || true
