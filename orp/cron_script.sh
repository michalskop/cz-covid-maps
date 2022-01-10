#!/bin/sh
cd /tmp
MYPATH="/home/michal/dev/coronavirus/cz-covid-maps/"
git -C $MYPATH pull
rm "$MYPATH"orp/ockovani-profese.csv
wget https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani-profese.csv
mv /tmp/ockovani-profese.csv "$MYPATH"orp/ockovani-profese.csv
