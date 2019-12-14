# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
import re
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass


def getinfo():
	info_={}
	info_['name']='Sport Tv V2.0.8 (Android App)'
	info_['version']='1.0 24/04/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='104'#'100'
	info_['desc']=' تطبيق اندوريد للبث المباشر للقنوات الرياضية'
	info_['icon']='https://i.ibb.co/cJ3jY40/8p4hc4g9.png'
	info_['recherche_all']='0'
		
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'sporttv.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.4.2; SAMSUNG-SM-N900A Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Safari/537.36'
		self.MAIN_URL = 'http://tvhistories.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'X-Requested-With': 'com.freesportstv.app','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		
		
	def showmenu(self,cItem):
		app_key = 'IsCKZMCNqa'		
		URL = ''
		ua = ''	
		sUrl = 'http://samdev.club/staging/public/api/free/getcategory'
		
		post_data = {'app_key':app_key}
		sts, data = self.cm.getPage(sUrl,{'header':self.HEADER}, post_data=post_data)
		t_data = re.findall('"webview":.*?url":"(.*?)".*?"user_agent":"(.*?)"', data, re.S)	
		if t_data:
			ua = t_data[0][1] 
			URL = t_data[0][0].replace('\/','/')

		sts, data = self.cm.getPage(URL, {'header':self.HEADER})
		URL_data = re.findall('href="(.*?)".*?src="(.*?)"', data, re.S)
		block_link = ['itvboxoffice.php', 'IPL_2019/index.php']		
		for (url,image) in URL_data:
			if str(url).startswith('http://tvhistories.com') and not any(x in url for x in block_link):
				titre_data = re.findall('//.*/.*/(.*?).php', str(url), re.S)
				if titre_data:
					titre = str(titre_data[0])
					titre=titre.replace('wss','')
					self.addVideo({'import':cItem['import'],'url': str(url),'title':titre,'icon':image,'ua':ua,'hst':'tshost','good_for_fav':True} )		
		

	def get_links(self,cItem):	
		urlTab = []	
		URL=cItem['url']
		ua=cItem['ua']			
		sts, data = self.cm.getPage(URL)
		data = re.sub('<!--.*?-->', '', data)
		URL_data = re.findall('<a.*?(http.*?)">(.*?)</', data, re.S)
		for (url,titre) in URL_data:
			titre = re.sub('<.*?>', '', str(titre))
			if (str(titre)!='.') and (str(titre)!='a') and (titre.strip()!='') and ('.png' not in url) and ('.swf' not in url):
				URl = strwithmeta(url,{'User-Agent' : ua})
				printDBG('#'+titre+'#'+URl)
				urlTab.append({'name':titre, 'url':URl , 'need_resolve':0})	
		return urlTab
	
	def start(self,cItem):
		list_=[]
		mode=cItem.get('mode', None)
		if mode=='00':
			list_ = self.showmenu(cItem)	
		elif mode=='10':
			list_ = self.showservers(cItem)
		return True
