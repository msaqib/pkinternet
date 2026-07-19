#!/bin/bash
# sync.sh — pull then push all changes
cd ~/pkinternet
git add -A
git stash
git pull --rebase origin main
git stash pop
git add -A
git commit -m "${1:-update}"
git push origin main

#use it: ./sync.sh "Add routing map and hop geo annotation"
