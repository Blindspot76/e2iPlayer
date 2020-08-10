#!/bin/sh
echo "autohu.sh: start"
cp $1/iptvupdate/custom/autohu.sh $2/iptvupdate/custom/autohu.sh
status=$?
if [ $status -ne 0 ]; then
	echo "autohu.sh: Critical error. The $0 file can not be copied, error[$status]."
	exit 1
fi
cp $1/hosts/hostautohu.py $2/hosts/
hosterr=$?
cp $1/icons/logos/autohulogo.png $2/icons/logos/
logoerr=$?
cp $1/icons/PlayerSelector/autohu*.png $2/icons/PlayerSelector/
iconerr=$?
if [ $hosterr -ne 0 ] || [ $logoerr -ne 0 ] || [ $iconerr -ne 0 ]; then
	echo "autohu.sh: copy error from source hosterr[$hosterr], logoerr[$logoerr, iconerr[$iconerr]"
fi
wget --no-check-certificate https://github.com/e2iplayerhosts/autohu/archive/master.zip -q -O /tmp/autohu.zip
if [ -s /tmp/autohu.zip ] ; then
	unzip -q -o /tmp/autohu.zip -d /tmp
	cp -r -f /tmp/autohu-master/IPTVPlayer/hosts/hostautohu.py $2/hosts/
	hosterr=$?
	cp -r -f /tmp/autohu-master/IPTVPlayer/icons/* $2/icons/
	iconerr=$?
	if [ $hosterr -ne 0 ] || [ $iconerr -ne 0 ]; then
		echo "autohu.sh: copy error from autohu-master hosterr[$hosterr], iconerr[$iconerr]"
	fi
else
	echo "autohu.sh: autohu.zip could not be downloaded."
fi
rm -r -f /tmp/autohu*
echo "autohu.sh: exit 0"
exit 0