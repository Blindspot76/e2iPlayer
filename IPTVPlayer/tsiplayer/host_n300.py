# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Components.config import config
import re

def getinfo():
	info_={}
	info_['name']='N300.Tv'
	info_['version']='1.3 11/07/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='99'
	info_['desc']='افلام و مسلسلات عربية واجنبية'
	info_['icon']='https://n300.tv/IMGCenter/sys/n300_tv.png'
	info_['recherche_all']='0'
	#info_['update']='Bugs Fix'
	return info_
		
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{})
		self.MAIN_URL = 'https://n300.tv'
		 
	def showmenu(self,cItem):
		desc = [('Info','<small>(.*?)</','','')]
		self.add_menu(cItem,'<ul class="list-group(.*?)</ul','<li.*?href="(.*?)".*?>(.*?)<(.*?)</li>','','20',del_=['الصفحة','contact','dvertising'],LINK='/d/series/all.aspx?series',ord=[0,1,-1,2],Desc=desc,search=False)					
	
	def showitms(self,cItem):
		desc = [('Info','<small.*?>(.*?)</','','')]
		self.add_menu(cItem,'','inline-block">.*?href=\'(.*?)\'.*?src="(.*?)".*?<h1.*?>(.*?)</h1>(.*?)</a>','','21',ord=[0,2,1,3],Desc=desc,EPG=True)					

	def showelms(self,cItem):
		self.add_menu(cItem,'<table id="Content(.*?)</table>','<a href="(.*?)".*?>(.*?)</a>','','video')					
		
	def get_links(self,cItem): 	
		local = [('www.n300','N300','1'),('vidspeed.','#0#Vidspeed','0'),]
		result = self.add_menu(cItem,'','<input id=.*?\(\'(.*?)\'.*?value="(.*?)"','','serv',local=local)						
		return result[1]	

	def getVideos(self,videoUrl):
		printDBG('getVideos:'+videoUrl)
		urlTab = []	
		videoUrl=videoUrl.replace('/../../../','/')
		if not videoUrl.startswith('http'): videoUrl  = self.MAIN_URL+videoUrl
		url = videoUrl
		if 'videoURL=' in url: url = url.split('videoURL=',1)[-1]
		url=url.replace('http://www.n300.net:8080/','https://ssl.n300.me:2020/')
		url = strwithmeta('Local'+'|'+url, {'Referer':videoUrl})
		urlTab.append((url,'4'))
		return urlTab