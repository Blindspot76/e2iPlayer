# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.tstools import TSCBaseHostClass
from Components.config import config

import re

def getinfo():
	info_={}
	info_['name']='Star7 Live (Android App)'
	info_['version']='1.0 24/04/2019'
	info_['dev']='TSMedia (yassinov) + RGYSoft (Adaptation)'
	info_['cat_id']='100'
	info_['desc']='Star7 Iptv and VOD'
	info_['icon']='http://star7apk.com/images/icon.png'
	info_['recherche_all']='0'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'star7.cookie'})
		self.Player_Agent ='REDLINECLIENT GN-CX1200 V2.0.63'
		self.USER_AGENT = 'Dalvik/2.1.0 (Linux; U; Android 7.1.1; E6633 Build/32.4.A.1.54)'
		self.MAIN_URL = 'http://www.t100v.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		#self.AJAX_HEADER = dict(self.HEADER)
		#self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest', 'Accept-Encoding':'gzip, deflate', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'Accept':'application/json, text/javascript, */*; q=0.01'} )
		#self.cacheLinks  = {}
		#self.defaultParams = {'header':self.HEADER, 'raw_post_data':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage=self.cm.getPage
				
	def showmenu0(self,cItem):
		list_=[]
		username=config.plugins.iptvplayer.ts_star7live_user.value#'110652'
		password=config.plugins.iptvplayer.ts_star7live_pass.value#'808008'
		if (username!='') and (password!=''):
			url='http://t100v.com/apk/api.php'+'?username='+username+'&password='+password
			sts, data = self.getPage(url,{'header':self.HEADER})	
			data = json_loads(data)
			lst_url  =    data['app_version']['list_url']
			play_url =    data['app_version']['play_url']
			vod_url  =    data['app_version']['vod_url']		
			img_url  =    data['app_version']['image_url']
			account_type= data['app_version']['account_type']
			expiry_date=  data['app_version']['expiry_date']
			desc='\c00????00'+'Type: '+'\c00??????'+account_type+'\\n'
			desc=desc+'\c00????00'+'expiry date: '+'\c00??????'+expiry_date
			if expiry_date=='invalid':
				desc='\c00????00'+'Invalid Account !!'
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'LIVE','url':lst_url,'desc':desc,'icon':cItem['icon'],'mode':'20','play_url':play_url})
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'VOD','url':lst_url,'desc':desc,'icon':cItem['icon'],'mode':'30','vod_url':vod_url})			
		else:
			self.addMarker({'title':'Please configure Star7 Live first','icon':cItem['icon'],'desc':'Please configure Star7 live first, (add user,pass in tsiplayer params) \\nGet 7 days free Account at \c00????00 http://star7apk.com/'})	

		return True	

 
	def showmenu1(self,cItem):
		lst_url=cItem['url']
		sts, data = self.getPage(lst_url,{'header':self.HEADER})
		data = json_loads(data)
		lst_cat =   data['cats']
		for elm in lst_cat:
			titre_=elm['desc']
			id_=elm['id']
			channels_=elm['channels']
			img='http://www.t100v.com/images/a/c'+id_+'.jpg'
			self.addDir({'import':cItem['import'],'category' : 'host2','title':titre_,'url':channels_,'icon':img,'mode':'21','play_url':cItem['play_url']})

	def showchannels(self,cItem):
		channels_=cItem['url']
		for elm in channels_:
			titre_=elm['name']
			id_=elm['id']
			url=cItem['play_url']+id_
			meta = {'User-Agent':self.Player_Agent}
			URL=strwithmeta(url, meta)			
			self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre_,'url':URL,'icon':cItem['icon'],'hst':'direct'})

	def showmenu2(self,cItem):
		lst_url=cItem['url']
		sts, data = self.getPage(lst_url,{'header':self.HEADER})
		data = json_loads(data)
		lst_cat =   data['vod_cats']
		for elm in lst_cat:
			titre_=elm['desc']
			id_=elm['id']
			vods_=elm['vods']
			#img='http://www.t100v.com/images/a/c'+id_+'.jpg'
			self.addDir({'import':cItem['import'],'category' : 'host2','title':titre_,'url':vods_,'icon':cItem['icon'],'mode':'31','vod_url':cItem['vod_url']})

		
	def showvods(self,cItem):
		vods_=cItem['url']
		for elm in vods_:
			titre_=elm['name']
			id_=elm['id']
			url=cItem['vod_url']+'&id='+id_+'&type=stream'
			img=cItem['vod_url']+'&img='+id_
			meta = {'User-Agent':self.Player_Agent}
			URL=strwithmeta(url, meta)			
			self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre_,'url':URL,'icon':img,'hst':'direct'})
		
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='21':
			self.showchannels(cItem)
		if mode=='30':
			self.showmenu2(cItem)
		if mode=='31':
			self.showvods(cItem)						
		return True

