# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass

import re

def getinfo():
	info_={}
	info_['name']='Mania Tv (Android App)'
	info_['version']='1.2 02/10/2019'
	info_['dev']='RGYSoft & handawi66'
	info_['cat_id']='100'#'104'
	info_['desc']='تطبيق اندوريد للبث المباشر'
	info_['icon']='https://media.cdnandroid.com/60/1a/58/af/imagen-yacine-tv-app-0thumb.jpg'
	info_['update']='Fix Links (only bein Sports)'	
	info_['recherche_all']='0'
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'liveplus.cookie'})
		self.Player_Agent ='www.yacineapp.tv'
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
		
	def get_cofig(self):
		#Bein	
		self.xtream_Agent = 'www.yacineapp.tv'
		self.xtream_Host  = 'http://yacinebeiin.ddns.net:8000'
		self.xtream_User  = 'beiinno6jojj0'
		self.xtream_Pass  = 'beiinno6jojj0'
		#Boomrang
		self.xtream_Agent2 = 'www.yacineapp.tv'
		self.xtream_Host2  = 'http://yacine-tvapk.ddns.net:8000'
		self.xtream_User2  = 'yacine01kok15'
		self.xtream_Pass2  = 'yacine01kok15'
		#Csat
		self.xtream_Agent3 = 'www.yacineapp.tv'
		self.xtream_Host3  = 'http://frryacineuuk.ddns.net:8000'
		self.xtream_User3  = 'yacineff09non3'
		self.xtream_Pass3  = 'yacineff09non3'

		Url_conf = 'https://pastebin.com/dl/jtUKnLwd'
		sts,data=self.getPage(Url_conf)
		if sts:
			try:
				exec(data)
			except:
				printDBG('erreur file')	
		if self.xtream_User	== 'beiinno045':
			self.xtream_User  = 'beiinno03341'
			self.xtream_Pass  = 'beiinno03341'
		
		self.xtream_Agent2 = self.Player_Agent
		self.xtream_Agent3 = self.Player_Agent
			
	def showmenu(self,cItem):

		self.get_cofig()
		
		
		
		'''
		sts,data=self.getPage('http://www.yacinelive.com/app/api.php?cat')
		printDBG('dattttta='+data)
		data = json_loads(data)
		
		elmdata = data['data']	
		printDBG('ffffffffffffff'+	str(elmdata))
		for elm in 	elmdata:
			titre=elm['category_name']
			code=elm['cid']
			self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':code,'desc':'','icon':cItem['icon'],'mode':'20'})
		'''
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'title': 'Bein Sport 720p',     'sub_mode':'0'},
					{'title': 'Bein Sport 360p',     'sub_mode':'1'},
					#{'title': 'Bein Sport 244p',     'sub_mode':'2'},
					#{'title': 'Bein Entertainment',  'sub_mode':'3'},					
					#{'title': 'Kids Channels',       'sub_mode':'4'},					
					]
		self.listsTab(Cat_TAB, {'category':hst,'import':cItem['import'],'icon':img_,'mode':'20','desc':''})				
	
		
	def showmenu2(self,cItem):
		'''
		code=cItem['url']
		sts,data=self.getPage('http://www.yacinelive.com/app/api.php?cat_id='+code)
		data = json_loads(data)
		elmdata = data['data']		
		for elm in 	elmdata:
			titre=elm['channel_title']
			url=elm['channel_url']
			image=elm['channel_thumbnail']
			url_tmp=url.split('/')
			if len(url_tmp)==6:
				type_=url_tmp[3]
				if type_=='tv':
					url=self.xtream_Host+'/live/'+self.xtream_User+'/'+self.xtream_Pass+'/'+url_tmp[5]+'.ts'
					url = strwithmeta(url, {'User-Agent':self.xtream_Agent})
				else:
					#url=self.xtream_Host2+'/live/'+self.xtream_User2+'/'+self.xtream_Pass2+'/'+url_tmp[5]+'.ts'
					url = strwithmeta(url, {'User-Agent':self.xtream_Agent2})			
				self.addVideo({'import':cItem['import'],'title':titre,'url':url,'icon':image,'hst':'direct'})
			elif len(url_tmp)==7:
				if 'alkass' in titre:
					#url=self.xtream_Host2+'/live/'+self.xtream_User2+'/'+self.xtream_Pass2+'/'+url_tmp[6]+'.ts'
					url = strwithmeta(url, {'User-Agent':self.xtream_Agent2})					
				else:
					#url=self.xtream_Host3+'/live/'+self.xtream_User3+'/'+self.xtream_Pass3+'/'+url_tmp[6]+'.ts'
					url = strwithmeta(url, {'User-Agent':self.xtream_Agent3})				
				self.addVideo({'import':cItem['import'],'title':titre,'url':url,'icon':image,'hst':'direct'})
				
		'''	
		gnr=cItem['sub_mode']
		url_prefix=self.xtream_Host+'/live/'+self.xtream_User+'/'+self.xtream_Pass+'/'
		if gnr == '0':
			self.addVideo({'import':cItem['import'],'title':'Bein Sport News HD' ,'url':strwithmeta(url_prefix+'146.ts' , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 1'   ,'url':strwithmeta(url_prefix+'6.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 2'   ,'url':strwithmeta(url_prefix+'7.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 3'   ,'url':strwithmeta(url_prefix+'8.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 4'   ,'url':strwithmeta(url_prefix+'9.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 5'   ,'url':strwithmeta(url_prefix+'10.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 6'   ,'url':strwithmeta(url_prefix+'12.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 7'   ,'url':strwithmeta(url_prefix+'20.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 8'   ,'url':strwithmeta(url_prefix+'21.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports HD 9'   ,'url':strwithmeta(url_prefix+'22.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
		
		if gnr == '1':
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 1'   ,'url':strwithmeta(url_prefix+'1.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 2'   ,'url':strwithmeta(url_prefix+'2.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 3'   ,'url':strwithmeta(url_prefix+'3.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 4'   ,'url':strwithmeta(url_prefix+'4.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 5'   ,'url':strwithmeta(url_prefix+'5.ts'   , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 6'   ,'url':strwithmeta(url_prefix+'13.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 7'   ,'url':strwithmeta(url_prefix+'20.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 8'   ,'url':strwithmeta(url_prefix+'21.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
			self.addVideo({'import':cItem['import'],'title':'Bein Sports SD 9'   ,'url':strwithmeta(url_prefix+'22.ts'  , {'User-Agent':self.xtream_Agent}),'icon':cItem['icon'],'hst':'direct'})
		
			
	def start(self,cItem):
		list_=[]
		mode=cItem.get('mode', None)
		if mode=='00':
			list_ = self.showmenu(cItem)	
		elif mode=='20':
			list_ = self.showmenu2(cItem)

		return True
