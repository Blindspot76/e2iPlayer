# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,resolve_liveFlash,resolve_zony,tscolor
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper        import getDirectM3U8Playlist
import re
from Plugins.Extensions.IPTVPlayer.tools.e2ijs import js_execute
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
import urllib

def getinfo():
	info_={}
	info_['name']='Beinmatch.Com'
	info_['version']='1.0 18/06/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='100'#2
	info_['desc']='موقع للبث المباشر ونقل المباريات'
	info_['icon']='http://www.beinmatch.com/assets/images/bim/logo.png'
	info_['recherche_all']='0'
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'coolkora.cookie'})
		self.MAIN_URL = 'http://beinmatch.tv'
		self.USER_AGENT = 'Mozilla/5.0 (Android 4.4; Mobile; rv:41.0) Gecko/41.0 Firefox/41.0'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage

	
		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Live Matches','url':'','icon':cItem['icon'],'mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Replay'        ,'url':'','icon':cItem['icon'],'mode':'25'})

	def showmatch1(self,cItem):
		image=cItem['icon']
		page=cItem.get('page',1)
		url=self.MAIN_URL#+'/'+str((page-1)*5)
		sts,data=self.getPage(url)
		if sts:
			if 'لا يوجد أي مقابلات مباشرة' in data:
				self.addMarker({'title':'No Live Found','desc':'','icon':image})
			else:
				I_list = re.findall('<table class="tabIndex">.*?url\((.*?)\).*?tdTeam">(.*?)</td>.*?onclick=["\'](.*?)[;](.*?)tdTeam">(.*?)</td>.*?class="compStl".*?>(.*?)<', data, re.S)
				for (image,team1,id_,x1,team2,desc) in I_list:
					if ('alert' not in id_) and ( 'الأهداف' not in x1):
						I_list2 = re.findall('goToMatch\((.*?)\)', id_, re.S)
						if I_list2: 
							id_=I_list2[0]
							titre = tscolor('\c0000??00')+'# '+ph.clean_html(team2)+' Vs '+ph.clean_html(team1)+' #'
							self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':id_,'desc':ph.clean_html(desc),'icon':image,'mode':'26','sub_mode':0})	
					elif ( 'الأهداف' not in x1):
						titre = tscolor('\c00????00')+'# '+ph.clean_html(team2)+' Vs '+ph.clean_html(team1)+' # Not Started yet'
						self.addMarker({'title':titre,'desc':ph.clean_html(desc),'icon':image})	



	def showreplay1(self,cItem):
		image=cItem['icon']
		page=cItem.get('page',1)
		url=self.MAIN_URL+'/home/videos/'+str((page-1)*5)
		sts,data=self.getPage(url)
		if sts:
			I_list = re.findall('<table class="tabIndex">.*?url\((.*?)\).*?tdTeam">(.*?)<.*?tdScore">(.*?)</td>.*?goToMatch\((.*?)\).*?tdScore">(.*?)</td>.*?tdTeam">(.*?)<.*?class="compStl".*?>(.*?)<', data, re.S)
			for (image,team1,score1,id_,score2,team2,desc) in I_list:
				titre = '# '+team1+' [ '+ph.clean_html(score1)+' - '+ph.clean_html(score2)+' ] '+team2+' #'
				self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':id_,'desc':ph.clean_html(desc),'icon':image,'mode':'26','sub_mode':1})	
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'Next','url':cItem['url'],'desc':'','icon':image,'mode':'25','page':page+1})	

	def showreplay2(self,cItem):
		image=cItem['icon']
		gnr=cItem['sub_mode']
		id_=cItem.get('url',',')
		e1,e2=id_.split(',',1)
		e2=e2.replace("'",'')
		url1=self.MAIN_URL+'/home/live/'+e1+'/1/'+urllib.quote(e2)
		url2=self.MAIN_URL+'/home/live/'+e1+'/2/'+urllib.quote(e2)
		if gnr==1:
			self.addVideo({'import':cItem['import'],'category' : 'host2','title':'Highlights','url':url1,'desc':'','icon':image,'hst':'tshost'})	
			self.addVideo({'import':cItem['import'],'category' : 'host2','title':'Full Match','url':url2,'desc':'','icon':image,'hst':'tshost'})	
		else:
			self.addVideo({'import':cItem['import'],'category' : 'host2','title':'Server 1','url':url1,'desc':'','icon':image,'hst':'tshost'})	
			self.addVideo({'import':cItem['import'],'category' : 'host2','title':'Server 2','url':url2,'desc':'','icon':image,'hst':'tshost'})	
			

	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		sts, data = self.getPage(URL)
		printDBG('uuuuuuuuuuuuuuuuuuu11=#'+data+'#')
		#<iframe width="100%" height="100%" xwidth="100%" xheight="100%" src="http://beinmatch.com/twitc.php" frameborder="0" allowfullscreen="" __idm_id__="893051905"></iframe>                        </div>
		url=''
		Tab_els = re.findall('<iframe.*?src="(.*?)"', data, re.S)
		if Tab_els:
			url=Tab_els[0]
			if url.startswith('//'): url='http:'+url
			if ('ok.php?id=' in url):
				url='http://ok.ru/videoembed/'+url.split('ok.php?id=',1)[1]
			elif ('beinmatch.' in url):
				sts, data1 = self.getPage(url)
				if sts:
					Tab_els1 = re.findall('<iframe.*?src="(.*?)"', data1, re.S)
					if Tab_els1:
						url=Tab_els1[0]
			urlTab.append({'name':'Video', 'url':url, 'need_resolve':1})
		else:
			Tab_els = re.findall('source.*?["\'](.*?)["\']', data, re.S)
			if Tab_els:
				meta_={'Referer':URL,'Origin':'http://beinmatch.tv'}
				url=strwithmeta(Tab_els[0],meta_)
			if 'm3u8' in url:
				urlTab = getDirectM3U8Playlist(url, checkExt=True, checkContent=True, sortWithMaxBitrate=999999999)
			else:
				urlTab.append({'name':'Video', 'url':url, 'need_resolve':0})		
		return urlTab
		

		
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		if mode=='20':
			self.showmatch1(cItem)
		elif mode=='21':
			self.showmatch2(cItem)
		elif mode=='25':
			self.showreplay1(cItem)
		elif mode=='26':
			self.showreplay2(cItem)
