# -*- coding: utf-8 -*-
#### Local imports
from __init__ import _
import settings
import webParts
import Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget

from Plugins.Extensions.IPTVPlayer.components.ihost import IHost, CDisplayListItem, RetHost, CUrlItem, ArticleContent, CFavItem
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper, DMItemBase
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdownloadercreator import IsUrlDownloadable
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import GetPluginDir, printDBG
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdmapi import IPTVDMApi, DMItem
#### e2 imports
from Components.config import configfile, config
from Components.Language import language

#### system imports
import os
from twisted.web import resource, http, util
import urllib

########################################################
def reloadScripts():
	#### Reload scripts if new version of source exists ####
	webPath = GetPluginDir(file = '/Web/')
	if os.path.exists(os.path.join(webPath, "webParts.py")):
		if os.path.exists(os.path.join(webPath, "webParts.pyo")):
			if (int(os.path.getmtime(os.path.join(webPath, "webParts.pyo"))) < 
				int(os.path.getmtime(os.path.join(webPath, "webParts.py")))):
				reload(webParts)
		else:
			reload(webParts)
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
   
	def __init__(self):
		pass
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		reloadScripts()
		html = '<html lang="%s">' % language.getLanguage()[:2]
		html += webParts.IncludeHEADER()
		html += webParts.Body().StartPageContent()
		return html 
#######################################################
class searchPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
	isLeaf = False
   
	def __init__(self):
		pass
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		reloadScripts()
		html = '<html lang="%s">' % language.getLanguage()[:2]
		html += webParts.IncludeHEADER()
		html += webParts.Body().StartPageContent()
		return html 


#######################################################
class hostsPage(resource.Resource):
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
    
	def __init__(self):
		pass
   
	def render(self, req):
		settings.initActiveHost( None )

		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		reloadScripts()
		html = '<html lang="%s">' % language.getLanguage()[:2]
		html += webParts.IncludeHEADER()
		html += webParts.Body().hostsPageContent()
		return html
##########################################################
class logsPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def __init__(self):
		pass
   
	def render(self, req):

		""" rendering server response """
		DBGFileName = ''
		htmlError = ''
		command = req.args.get("cmd",None)
		if command is None:
			pass
		elif command[0] ==  "getLog" or command[0] ==  "deleteLog":
			if os.path.exists('/hdd/iptv.dbg'):
				DBGFileName = '/hdd/iptv.dbg'
			elif os.path.exists('/tmp/iptv.dbg'):
				DBGFileName = '/tmp/iptv.dbg'
			else:
				htmlError = '<p align="center"><b><font color="#FFE4C4">%s</font></b></p>' % _('Debug file does not exist - nothing to download')

		if DBGFileName == '':
			req.setHeader('Content-type', 'text/html')
			req.setHeader('charset', 'UTF-8')
			reloadScripts()
			html = '<html lang="%s">' % language.getLanguage()[:2]
			html += webParts.IncludeHEADER()
			html += webParts.Body().logsPageContent()
			html += htmlError
		elif command[0] ==  "getLog":
			req.responseHeaders.setRawHeaders('content-disposition', ['attachment; filename="iptv_dbg.txt"'])
			with open(DBGFileName, 'r') as f:
			      html = f.read()
			      f.close()
		elif command[0] ==  'deleteLog':
			req.setHeader('Content-type', 'text/html')
			req.setHeader('charset', 'UTF-8')
			reloadScripts()
			html = '<html lang="%s">' % language.getLanguage()[:2]
			html += webParts.IncludeHEADER()
			if os.path.exists(DBGFileName):
				try:
					os.remove(DBGFileName)
					status = 'deleteLogOK'
				except Exception:
					status = 'deleteLogError'
			else:
				status = 'deleteLogNO'
			html += webParts.Body().logsPageContent(status)
		  
		return html
#######################################################
class settingsPage(resource.Resource):
   
	title = "IPTVPlayer Webinterface"
	isLeaf = False
   
	def __init__(self):
		pass
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		if len(req.args.keys()) > 0:
			key = req.args.keys()[0]
			arg = req.args.get(key,None)[0]
			print 'Received: ', key, '=' , arg
		
			try:
				if key is None or arg is None:
					pass
				elif key == 'cmd' and arg[:3] == 'ON:':
					exec('config.plugins.iptvplayer.%s.setValue(True)\nconfig.plugins.iptvplayer.%s.save()' % (arg[3:],arg[3:]) )
					#exec('config.plugins.iptvplayer.%s.save()') % 
				elif key == 'cmd' and arg[:4] == 'OFF:':
					exec('config.plugins.iptvplayer.%s.setValue(False)\nconfig.plugins.iptvplayer.%s.save()' % (arg[4:],arg[4:]) )
					settings.activeHostsHTML.pop(arg[4:], None)
				elif key[:4] ==  "CFG:":
					exec('config.plugins.iptvplayer.%s.setValue("%s")' % (key[4:],arg))
				elif key[:4] ==  "INT:":
					exec('config.plugins.iptvplayer.%s.setValue("%s")' % (key[4:],arg))
				configfile.save()
			except Exception:
				printDBG("[webSite.py:settingsPage] EXCEPTION for updating value '%s' for key '%s'" %(arg,key))

		reloadScripts()
		html = '<html lang="%s">' % language.getLanguage()[:2]
		html += webParts.IncludeHEADER()
		html += webParts.Body().settingsPageContent()

		return html
