#!/bin/bash

for f in g36-*.py
do
    ttl=${f/[.]py/.ttl}
    echo $ttl
    python "$f" | python sort_turtle_file.py > "$ttl"
done
