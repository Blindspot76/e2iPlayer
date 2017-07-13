import os
from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from webSite import StartPage, redirectionPage, hostsPage, downloaderPage, settingsPage, logsPage
from twisted.web import static

from Plugins.Extensions.IPTVPlayer.tools.iptvtools import GetPluginDir
from __init__ import getWebInterfaceVersion

IPTVwebRoot = static.File(GetPluginDir()) #webRoot = pluginDir to get access to icons and logos
IPTVwebRoot.putChild("", StartPage())
IPTVwebRoot.putChild("hosts", hostsPage())
IPTVwebRoot.putChild("downloader", downloaderPage())
IPTVwebRoot.putChild("settings", settingsPage())
IPTVwebRoot.putChild("logs", logsPage())

def checkForFC():
	ret = False
	if os.path.exists(resolveFilename(SCOPE_PLUGINS,'Extensions/OpenWebif/controllers/base.pyo')):
		myfileName = resolveFilename(SCOPE_PLUGINS,'Extensions/OpenWebif/controllers/base.pyo')
	elif os.path.exists(resolveFilename(SCOPE_PLUGINS,'Extensions/OpenWebif/controllers/base.pyc')):
		myfileName = resolveFilename(SCOPE_PLUGINS,'Extensions/OpenWebif/controllers/base.pyc')
	else:
		return False
	
	try:
		with open (myfileName, "r") as myfile:
			data = myfile.read()
			myfile.close()
		if data.find('fancontrol') > 0 and data.find('iptvplayer') < 0:
			ret = True
			data = None
	except Exception:
		pass
	      
	data = None
	return ret
	      
# registration for old webinterface
if os.path.exists(resolveFilename(SCOPE_PLUGINS,'Extensions/WebInterface/web/external.xml')):
	try:
		addExternalChild( ("iptvplayer", IPTVwebRoot, "IPTVPlayer", getWebInterfaceVersion(), True) )
	except Exception:
		addExternalChild( ("iptvplayer", IPTVwebRoot) )
# registration for openwebif
elif os.path.exists(resolveFilename(SCOPE_PLUGINS,'Extensions/OpenWebif/pluginshook.src')):
	# Old openwebif version has a bug and does not populate links to all properly registered web addons except fancontrol
	# see: https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/pull/628/commits/bb7c9e46c0b896d7fe53485aaf43d08f9ba642b8
	#  A HACK: we will canibalize fancontrol entry point (if not installed) to present IPTVplayer option on the web
	if checkForFC() == True and not os.path.exists(resolveFilename(SCOPE_PLUGINS,'Extensions/FanControl2/FC2webSite.pyo')):
		fcRoot = static.File(GetPluginDir('Web/'))
		fcRoot.putChild("", redirectionPage())
		try:
			addExternalChild( ("fancontrol", fcRoot, "IPTV Player", getWebInterfaceVersion()) )
			addExternalChild( ("iptvplayer", IPTVwebRoot, None, None) )
		except Exception:
			pass
	else: #user still can use IPTV web interface, but need to mark URL manually
		try:
			addExternalChild( ("iptvplayer", IPTVwebRoot, "IPTVPlayer", getWebInterfaceVersion()) )
		except Exception:
			pass
else:
	print "No known webinterface available"
