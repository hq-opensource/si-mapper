#!/bin/bash

# save the current branch
current=$(git rev-parse --abbrev-ref HEAD)

# get a list of the branches and trim out the '*' in front of
# the current branch
for branch in $(git branch --list | tr " " "\n" | grep -v '^[*]')
do
    echo ""
    echo "    $branch"
    echo ""

    git checkout $branch
    git pull
done

# restore the branch
git checkout $current
