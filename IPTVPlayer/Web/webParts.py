#### Local imports
from __init__ import _ , getWebInterfaceVersion
from Plugins.Extensions.IPTVPlayer.version import IPTV_VERSION
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import GetHostsList, IsHostEnabled, SaveHostsOrderList, SortHostsList, GetLogoDir

#### system imports
import os

########################################################
def IncludeHEADER():
	tempText = """
<head>
	<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
	<meta http-equiv="cache-control" content="no-cache" />
	<meta http-equiv="pragma" content="no-cache" />
	<meta http-equiv="expires" content="0">
	<title>IPTVPlayer %s</title>
  <style>
    body {margin:0;}

    .topbar {overflow: hidden; background-color: #333; position: fixed; top: 0; width: 100%%; }
    .topbar a {float: left; display: block; color: #f2f2f2; text-align: center; padding: 14px 16px; text-decoration: none; font-size: 17px; }
    .bottombar {overflow: hidden; background-color: #333; position: fixed; bottom: 0; width: 100%%; }
    .bottombar a {float: left; display: block; color: #f2f2f2; text-align: center; padding: 14px 16px; text-decoration: none; font-size: 12px; }

    .main {
      padding: 16px;
      margin-top: 40px;
      margin-bottom: 40px;
      height: 1500px; /* Used in this example to enable scrolling */
    }
  </style>
</head>
""" % (IPTV_VERSION)
	return tempText
	
########################################################
def IncludeMENU():
	tempText = """
  <div class="topbar">
    <a href="http://iptvplayer.vline.pl/" target="_blank"> <img border="0" alt="IPTVPlayer" src="/iptvplayer/icons/iptvlogo.png" width="60" height="24"></a>
    <a href="/iptvplayer/" >%s</a>
    <a href="/iptvplayer/hosts" ">%s</a>
    <a href="/iptvplayer/downloader" >%s</a>
    <a href="/iptvplayer/settings" >%s</a>
    <a href="/iptvplayer/logs" >%s</a>
  </div>
  <div class="bottombar">
    <a href="https://gitlab.com/iptvplayer-for-e2/iptvplayer-for-e2/commits/master" target="_blank" >IPTVPlayer %s: <b><font color="#A9F5F2">%s</font></b></a>
    <a>, %s: <b>%s</b></a/>
  </div>
""" % ( _('Information'), _('Supported hosts'), _('Downloader status'), _('Settings'), _('Logs'), _('version'), IPTV_VERSION, _('Web interface version'), getWebInterfaceVersion() )

	return tempText

########################################################
def StartPageBodyContent():
	tempText = '<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n'
	tempText += '<form method="POST" action="--WEBBOT-SELF--">\n'
	tempText += IncludeMENU()
	tempText += '<div class="main">\n'
	tempText += '<p align="center"><b><font color="#FE642E">REMEMBER:</font></b> IPTVPlayer <b>IS ONLY</b> specialized Web browser. It does <b>NOT</b> host any materials!!!</font></b></p>'
	tempText += '</div></body>\n'
	return tempText

########################################################
def hostsPageBodyContent():
	tempText = '<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n'
	tempText += IncludeMENU()
	tempText += '<div class="main">\n<table border="1">\n<tbody>\n'
	for hostName in SortHostsList(GetHostsList()):
		# column 1 containing logo and link if available
		try:
			_temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + hostName, globals(), locals(), ['gettytul'], -1)
			title = _temp.gettytul()
		except Exception:
			continue # we do NOT use broken hosts!!!
		
		if os.path.exists(GetLogoDir('%slogo.png' % hostName)):
			logo = '<img border="0" alt="hostLogo" src="/iptvplayer/icons/logos/%slogo.png" width="120" height="40">' % hostName
		else:
			logo = title
		
		if title[:4] == 'http':
			hostNameWithURLandLOGO = '<a href="%s" target="_blank">%s</a>' % (title, logo)
		else:
			hostNameWithURLandLOGO = '<a>%s</a>' % (logo)
		# Column 2 TBD
		
		# Column 3 enable/disable host in GUI
		OnOffState = IsHostEnabled(hostName)
		if OnOffState == True:
			OnOffState = '<button type="button" disabled>%s</button>' % _('Disabled in GUI, press to enable it')
		else:
			OnOffState = '<button type="button" disabled>%s</button>' % _('Enabled in GUI, press to disable it')
		
		# Column 4 host configuration options
		try:
			_temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + hostName, globals(), locals(), ['GetConfigList'], -1)
			OptionsList = _temp.GetConfigList()
		except Exception:
			OptionsList = []
		
		#build table row
		tempText += '<tr>'
		tempText += '<td style="width:120px">%s</td>' % hostNameWithURLandLOGO
		tempText += '<td><button type="button" disabled>%s</button> </td>' % _('Use it')
		tempText += '<td>%s</td>' % OnOffState 
		if len(OptionsList) == 0:
			tempText += '<td><a>%s</a></td>' % "" # _('Host does not have configuration options')
		else:
			tempText += '<td><table>'
			for option in OptionsList:
				tempText += '<tr><td><tt>%s</tt></td><td><input type="text" name="aqq" value="%s"></td></tr>' % (option[0], option[1].value)
			tempText += '</table></td>'
		tempText += '</tr>'
	tempText += '</tbody></table></div></body>\n'
	return tempText

########################################################
def downloaderPageBodyContent():
	tempText = '<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n'
	tempText += IncludeMENU()
	tempText += '<div class="main">\n'
	tempText += '<p align="center"><b><font color="#FFE4C4">downloaderPageBodyContent</font></b></p>'
	tempText += '</div></body>\n'
	return tempText

########################################################
def settingsPageBodyContent():
	tempText = '<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n'
	tempText += IncludeMENU()
	tempText += '<div class="main">\n'
	tempText += '<p align="center"><b><font color="#FFE4C4">settingsPageBodyContent</font></b></p>'
	tempText += '</div></body>\n'
	return tempText

########################################################
def logsPageBodyContent():
	tempText = '<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n'
	tempText += IncludeMENU()
	tempText += '<div class="main">\n'
	tempText += '<p align="center"><b><font color="#FFE4C4">logoPageBodyContent</font></b></p>'
	tempText += '</div></body>\n'
	return tempText
