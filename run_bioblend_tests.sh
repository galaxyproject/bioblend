#!/bin/sh

show_help () {
  echo "Usage:  $0 -g GALAXY_DIR [-p PORT] [-t BIOBLEND_TESTS] [-r GALAXY_REV]

  Run tests for BioBlend. Useful for Continuous Integration testing.
  *Please note* that this script overwrites the sqlite database of the Galaxy
  instance target (-g), so only use it on 'test' or otherwise disposable
  instances.

Options:
  -g GALAXY_DIR
      Path of the local Galaxy Mercurial repository. The sqlite database of
      this instance will be overwritten.
  -p PORT
      Port to use for the Galaxy server. Defaults to 8080.
  -t BIOBLEND_TESTS
      Subset of tests to run, e.g. 'tests/TestGalaxyObjects.py:TestHistory'.
      See 'man nosetests' for more information. Defaults to all tests.
  -r GALAXY_REV
      Revision of the local Galaxy Mercurial repository to checkout. Defaults
      to tip. Minimum is 4f3f92ca8e7488f4f5a90b8d57eddaeb3e1645d6 ."
}

get_abs_dirname () {
  # $1 : relative dirname
  echo $(cd "$1" && pwd)
}

p_val=8080
while getopts 'hb:g:p:t:r:' option
do
  case $option in
    h) show_help
       exit;;
    g) g_val=$(get_abs_dirname $OPTARG);;
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
python setup.py install --user || exit 1

# Setup Galaxy
cd ${g_val}
# Stop Galaxy if it was running
GALAXY_RUN_ALL=1 ./run.sh --daemon stop
# Update repository (may change the sample files or the list of eggs)
hg pull
hg update ${r_val}
# Setup Galaxy master API key and admin user
TEMP_DIR=`mktemp -d 2>/dev/null || mktemp -d -t 'mytmpdir'`
export GALAXY_CONFIG_FILE=$TEMP_DIR/galaxy.ini
GALAXY_MASTER_API_KEY=`date --rfc-3339=ns | md5sum | cut -f 1 -d ' '`
GALAXY_USER_EMAIL=${USER}@localhost.localdomain
sed -e "s/^#master_api_key.*/master_api_key = $GALAXY_MASTER_API_KEY/" -e "s/^#admin_users.*/admin_users = $GALAXY_USER_EMAIL/" config/galaxy.ini.sample > $GALAXY_CONFIG_FILE
# Change configuration needed by many tests
sed -i -e 's/^#allow_user_dataset_purge.*/allow_user_dataset_purge = True/' $GALAXY_CONFIG_FILE
# Change configuration needed by some library tests
sed -i -e 's/^#allow_library_path_paste.*/allow_library_path_paste = True/' $GALAXY_CONFIG_FILE
if [ -n "${p_val}" ]; then
  # Change only the first occurence of port number
  sed -i -e "0,/^#port/ s/^#port.*/port = $p_val/" $GALAXY_CONFIG_FILE
fi
# Restore empty database at latest migration stage, if available
cp -f universe.sqlite.empty_at_latest_migration database/universe.sqlite
# Start Galaxy and wait for successful server start
./rolling_restart.sh || exit 1
# Save empty database at latest migration stage
cp -f database/universe.sqlite universe.sqlite.empty_at_latest_migration

# Use the master API key to create the admin user and get its API key
export BIOBLEND_GALAXY_URL=http://localhost:${p_val}
GALAXY_USER=$USER
GALAXY_USER_PASSWD=`date --rfc-3339=ns | md5sum | cut -f 1 -d ' '`
export BIOBLEND_GALAXY_API_KEY=`python ${BIOBLEND_DIR}/docs/examples/create_user_get_api_key.py $BIOBLEND_GALAXY_URL $GALAXY_MASTER_API_KEY $GALAXY_USER $GALAXY_USER_EMAIL $GALAXY_USER_PASSWD`
echo "Created new Galaxy user $GALAXY_USER with email $GALAXY_USER_EMAIL , password $GALAXY_USER_PASSWD and API key $BIOBLEND_GALAXY_API_KEY"
# Run the tests
cd ${BIOBLEND_DIR}
if [ -n "${t_val}" ]; then
  python setup.py nosetests --tests ${t_val}
else
  python setup.py test
fi

# Stop Galaxy
cd ${g_val}
GALAXY_RUN_ALL=1 ./run.sh --daemon stop
rm -rf $TEMP_DIR
