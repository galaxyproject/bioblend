IN_VENV=. .venv/bin/activate

.PHONY: release venv

all:
	@echo "This makefile is used for the release process. A sensible all target is not implemented."

venv:
	# Create and activate a virtual environment
	[ -f .venv/bin/activate ] || virtualenv .venv
	( $(IN_VENV); \
	  # Install latest versions of pip and setuptools \
	  pip install --upgrade pip setuptools; \
	  # Install latest versions of other needed packages in the virtualenv \
	  pip install --upgrade twine wheel; \
	)

release: venv
	# Cleanup
	rm -rf bioblend.egg-info/ build/ dist/
	make -C docs/ clean
	( $(IN_VENV); \
	  # Create files in dist/ \
	  python setup.py sdist; \
	  python setup.py bdist_wheel; \
	  twine upload dist/*; \
	  deactivate; \
	)
