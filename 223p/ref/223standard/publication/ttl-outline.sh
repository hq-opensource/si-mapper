#!/bin/bash

g36_files="$(find ../extensions -name '*.ttl' | grep -v "SETTINGS_SP223-v1.0.ttl")"

ttl_files="$g36_files ./223standard.ttl $(find ../models ../vocab ../inference ../validation -name '*.ttl')"

#
# make sure there are files
if [[ "$ttl_files" == "" ]]
then
    echo 'No .ttl files found'
    exit 1
fi

# generate the outline
python3 ttl-outline.py 223p_publication.md $ttl_files
