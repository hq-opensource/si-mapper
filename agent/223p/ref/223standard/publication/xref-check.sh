#!/bin/bash

# change this to where the index.html file will be stored
# The generated HTML file is in html-doc-gen/static/index.html
export S223_DOC_HOST="https://223p.gtf.fyi"

ttl_files="./223standard.ttl $(find ../models ../vocab ../inference ../validation -name '*.ttl')"

#
# make sure there are files
if [[ "$ttl_files" == "" ]]
then
    echo 'No .ttl files found'
    exit 1
fi

# dump out the clauses
python3 xref-check.py $ttl_files
