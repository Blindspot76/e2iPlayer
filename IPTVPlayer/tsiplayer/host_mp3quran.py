# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tunisia_gouv,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Components.config import config
import re
import urllib
import HTMLParser

tunisia_gouv_code = [0,23,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,24]

def getinfo():
	info_={}
	info_['name']='MP3Quran.Net'
	info_['version']='1.0 05/05/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='204'
	info_['desc']='Quran Audio Library'
	info_['icon']='https://www.mp3quran.net/images/quraan-logo.png'
	info_['recherche_all']='0'
	return info_
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'mp3quran.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.mp3quran.net'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		#self.getPage = self.cm.getPage
		
	def showmenu(self,cItem):	
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Videos | '+'المكتبة المرئية','icon':cItem['icon'],'mode': '30','url':'https://videos.mp3quran.net/Site/Gallery/VideosGroup/76'})		
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Reciters | '+'القرّاء'+' Ar','icon':cItem['icon'],'mode': '20','sub_mode':'1'})			
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Reciters | '+'القرّاء'+' En','icon':cItem['icon'],'mode': '20','sub_mode':'2'})			
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Radios','icon':cItem['icon'],'mode': '21'})			
		self.addAudio({'import':cItem['import'],'title':'LIVE Radio','url':'http://live.mp3quran.net:8006/;','icon':cItem['icon'],'desc':tscolor('\c00??0000')+'LIVE','hst':'direct'})			

	def showmenu1(self,cItem):
		lng_id=	cItem['sub_mode']
		Url0='https://www.mp3quran.net/changement-lang.php'
		post_data0={'langue':lng_id}
		self.getPage(Url0,post_data=post_data0) 
		Url='https://www.mp3quran.net/includes/ajax.php'
		post_data={'lang_id':lng_id,'search':'all','action':'filterByLetter'}
		sts, data = self.getPage(Url,post_data=post_data) 	
		if sts:
			data_ = re.findall('reciter-item.*?id="(.*?)".*?reciter-name.*?>(.*?)<', data, re.S)
			for (id_,name) in data_:
				self.addDir({'import':cItem['import'],'category' :'host2','title':name,'icon':cItem['icon'],'rec_id':id_,'mode': '40','sub_mode':lng_id})
						
	def showmenu2(self,cItem):
		url='http://api.mp3quran.net/radios/get_radios.php'
		sts, data = self.getPage(url) 
		if sts:
			data = json_loads(data)
			for elm in data['language']:
				id_=elm['id']
				language=elm['language']
				radio_url=elm['radio_url']
				self.addDir({'import':cItem['import'],'category' :'host2','title':language,'url':radio_url,'icon':cItem['icon'],'mode': '22'})
			
	def showmenu3(self,cItem):
		url=cItem['url']
		sts, data = self.getPage(url)
		if sts: 
			data = json_loads(data)
			for elm in data['radios']:
				name=elm['name']
				radio_url=elm['radio_url']
				self.addAudio({'import':cItem['import'],'title':name,'url':radio_url,'icon':cItem['icon'],'hst': 'direct'})

		
		

	def showitms(self,cItem):		
		Url=cItem['url']
		page=cItem.get('page',1)
		url_=Url+'?page='+str(page)
		sts, data = self.getPage(url_) 	
		if sts:
			data_ = re.findall('class="thumbnail">.*?href="(.*?)".*?src="(.*?)".*?<h5>(.*?)</h5>', data, re.S)
			for (url,image,titre) in data_:
				url='https://videos.mp3quran.net'+url.replace('//','/')
				image='https://videos.mp3quran.net'+image
				self.addVideo({'import':cItem['import'],'category' :'host2','title':titre,'url':url,'icon':image,'hst': 'tshost'})			
			self.addDir({'import':cItem['import'],'category' : 'host2','title':'Next','url':Url,'page':page+1,'mode':'30'})


			
	def showitms1(self,cItem):		
		rec_id=	cItem['rec_id']
		Url='https://www.mp3quran.net/includes/ajax.php'
		post_data={'readerID':rec_id,'action':'reader_slider_by_alias'}
		sts, data = self.getPage(Url,post_data=post_data) 	
		if sts:
			data = json_loads(data)
			id_=data['id']
			name_=data['name']
			
			
			Url='https://www.mp3quran.net/includes/reciter_page.php'
			post_data={'alias':rec_id,'action':'ajaxreader'}
			sts, data = self.getPage(Url,post_data=post_data) 
			if sts:	
				data_ = re.findall('"ms_weekly_box">.*?data-name="(.*?)".*?data-media="(.*?)".*?<h3>(.*?)</h3>.*?<p>(.*?)<', data, re.S)
				for (desc,url,name,time_) in data_:
					self.addAudio({'import':cItem['import'],'title':ph.clean_html(name),'url':url,'icon':cItem['icon'],'desc':'duration: '+tscolor('\c00????00')+time_+'\\n '+tscolor('\c00??????')+'Reciters: '+tscolor('\c00????00')+desc,'hst':'direct'})			
				
				Url='https://www.mp3quran.net/includes/ajax.php'
				post_data={'loadReaderId':id_,'page':'NaN','classification_id':'1','action':'loadMoreByReader'}
				sts, data = self.getPage(Url,post_data=post_data)
				if sts: 	
					data_ = re.findall('"ms_weekly_box">.*?data-name="(.*?)".*?data-media="(.*?)".*?<h3>(.*?)</h3>.*?<p>(.*?)<', data, re.S)
					for (desc,url,name,time_) in data_:
						self.addAudio({'import':cItem['import'],'title':ph.clean_html(name),'url':url,'icon':cItem['icon'],'desc':'duration: '+tscolor('\c00????00')+time_+'\\n '+tscolor('\c00??????')+'Reciters: '+tscolor('\c00????00')+desc,'hst':'direct'})			
		
			
	def getPage(self,baseUrl, addParams = {}, post_data = None):
		while True:
			if addParams == {}: addParams = dict(self.defaultParams)
			origBaseUrl = baseUrl
			baseUrl = self.cm.iriToUri(baseUrl)
			sts, data = self.cm.getPage(baseUrl, addParams, post_data)			
			return sts, data		 

	def get_links(self,cItem): 	
		urlTab = []
		URL=cItem['url']	
		sts, data = self.getPage(URL)
		if sts:
			_data = re.findall('video-grid">.*?src="(.*?)"', data, re.S)
			if _data:
				url='https://videos.mp3quran.net'+_data[0]
				url=url.replace('&#39;',"'")
				urlTab.append({'name':cItem['title'], 'url':url, 'need_resolve':0})
		return urlTab	




	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='21':
			self.showmenu2(cItem)
		if mode=='22':
			self.showmenu3(cItem)
		if mode=='30':
			self.showitms(cItem)
		if mode=='40':
			self.showitms1(cItem)		
		return True
