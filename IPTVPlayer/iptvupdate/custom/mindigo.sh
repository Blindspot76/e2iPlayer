#!/bin/sh
echo "mindigo.sh: start"
cp $1/iptvupdate/custom/mindigo.sh $2/iptvupdate/custom/mindigo.sh
status=$?
if [ $status -ne 0 ]; then
	echo "mindigo.sh: Critical error. The $0 file can not be copied, error[$status]."
	exit 1
fi
cp $1/hosts/hostmindigo.py $2/hosts/
hosterr=$?
cp $1/icons/logos/mindigologo.png $2/icons/logos/
logoerr=$?
cp $1/icons/PlayerSelector/mindigo*.png $2/icons/PlayerSelector/
iconerr=$?
if [ $hosterr -ne 0 ] || [ $logoerr -ne 0 ] || [ $iconerr -ne 0 ]; then
	echo "mindigo.sh: copy error from source hosterr[$hosterr], logoerr[$logoerr, iconerr[$iconerr]"
fi
wget --no-check-certificate https://github.com/e2iplayerhosts/mindigo/archive/master.zip -q -O /tmp/mindigo.zip
if [ -s /tmp/mindigo.zip ] ; then
	unzip -q -o /tmp/mindigo.zip -d /tmp
	cp -r -f /tmp/mindigo-master/IPTVPlayer/hosts/hostmindigo.py $2/hosts/
	hosterr=$?
	cp -r -f /tmp/mindigo-master/IPTVPlayer/icons/* $2/icons/
	iconerr=$?
	if [ $hosterr -ne 0 ] || [ $iconerr -ne 0 ]; then
		echo "mindigo.sh: copy error from mindigo-master hosterr[$hosterr], iconerr[$iconerr]"
	fi
else
	echo "mindigo.sh: mindigo.zip could not be downloaded."
fi
rm -r -f /tmp/mindigo*
echo "mindigo.sh: exit 0"
exit 0