#!/bin/bash

git push origin --delete $1
git branch -d $1

exit
