#!/usr/bin/env bash 
set -u 
#set -e

blue=$(tput setaf 4)
green=$(tput setaf 64)
red=$(tput setaf 124)
normal=$(tput sgr0)

FORMAT='%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} %{time_starttransfer} %{time_total}\n'

mp() {
    echo "curl $1 using 80"
    echo $FORMAT
    curl --proxy socks5h://127.0.0.1:${port} -s -o /dev/null -w "$FORMAT" $1 
    echo "curl $1 using 443"
    curl --proxy socks5h://127.0.0.1:${port} -s -o /dev/null -w "$FORMAT" https://$1 
}

normal() {
    echo "curl $1 without proxy"
    echo https://$1
    curl  -s -o /dev/null  -w "$FORMAT" $1 
    curl  -s -o /dev/null  -w "$FORMAT" https://$1
}

all() {
    ports=(7000 1080 9150) # ss , v2
    for p in "${ports[@]}"; do
        echo "${red}curl $1 using $p${normal}"
        curl --proxy socks5h://127.0.0.1:${p} -s -o /dev/null  -w "$FORMAT" $1 
        echo "${green}curl https://$1 using $p${normal}"
        curl --proxy socks5h://127.0.0.1:${p} -s -o /dev/null  -w "$FORMAT" https://$1 
    done
}


_main() {
    if [[ $1 == "no" ]]; then
        normal $2
        exit 0 
    elif [[ $1 == "all" ]]; then
        all $2
        exit 0
    fi

    if [[ $1 == "mp" ]]; then
        echo "use mp with port 40000"
        port=40000
    elif [[ $1 == "ss" ]]; then
        echo "use ss with port 7000"
        port=7000
    elif [[ $1 == "v2" ]]; then
        echo "use v2 with port 1080"
        port=1080
    fi
    mp $2
}    

_main "$@"
