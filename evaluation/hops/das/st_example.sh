#!/usr/bin/env bash

send_screen() {
    ssh "node0"$1 /bin/bash << EOF
    pkill screen; # kill the session
    screen -dm -S test; # create a detached new session
    screen -S test -X stuff "ls;ls^M";# send ls
    screen -S test -X stuff "pwd^M";# send ls
EOF
ssh -t "node0"$1 screen -r test  # need a terminal to reattach the session
}

send_tmux() {
	echo "node0"$1
	ssh "node061"$1 /bin/bash <<EOF
	#tmux kill-session -t demo;
	tmux new -s demo -d;
	tmux send-keys -t demo "ls;pwd" C-m;
EOF
	ssh -t "node0"$1 tmux attach -t "demo" 
}
