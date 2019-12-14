# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

import re
import base64

def getinfo():
	info_={}
	info_['name']='Embratoria.Net'
	info_['version']='1.2 12/10/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='100'
	info_['desc']='Live TV Channels'
	info_['icon']='http://www.embratoria.net/uploads/system_logo/logo.png?1566827141'
	info_['update']='Fix Link Extract (only beinsports work in browser - 12/10/2019)'	
	info_['recherche_all']='0'
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'embratoria.cookie'})
		self.Player_Agent ='ExoPlayerDemo/80.0 (Linux;Android 7.1.1) ExoPlayerLib/2.5.3'
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0'
		self.MAIN_URL = 'http://www.embratoria.net'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Accept':'application/json','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}			
		self.getPage = self.cm.getPage
		
	def getPage1(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		origBaseUrl = baseUrl
		baseUrl = self.cm.iriToUri(baseUrl)
		sts, data = self.cm.getPage(baseUrl, addParams, post_data)
		return sts,data	
		
		
	def showmenu(self,cItem):
		url=self.MAIN_URL+'/live-tv.html'
		sts,data=self.getPage(url)		
		if sts:
			data1=re.findall('nav ignore">(.*?)</ul', data, re.S)
			if data1:
				i=0
				data2=re.findall('href="(.*?)".*?>(.*?)<', data1[0], re.S)
				data3=re.findall('-pane[" ](.*?)class="tab', data, re.S)
				for (url,titre) in data2:
					if len(data3)>i:
						self.addDir({'import':cItem['import'],'category' : 'host2','url': data3[i],'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
					i=i+1
					
	def showlive(self,cItem):
		data=re.findall('class="figure">.*?title="(.*?)".*?href="(.*?)".*?src="(.*?)"', cItem['url'], re.S)
		for (titre,url,image) in data:
			self.addVideo({'import':cItem['import'],'category' : 'host2','hst':'tshost','good_for_fav':True,'url': url,'title':titre,'desc':'','icon':image})	

		
	def get_links(self,cItem): 	
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			#old methode
			#printDBG('ddddddddddttttttaaaaa00'+data)
			#server_data = re.findall('sources.*?src.*?"(.*?)"', data, re.S)
			#if server_data:
			#	urlout=server_data[0]
			#	if urlout.startswith('//'):
			#		urlout='http:'+urlout
			#		urlTab.append({'name':'Direct', 'url':urlout, 'need_resolve':0})
			#New
			server_data = re.findall("var hls..*?'(.*?)'", data, re.S)
			if server_data:
				URL = base64.b64decode(server_data[0])
				if URL.startswith('//'): URL = 'https:'+URL
				urlTab.append({'name':'M3U8', 'url':'hst#tshost#'+URL, 'need_resolve':1})
			
		return urlTab

	def getVideos(self,videoUrl):
		urlTab = []	
		urlTab.append((videoUrl,'3'))	
		return urlTab
		
		
	def start(self,cItem):
		list_=[]
		mode=cItem.get('mode', None)
		if mode=='00':
			list_ = self.showmenu(cItem)	
		elif mode=='30':
			list_ = self.showlive(cItem)

		return True
