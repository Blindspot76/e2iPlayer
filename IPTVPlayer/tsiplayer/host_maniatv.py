# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.tstools import TSCBaseHostClass

import re

def getinfo():
	info_={}
	info_['name']='Mania Tv (Android App)'
	info_['version']='1.0 20/06/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='100'
	info_['desc']='تطبيق اندوريد للبث المباشر'
	info_['icon']='https://media.cdnandroid.com/60/1a/58/af/imagen-yacine-tv-app-0thumb.jpg'
	info_['recherche_all']='0'
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'liveplus.cookie'})
		self.Player_Agent ='yacine00'
		self.USER_AGENT = 'Dalvik/2.1.0 (Linux; U; Android 8.0.0; SM-G570F Build/R16NW)'
		self.MAIN_URL = 'http://www.live-plus.io'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Accept':'application/json','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
	
		
	def getPage(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		origBaseUrl = baseUrl
		baseUrl = self.cm.iriToUri(baseUrl)
		sts, data = self.cm.getPage(baseUrl, addParams, post_data)
		return sts,data	
		
		
	def showmenu(self,cItem):
		sts,data=self.getPage('http://www.yacinelive.com/app/api.php?cat')
		data = json_loads(data)
		elmdata = data['data']		
		for elm in 	elmdata:
			titre=elm['category_name']
			code=elm['cid']
			self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':code,'desc':'','icon':cItem['icon'],'mode':'20'})

	def showmenu2(self,cItem):
		code=cItem['url']
		sts,data=self.getPage('http://www.yacinelive.com/app/api.php?cat_id='+code)
		data = json_loads(data)
		elmdata = data['data']		
		for elm in 	elmdata:
			titre=elm['channel_title']
			url=elm['channel_url']
			image=elm['channel_thumbnail']
			url = strwithmeta(url, {'User-Agent':self.Player_Agent})
			self.addVideo({'import':cItem['import'],'title':titre,'url':url,'icon':image,'hst':'direct'})
		
	def start(self,cItem):
		list_=[]
		mode=cItem.get('mode', None)
		if mode=='00':
			list_ = self.showmenu(cItem)	
		elif mode=='20':
			list_ = self.showmenu2(cItem)

		return True
