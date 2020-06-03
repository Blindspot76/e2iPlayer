#!/bin/sh
echo "rtlmost.sh: start"
cp $1/iptvupdate/custom/rtlmost.sh $2/iptvupdate/custom/rtlmost.sh
status=$?
if [ $status -ne 0 ]; then
	echo "rtlmost.sh: Critical error. The $0 file can not be copied, error[$status]."
	exit 1
fi
cp $1/hosts/hostrtlmost.py $2/hosts/
hosterr=$?
cp $1/icons/logos/rtlmostlogo.png $2/icons/logos/
logoerr=$?
cp $1/icons/PlayerSelector/rtlmost*.png $2/icons/PlayerSelector/
iconerr=$?
if [ $hosterr -ne 0 ] || [ $logoerr -ne 0 ] || [ $iconerr -ne 0 ]; then
	echo "rtlmost.sh: copy error from source hosterr[$hosterr], logoerr[$logoerr, iconerr[$iconerr]"
fi
wget --no-check-certificate https://github.com/e2iplayerhosts/rtlmost/archive/master.zip -q -O /tmp/rtlmost.zip
if [ -s /tmp/rtlmost.zip ] ; then
	unzip -q -o /tmp/rtlmost.zip -d /tmp
	cp -r -f /tmp/rtlmost-master/IPTVPlayer/hosts/hostrtlmost.py $2/hosts/
	hosterr=$?
	cp -r -f /tmp/rtlmost-master/IPTVPlayer/icons/* $2/icons/
	iconerr=$?
	if [ $hosterr -ne 0 ] || [ $iconerr -ne 0 ]; then
		echo "rtlmost.sh: copy error from rtlmost-master hosterr[$hosterr], iconerr[$iconerr]"
	fi
else
	echo "rtlmost.sh: rtlmost.zip could not be downloaded."
fi
rm -r -f /tmp/rtlmost*
echo "rtlmost.sh: exit 0"
exit 0