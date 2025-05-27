# This Makefile is just here to allow auto-completion in the terminal.

actions = \
	build \
	check \
	check-api \
	check-docs \
	check-quality \
	check-types \
	clean \
	clean_cache \
	coverage \
	docker-build \
	docker-start \
	docker-stop \
	docker-exec-check \
	docker-exec-check-api \
	docker-exec-check-docs \
	docker-exec-check-quality \
	docker-exec-check-types \
	docker-exec-coverage \
	docker-exec-docs \
	docker-exec-test \
	docker-exec-tox \
	docs \
	docs-deploy \
	format \
	release \
	setup \
	setup-dev \
	test\
	tox


.PHONY: $(actions)
$(actions):
	@uv run duty "$@"


.PHONY: help
help:
	@uv run duty --list

.DEFAULT_GOAL := help
