IN_VENV=. .venv/bin/activate

.PHONY: clean release venv

all:
	@echo "This makefile is used for the release process. A sensible all target is not implemented."

clean:
	rm -rf bioblend.egg-info/ build/ dist/
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	make -C docs/ clean

venv:
	# Create and activate a virtual environment
	[ -f .venv/bin/activate ] || python3 -m venv .venv || virtualenv -p python3 .venv
	# Install latest versions of pip and setuptools
	( $(IN_VENV) \
	  && python3 -m pip install --upgrade pip setuptools \
	)
