#!/bin/bash

if [[ -f result && -f roundtriptime ]]; then
    echo "delete result"
    rm result RTT
fi
ag RTT --filename debug1.txt debug2.txt > result # find RTT
awk '{print $NF}' result > RTT # extract RTT
