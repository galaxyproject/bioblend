#!/bin/sh

#This script should be run from inside the Galaxy base directory
#cd `dirname $0`

# If there is a file that defines a shell environment specific to this
# instance of Galaxy, source the file.
if [ -z "$GALAXY_LOCAL_ENV_FILE" ];
then
    GALAXY_LOCAL_ENV_FILE='./config/local_env.sh'
fi

if [ -f $GALAXY_LOCAL_ENV_FILE ];
then
    . $GALAXY_LOCAL_ENV_FILE
fi

if [ -f scripts/common_startup.sh ]; then
    ./scripts/common_startup.sh || exit 1
else
    if [ -f scripts/copy_sample_files.sh ]; then
        ./scripts/copy_sample_files.sh
    else
        SAMPLES="
            community_wsgi.ini.sample
            datatypes_conf.xml.sample
            external_service_types_conf.xml.sample
            migrated_tools_conf.xml.sample
            reports_wsgi.ini.sample
            shed_tool_conf.xml.sample
            tool_conf.xml.sample
            shed_tool_data_table_conf.xml.sample
            tool_data_table_conf.xml.sample
            tool_sheds_conf.xml.sample
            data_manager_conf.xml.sample
            shed_data_manager_conf.xml.sample
            openid_conf.xml.sample
            universe_wsgi.ini.sample
            tool-data/shared/ncbi/builds.txt.sample
            tool-data/shared/ensembl/builds.txt.sample
            tool-data/shared/ucsc/builds.txt.sample
            tool-data/shared/ucsc/publicbuilds.txt.sample
            tool-data/shared/ucsc/ucsc_build_sites.txt.sample
            tool-data/shared/igv/igv_build_sites.txt.sample
            tool-data/shared/rviewer/rviewer_build_sites.txt.sample
            tool-data/*.sample
            static/welcome.html.sample
        "
        # Create any missing config/location files
        for sample in $SAMPLES; do
            file=`echo $sample | sed -e 's/\.sample$//'`
            if [ ! -f "$file" -a -f "$sample" ]; then
                echo "Initializing $file from `basename $sample`"
                cp $sample $file
            fi
        done
    fi
    # explicitly attempt to fetch eggs before running
    FETCH_EGGS=1
    for arg in "$@"; do
        [ "$arg" = "--stop-daemon" ] && FETCH_EGGS=0; break
    done
    if [ $FETCH_EGGS -eq 1 ]; then
        python ./scripts/check_eggs.py -q
        if [ $? -ne 0 ]; then
            echo "Some eggs are out of date, attempting to fetch..."
            python ./scripts/fetch_eggs.py
            if [ $? -eq 0 ]; then
                echo "Fetch successful."
            else
                echo "Fetch failed."
                exit 1
            fi
        fi
    fi
fi

# If there is a .venv/ directory, assume it contains a virtualenv that we
# should run this instance in.
if [ -d .venv ];
then
    printf "Activating virtualenv at %s/.venv\n" $(pwd)
    . .venv/bin/activate
fi

python ./scripts/check_python.py || exit 1

if [ -n "$GALAXY_UNIVERSE_CONFIG_DIR" ]; then
    python ./scripts/build_universe_config.py "$GALAXY_UNIVERSE_CONFIG_DIR"
fi

if [ -z "$GALAXY_CONFIG_FILE" ]; then
    if [ -f universe_wsgi.ini ]; then
        GALAXY_CONFIG_FILE=universe_wsgi.ini
    elif [ -f config/galaxy.ini ]; then
        GALAXY_CONFIG_FILE=config/galaxy.ini
    else
        GALAXY_CONFIG_FILE=config/galaxy.ini.sample
    fi
    export GALAXY_CONFIG_FILE
fi

if [ -n "$GALAXY_RUN_ALL" ]; then
    servers=`sed -n 's/^\[server:\(.*\)\]/\1/  p' $GALAXY_CONFIG_FILE | xargs echo`
    echo "$@" | grep -q 'daemon\|restart'
    if [ $? -ne 0 ]; then
        echo 'ERROR: $GALAXY_RUN_ALL cannot be used without the `--daemon`, `--stop-daemon` or `restart` arguments to run.sh'
        exit 1
    fi
    (echo "$@" | grep -q -e '--daemon\|restart') && (echo "$@" | grep -q -e '--wait')
    WAIT=$?
    ARGS=`echo "$@" | sed 's/--wait//'`
    for server in $servers; do
        if [ $WAIT -eq 0 ]; then
            python ./scripts/paster.py serve $GALAXY_CONFIG_FILE --server-name=$server --pid-file=$server.pid --log-file=$server.log $ARGS
            while true; do
                sleep 1
                printf "."
                # Grab the current pid from the pid file
                if ! current_pid_in_file=$(cat $server.pid); then
                    echo "A Galaxy process died, interrupting" >&2
                    exit 1
                fi
                # Search for all pids in the logs and tail for the last one
                latest_pid=`egrep '^Starting server in PID [0-9]+\.$' $server.log -o | sed 's/Starting server in PID //g;s/\.$//g' | tail -n 1`
                # If they're equivalent, then the current pid file agrees with our logs
                # and we've succesfully started
                [ -n "$latest_pid" ] && [ $latest_pid -eq $current_pid_in_file ] && break
            done
            echo
        else
            echo "Handling $server with log file $server.log..."
            python ./scripts/paster.py serve $GALAXY_CONFIG_FILE --server-name=$server --pid-file=$server.pid --log-file=$server.log $@
        fi
    done
else
    # Handle only 1 server, whose name can be specified with --server-name parameter (defaults to "main")
    python ./scripts/paster.py serve $GALAXY_CONFIG_FILE $@
fi
