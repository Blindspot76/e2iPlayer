# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tunisia_gouv,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Components.config import config
import re
import urllib
import HTMLParser


def getinfo():
	info_={}
	info_['name']='MP3Quran.Net'
	info_['version']='1.1 07/07/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='24'
	info_['desc']='Quran Audio Library'
	info_['icon']='https://i.ibb.co/4M5FBQR/logo2.png'
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


	def getPage(self,baseUrl, addParams = {}, post_data = None):
		while True:
			if addParams == {}: addParams = dict(self.defaultParams)
			origBaseUrl = baseUrl
			baseUrl = self.cm.iriToUri(baseUrl)
			sts, data = self.cm.getPage(baseUrl, addParams, post_data)			
			return sts, data	

			
	def showmenu(self,cItem):	
		#self.addDir({'import':cItem['import'],'category' :'host2','title':'Videos | '+'المكتبة المرئية','icon':cItem['icon'],'mode': '30','url':'https://videos.mp3quran.net/Site/Gallery/VideosGroup/76'})		
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Reciters | '+'القرّاء'+' Ar','icon':cItem['icon'],'mode': '20','lng':'ar'})			
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Reciters | '+'القرّاء'+' En','icon':cItem['icon'],'mode': '20','lng':'eng'})			
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Radios','icon':cItem['icon'],'mode': '21'})			
		self.addAudio({'import':cItem['import'],'title':'LIVE Radio','url':'http://live.mp3quran.net:8006/;','icon':cItem['icon'],'desc':tscolor('\c00??0000')+'LIVE','hst':'direct'})			


	def showmenu1(self,cItem):
		lng = cItem['lng']
		Url=self.MAIN_URL + '/'+lng+'/ajax?r=0&t=all'
		addParams = dict(self.defaultParams)
		addParams['header']['X-Requested-With'] = 'XMLHttpRequest'
		sts, data = self.getPage(Url,addParams) 	
		if sts:
			data = json_loads(data)
			reads = data.get('reads',{})
			for key, value in sorted(reads.items(), key=lambda t: t[0]):
				self.addMarker({'title':key,'icon':cItem['icon']})
				for elm in value:
					titre   = elm.get('title','')
					count   = elm.get('soar_count','')
					rewaya  = elm.get('rewaya_name','')
					reciter = elm.get('reciter_name','')
					id_     = elm.get('id','')
					slug    = elm.get('slug','')					
					desc = tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+count+'\n'
					desc = desc + tscolor('\c00????00')+'Reciter: '+tscolor('\c00??????')+reciter+'\n'
					desc = desc + tscolor('\c00????00')+'Rewaya: '+tscolor('\c00??????')+rewaya+'\n'
					self.addDir({'import':cItem['import'],'category' :'host2','title':titre,'desc':desc,'icon':cItem['icon'],'slug':slug,'mode': '40','lng':lng})
						
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
		lng = cItem['lng']
		slug = cItem['slug']
		Url=self.MAIN_URL + '/'+lng+'/ajax/'+slug
		addParams = dict(self.defaultParams)
		addParams['header']['X-Requested-With'] = 'XMLHttpRequest'
		sts, data = self.getPage(Url,addParams) 	
		if sts:
			data = json_loads(data)
			reciter = data.get('reciter',{})
			reads_ = reciter.get('reads',[])
			for reads in reads_:
				soar = reads.get('soar',[])
				for elm in soar:
					titre = elm.get('sora_name','')
					url   = elm.get('sora_audio','')
					time_ = elm.get('sora_duration','')
					num   = elm.get('sora_num','')	
					self.addAudio({'import':cItem['import'],'title':titre,'url':url,'icon':cItem['icon'],'desc':'Duration: '+tscolor('\c00????00')+str(time_)+'\\n'+tscolor('\c00??????')+'Num: '+tscolor('\c00????00')+str(num),'hst':'direct'})			
		
				 

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
