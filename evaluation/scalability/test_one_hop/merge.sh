#!/usr/bin/env bash
# input $1: nodes number for files
set -e
set -u
echo $1

# create dir if not exists
if [[ ! -d ~/scares ]]; then
    mkdir ~/scares
fi

cat ~/ipv8t/evaluation/scalability/scalability_res/file* > ~/scares/node${1}.txt

ls -al ~/scares/
# bash test_scalability.sh ;sleep 5m;bash merge.sh 200;kill_all;