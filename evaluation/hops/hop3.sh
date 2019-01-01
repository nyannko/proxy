#!/usr/bin/env bash
###
# start four nodes: python multiproxy.py --client 1; python multiproxy.py --forwarder 2; python multiproxy.py --server 1
# Linux: timeut 2h bash normal.sh
###
counter=0
echo "time_lookup time_connect time_appconnect time_pretransfer time_redirect timestarttransfer time_total" > hop3.txt
while true; do
result=`curl --proxy socks5h://127.0.0.1:40000 -s -o /dev/null  -w "%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} \
%{time_starttransfer} %{time_total}\n" https://www.google.com`;
error_code=$?
if [ $error_code -ne 0 ]; then
    echo $counter test failed $error_code
else
    echo $result | tail -n 1 >> hop3.txt;
    sleep 3;
    let counter++
    echo $counter "done" $result
fi
done
