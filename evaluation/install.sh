#!/usr/bin/env bash
install() {
    #######################################################################
    # Project preparation script for gcloud/DAS5 centOS7
    #######################################################################
    set -e

    gcloud_flag=''
    das_flag=''

    LIBSODIUM_LIB_DIR="$HOME/libsodium-stable"
    PROJECT_LIB_DIR="$HOME/ipv8t/pyipv8"
    PROJECT_WORK_DIR="$HOME/ipv8t/socks5_ipv8/hops"

    # load modules for das
    if [[ "${das_flag}" = true ]]; then
        module load python/2.7.13
        module load prun
        module load gcc
    fi
    #######################################################################
    # install libsodium
    #######################################################################
    cd $HOME
    # install gcc for gcloud
    if [[ "${gcloud_flag}" = true ]];then
        sudo yum -y install gcc
    fi

    if [[ ! -d "$LIBSODIUM_LIB_DIR" ]]; then
        curl -O https://download.libsodium.org/libsodium/releases/LATEST.tar.gz;
        tar -xvzf LATEST.tar.gz;
        cd libsodium*;
        ./configure --prefix=$LIBSODIUM_LIB_DIR;
        make && make check;
        make install;

        # export libsodium lib path
        cp ~/.bashrc ~/.bashrc_backup
        echo 'export LD_LIBRARY_PATH=$HOME/libsodium-stable/lib' >> ~/.bashrc
        source ~/.bashrc
    fi

    #######################################################################
    # install project dependencies
    #######################################################################
    # only for gcloud
    if [[ "${gcloud_flag}" = true ]];then
        sudo yum -y install python-devel python-pip git
    fi
    cd $PROJECT_LIB_DIR
    pip install --user -r requirements.txt
    pip install --user service_identity
    #
    # https://stackoverflow.com/questions/47600597/import-error-cannot-import-name-opentype
    #
    pip install --user --upgrade google-auth-oauthlib

    # use rsync here
    # git submodule update --remote --recursive

    #######################################################################
    # set project path
    #######################################################################
    echo 'export PYTHONPATH=$HOME/ipv8t' >> ~/.bashrc
    source ~/.bashrc
    # here `source ~/.bashrc` is only executed in the sub shell. In order to export
    # the env vars, do `source install.sh` or open a new tty after do `bash install.sh`
    # or just using `exec $SHELL -l` in the end of the script.

    #######################################################################
    # test
    #######################################################################
    cd $PROJECT_WORK_DIR
    timeout 5s python multiproxy.py --client 1 --server 1
    # we don't have environment variables except `source ~/.bashrc` again.

    #######################################################################
    # set project alias
    #######################################################################
    cat >> ~/.bashrc << EOF
    alias ks='pkill screen'
    alias se='screen -r eval'
    alias sr='screen -r run'
    alias tc='curl --proxy socks5h://127.0.0.1:40000 -s -o /dev/null -w "%{time_total}" https://www.google.com'
EOF

    echo "run source ~/.bashrc"
}

print_usage() {
  printf "Usage: \nbash install.sh -g # install in gcloud instance;\nbash install.sh -d # install in das instance\n"
}

while getopts 'gd' flag; do
    case "${flag}" in
        g) gcloud_flag='true';
            das_flag='false';
            echo "environment preparation for gcloud";
            install;
            ;;
        d) gcloud_flag='false';
            das_flag='true';
            echo "environment preparation for DAS5";
            install;
            ;;
        *) print_usage
        exit 1
        ;;
    esac
done

# if flag not set, exit
if [[ -z "${gcloud_flag}" && -z "${das_flag}" ]]; then
    print_usage
fi
