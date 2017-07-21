from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem, ArticleContent, CFavItem

WebInterfaceVersion = '0.3'
MaxLogLinesToShow = 1000
configsHTML = {}
excludedCFGs = ['fakeUpdate','fakeHostsList','fakExtMoviePlayerList']
activeHostsHTML = {}
activeHost = {}
retObj = None
currItem = {}

def initActiveHost( hostName ):
	global activeHost
	global retObj
	global currItem
	activeHost = {}
	retObj = None
	currItem = {}
	
	if hostName is None:
		pass
	else:
		
		activeHost['Name'] = hostName
		_temp = __import__('Plugins.Extensions.IPTVPlayer.hosts.host' + hostName, globals(), locals(), ['IPTVHost'], -1)
		activeHost['Title'] = _temp.gettytul()
		activeHost['Obj'] = _temp.IPTVHost()
		activeHost['PIC'] = activeHost['Obj'].getLogoPath().value[0]
		activeHost['SupportedTypes'] = activeHost['Obj'].getSupportedFavoritesTypes().value
		activeHost['PathLevel'] = 1
		activeHost['Status'] =  ''
		retObj = activeHost['Obj'].getInitList()
		activeHost['ListType'] = 'ListForItem'
	return

def isActiveHostInitiated():
	global activeHost
	if len(activeHost.keys()) == 0:
		return False
	else:
		return True

def isCurrentItemSelected():
	global currItem
	if len(currItem.keys()) == 0:
		return False
	else:
		return True
