#!/bin/sh
cp $1/iptvupdate/custom/tsiplayer.sh $2/iptvupdate/custom/tsiplayer.sh
status=$?
if [ $status -ne 0 ]; then
	echo "Critical error. The $ 0 file can not be copied, error[$status]."
	exit 1
fi
mkdir $2/tsiplayer
mkdir $2/tsiplayer/Libs
cp $1/hosts/hosttsiplayer.py $2/hosts/
cp $1/icons/logos/tsiplayerlogo.png $2/icons/logos/
cp $1/icons/PlayerSelector/tsiplayer*.png $2/icons/PlayerSelector/ 
cp $1/tsiplayer/* $2/tsiplayer/
status=$?
if [ $status -ne 0 ]; then
	echo "Note, tsiplayer could not be copied, error[$status]."
else
	echo "duplication tsiplayer OK"
fi
if [ -x /usr/bin/fullwget ] ; then
	/usr/bin/fullwget --no-check-certificate https://gitlab.com/Rgysoft/iptv-host-e2iplayer/repository/master/archive.tar.gz -q -O /tmp/iptv-host-e2iplayer.tar.gz
else
	wget --no-check-certificate https://gitlab.com/Rgysoft/iptv-host-e2iplayer/repository/master/archive.tar.gz -q -O /tmp/iptv-host-e2iplayer.tar.gz
fi
	if [ -s /tmp/iptv-host-e2iplayer.tar.gz ] ; then
		tar -xzf /tmp/iptv-host-e2iplayer.tar.gz -C /tmp 
		cp -r -f /tmp/iptv-host-e2iplayer-master*/IPTVPlayer/icons/PlayerSelector/* $2/icons/PlayerSelector/
		cp -r -f /tmp/iptv-host-e2iplayer-master*/IPTVPlayer/icons/logos/* $2/icons/logos/
		cp -r -f /tmp/iptv-host-e2iplayer-master*/IPTVPlayer/iptvupdate/custom/* $2/iptvupdate/custom/
		cp -r -f /tmp/iptv-host-e2iplayer-master*/IPTVPlayer/hosts/* $2/hosts/
		cp -r -f /tmp/iptv-host-e2iplayer-master*/IPTVPlayer/tsiplayer/* $2/tsiplayer/
		
		rm -r -f /tmp/iptv-host-e2iplayer*

		echo "Download tsiplayer tar.gz OK"
	else
		echo "download tsiplayer tar.gz failed"
	fi
echo " $0 successful."
exit 0
