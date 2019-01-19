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
                 "eu2"
                )

declare -a sessions=(
                      "run1"
                      "eval1"
                      "run2"
                      "run3"
                      "eval2"
                      "eval3"
                     )

send_screen() {
    check_param $@
    ## node ip; session name; command
    echo "ssh to node $1"
	ssh $1 /bin/bash << EOF
	source ~/.bashrc
	screen -dm -S $2
	sleep 0.2
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
    eval_dir="/ipv8t/evaluation/hops/script/global"
    run_dir="/ipv8t/socks5_ipv8/hops"
    client_node=${ips[0]}
    server_node=${ips[3]}

    client_run_command="$run_dir; timeout $max_total_time python multiproxy1.py --client 1"
    server_run_command="$run_dir; timeout $max_total_time python multiproxy1.py --server 1"

    client_eval_command="$eval_dir; timeout $max_total_time bash eval_curl_hop.sh hop1 40000"

    echo $client_node
    echo $server_node
    echo $client_run_command
    echo $client_eval_command
    echo $server_run_command

    send_screen $client_node run1 $client_run_command
    echo "client run cmd sent"
    send_screen $server_node run1 $server_run_command
    echo "server run cmd sent"

    send_screen $client_node eval1 $client_eval_command
    echo "client eval cmd sent"
}

######################### test hop2 #################################
test_hop2d() {
    max_total_time=55m

    eval_dir="/ipv8t/evaluation/hops/script/global"
    run_dir="/ipv8t/socks5_ipv8/hops"
    client_node=${ips[0]}       # cn
    forwarder_node=${ips[1]}    # tw
    helper_node=${ips[2]}       # eu
    server_node=${ips[3]}       # am

    client_run_command="$run_dir; timeout $max_total_time python multiproxy2.py --client 1"
    forwarder_run_command="$run_dir; timeout $max_total_time python multiproxy2.py --forwarder 1"
    server_run_command="$run_dir; timeout $max_total_time python multiproxy2.py --server 1"

    client_eval_command="$eval_dir; timeout $max_total_time bash eval_curl_hop.sh hop2 40001"

    send_screen $client_node run2 $client_run_command
    echo "client run cmd sent"

    send_screen $forwarder_node run2 $forwarder_run_command
    send_screen $helper_node run2 $forwarder_run_command
    echo "f and h sent"

    send_screen $server_node run2 $server_run_command
    echo "server run cmd sent"

    send_screen $client_node eval2 $client_eval_command
    echo "client eval cmd sent"
}

######################### test hop3 #################################
test_hop3d() {
    max_total_time=55m

    eval_dir="/ipv8t/evaluation/hops/script/global"
    run_dir="/ipv8t/socks5_ipv8/hops"
    client_node=${ips[0]}
    helper_node=${ips[4]}
    forwarder_node2=${ips[2]}
    server_node=${ips[3]}
    forwarder_node1=${ips[1]}

    client_run_command="$run_dir; timeout $max_total_time python multiproxy3.py --client 1"
    forwarder_run_command="$run_dir; timeout $max_total_time python multiproxy3.py --forwarder 1"
    server_run_command="$run_dir; timeout $max_total_time python multiproxy3.py --server 1"

    client_eval_command="$eval_dir; timeout $max_total_time bash eval_curl_hop.sh hop3 40002"

    send_screen $client_node run3 $client_run_command
    echo "client run cmd sent"

    send_screen $forwarder_node1 run3 $forwarder_run_command
    send_screen $forwarder_node2 run3 $forwarder_run_command
    send_screen $helper_node run3 $forwarder_run_command
    echo "f and h sent"

    send_screen $server_node run3 $server_run_command
    echo "server run cmd sent"

#    send_screen $client_node eval3 $client_eval_command
    echo "client eval cmd sent"
}

send_kill() {
    ## node ip
    echo "ssh to node $1"
	ssh $1 /bin/bash << EOF
	pkill screen
EOF
}

kill_all_screen() {
    for node in "${ips[@]}"; do
        send_kill $node
    done
}

kill_all_screen
#test_hop1d
#test_hop2d
#test_hop3d