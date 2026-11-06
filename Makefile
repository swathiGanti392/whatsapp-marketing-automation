# Allowlist the Lambda artifact: private .env and repository history are excluded.
build-PropertyBot:
	python3 -m pip install -r requirements.txt --target "$(ARTIFACTS_DIR)" --platform manylinux2014_x86_64 --python-version 3.12 --implementation cp --only-binary=:all: --upgrade
	cp bot.py listings.py conversation.py lead_analytics.py lambda_handler.py "$(ARTIFACTS_DIR)/"
	mkdir -p "$(ARTIFACTS_DIR)/data"
	cp data/listings.json "$(ARTIFACTS_DIR)/data/"

.PHONY: test
test:
	python3 -m unittest discover -p 'test_*.py' -v
