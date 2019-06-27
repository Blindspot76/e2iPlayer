#!/bin/sh
echo "sonyplayer.sh: start"
cp $1/iptvupdate/custom/sonyplayer.sh $2/iptvupdate/custom/sonyplayer.sh
status=$?
if [ $status -ne 0 ]; then
	echo "sonyplayer.sh: Critical error. The $0 file can not be copied, error[$status]."
	exit 1
fi
cp $1/hosts/hostsonyplayer.py $2/hosts/
hosterr=$?
cp $1/icons/logos/sonyplayerlogo.png $2/icons/logos/
logoerr=$?
cp $1/icons/PlayerSelector/sonyplayer*.png $2/icons/PlayerSelector/
iconerr=$?
if [ $hosterr -ne 0 ] || [ $logoerr -ne 0 ] || [ $iconerr -ne 0 ]; then
	echo "sonyplayer.sh: copy error from source hosterr[$hosterr], logoerr[$logoerr, iconerr[$iconerr]"
fi
wget --no-check-certificate https://github.com/e2iplayerhosts/sonyplayer/archive/master.zip -q -O /tmp/sonyplayer.zip
if [ -s /tmp/sonyplayer.zip ] ; then
	unzip -q -o /tmp/sonyplayer.zip -d /tmp
	cp -r -f /tmp/sonyplayer-master/IPTVPlayer/hosts/hostsonyplayer.py $2/hosts/
	hosterr=$?
	cp -r -f /tmp/sonyplayer-master/IPTVPlayer/icons/* $2/icons/
	iconerr=$?
	if [ $hosterr -ne 0 ] || [ $iconerr -ne 0 ]; then
		echo "sonyplayer.sh: copy error from sonyplayer-master hosterr[$hosterr], iconerr[$iconerr]"
	fi
else
	echo "sonyplayer.sh: sonyplayer.zip could not be downloaded."
fi
rm -r -f /tmp/sonyplayer*
echo "sonyplayer.sh: exit 0"
exit 0