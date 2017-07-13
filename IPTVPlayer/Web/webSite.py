# -*- coding: utf-8 -*-
#### Local imports
from __init__ import _, getWebInterfaceVersion
import webParts
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import GetPluginDir

#### e2 imports
from Components.config import configfile, config
from Components.Language import language

#### system imports
import os
from twisted.web import resource, http

########################################################
def generateWebPage(pageName = 'StartPage'):
	#### Reload scripts if new version of source exists ####
	webPath = GetPluginDir(file = '/Web/')
	if os.path.exists(os.path.join(webPath, "webParts.pyo")):
		if (int(os.path.getmtime(os.path.join(webPath, "webParts.pyo"))) < 
			int(os.path.getmtime(os.path.join(webPath, "webParts.py")))):
			reload(webParts)
	else:
		reload(webParts)
	#### Building html ####
	html = '<html lang="%s">' % language.getLanguage()[:2]
	html += webParts.IncludeHEADER()
	if pageName == 'StartPage':
		html += webParts.StartPageBodyContent()
	elif pageName == 'hostsPage':
		html += webParts.hostsPageBodyContent()
	elif pageName == 'downloaderPage':
		html += webParts.downloaderPageBodyContent()
	elif pageName == 'settingsPage':
		html += webParts.settingsPageBodyContent()
	elif pageName == 'logsPage':
		html += webParts.logsPageBodyContent()
	else:
		html += '<body bgcolor=\"#666666\" text=\"#FFFFFF\">\n'
		html += webParts.IncludeMENU()
		html += '<div class="main">\n<p align="center"><b><font color="#FFE4C4">%s not available</font></b></p></div>\n</body>\n' % pageName
	html += "</html>\n"
	html += "</form>\n"
		
	return html
  
########################################################
class redirectionPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		command = req.args.get("cmd",None)
		html = """
<html lang="%s">
  <head>
    <title>%s</title>
    <meta http-equiv="refresh" content="5; URL=/iptvplayer/">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="keywords" content="automatic redirection">
  </head>
  <body>
  <p align="center"> %s
  <a href="/iptvplayer/">%s</a></p>
  </body>
</html>""" % (language.getLanguage()[:2],
	      _('Redirect'),
	      _('You are using old version of OpenWebif.<br> To go to IPTVPlayer web Select the following link<br>'),
	      _('Click'))

		return html

#######################################################
class StartPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		command = req.args.get("cmd",None)
		return generateWebPage('StartPage')

#######################################################
class hostsPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		command = req.args.get("cmd",None)
		return generateWebPage('hostsPage')
#######################################################
class downloaderPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		command = req.args.get("cmd",None)
		return generateWebPage('downloaderPage')
#######################################################
class settingsPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		command = req.args.get("cmd",None)
		return generateWebPage('settingsPage')
##########################################################
class logsPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		command = req.args.get("cmd",None)
		return generateWebPage('logsPage')
##########################################################
