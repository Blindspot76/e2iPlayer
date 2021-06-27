# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re
import base64,urllib

def getinfo():
	info_={}
	info_['name']='Playbox TV (Android App)'
	info_['version']='1.0 12/07/2020'
	info_['dev']='RGYSoft >> Thx to TSmedia <<'
	info_['cat_id']='21'
	info_['desc']='افلام'
	info_['icon']='https://i.ibb.co/9sVwFzc/playbox.png'
	info_['recherche_all']='1'
	return info_


class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{})
		self.MAIN_URL = 'https://infiniteks.com/showtime_service'
		
	def showmenu(self,cItem):
		TAB = [('أفلام عربية','/ws_v1/bycat.php?cat=movies','20',''),('مسرحيات','/ws_v1/bycat.php?cat=plays','20','')]
		self.add_menu(cItem,'','','','','',TAB=TAB,search=True)

	def showitms(self,cItem):
		sts, data = self.getPage(cItem['url'])
		if sts:
			data = json_loads(data)
			if data['status']:
				for elm in data['result']['items']:
					titre = elm['title']
					image = self.MAIN_URL + '/imgs/' + elm['mainimg']
					url   = elm['mainlink']
					story = elm.get('description','')
					added = elm.get('added','')
					desc = tscolor('\c00????00') + 'Added: ' + tscolor('\c00??????') + added + '\n'
					desc = desc + tscolor('\c00????00') + 'Story: ' + tscolor('\c00??????') + story + '\n'
					if 'm3u8' in url: hst = 'tshost'
					else: hst = 'direct'
					self.addVideo({'category':'host2', 'title': titre,'url':url, 'desc':desc,'import':cItem['import'],'icon':image,'hst':hst})	
			
	def SearchResult(self,str_ch,page,extra):
		url = self.MAIN_URL+'/ws_v1/search.php?q='+str_ch
		sts, data = self.getPage(url)
		if sts:
			data = json_loads(data)
			if data['status']:
				for elm in data['result']['items']:
					titre = elm['title']
					image = self.MAIN_URL + '/imgs/' + elm['mainimg']
					url   = elm['mainlink']
					story = elm.get('description','')
					added = elm.get('added','')
					desc = tscolor('\c00????00') + 'Added: ' + tscolor('\c00??????') + added + '\n'
					desc = desc + tscolor('\c00????00') + 'Story: ' + tscolor('\c00??????') + story + '\n'
					if 'm3u8' in url: hst = 'tshost'
					else: hst = 'direct'
					self.addVideo({'category' : 'video', 'title': titre,'url':url, 'desc':desc,'import':extra,'icon':image,'hst':hst})	

	def get_links(self,cItem): 		
		urlTab = []
		URL    = cItem['url'] 
		urlTab.extend(getDirectM3U8Playlist(URL, checkExt=True, checkContent=True, sortWithMaxBitrate=999999999))					
		return urlTab	
		
