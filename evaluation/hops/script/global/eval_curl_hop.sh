#!/usr/bin/env bash
# param: website/dir/filename
# $1: "www.google.com"; $2: "test/go"; $3: "normal.txt"

declare -a ws=( "go" "yt" "in" "fb" "tw" )

go="https://www.google.com"
yt="https://www.youtube.com"
in="https://www.instagram.com"
fb="https://www.facebook.com"
tw="https://twitter.com"

normal="normal.txt"
hop0="hop0.txt"
hop1="hop1.txt"
hop2="hop2.txt"
hop3="hop3.txt"

max_time=30s

import() {
    source curl_hop.sh
    # export function definitions to sub-shell
    export -f create_file test_normal test_hop
}

eval_normal_curl_time() {
    import
    input=$1 # normal
    echo $input
    for w in ${ws[@]}; do
        echo ${!w}
        timeout $max_time bash -c "test_normal ${!w} test/$w ${!input}"
#        gtimeout $max_time bash -c "test_normal ${!w} test/$w ${!input}"
    done
}

eval_hop_curl_time() {
    import
    input=$1 # hop1-3
    echo $input
    for w in ${ws[@]}; do
        echo ${!w}
        timeout $max_time bash -c "test_hop ${!w} test/$w ${!input}"
#        gtimeout $max_time bash -c "test_hop ${!w} test/$w ${!input}"
    done
}

test_function() {
    import
    # bash -c the command are read from the string
    #################### test normal ####################
    gtimeout 5s bash -c "test_normal $go test/go $normal"

    #################### test hop0 ######################
    gtimeout 5s bash -c "test_hop $yt test/yt $hop0"

    #################### test hop1 ######################
    # start two nodes: python multiproxy.py --client 1 ; python multiproxy.py --server 1
    gtimeout 5s bash -c "test_hop $in test/in $hop1"

    #################### test hop2 ######################
    # start three nodes: python multiproxy.py --client 1; python multiproxy.py --forwarder 1; python multiproxy.py --server 1
    gtimeout 5s bash -c "test_hop $fb test/fb $hop2"

    #################### test hop3 ######################
    # start four nodes: python multiproxy.py --client 1; python multiproxy.py --forwarder 2; python multiproxy.py --server 1
    #source curl_hop.sh && test_hop $tw test/tw $hop3
    gtimeout 5s bash -c "test_hop $tw test/tw $hop3"
}

if [[ $1 = "normal" ]]; then
    eval_normal_curl_time normal
elif [[ $1 = "hop1" ]]; then
    eval_hop_curl_time hop1
elif [[ $1 = "hop2" ]]; then
    eval_hop_curl_time hop2
elif [[ $1 = "hop3" ]]; then
    eval_hop_curl_time hop3
else
    echo "unknown"
fi

# for test
#PS3='Please enter your choice: '
#options=("normal" "hop1" "hop2" "hop3" "test" "quit")
#select opt in "${options[@]}"
#do
#    case $opt in
#        "normal")
#            echo "evaluate normal"
#            eval_normal_curl_time normal
#            break
#            ;;
#        "hop1")
#            echo "evaluate one hop"
#            eval_hop_curl_time hop1
#            break
#            ;;
#        "hop2")
#            echo "evaluate two hops"
#            eval_hop_curl_time hop2
#            break
#            ;;
#        "hop3")
#            echo "evaluate three three hops"
#            eval_hop_curl_time hop3
#            break
#            ;;
#        "test")
#            echo "test function"
#            test_function
#            break
#            ;;
#        "Quit")
#            break
#            ;;
#        *) echo "invalid option $REPLY";;
#
#    esac
#done