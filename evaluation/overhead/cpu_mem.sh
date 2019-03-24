#!/usr/bin/env bash
set -u

# check status
while true; do
    ps -ef | grep python\ multiproxy | grep -v grep
    error=$?
    if [[ ${error} -eq 0 ]]; then
        echo "program running";
        break;
    fi
done

# get pid
pid=`ps -ef | grep python\ multiproxy | grep -v grep | awk '{print $2}'`
echo ${pid}

# write to file
while true; do
#    ps -p ${pid} -o %cpu,%mem | tail -n 1 >> overhead_${1}.txt
#    ps -p ${pid} -O etimes -o %cpu,%mem | awk '{print $2, $9, $10}' |tail -n 1  >> overhead_${1}.txt
    ps -p ${pid} -o etimes -o %cpu,'rsz' | tail -n 1 >> memoverhead_${1}.txt # (physical) memory usage
    sleep 1
done