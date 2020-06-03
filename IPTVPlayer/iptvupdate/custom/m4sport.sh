#!/bin/sh
echo "m4sport.sh: start"
cp $1/iptvupdate/custom/m4sport.sh $2/iptvupdate/custom/m4sport.sh
status=$?
if [ $status -ne 0 ]; then
	echo "m4sport.sh: Critical error. The $0 file can not be copied, error[$status]."
	exit 1
fi
cp $1/hosts/hostm4sport.py $2/hosts/
hosterr=$?
cp $1/icons/logos/m4sportlogo.png $2/icons/logos/
logoerr=$?
cp $1/icons/PlayerSelector/m4sport*.png $2/icons/PlayerSelector/
iconerr=$?
if [ $hosterr -ne 0 ] || [ $logoerr -ne 0 ] || [ $iconerr -ne 0 ]; then
	echo "m4sport.sh: copy error from source hosterr[$hosterr], logoerr[$logoerr, iconerr[$iconerr]"
fi
wget --no-check-certificate https://github.com/e2iplayerhosts/m4sport/archive/master.zip -q -O /tmp/m4sport.zip
if [ -s /tmp/m4sport.zip ] ; then
	unzip -q -o /tmp/m4sport.zip -d /tmp
	cp -r -f /tmp/m4sport-master/IPTVPlayer/hosts/hostm4sport.py $2/hosts/
	hosterr=$?
	cp -r -f /tmp/m4sport-master/IPTVPlayer/icons/* $2/icons/
	iconerr=$?
	if [ $hosterr -ne 0 ] || [ $iconerr -ne 0 ]; then
		echo "m4sport.sh: copy error from m4sport-master hosterr[$hosterr], iconerr[$iconerr]"
	fi
else
	echo "m4sport.sh: m4sport.zip could not be downloaded."
fi
rm -r -f /tmp/m4sport*
echo "m4sport.sh: exit 0"
exit 0