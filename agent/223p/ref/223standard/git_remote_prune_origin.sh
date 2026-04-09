#!/bin/bash

# prunes tracking branches not on the remote
git remote prune origin

# delete local branches that are 'gone'
git branch -vv | grep ': gone[]]' | awk '{ print $1 }' | xargs git branch -v -D

