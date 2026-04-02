#!/bin/bash

# save the current branch
current=$(git rev-parse --abbrev-ref HEAD)

# get a list of the branches and trim out the '*' in front of
# the current branch
for branch in $(git branch --list | tr " " "\n" | grep -v '^[*]')
do
    git remote update > /dev/null

    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u})
    BASE=$(git merge-base @ @{u})

    if [ $LOCAL = $REMOTE ]; then
        echo "$branch: Up-to-date"
    elif [ $LOCAL = $BASE ]; then
        echo "$branch: Need to pull"
    elif [ $REMOTE = $BASE ]; then
        echo "$branch: Need to push"
    else
        echo "$branch: Diverged"
    fi
done

# restore the branch
git checkout $current

