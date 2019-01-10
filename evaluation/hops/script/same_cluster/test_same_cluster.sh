#!/bin/bash

reserve_normal() {
	reserve_list=(1)
	normal_nodes=()
	for ((i=0;i<${#reserve_list[@]};++i));
	do
		# detect the last row
		# the start of the main logic
		preserve -t 02:00:00 -# ${reserve_list[i]} 
		sleep 3
		nodes=($(preserve -long-list | grep gshi | awk 'END{for(i=9;i<=NF;++i)print $i}' ))
		hop_id=$(preserve -long-list | grep gshi | awk 'END{{print $1}}')
		for n in "${nodes[@]}"
		do
			normal_nodes+=(${n})
		done
	done
}

#hop0
reserve_hop0() {
	hop0_nodes=()
	preserve -t 01:00:00 -# 1
	sleep 3
	nodes=($(preserve -long-list | grep gshi |awk 'END{for(i=9;i<=NF;++i)print $i}' ))
	hop0_id=$(preserve -long-list | grep gshi | awk 'END{{print $1}}')
	for n in "${nodes[@]}"
	do
		hop0_nodes+=(${n})
	done
}

#hop1
reserve_hop1() {
	hop1_nodes=()
	preserve -t 01:00:00 -# 2
	sleep 3
	nodes=($(preserve -long-list | grep gshi |awk 'END{for(i=9;i<=NF;++i)print $i}' ))
	hop1_id=$(preserve -long-list | grep gshi | awk 'END{{print $1}}')
	for n in "${nodes[@]}"
	do
		hop1_nodes+=(${n})
	done
}

#hop2
reserve_hop2() {
	hop2_nodes=()
	preserve -t 01:00:00 -# 4
	sleep 3
	nodes=($(preserve -long-list | grep gshi |awk 'END{for(i=9;i<=NF;++i)print $i}' ))
	hop2_id=$(preserve -long-list | grep gshi | awk 'END{{print $1}}')
	for n in "${nodes[@]}"
	do
		hop2_nodes+=(${n})
	done
}

#hop3
reserve_hop3() {
	hop3_nodes=()
	preserve -t 01:00:00 -# 5
	sleep 5
	nodes=($(preserve -long-list | grep gshi |awk 'END{for(i=9;i<=NF;++i)print $i}' ))
	hop3_id=$(preserve -long-list | grep gshi | awk 'END{{print $1}}')
	
	for n in "${nodes[@]}"
	do
		hop3_nodes+=(${n})
	done
}

check_nodes_num() {
	echo "normal nodes"
	for j in "${normal_nodes[@]}"
	do
		echo $j
	done
	
	echo "hop0 nodes"
	for j in "${hop0_nodes[@]}"
	do
		echo $j
	done
	
	echo "hop1 nodes"
	for j in "${hop1_nodes[@]}"
	do
		echo $j
	done
	
	echo "hop2 nodes"
	for j in "${hop2_nodes[@]}"
	do
		echo $j
	done
	
	echo "hop3 nodes"
	for j in "${hop3_nodes[@]}"
	do
		echo $j
	done
}

cancel_current_reserved_nodes() {
	preserve -c $hop_id
	preserve -c $hop0_id
	preserve -c $hop1_id
	preserve -c $hop2_id
	preserve -c $hop3_id
}

cancel_all_reserved_nodes() {
	cancel_id=($(preserve -long-list | grep gshi | awk '{{print $1}}'))
	for cid in "${cancel_id[@]}"
	do
		preserve -c $cid
	done
}

eval_normal() {
	normal_node=${normal_nodes[0]}
	echo $normal_node
	command="cd \$e;timeout 1h bash normal.sh"
	send_screen $normal_node eval $command
}

attach_normal() {
    ssh -t $normal_node screen -r eval
#	ssh -t $normal_node tmux attach -t "eval" -d #ctrlb + d then
}

kill_task() {
	# check
	for node in "$@"
	do
		ssh -t $node tmux kill-session -t "run"
		ssh -t $node tmux kill-session -t "eval"
	done
}

########## test #################
test_normal() {
	reserve_normal
	eval_normal
#	attach_normal
#	kill_task $normal_node
}

send_screen() {
	ssh $1 /bin/bash << EOF
	source ~/.bashrc
	screen -dm -S $2
	screen -S $2 -X stuff "${@:3}^M"
EOF
#	ssh -t $1 tmux new -s $2 -d;
#	ssh -t $1 tmux send-keys -t $2 "${@:3}" C-m;
#	ssh -t $1 tmux attach -t $2 -d
}


########## test hop0 #############
test_hop0() {
	# usage
	arr=("http://www.google.com" "http://www.youtube.com" "http://www.instagram.com" "http://www.facebook.com" "http://www.twitter.com")
	reserve_hop0
	node=${hop0_nodes[0]}
	run_command="cd \$w;for i in `seq 1 5`; do timeout 5s python multiproxy.py --client 1 --server 1; done"
	eval_command="cd \$e;for i in {"a" "b" "c")}; do timeout 1h bash hop0.sh; done"

	echo $node
	echo $run_command
	send_screen $node "run" $run_command
	send_screen $node "eval" $eval_command
 	#kill_task $node
}

########## test hop1 #############
test_hop1() {
	reserve_hop1

	client_node=${hop1_nodes[0]}
	server_node=${hop1_nodes[1]}

	client_run_command="cd \$w;timeout 1h python multiproxy1.py --client 1"
	server_run_command="cd \$w;timeout 1h python multiproxy1.py --server 1"

	client_eval_command="cd \$e;timeout 1h bash hop1.sh"

	send_screen $client_node run $client_run_command
	send_screen $server_node run $server_run_command

	send_screen $client_node "eval" $client_eval_command

	#kill_task $client_node $server_node
}

########## test hop2 #############
test_hop2() {
	reserve_hop2

	client_node=${hop2_nodes[0]}
	forwarder_node=${hop2_nodes[1]}
	server_node=${hop2_nodes[2]}
	helper_node=${hop2_nodes[3]}

	client_run_command="cd \$w;timeout 1h python multiproxy2.py --client 1"
	forwarder_run_command="cd \$w;timeout 1h python multiproxy2.py --forwarder 1"
	server_run_command="cd \$w;timeout 1h python multiproxy2.py --server 1"

	client_eval_command="cd \$e;timeout 1h bash hop2.sh"

	send_screen $client_node "run" $client_run_command
	send_screen $forwarder_node "run" $forwarder_run_command
	send_screen $helper_node "run" $forwarder_run_command
	send_screen $server_node "run" $server_run_command

	send_screen $client_node "eval" $client_eval_command

	#kill_task $client_node $server_node
}

########## test hop3 #############
test_hop3() {
	reserve_hop3

	client_node=${hop3_nodes[0]}
	forwarder_node1=${hop3_nodes[1]}
	forwarder_node2=${hop3_nodes[2]}
	server_node=${hop3_nodes[3]}
	helper_node=${hop3_nodes[4]}

	client_run_command="cd \$w;timeout 1h python multiproxy3.py --client 1"
	forwarder_run_command="cd \$w;timeout 1h python multiproxy3.py --forwarder 1"
	server_run_command="cd \$w;timeout 1h python multiproxy3.py --server 1"

	client_eval_command="cd \$e;timeout 1h bash hop3.sh"

	send_screen $client_node "run" $client_run_command
	send_screen $forwarder_node1 "run" $forwarder_run_command
	send_screen $forwarder_node2 "run" $forwarder_run_command
	send_screen $helper_node "run" $forwarder_run_command
	send_screen $server_node "run" $server_run_command

	send_screen $client_node "eval" $client_eval_command

}

########## test_normal
cancel_all_reserved_nodes
test_normal
test_hop0
test_hop1
test_hop2
test_hop3
#send_screen "node" "run" "cd \$e;timeout 2h bash hop3.sh"