#!/usr/bin/env bash
# test curl times of different hops between headnodes
# run in own computer

# head node ip address
# declare -a ips=( "130.37.199.8"
#                 "132.229.137.11"
#                 "146.50.10.226"
#                 "131.180.125.22"
#                 "146.50.10.227"
#                 "192.87.1.33" )

# declare -a ips=( "fs0"
#                 "fs1"
#                 "fs2"
#                 "fs3"
#                 "fs4"
#                 "fs5"
#                )

declare -a ips=( "cn"
                 "tw"
                 "eu"
                 "am"
                )

declare -a sessions=( "run"
                      "eval"
                     )

send_screen() {
    check_param $@
    ## node ip; session name; command
    echo "ssh to node $1"
	ssh $1 /bin/bash << EOF
#	pkill -u `id -u gshi` screen # kill my own process
	source ~/.bashrc
	screen -dm -S $2

	screen -S $2 -X stuff "cd /home/umr${@:3}^M"
EOF
}

check_param() {
    # check if ips and sessions match
    if [[ ! " ${ips[@]} " =~ " $1 " || ! " ${sessions[@]} " =~ " $2 " ]]; then
        echo "input wrong"
        exit 1
    else
        echo $1
        echo $2
        echo "cd ${HOME}${@:3}^M"
    fi
}

######################### test hop1 #################################
test_hop1d() {
    max_total_time=55m
#    run_dir="\$w"
#    eval_dir="\$e"
    eval_dir="/ipv8t/evaluation/hops"
    run_dir="/ipv8t/socks5_ipv8/hops"
    client_node=${ips[0]}
    server_node=${ips[3]}

    client_run_command="$run_dir; timeout $max_total_time python multiproxy1.py --client 1"
    server_run_command="$run_dir; timeout $max_total_time python multiproxy1.py --server 1"

    client_eval_command="$eval_dir; timeout $max_total_time bash eval_curl_hop.sh hop1"

    echo $client_node
    echo $server_node
    echo $client_run_command
    echo $client_eval_command
    echo $server_run_command

    send_screen $client_node run $client_run_command
    echo "client run cmd sent"
    send_screen $server_node run $server_run_command
    echo "server run cmd sent"

    send_screen $client_node eval $client_eval_command
    echo "client eval cmd sent"
}

######################### test hop2 #################################
test_hop2d() {
    max_total_time=55m

    eval_dir="/ipv8t/evaluation/hops"
    run_dir="/ipv8t/socks5_ipv8/hops"
    client_node=${ips[0]}
    forwarder_node=${ips[1]}
    helper_node=${ips[2]}
    server_node=${ips[3]}

    client_run_command="$run_dir; timeout $max_total_time python multiproxy2.py --client 1"
    forwarder_run_command="$run_dir; timeout $max_total_time python multiproxy2.py --forwarder 1"
    server_run_command="$run_dir; timeout $max_total_time python multiproxy2.py --server 1"

    client_eval_command="$eval_dir; timeout $max_total_time bash eval_curl_hop.sh hop1"

    send_screen $client_node run $client_run_command
    echo "client run cmd sent"

    send_screen $forwarder_node run $forwarder_run_command
    send_screen $helper_node run $forwarder_run_command
    echo "f and h sent"

    send_screen $server_node run $server_run_command
    echo "server run cmd sent"

    send_screen $client_node eval $client_eval_command
    echo "client eval cmd sent"
}

#test_hop1d
test_hop2d

