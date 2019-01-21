#!/usr/bin/env bash
# set -u
# options
#    curl -s -S https://www.nyannko.tk/speedtest/${file} -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"
#    curl -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"
#    curl -s -S https://www.nyannko.tk/speedtest/file100m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"
#    curl -s -S https://www.nyannko.tk/speedtest/file500m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"
#for file in $@; do

## test download 10 times
for i in `seq 1 10`; do
    # normal
    res=`curl -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"`
    echo "normal: $res" >> speed.txt
    #mp
    res=`curl --proxy socks5h://127.0.0.1:40000 -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"`
    echo "mp: $res" >> speed.txt
    #ss
    res=`curl --proxy socks5h://127.0.0.1:7000 -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"`
    echo "ss: $res" >> speed.txt
    #v2
    res=`curl --proxy socks5h://127.0.0.1:1080 -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"`
    echo "v2: $res" >> speed.txt
done


#diff hops.. then
for i in `seq 1 10`; do
    res=`curl --proxy socks5h://127.0.0.1:40000 -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"`
    echo "mp: $res" >> speed.txt
done

#oc test..then
#ovpn test.. then
echo "#oc" >> speed.txt
for i in `seq 1 10`; do
    res=`curl -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"`
    echo "normal: $res" >> speed.txt
done

echo "#ovpn" >> speed.txt
for i in `seq 1 10`; do
    res=`curl -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"`
    echo "normal: $res" >> speed.txt
done

#tor test.. then
for i in `seq 1 10`; do
    res=`curl --proxy socks5h://127.0.0.1:9050 -s -S https://www.nyannko.tk/speedtest/file10m -o /dev/null -w "%{time_total},%{size_download},%{speed_download}\n"`
    echo "v2: $res" >> speed3.txt
done



