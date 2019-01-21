#!/usr/bin/env bash
###
# param meaning: website/dir/filename
# $1: "www.google.com"; $2: "example_print_peers"; $3: "normal.txt"
# source filename && test_xxx() [args]
###

### create new file ###
create_file() {
echo "dir: $1; fn: $2"
if [[ ! -d "$1" ]]; then
    mkdir -p $1
fi
new_file="$1/$2"
echo "write result to $new_file"
echo "time_lookup time_connect time_appconnect time_pretransfer time_redirect timestarttransfer time_total" > $new_file
declare -i counter=0
}

test_normal() {
    create_file $2 $3
    while true; do
        curl -s -o /dev/null  -w "%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} %{time_starttransfer} %{time_total}\n" $1 | tail -n 1 >> $new_file;
        sleep 3;
        let counter++
        if (( $counter % 100 == 0 )); then
            echo $counter
        fi
    done
}

test_hop() {
    create_file $3 $4
#    port=$2
    port=40000 # for debug
    while true; do
#        echo "socks5h://127.0.0.1:${port}" # for debug
        result=`curl --proxy socks5h://127.0.0.1:${port} -s -o /dev/null  -w "%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} %{time_starttransfer} %{time_total}\n" $1`;
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
}