#######################################################
class downloaderPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def __init__(self):
		pass
   
	def render(self, req):
		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		""" rendering server response """
		extraMeta = '<meta http-equiv="refresh" content="5">'
		key = None
		arg = None
		arg2 = None
		arg3 = None
		DMlist = []
		if len(req.args.keys()) >= 1:
			key = req.args.keys()[0]
			arg = req.args.get(key,None)[0]
			try: arg2 = req.args.get(key,None)[1]
			except Exception: pass
			try: arg3 = req.args.get(key,None)[2]
			except Exception: pass
			print 'Received: "%s"="%s","%s","%s"' % ( key,arg,arg2,arg3)

		if key is None or arg is None:
			if None != Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				DMlist = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList()
		elif key == 'cmd' and arg == 'initDM':
			if None == Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				printDBG('============WebSite.py Initialize Download Manager============')
				Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager = IPTVDMApi(2, int(config.plugins.iptvplayer.IPTVDMMaxDownloadItem.value))
				DMlist = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList()
		elif key == 'cmd' and arg == 'runDM':
			if None != Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.runWorkThread() 
				DMlist = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList()
		elif key == 'cmd' and arg == 'stopDM':
			if None != Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.stopWorkThread()
				DMlist = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList()
			  	extraMeta = '<meta http-equiv="refresh" content="10">'
		elif key == 'cmd' and arg == 'downloadsDM':
			if None != Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				DMlist = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList()
		elif key == 'watchMovie' and os.path.exists(arg):
			return util.redirectTo("/file?action=download&file=%s" % urllib.quote(arg.decode('utf8', 'ignore').encode('utf-8')) , req)
		elif key == 'stopDownload' and arg.isdigit():
			if None != Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.stopDownloadItem(int(arg))
				DMlist = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList()
		elif key == 'downloadAgain' and arg.isdigit():
			if None != Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.continueDownloadItem(int(arg))
				DMlist = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList()
		elif key == 'removeMovie' and arg.isdigit():
			if None != Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.removeDownloadItem(int(arg))
				DMlist = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList()

		elif key == 'cmd' and arg == 'arvchiveDM':
			if arg2 == 'deleteMovie' and os.path.exists(arg3):
				os.remove(arg3)
			elif arg2 == 'watchMovie' and os.path.exists(arg3):
				return util.redirectTo("/file?action=download&file=%s" % urllib.quote(arg3.decode('utf8', 'ignore').encode('utf-8')) , req)
			if os.path.exists(config.plugins.iptvplayer.NaszaSciezka.value) and None != Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
				files = os.listdir(config.plugins.iptvplayer.NaszaSciezka.value)
				files.sort(key=lambda x: x.lower())
				for item in files:
					if item.startswith('.'): continue # do not list hidden items
					if item[-4:].lower() not in ['.flv', '.mp4']: continue
					fileName = os.path.join(config.plugins.iptvplayer.NaszaSciezka.value, item)
					skip = False
					for item2 in Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.getList():
						if fileName == item2.fileName.replace('//', '/'):
							skip = True
							break
					if skip: continue
					listItem = DMItemBase(url=fileName, fileName=fileName)
					try: listItem.downloadedSize = os.path.getsize(fileName)
					except Exception: listItem.downloadedSize = 0
					listItem.status      = DMHelper.STS.DOWNLOADED
					listItem.downloadIdx = -1
					DMlist.append( listItem )
				if len(DMlist) == 0:
					listItem = DMItemBase(_('Nothing has been downloaded yet.'), '')
					listItem.status = 'INFO'
					DMlist.append( listItem )
			
		if len(DMlist) == 0 and arg != 'arvchiveDM':
			listItem = DMItemBase(_('No materials waiting in the downloader queue'), '')
			listItem.status      = 'INFO'
			DMlist.append( listItem )
			extraMeta = ''
		elif len(DMlist) == 0 and arg in ['arvchiveDM','stopDM'] :
			extraMeta = ''
			
		reloadScripts()
		html = '<html lang="%s">' % language.getLanguage()[:2]
		html += webParts.IncludeHEADER(extraMeta)
		html += webParts.Body().downloaderPageContent(Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager, DMlist)
		return html
