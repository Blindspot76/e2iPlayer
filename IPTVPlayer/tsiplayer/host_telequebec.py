# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

from os import path as os_path
import re
telequebec_path = resolveFilename(SCOPE_PLUGINS, 'Extensions/IPTVPlayer/tsiplayer/libs/telequebec.tsbase')

###################################################
#01# HOST http://www.telequebec.tv/
###################################################	
def getinfo():
	info_={}
	info_['name']='TeleQuebec.Tv'
	info_['version']='1.0 16/04/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='303'
	info_['desc']='Jeunesse VF'
	info_['icon']='https://www.telequebec.tv/apple-touch-icon.png'
	info_['recherche_all']='0'
	
	return info_
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'telequebec.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://mnmedias.api.telequebec.tv'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
	 
	def showmenu0(self,cItem):
		image=cItem.get('icon', '')
		if os_path.isfile(telequebec_path):	
			with open(telequebec_path) as f: 
				lst=[]
				for line in f:
					if line.strip()!='':
						printDBG('line='+line)
						img_,name_,episode_,code_,x1=line.split(';')
						if name_ not in lst:
							lst.append(name_)
							if img_.strip()!='':
								img_='https://images.tele.quebec/emissions/'+img_.strip()+'/default/w176_h99.jpg'
							else:
								img_=image
							self.addDir({'import':cItem['import'],'category' : 'host2','title':name_,'icon':img_,'mode':'20','good_for_fav':True})	

	def showmenu1(self,cItem):
		name=cItem.get('title', '')
		if os_path.isfile(telequebec_path):	
			with open(telequebec_path) as f: 
				for line in f:
					if line.strip()!='':
						img_,name_,episode_,code_,x1=line.split(';')
						if name_ == name:		
							self.addVideo({'import':cItem['import'],'category' : 'host2','title':episode_,'url':code_,'icon':cItem['icon'],'hst':'tshost','good_for_fav':True})
	def get_links(self,cItem): 	
		urlTab = []
		code_=cItem['url']
		URL='https://mnmedias.api.telequebec.tv/m3u8/'+code_+'.m3u8'
		urlTab = getDirectM3U8Playlist(URL, False, checkContent=True, sortWithMaxBitrate=999999999)
		return urlTab	
		
			
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		return True

