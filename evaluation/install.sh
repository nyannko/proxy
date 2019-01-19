#!/usr/bin/env bash
#
# Project preparation script for gcloud centOS7
#
set -e
#
LIBSODIUM_LIB_DIR="$HOME/libsodium-stable"
PROJECT_LIB_DIR="$HOME/ipv8t/pyipv8"
PROJECT_WORK_DIR="$HOME/ipv8t/socks5_ipv8/hops"
#
#######################################################################
# install libsodium
#######################################################################
cd $HOME
sudo yum -y install gcc

curl -O https://download.libsodium.org/libsodium/releases/LATEST.tar.gz
tar -xvzf LATEST.tar.gz
cd libsodium*
./configure --prefix=$LIBSODIUM_LIB_DIR
make && make check
make install

# export libsodium lib path
cp ~/.bashrc ~/.bashrc_backup
echo 'export LD_LIBRARY_PATH=$HOME/libsodium-stable/lib' >> ~/.bashrc
source ~/.bashrc

#######################################################################
# install project dependencies
#######################################################################
sudo yum -y install python-devel python-pip git
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