#######################################################
class useHostPage(resource.Resource):
    
	title = "IPTVPlayer Webinterface"
 	isLeaf = False
   
	def __init__(self):
		pass
   
	def render(self, req):
		reloadScripts()
		
		""" rendering server response """
		key = None
		arg = None
		html= ''
		extraMeta = ''
		#extraMeta = '<meta http-equiv="refresh" content="10">'
		errMSG = ''
		
		if len(req.args.keys()) > 0:
			key = req.args.keys()[0]
			arg = req.args.get(key,None)[0]
			print "useHostPage received: '%s'='%s'" % (key, str(arg))
		
		if key is None and settings.isActiveHostInitiated() == False:
			return util.redirectTo("/iptvplayer/hosts", req)
		elif key == 'activeHost' and settings.isActiveHostInitiated() == False:
			settings.initActiveHost(arg)
		elif key == 'activeHost' and arg != settings.activeHost['Name']:
			settings.initActiveHost(arg)
		elif key == 'cmd' and arg == 'hosts':
			return util.redirectTo("/iptvplayer/hosts", req)
		elif key == 'cmd' and arg == 'InitList':
			settings.retObj = settings.activeHost['Obj'].getInitList()
			settings.activeHost['PathLevel'] = 1
			settings.activeHost['ListType'] = 'ListForItem'
			settings.activeHost['Status'] =  ''
			settings.currItem = {}
		elif key == 'cmd' and arg == 'RefreshList':
			settings.retObj = settings.activeHost['Obj'].getCurrentList()
			settings.activeHost['ListType'] = 'ListForItem'
			settings.currItem = {}
		elif key == 'cmd' and arg == 'PreviousList':
			settings.retObj = settings.activeHost['Obj'].getPrevList()
			settings.activeHost['PathLevel'] -= 1
			settings.activeHost['ListType'] = 'ListForItem'
			settings.currItem = {}
		elif key == 'DownloadURL' and arg.isdigit():
			myID = int(arg)
			url = settings.retObj.value[myID].url
			if url != '' and IsUrlDownloadable(url):
				titleOfMovie = settings.currItem['itemTitle'].replace('/','-').replace(':','-').replace('*','-').replace('?','-').replace('"','-').replace('<','-').replace('>','-').replace('|','-')
				fullFilePath = config.plugins.iptvplayer.NaszaSciezka.value + '/' + titleOfMovie + 'mp4'
				if None == Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager:
					printDBG('============WebSite.py Initialize Download Manager============')
					Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager = IPTVDMApi(2, int(config.plugins.iptvplayer.IPTVDMMaxDownloadItem.value))
				ret = Plugins.Extensions.IPTVPlayer.components.iptvplayerwidget.gDownloadManager.addToDQueue( DMItem(url, fullFilePath))
				print ret
		elif key == 'ListForItem' and arg.isdigit():
			myID = int(arg)
			settings.activeHost['selectedItemType'] = settings.retObj.value[myID].type
			if settings.activeHost['selectedItemType'] in ['CATEGORY']:
				settings.currItem = {}
				settings.retObj = settings.activeHost['Obj'].getListForItem(myID,0,settings.retObj.value[myID])
				settings.activeHost['PathLevel'] += 1
			elif settings.activeHost['selectedItemType'] in ['VIDEO']:
				settings.currItem['itemTitle'] = settings.retObj.value[myID].name
				try:
					print "ListForItem>getLinksForVideo"
					settings.retObj = settings.activeHost['Obj'].getLinksForVideo(myID,settings.retObj.value[myID]) #returns "NOT_IMPLEMENTED" when host is using curlitem
					print 'got status' , settings.retObj.status
					if settings.retObj.status == "NOT_IMPLEMENTED" or len(settings.retObj.value) == 0:
						raise Exception
				except Exception:
					print "building CUrlItem"
					settings.retObj = RetHost(RetHost.NOT_IMPLEMENTED, value = [(CUrlItem("No valid urls", "fakeUrl", 0))])
					try:
						tempUrls=[]
						iindex=1
						links = ret.value[myID].urlItems
						for link in links:
							if link.name == '':
								tempUrls.append(CUrlItem('link %d' % iindex, link.url, link.urlNeedsResolve))
							else:
								tempUrls.append(CUrlItem(link.name, link.url, link.urlNeedsResolve))
							iindex += 1
						settings.retObj = RetHost(RetHost.OK, value = tempUrls)
					except:
						pass

		req.setHeader('Content-type', 'text/html')
		req.setHeader('charset', 'UTF-8')

		html += '<html lang="%s">' % language.getLanguage()[:2]
		html += webParts.IncludeHEADER(extraMeta)
		html += webParts.Body().useHostPageContent( errMSG )
		return html
##########################################################
