#!/bin/sh

cat "$2/iptvupdate/updatemainwindow.py" | grep "e2iplayer-master"
status=$?
if [ $status -ne 0 ]; then
	cp "$1/iptvupdate/custom/update.sh" "$2/iptvupdate/custom/update.sh"
	status=$?
	if [ $status -ne 0 ]; then
		echo "Błąd krytyczny. Plik update.sh nie może zostać skopiowany, error[$status]."
		exit 1
	fi

	cp "$1/iptvupdate/updatemainwindow.py" "$2/iptvupdate/"
	status=$?
	if [ $status -ne 0 ]; then
		echo "Uwaga nie udało się skopiować updatemainwindow.py ze starej wersji, error[$status]."
		exit 1
	fi
	
	cp "$1/components/iptvconfigmenu.py" "$2/components/"
	status=$?
	if [ $status -ne 0 ]; then
		echo "Uwaga nie udało się skopiować iptvconfigmenu.py ze starej wersji, error[$status]."
		exit 1
	fi
fi
echo "Wykonywanie update.sh zakończone sukcesem."
exit 0