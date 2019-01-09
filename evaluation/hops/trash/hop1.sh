#!/usr/bin/env bash
###
# start two nodes: python multiproxy.py --client 1 ; python multiproxy.py --server 1
# Linux: timeut 2h bash normal.sh
# param meaning: website/dir/filename
# $1: "www.google.com"; $2: "example_print_peers"; $3: "normal.txt"
###
counter=0
echo "time_lookup time_connect time_appconnect time_pretransfer time_redirect timestarttransfer time_total" > hop1.txt
while true; do
result=`curl --proxy socks5h://127.0.0.1:40000 -s -o /dev/null  -w "%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} \
%{time_starttransfer} %{time_total}\n" https://www.instagram.com`;
error_code=$?
if [ $error_code -ne 0 ]; then
    echo $counter test failed $error_code
else
    echo $result | tail -n 1 >> hop1.txt;
    sleep 5;
    let counter++
    echo $counter "done" $result
fi
done
