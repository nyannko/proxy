#!/usr/bin/env bash
###
# OSX:   gtimeout 2h bash normal.sh
# Linux: timeut 2h bash normal.sh
###
counter=0
echo "time_lookup time_connect time_appconnect time_pretransfer time_redirect timestarttransfer time_total" > normal.txt
while true; do
curl -s -o /dev/null  -w "%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} \
%{time_starttransfer} %{time_total}\n" https://www.google.co | tail -n 1 >> normal.txt;
sleep 3;
let counter++
echo $counter "done"
done
