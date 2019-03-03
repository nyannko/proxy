#!/usr/bin/env bash
# input
# $1: port
# $2: id of file

#ws1="https://www.nyannko.tk"
#ws2="https://www.nyannko.tk/speedtest/file10m"

ws1="https://www.google.com"

# wait for connection
while true; do
    curl -s -o /dev/null --proxy socks5h://127.0.0.1:${1} -s -S ${ws1}
    error=$?
    echo $error
    if [[ $error -eq 0 ]];then
        echo "connected"
        break
    fi
done

if [[ ! -d scalability_res ]]; then
    mkdir scalability_res;
fi

while true; do
    curl --proxy socks5h://127.0.0.1:${1} -s -S ${ws1} -o /dev/null -w "%{speed_download} %{time_total}\n" \
    | tail -n 1 >> ./scalability_res/file_${2}_${1}.txt;
done