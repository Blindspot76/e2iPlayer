#!/bin/sh
echo "mytvtelenor.sh: start"
cp $1/iptvupdate/custom/mytvtelenor.sh $2/iptvupdate/custom/mytvtelenor.sh
status=$?
if [ $status -ne 0 ]; then
	echo "mytvtelenor.sh: Critical error. The $0 file can not be copied, error[$status]."
	exit 1
fi
cp $1/hosts/hostmytvtelenor.py $2/hosts/
hosterr=$?
cp $1/icons/logos/mytvtelenorlogo.png $2/icons/logos/
logoerr=$?
cp $1/icons/PlayerSelector/mytvtelenor*.png $2/icons/PlayerSelector/
iconerr=$?
if [ $hosterr -ne 0 ] || [ $logoerr -ne 0 ] || [ $iconerr -ne 0 ]; then
	echo "mytvtelenor.sh: copy error from source hosterr[$hosterr], logoerr[$logoerr, iconerr[$iconerr]"
fi
wget --no-check-certificate https://github.com/e2iplayerhosts/mytvtelenor/archive/master.zip -q -O /tmp/mytvtelenor.zip
if [ -s /tmp/mytvtelenor.zip ] ; then
	unzip -q -o /tmp/mytvtelenor.zip -d /tmp
	cp -r -f /tmp/mytvtelenor-master/IPTVPlayer/hosts/hostmytvtelenor.py $2/hosts/
	hosterr=$?
	cp -r -f /tmp/mytvtelenor-master/IPTVPlayer/icons/* $2/icons/
	iconerr=$?
	if [ $hosterr -ne 0 ] || [ $iconerr -ne 0 ]; then
		echo "mytvtelenor.sh: copy error from mytvtelenor-master hosterr[$hosterr], iconerr[$iconerr]"
	fi
else
	echo "mytvtelenor.sh: mytvtelenor.zip could not be downloaded."
fi
rm -r -f /tmp/mytvtelenor*
echo "mytvtelenor.sh: exit 0"
exit 0