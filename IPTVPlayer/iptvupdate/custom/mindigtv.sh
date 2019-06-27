#!/bin/sh
echo "mindigtv.sh: start"
cp $1/iptvupdate/custom/mindigtv.sh $2/iptvupdate/custom/mindigtv.sh
status=$?
if [ $status -ne 0 ]; then
	echo "mindigtv.sh: Critical error. The $0 file can not be copied, error[$status]."
	exit 1
fi
cp $1/hosts/hostmindigtv.py $2/hosts/
hosterr=$?
cp $1/icons/logos/mindigtvlogo.png $2/icons/logos/
logoerr=$?
cp $1/icons/PlayerSelector/mindigtv*.png $2/icons/PlayerSelector/
iconerr=$?
if [ $hosterr -ne 0 ] || [ $logoerr -ne 0 ] || [ $iconerr -ne 0 ]; then
	echo "mindigtv.sh: copy error from source hosterr[$hosterr], logoerr[$logoerr, iconerr[$iconerr]"
fi
wget --no-check-certificate https://github.com/e2iplayerhosts/mindigtv/archive/master.zip -q -O /tmp/mindigtv.zip
if [ -s /tmp/mindigtv.zip ] ; then
	unzip -q -o /tmp/mindigtv.zip -d /tmp
	cp -r -f /tmp/mindigtv-master/IPTVPlayer/hosts/hostmindigtv.py $2/hosts/
	hosterr=$?
	cp -r -f /tmp/mindigtv-master/IPTVPlayer/icons/* $2/icons/
	iconerr=$?
	if [ $hosterr -ne 0 ] || [ $iconerr -ne 0 ]; then
		echo "mindigtv.sh: copy error from mindigtv-master hosterr[$hosterr], iconerr[$iconerr]"
	fi
else
	echo "mindigtv.sh: mindigtv.zip could not be downloaded."
fi
rm -r -f /tmp/mindigtv*
echo "mindigtv.sh: exit 0"
exit 0