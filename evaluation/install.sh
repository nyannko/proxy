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

#######################################################################
# test
#######################################################################
cd $PROJECT_WORK_DIR
timeout 5s python multiproxy.py --client 1 --server 1
