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
	info_['name']='Assabile.Com'
	info_['version']='1.0 05/05/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='204'
	info_['desc']='Quran Audio Library'
	info_['icon']='http://ar.assabile.com/img/logo-assabile.png'
	info_['recherche_all']='0'
	return info_
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'mp3quran.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'http://ar.assabile.com'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'X-Requested-With': 'XMLHttpRequest','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage

		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' :'host2','title':'القرآن','icon':cItem['icon'],'mode': '11'})		
#		self.addDir({'import':cItem['import'],'category' :'host2','title':'خطب','icon':cItem['icon'],'mode': '12'})		
#		self.addDir({'import':cItem['import'],'category' :'host2','title':'اناشيد و اذان','icon':cItem['icon'],'mode': '13'})				

	def showmenu11(self,cItem):
		self.addDir({'import':cItem['import'],'category' :'host2','title':'القراء','icon':cItem['icon'],'mode': '14'})		
		self.addDir({'import':cItem['import'],'category' :'host2','title':'نوعية التلاوة','icon':cItem['icon'],'mode': '15'})		
		self.addDir({'import':cItem['import'],'category' :'host2','title':'الروايات','icon':cItem['icon'],'mode': '17'})				



	def showmenu12(self,cItem):
		self.addDir({'import':cItem['import'],'category' :'host2','title':'دعات','icon':cItem['icon'],'mode': '21'})		
		self.addDir({'import':cItem['import'],'category' :'host2','title':'الدروس الاكثر مشاهدة','icon':cItem['icon'],'mode': '15'})		
		self.addDir({'import':cItem['import'],'category' :'host2','title':'جديد الدروس','icon':cItem['icon'],'mode': '17'})	



	def showmenu21(self,cItem):
		Url0='http://ar.assabile.com/lesson'
		sts, data = self.getPage(Url0) 
		if sts:
			data_ = re.findall('<li class="activeFilter">(.*?)id="sort-container"', data, re.S)
			if data_:
				data_2 = re.findall('<li.*?href="(.*?)".*?">(.*?)<', '<li '+data_[0], re.S)
				for (url,name) in data_2:
					self.addDir({'import':cItem['import'],'category' :'host2','title':name,'url':'http://ar.assabile.com'+url,'icon':cItem['icon'],'mode': '22'})

	def showmenu22(self,cItem):
		page=cItem.get('page',1)
		uRL=	cItem['url']
		Url0=uRL+'/page:'+str(page)
		sts, data = self.getPage(Url0) 
		if sts:
			data_ = re.findall('portfolio-image">.*?href="(.*?)".*?src="(.*?)".*?title="(.*?)"', data, re.S)
			i=0
			for (url,image,name) in data_:
				if name !='':
					self.addDir({'import':cItem['import'],'category' :'host2','title':name,'url':'http://ar.assabile.com'+url,'icon':'http://ar.assabile.com'+image,'mode': '30'})
					i=i+1
			if i>10:
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'Next','url':uRL,'page':page+1,'mode':'20'})
			
		
	def showmenu14(self,cItem):
		Url0='http://ar.assabile.com/quran'
		sts, data = self.getPage(Url0) 
		if sts:
			data_ = re.findall('<li class="activeFilter">(.*?)id="sort-container"', data, re.S)
			if data_:
				data_2 = re.findall('<li.*?href="(.*?)".*?">(.*?)<', '<li '+data_[0], re.S)
				for (url,name) in data_2:
					self.addDir({'import':cItem['import'],'category' :'host2','title':name,'url':'http://ar.assabile.com'+url,'icon':cItem['icon'],'mode': '20'})

	def showmenu15(self,cItem):
		Url0='http://ar.assabile.com/quran'
		sts, data = self.getPage(Url0) 
		if sts:
			data_ = re.findall('<div>المصاحف المسموعة</div>(.*?)<div>الروايات</div>', data, re.S)
			if data_:
				data_2 = re.findall('<li.*?href="(.*?)">(.*?)</a>', data_[0], re.S)
				for (url,name) in data_2:
					self.addDir({'import':cItem['import'],'category' :'host2','title':ph.clean_html(name),'url':'http://ar.assabile.com'+url,'icon':cItem['icon'],'mode': '16'})

	def showmenu16(self,cItem):
		page=cItem.get('page',1)
		uRL=	cItem['url']
		Url0=uRL+'/page:'+str(page)
		sts, data = self.getPage(Url0) 
		if sts:
			i=0
			data_ = re.findall('name-surat">.*?href="(.*?)".*?data-recitation="(.*?)".*?data-name="(.*?)".*?reciters">(.*?)<.*?<span>(.*?)</span>', data, re.S)
			for (url,desc,name,desc2,riwaya) in data_:
				if name !='':
					i=i+1
					self.addDir({'import':cItem['import'],'category' :'host2','title':name+' - '+ph.clean_html(riwaya)+ ' - '+desc2,'desc':tscolor('\c00????00')+' تلاوة'+desc,'url':'http://ar.assabile.com'+url,'icon':cItem['icon'],'mode': '31'})
			if i>14:
				self.addDir({'import':cItem['import'],'category' : 'host2','icon':cItem['icon'],'title':'Next','url':uRL,'page':page+1,'mode':'16'})

	def showmenu17(self,cItem):
		Url0='http://ar.assabile.com/quran'
		sts, data = self.getPage(Url0) 
		if sts:
			data_ = re.findall('<div>الروايات</div>(.*?)"/quran/top">', data, re.S)
			if data_:
				data_2 = re.findall('<li.*?href="(.*?)">(.*?)</a>', data_[0], re.S)
				for (url,name) in data_2:
					self.addDir({'import':cItem['import'],'category' :'host2','title':ph.clean_html(name),'url':'http://ar.assabile.com'+url,'icon':cItem['icon'],'mode': '16'})



								
	def showmenu20(self,cItem):
		page=cItem.get('page',1)
		uRL=	cItem['url']
		Url0=uRL+'/page:'+str(page)
		sts, data = self.getPage(Url0) 
		if sts:
			data_ = re.findall('portfolio-image">.*?href="(.*?)".*?src="(.*?)".*?title="(.*?)"', data, re.S)
			i=0
			for (url,image,name) in data_:
				if name !='':
					self.addDir({'import':cItem['import'],'category' :'host2','title':name,'url':'http://ar.assabile.com'+url,'icon':'http://ar.assabile.com'+image,'mode': '30'})
					i=i+1
			if i>10:
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'Next','url':uRL,'page':page+1,'mode':'20'})

	def showmenu30(self,cItem):
		uRL=	cItem['url']
		data_ = re.findall('(.*)/', uRL, re.S)
		if data_:
			URL=data_[0]+'/collection'
			sts, data = self.getPage(URL) 
			if sts:
				data_ = re.findall('name-surat">.*?href="(.*?)".*?data-recitation="(.*?)".*?data-name="(.*?)".*?data-riwaya="(.*?)"', data, re.S)
				for (url,desc,name,riwaya) in data_:
					if name !='':
						self.addDir({'import':cItem['import'],'category' :'host2','title':name+' - '+riwaya,'desc':tscolor('\c00????00')+' تلاوة'+desc,'url':'http://ar.assabile.com'+url,'icon':cItem['icon'],'mode': '31'})


	def showmenu31(self,cItem):
		uRL=	cItem['url']
		sts, data = self.getPage(uRL) 
		if sts:
			data_ = re.findall('class="name">.*?link-media never".*?href="#(.*?)".*?">(.*?)</a.*?"timer">(.*?)<', data, re.S)
			for (url,name,desc) in data_:
				if name !='':
					self.addAudio({'import':cItem['import'],'category' :'host2','title':ph.clean_html(name),'desc':desc,'url':url,'icon':cItem['icon'],'hst': 'tshost'})



	def get_links(self,cItem): 	
		urlTab = []
		URL='http://ar.assabile.com/ajax/getrcita-link-'+cItem['url']
		
		sts, data = self.getPage(URL,self.defaultParams)
		if sts:
			if data:
				urlTab.append({'name':cItem['title'], 'url':data, 'need_resolve':0})
		return urlTab	





	def start(self,cItem):
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu(cItem)
		if mode=='11':
			self.showmenu11(cItem)
		if mode=='14':
			self.showmenu14(cItem)
		if mode=='15':
			self.showmenu15(cItem)
		if mode=='16':
			self.showmenu16(cItem)
		if mode=='17':
			self.showmenu17(cItem)
		if mode=='20':
			self.showmenu20(cItem)
		if mode=='21':
			self.showmenu21(cItem)
		if mode=='22':
			self.showmenu22(cItem)
		if mode=='30':
			self.showmenu30(cItem)
		if mode=='31':
			self.showmenu31(cItem)			
			
			
			
		return True
