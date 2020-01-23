IN_VENV=. .venv/bin/activate

.PHONY: clean release venv

all:
	@echo "This makefile is used for the release process. A sensible all target is not implemented."

clean:
	rm -rf bioblend.egg-info/ build/ dist/
	make -C docs/ clean

venv:
	# Create and activate a virtual environment
	[ -f .venv/bin/activate ] || virtualenv -p python3 .venv
	( $(IN_VENV) && \
	  # Install latest versions of pip and setuptools \
	  python3 -m pip install --upgrade pip setuptools && \
	  # Install latest versions of other needed packages in the virtualenv \
	  python3 -m pip install --upgrade twine wheel \
	)

release: clean venv
	( $(IN_VENV) && \
	  # Create files in dist/ \
	  python3 setup.py sdist bdist_wheel && \
	  twine check dist/* && \
	  twine upload dist/*
	)
