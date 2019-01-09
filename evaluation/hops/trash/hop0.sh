#!/usr/bin/env bash
###
# python multiproxy.py --client 1 --server 1
# Linux: timeut 2h bash normal.sh
# param meaning: website/dir/filename
# $1: "www.google.com"; $2: "example_print_peers"; $3: "normal.txt"
###
if [[ ! -d "$2" ]]; then
    mkdir -p $2
fi
new_file="$2/$3"
echo "write result to $new_file"

counter=0
echo "time_lookup time_connect time_appconnect time_pretransfer time_redirect timestarttransfer time_total" > $new_file
while true; do
result=`curl --proxy socks5h://127.0.0.1:40000 -s -o /dev/null  -w "%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} \
%{time_starttransfer} %{time_total}\n" $1`;
error_code=$?
if [ $error_code -ne 0 ]; then
    echo $counter test failed $error_code
else
    echo $result | tail -n 1 >> $new_file;
    sleep 5;
    let counter++
    echo $counter "done" $result
fi
done
