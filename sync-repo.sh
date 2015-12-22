#!/bin/bash
cd ~/iptvplayer-GitLab-j00zek-fork
#git remote add original git@gitlab.com:iptvplayer-for-e2/iptvplayer-for-e2.git
git fetch original
git merge original/master
git push