#!/bin/bash
files=$(ls ${path}/pid)
for filename in $files
do
    kill -9 ${filename}
    rm ${path}/pid/${filename}
done
