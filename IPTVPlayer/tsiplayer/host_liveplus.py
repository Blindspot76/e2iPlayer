# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re

def getinfo():
	info_={}
	info_['name']='Live-Plus (Android App)'
	info_['version']='1.0 16/04/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='100'
	info_['desc']='لايف بلس - تطبيق اندوريد للبث المباشر ونقل المباريات'
	info_['icon']='https://1.bp.blogspot.com/-3pyupZsjjYQ/XCebvbl5wrI/AAAAAAAAE7Y/ImJpNdUk2EQGupEYnsfUOFXfkBBuY_4JQCLcBGAs/s640/DOWNLOAD%2BLIVE%2BPLUS%2BAPK%2B2018.png'
	info_['recherche_all']='0'
	return info_

class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'liveplus.cookie'})
		self.Player_Agent ='ExoPlayerDemo/80.0 (Linux;Android 7.1.1) ExoPlayerLib/2.5.3'
		self.USER_AGENT = 'okhttp/3.8.0'
		self.MAIN_URL = 'http://www.live-plus.io'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Accept':'application/json','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

	def get_token(self):
		payload={'grant_type':'client_credentials','client_id':'20','client_secret':'6RzVdIW8wsASXBUJ8HDj4CYLRq62bNI6khr5q0pJ','scope':'*'}
		sts,data=self.getPage('http://www.live-plus.io/oauth/token', post_data = payload)
		data = json_loads(data)
		tokendata = data['access_token']
		return tokendata   			
		
	def getPage(self,baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		origBaseUrl = baseUrl
		baseUrl = self.cm.iriToUri(baseUrl)
		sts, data = self.cm.getPage(baseUrl, addParams, post_data)
		return sts,data	
		
		
	def showmenu(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'مباريات اليوم','url':'','icon':cItem['icon'],'mode':'20'})
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'قنوات'        ,'url':'','icon':cItem['icon'],'mode':'30'})
		self.HEADER.update({'Authorization': 'Bearer '+self.get_token()})
		self.defaultParams.update({'header':self.HEADER})		


	def showlive(self,cItem):
		sts,data=self.getPage('http://www.live-plus.io:80/api/home')
		data = json_loads(data)
		elmdata = data['items']['all']
		for elm in 	elmdata:
			desc=tscolor('\c00????00')+elm['text']
			img=elm['image']
			self.addMarker({'title':desc,'desc':desc,'icon':img})
			for match in elm['match']:
				titre=match['team']+' Vs '+match['team2']
				data=match['commentators']
				date_=match['match_date_time']
				res1=match['team_2_result']
				res2=match['team_2_result']
				statut=match['is_live']
				if match['is_live']==1:
					statut= tscolor('\c0000??00')+'  (LIVE)'
				else:
					x1,x2,x3 = date_.split(' ')
					statut= tscolor('\c00????00')+'  ['+x2+' '+x3+']'
				desc=tscolor('\c00????00')+'Date: '+date_
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'# Match: '+titre+' #'+statut,'url':data,'desc':desc,'icon':img,'mode':'21'})

	def getlive(self,cItem):
		data=cItem.get('url', '')
		for comm in data:
			titre=comm['title']
			for data2 in comm['channel']:
				titre2=tscolor('\c00????00')+data2['name']+' - '+tscolor('\c0000??00')+titre
				image=data2['image']
				self.addMarker({'title':titre2,'icon':image})
				for serv in data2['servers']:
					titre=serv['title']
					url=serv['secure_url']
					params = dict(self.defaultParams)
					params['no_redirection'] = True
					sts,data=self.getPage(url,params)
					red=self.cm.meta.get('location', '')
					url = strwithmeta(red.replace('/_definst_/','/'), {'User-Agent':self.Player_Agent})
					self.addVideo({'import':cItem['import'],'title':titre,'url':url,'icon':image,'hst':'direct'})			

	def showgroup(self,cItem):
		sts,data=self.getPage('http://www.live-plus.io:80/api/channels')
		data = json_loads(data)
		elmdata = data['all']
		for elm in 	elmdata:
			text=elm['text']
			img=elm['image']
			data=elm['channels']
			self.addDir({'import':cItem['import'],'category' : 'host2','title':text,'url':data,'icon':img,'mode':'31'})

	def showchan(self,cItem):
		data=cItem.get('url', '')
		for elm in data:
			titre=elm['name']
			image=elm['image']
			servers=elm['servers']
			self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':servers,'icon':image,'mode':'32'})

	def getchan(self,cItem):
		list_=[]
		data=cItem.get('url', '')
		for serv in data:
			titre=serv['title']
			url=serv['secure_url']
			params = dict(self.defaultParams)
			params['no_redirection'] = True
			sts,data=self.getPage(url,params)
			red=self.cm.meta.get('location', '')
			url = strwithmeta(red.replace('/_definst_/','/'), {'User-Agent':self.Player_Agent})
			self.addVideo({'import':cItem['import'],'title':titre,'url':url,'icon':cItem['icon'],'hst':'direct'})			
		return list_
		
		
	def start(self,cItem):
		list_=[]
		mode=cItem.get('mode', None)
		if mode=='00':
			list_ = self.showmenu(cItem)	
		elif mode=='20':
			list_ = self.showlive(cItem)
		elif mode=='21':
			list_ = self.getlive(cItem)
		elif mode=='30':
			list_ = self.showgroup(cItem)
		elif mode=='31':
			list_ = self.showchan(cItem)
		elif mode=='32':
			list_ = self.getchan(cItem)				
		'''							
		elif mode=='40':
			list_ = self.showresum(cItem)
		elif mode=='41':
			list_ = self.getresum(cItem)	
		'''
		return True

'''

	def showresum(self,cItem):
		list_=[]
		HEADER={'User-Agent':USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Accept':'application/json','Authorization': 'Bearer '+get_token()}
		defaultParams1 = {'header':HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
		addParams = dict(defaultParams1)
		sts,data=self.getPage('http://www.live-plus.io:80/api/videos')
		data = byteify(json.loads(data))
		printDBG('rrrrrrrrrrrrrrrrrrrr'+str(data))
		elmdata = data['data']
		for elm in 	elmdata:
			desc=elm['desc']
			img=elm['image']
			titre=elm['title']
			url=[]
			try:
				url1=elm['secure_url']
				url.append(url1)
			except:
				pass
			try:
				url2=elm['secure_url2']
				url.append(url2)
			except:
				pass			
			list_.append((titre,url,img,str(desc),'31','',1,False,False,))	
		return list_

	def getresum(self,cItem):
		list_=[]
		data=cItem.get('url', '')
		for url in data:
			url = strwithmeta(url, {'User-Agent':self.Player_Agent})
			list_.append((cItem['title'],url,'','','92','',1,False,False,))							
		return list_

'''			
