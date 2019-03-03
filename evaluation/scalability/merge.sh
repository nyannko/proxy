#!/usr/bin/env bash
# input $1: nodes number for files
set -e
set -u
echo $1
cat scalability_res/file* > ~/scares/node${1}.txt

ls -al ~/scares/
# bash test_scalability.sh ;sleep 5m;bash merge.sh 200;kill_all;