#!/bin/sh
cd /tmp
MYPATH="/home/michal/dev/coronavirus/cz-covid-maps/"
wget https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani-profese.csv
rm "$MYPATH"orp/ockovani-profese.csv
mv /tmp/ockovani-profese.csv "$MYPATH"orp/ockovani-profese.csv

git -C $MYPATH pull
/home/michal/dev/anaconda3/bin/python3 "$MYPATH"orp/pivot.py
git -C $MYPATH add orp/orp.csv
DATE=$(date -Iseconds)
git -C $MYPATH commit -m "ORP updated ${DATE}"
git -C $MYPATH push