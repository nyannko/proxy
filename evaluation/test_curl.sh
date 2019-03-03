#!/usr/bin/env bash 
set -u 
#set -e


HOME_DIR="$HOME/evaluation"

blue=$(tput setaf 4)
green=$(tput setaf 64)
red=$(tput setaf 124)
normal=$(tput sgr0)

FORMAT='%{time_namelookup} %{time_connect} %{time_appconnect} %{time_pretransfer} %{time_redirect} %{time_starttransfer} %{time_total}\n'


mp() {
#    echo "curl $1 using 80"
#    echo $FORMAT
#    curl --proxy socks5h://127.0.0.1:${port} -s -o /dev/null -w "$FORMAT" $1
#    echo "curl $1 using 443"
    curl --proxy socks5h://127.0.0.1:${port} -s -o /dev/null -w "$FORMAT" https://$1 
}

## for normal or VPN
normal() {
    curl  -s -o /dev/null  -w "$FORMAT" $1
}

declare -a ws=( "go" "yt" "in" "fb" "tw" )

go="https://www.google.com"
yt="https://www.youtube.com"
in="https://www.instagram.com"
fb="https://www.facebook.com"
tw="https://twitter.com"

loop() {
    count=$1
    for w in "${ws[@]}"; do
        # website; filename
        for i in `seq 1 $count`; do
            all ${!w} $w
        done
    done
}

all() {
#    declare -a ports=(40000 7000 1080) # ss , v2, tor
    declare -a ports=(9050) # ss , v2, tor
    WEBSITE=$1
    FILENAME="$2.txt"

    for p in "${ports[@]}"; do
#        echo "${red}curl $1 using $p${normal}"
#        curl --proxy socks5h://127.0.0.1:${p} -s -o /dev/null  -w "$FORMAT" $1
        echo "${green}curl $WEBSITE using $p${normal}"
        if [[ p -eq 40000 ]]; then
            DIRNAME="mp"
        elif [[ p -eq 7000 ]]; then
            DIRNAME="ss"
        elif [[ p -eq 1080 ]]; then
            DIRNAME="v2"
        elif [[ p -eq 9050 ]]; then
            DIRNAME="tor" # tor
        fi

        echo "website: "$WEBSITE "filename:" $DIRNAME/$FILENAME
        # new dir
        if [[ ! -d "result/$DIRNAME" ]]; then
            mkdir -p result/$DIRNAME
        fi
        # curl --proxy socks5h://127.0.0.1:${p} -s -o /dev/null  -w "$FORMAT" $WEBSITE
        # append
        res=`curl --proxy socks5h://127.0.0.1:${p} -s -o /dev/null  -w "$FORMAT" $WEBSITE`
        echo $res
        echo $res >> "result/${DIRNAME}/${FILENAME}"
    done
}

loop_oc() {
    count=$1
    for w in "${ws[@]}"; do
        # website; filename
        for i in `seq 1 $count`; do
            oc ${!w} $w
        done
    done
}

oc() {
#    sudo openconnect --protocol=anyconnect --user=mei --authgroup=Route \
#    --servercert sha256:2f4776a07760c20be03bb27548395c60204e413fad9bf1d0f8d5614083570fe9 https://35.196.96.100:4433
    # enter password here
    WEBSITE=$1
    FILENAME="$2.txt"
    DIRNAME="oc"
    if [[ ! -d "result/$DIRNAME" ]]; then
            mkdir -p result/$DIRNAME
    fi
    res=`curl  -s -o /dev/null  -w "$FORMAT" $WEBSITE`
    echo $res
    echo $res >> "result/${DIRNAME}/${FILENAME}"
}

loop_ov () {
    count=$1
    for w in "${ws[@]}"; do
        # website; filename
        for i in `seq 1 $count`; do
            ovpn ${!w} $w
        done
    done
}

ovpn() {
#    cd $HOME_DIR
#    sudo openvpn --config CLIENTNAME.ovpn
    WEBSITE=$1
    FILENAME="$2.txt"
    DIRNAME="ovpn"
    if [[ ! -d "result/$DIRNAME" ]]; then
            mkdir -p result/$DIRNAME
    fi
    res=`curl  -s -o /dev/null  -w "$FORMAT" $WEBSITE`
    echo $res
    echo $res >> "result/${DIRNAME}/${FILENAME}"
}

_main() {
#   1
#    loop 10
#   2 tor
    loop 10
#   3
#    loop_oc 10
#    loop_ov 10

#    if [[ $1 == "no" ]]; then
#        normal $2
#        exit 0
#    elif [[ $1 == "all" ]]; then
#        all $2
#        exit 0
#    fi
#
#    if [[ $1 == "mp" ]]; then
#        echo "use mp with port 40000"
#        port=40000
#    elif [[ $1 == "ss" ]]; then
#        echo "use ss with port 7000"
#        port=7000
#    elif [[ $1 == "v2" ]]; then
#        echo "use v2 with port 1080"
#        # init tor here
#        port=1080
#    elif [[ $1 == "tor" ]]; then
#        echo "use tor with port 9050"
#        port=9050
#    elif [[ $1 == "oc" ]]; then
#        echo "use ocserv"
#        # init ocserv here
#    elif [[ $1 == "ov" ]]; then
#        echo "use openVPN"
#        # init openVPN here
#    fi
#    mp $2
}    

_main "$@"

# usage: test_curl.sh all www.google.com
