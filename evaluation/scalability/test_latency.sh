#!/usr/bin/env bash

while true;do
# curl --proxy socks5h://127.0.0.1:${1} -s -o /dev/null  -w "%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} %{time_starttransfer} %{time_total}\n" \
# https://www.google.com | tail -n 1 >> ./scalability_res/file${1}.txt;
 curl --proxy socks5h://127.0.0.1:${1} -s -o /dev/null  -w "%{time_total}\n" \
 https://www.google.com | tail -n 1 >> ./scalability_res/file${2}${1}.txt;
done
