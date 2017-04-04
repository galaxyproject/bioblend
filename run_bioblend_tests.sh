#!/bin/sh

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
      Work against specified tox environments. Defaults to py27.
  -t BIOBLEND_TESTS
      Subset of tests to run, e.g. 'tests/TestGalaxyObjects.py:TestHistory'.
      See 'man nosetests' for more information. Defaults to all tests.
  -r GALAXY_REV
      Branch or commit of the local Galaxy git repository to checkout. Defaults
      to the dev branch.
  -c
      Force removal of the temporary directory created for Galaxy, even if some
      test failed."
}

get_abs_dirname () {
  # $1 : relative dirname
  echo $(cd "$1" && pwd)
}

e_val=py27
p_val=8080
r_val=dev
while getopts 'hcg:e:p:t:r:' option
do
  case $option in
    h) show_help
       exit;;
    c) c_val=1;;
    g) g_val=$(get_abs_dirname $OPTARG);;
    e) e_val=$OPTARG;;
    p) p_val=$OPTARG;;
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
BIOBLEND_DIR=$(get_abs_dirname $(dirname $0))
cd ${BIOBLEND_DIR}
if [ ! -d .venv ]; then
  virtualenv .venv
fi
. .venv/bin/activate
python setup.py install || exit 1
pip install --upgrade "tox>=1.8.0"

# Setup Galaxy
cd ${g_val}
# Update repository (may change the sample files or the list of eggs)
git fetch
git checkout ${r_val}
if git show-ref -q --verify "refs/heads/${r_val}" 2>/dev/null; then
  # ${r_val} is a branch
  export GALAXY_VERSION=${r_val}
  git pull --ff-only
fi
# Setup Galaxy master API key and admin user
if [ -f universe_wsgi.ini.sample ]; then
  GALAXY_SAMPLE_CONFIG_FILE=universe_wsgi.ini.sample
  GALAXY_CONFIG_DIR=.
else
  GALAXY_SAMPLE_CONFIG_FILE=config/galaxy.ini.sample
  GALAXY_CONFIG_DIR=config
fi
TEMP_DIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir')
echo "Created temporary directory $TEMP_DIR"
export GALAXY_CONFIG_FILE=$TEMP_DIR/galaxy.ini
export BIOBLEND_GALAXY_MASTER_API_KEY=$(cat /dev/urandom | LC_ALL=C tr -dc A-Za-z0-9 | head -c 32)
export BIOBLEND_GALAXY_USER="${USER}"
GALAXY_USER_EMAIL="${USER}@localhost.localdomain"
sed -e "s/^#master_api_key.*/master_api_key = $BIOBLEND_GALAXY_MASTER_API_KEY/" -e "s/^#admin_users.*/admin_users = $GALAXY_USER_EMAIL/" $GALAXY_SAMPLE_CONFIG_FILE > $GALAXY_CONFIG_FILE
sed -i.bak -e "s|^#database_connection.*|database_connection = sqlite:///$TEMP_DIR/universe.sqlite?isolation_level=IMMEDIATE|" -e "s|^#file_path.*|file_path = $TEMP_DIR/files|" -e "s|^#new_file_path.*|new_file_path = $TEMP_DIR/tmp|" -e "s|#job_working_directory.*|job_working_directory = $TEMP_DIR/job_working_directory|" $GALAXY_CONFIG_FILE
# Change Galaxy configuration needed by many tests
sed -i.bak -e 's/^#allow_user_dataset_purge.*/allow_user_dataset_purge = True/' $GALAXY_CONFIG_FILE
# Change Galaxy configuration needed by some library tests
sed -i.bak -e 's/^#allow_library_path_paste.*/allow_library_path_paste = True/' $GALAXY_CONFIG_FILE
# Change Galaxy configuration needed by some tool tests
sed -i.bak -e 's/^#conda_auto_init.*/conda_auto_init = True/' $GALAXY_CONFIG_FILE
# Change Galaxy configuration needed by some workflow tests
sed -i.bak -e 's/^#enable_beta_workflow_modules.*/enable_beta_workflow_modules = True/' $GALAXY_CONFIG_FILE
# Change Galaxy configuration needed by some user tests
sed -i.bak -e 's/^#allow_user_deletion.*/allow_user_deletion = True/' $GALAXY_CONFIG_FILE
if [ -f test/functional/tools/samples_tool_conf.xml ]; then
  sed -i.bak -e "s/^#tool_config_file.*/tool_config_file = $GALAXY_CONFIG_DIR\/tool_conf.xml.sample,$GALAXY_CONFIG_DIR\/shed_tool_conf.xml.sample,test\/functional\/tools\/samples_tool_conf.xml/" $GALAXY_CONFIG_FILE
fi
if [ -n "${p_val}" ]; then
  # Change only the first occurence of port number
  sed -i.bak -e "0,/^#port/ s/^#port.*/port = $p_val/" $GALAXY_CONFIG_FILE
fi
# Start Galaxy and wait for successful server start
GALAXY_RUN_ALL=1 ${BIOBLEND_DIR}/run_galaxy.sh --daemon --wait || exit 1

# Use the master API key to create the admin user and get its API key
export BIOBLEND_GALAXY_URL=http://localhost:${p_val}
# Run the tests
cd ${BIOBLEND_DIR}
if [ -n "${t_val}" ]; then
  tox -e ${e_val} -- --tests ${t_val}
else
  tox -e ${e_val}
fi
exit_code=$?
deactivate

# Stop Galaxy
cd ${g_val}
GALAXY_RUN_ALL=1 ./run.sh --daemon stop
# Remove temporary directory if -c is specified or if all tests passed
if [ -n "${c_val}" ] || [ $exit_code -eq 0 ]; then
  rm -rf $TEMP_DIR
fi
