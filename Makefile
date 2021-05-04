.DEFAULT_GOAL := help
SOURCES := src/main.py src/data.py src/ui.py src/utils.py src/miner.py src/proto.py
TESTS := src/test_data.py src/test_proto.py

# Porcelain
# ###############
.PHONY: env-up env-down env-recreate container run run-watch build lint test

run: setup ## run the app
	APP_COOL_MINER=y APP_PORT=1234 python src/main.py

run-watch: setup ## run the app in dev mode, hot reloading
	ls $(SOURCES) Makefile | entr -cr make run

env-up: ## set up dev environment
	@echo "Not implemented"; false

env-down: ## tear down dev environment
	@echo "Not implemented"; false

env-recreate: env-down env-up ## deconstruct current env and create another one

build: setup ## create artifact
	@echo "Not implemented"; false

lint: setup ## run static analysis
	@echo "Not implemented"; false

test: setup ## run all tests
	python -m pytest

test-watch: setup ## run tests in watch mode
	ls $(SOURCES) $(TESTS) | entr -c make test

container: build ## create container
	#docker build -t lmap .
	@echo "Not implemented"; false

# Plumbing
# ###############
.PHONY: setup gitclean gitclean-with-libs

setup:

gitclean:
	@# will remove everything in .gitignore expect for blocks starting with dep* or lib* comment
	diff --new-line-format="" --unchanged-line-format="" <(grep -v '^#' .gitignore | grep '\S' | sort) <(awk '/^# *(dep|lib)/,/^$/' testowy | head -n -1 | tail -n +2 | sort) | xargs rm -rf

gitclean-with-libs:
	diff --new-line-format="" --unchanged-line-format="" <(grep -v '^#' .gitignore | grep '\S' | sort) | xargs rm -rf

# Helpers
# ###############
.PHONY:

# Utilities
# ###############
.PHONY: help todo clean really_clean init
init: ## one time setup
	direnv allow .

todo: ## list all TODOs in the project
	git grep -I --line-number TODO | grep -v 'list all TODOs in the project' | grep TODO

clean: gitclean ## remove artifacts

really_clean: gitclean-with-libs clean ## remove EVERYTHING

help: ## print this message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
