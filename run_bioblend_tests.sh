#!/bin/sh
set -e

show_help () {
  echo "Usage:  $0 -g GALAXY_DIR [-p PORT] [-e TOX_ENV] [-t BIOBLEND_TESTS] [-r GALAXY_REV] [-c]

  Run tests for BioBlend. Useful for Continuous Integration testing.
  *Please note* that this script overwrites the main.pid file and appends to the
  main.log file inside the specified Galaxy directory (-g).

Options:
  -g GALAXY_DIR
      Path of the local Galaxy git repository.
  -p PORT
      Port to use for the Galaxy server. Defaults to 8080.
  -e TOX_ENV
      Work against specified tox environments. Defaults to py35.
  -t BIOBLEND_TESTS
      Subset of tests to run, e.g.
      'tests/TestGalaxyObjects.py::TestHistory::test_create_delete' . Defaults
      to all tests.
  -r GALAXY_REV
      Branch or commit of the local Galaxy git repository to checkout.
  -c
      Force removal of the temporary directory created for Galaxy, even if some
      test failed."
}

get_abs_dirname () {
  # $1 : relative dirname
  cd "$1" && pwd
}

e_val=py35
GALAXY_PORT=8080
while getopts 'hcg:e:p:t:r:' option
do
  case $option in
    h) show_help
       exit;;
    c) c_val=1;;
    g) g_val=$(get_abs_dirname "$OPTARG");;
    e) e_val=$OPTARG;;
    p) GALAXY_PORT=$OPTARG;;
    t) t_val=$OPTARG;;
    r) r_val=$OPTARG;;
  esac
done

if [ -z "$g_val" ]; then
  echo "Error: missing -g value."
  show_help
  exit 1
fi

# Install BioBlend
BIOBLEND_DIR=$(get_abs_dirname "$(dirname "$0")")
cd "${BIOBLEND_DIR}"
if [ ! -d .venv ]; then
  virtualenv -p python3 .venv
fi
. .venv/bin/activate
python3 setup.py install
python3 -m pip install --upgrade "tox>=1.8.0"

# Setup Galaxy
cd "${g_val}"
if [ -n "${r_val}" ]; then
    # Update repository (may change the sample files or the list of eggs)
    git fetch
    git checkout "${r_val}"
    if git show-ref -q --verify "refs/heads/${r_val}" 2>/dev/null; then
        # ${r_val} is a branch
        export GALAXY_VERSION=${r_val}
        git pull --ff-only
    fi
else
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    case $BRANCH in
        dev | release_*)
            export GALAXY_VERSION=$BRANCH
            ;;
    esac
fi
# Setup Galaxy master API key and admin user
TEMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
echo "Created temporary directory $TEMP_DIR"
# Export GALAXY_CONFIG_FILE environment variable to be used by run_galaxy.sh
export GALAXY_CONFIG_FILE="$TEMP_DIR/galaxy.ini"
# Export BIOBLEND_ environment variables to be used in BioBlend tests
export BIOBLEND_GALAXY_MASTER_API_KEY=$(LC_ALL=C tr -dc A-Za-z0-9 < /dev/urandom | head -c 32)
export BIOBLEND_GALAXY_USER_EMAIL="${USER}@localhost.localdomain"
DATABASE_CONNECTION="sqlite:///$TEMP_DIR/universe.sqlite?isolation_level=IMMEDIATE"
eval "echo \"$(cat "${BIOBLEND_DIR}/tests/template_galaxy.ini")\"" > "$GALAXY_CONFIG_FILE"
# Update kombu requirement (and its dependency amqp) to a version compatible with Python 2.7.11, see https://github.com/celery/kombu/pull/540
if [ -f eggs.ini ]; then
  sed -i.bak -e 's/^kombu = .*$/kombu = 3.0.30/' -e 's/^amqp = .*$/amqp = 1.4.8/' eggs.ini
fi

# Start Galaxy and wait for successful server start
export GALAXY_SKIP_CLIENT_BUILD=1
GALAXY_RUN_ALL=1 "${BIOBLEND_DIR}/run_galaxy.sh" --daemon --wait
export BIOBLEND_GALAXY_URL=http://localhost:${GALAXY_PORT}

# Run the tests
cd "${BIOBLEND_DIR}"
set +e  # don't stop the script if tox fails
if [ -n "${t_val}" ]; then
  tox -e "${e_val}" -- "${t_val}"
else
  tox -e "${e_val}"
fi
exit_code=$?
deactivate

# Stop Galaxy
cd "${g_val}"
GALAXY_RUN_ALL=1 "${BIOBLEND_DIR}/run_galaxy.sh" --daemon stop
# Remove temporary directory if -c is specified or if all tests passed
if [ -n "${c_val}" ] || [ $exit_code -eq 0 ]; then
  rm -rf "$TEMP_DIR"
fi
