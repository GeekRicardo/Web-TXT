#!/bin/bash
path=$(dirname $(readlink -f "$0"))
if [ ! -d ${path}/pid ]; then
    mkdir ${path}/pid
fi

files=$(ls ${path}/pid)
for filename in $files
do
    kill -9 ${filename}
    rm ${path}/pid/${filename}
done

nohup sudo python3 ${path}/main.py > /dev/null 2>&1 echo  $! > ${path}/pid/$!
