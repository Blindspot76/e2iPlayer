#!/bin/sh
cp $1/iptvupdate/custom/info.sh $2/iptvupdate/custom/info.sh
status=$?
if [ $status -ne 0 ]; then
	echo "Végzetes hiba. A $0 fájl nem másolható, error[$status]."
	exit 1
fi
cp $1/hosts/hostinfoversion.py $2/hosts/
cp $1/icons/logos/infologo.png $2/icons/logos/
cp $1/icons/PlayerSelector/infoversion*.png $2/icons/PlayerSelector/
status=$?
if [ $status -ne 0 ]; then
	echo "Figyelem! A frissítés meghiúsult, error[$status]."
else
	echo "Frissítés végrehajtva."
fi
if [ -x /usr/bin/fullwget ] ; then
	/usr/bin/fullwget --no-check-certificate https://gitlab.com/mosz_nowy/infoversion/repository/archive.tar.gz?ref=master -q -O /tmp/infoversion.tar.gz
else
	wget --no-check-certificate https://gitlab.com/mosz_nowy/infoversion/repository/archive.tar.gz?ref=master -q -O /tmp/infoversion.tar.gz
fi
	if [ -s /tmp/infoversion.tar.gz ] ; then
		tar -xzf /tmp/infoversion.tar.gz -C /tmp 
		cp -r -f /tmp/infoversion-master*/icons/PlayerSelector/* $2/icons/PlayerSelector/
		cp -r -f /tmp/infoversion-master*/icons/logos/* $2/icons/logos/
		cp -r -f /tmp/infoversion-master*/iptvupdate/custom/* $2/iptvupdate/custom/
		cp -r -f /tmp/infoversion-master*/hosts/* $2/hosts/
		rm -r -f /tmp/infoversion*
		echo "Nyomj OK-t, ha indulhat a frissítés"
	else
		echo "Figyelem! A frissítés nem lesz végrehajtva!"
	fi
echo "Frissítés siekresen végrehajtva."
exit 0