# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
###################################################


import re
import base64
import urllib

def getinfo():
	info_={}
	info_['name']='RobinDesDroits.Me'
	info_['version']='1.0 20/07/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='110'
	info_['desc']='Sports Replay VF'
	info_['icon']='https://i.ibb.co/4f0fLpP/bs1kgdez.png'
	info_['recherche_all']='1'
	info_['update']='New Host'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'robindesdroits.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'http://robindesdroits.me'
		self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'with_metadata':True,'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

	def getPage(self,baseUrl, addParams = {}, post_data = None):
		while True:
			if addParams == {}: addParams = dict(self.defaultParams)
			origBaseUrl = baseUrl
			baseUrl = self.cm.iriToUri(baseUrl)
			addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
			sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
			printDBG(str(sts))
			if sts and 'class="loading"' in data:
				GetIPTVSleep().Sleep(5)
				continue
			break
		return sts, data
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']					
		Cat_TAB = [
					{'category':hst,'title': 'Nouveautés',       'mode':'30','url':self.MAIN_URL + '/derniers-uploads/'},
					{'category':hst,'title': 'Football',         'mode':'30','url':self.MAIN_URL + '/football/'},
					{'category':hst,'title': 'Rugby',            'mode':'30','url':self.MAIN_URL + '/rugby/'},					
					{'category':hst,'title': 'Basketball',       'mode':'30','url':self.MAIN_URL + '/basketball/'},							
					{'category':hst,'title': 'Sport Automobiles','mode':'30','url':self.MAIN_URL + '/sports-automobiles/'},							
					{'category':hst,'title': 'Sport US',         'mode':'30','url':self.MAIN_URL + '/sports-us/'},							
					{'category':hst,'title': 'Tennis',           'mode':'30','url':self.MAIN_URL + '/tennis/'},							
					{'category':hst,'title': 'Handball',         'mode':'30','url':self.MAIN_URL + '/handball/'},							
					{'category':hst,'title': 'Divers',           'mode':'30','url':self.MAIN_URL + '/divers/'},					
					#{'category':hst,'title': 'By Genre',         'mode':'21','sub_mode':0},
					{'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},					
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})		
	
	
		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		url1=url1+'page/'+str(page)+'/'
		sts, data = self.getPage(url1)
		printDBG('ddddddddddddddddddddddddddd'+data)
		sPattern = 'mh-loop-thumb">.*?href="(.*?)".*?url\(\'(.+?)\'.*?bookmark">(.+?)</h3>'
		data_list = re.findall(sPattern, data, re.S)
		i=0
		for (url,image,titre) in data_list:
			i=i+1
			self.addVideo({'import':cItem['import'],'category' : 'host2','url': url,'title':ph.clean_html(titre),'desc':'','icon':image,'hst':'tshost','good_for_fav':True})	
		if i>9:
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000????')+'Page Suivante','page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			data_list = re.findall('mh-loop-thumb">.*?href="(.*?)".*?url\(\'(.+?)\'.*?bookmark">(.+?)</h3>', data, re.S)
			for (url,image,titre) in data_list:
				self.addVideo({'import':extra,'category' : 'host2','url': url,'title':ph.clean_html(titre),'desc':'','icon':image,'hst':'tshost','good_for_fav':True})	


	def get_links(self,cItem):
		urlTab = []
		URL=cItem['url']
		sts, data = self.getPage(URL)
		data_list = re.findall('<a href="([^"]+)">(?:<span.+?|)<b>([^<]+)</b>.+?</span>', data, re.S)
		for (url,host) in data_list:
			if ('ulti' not in host) and ('heberg' not in host):
				urlTab.append({'name':host.replace('&#8211;','-'), 'url':'hst#tshost#'+url, 'need_resolve':1})
					
		return urlTab	
		 
	def getVideos(self,videoUrl):
		urlTab = []
		sts, data = self.getPage(videoUrl)
		if sts:
			if '<meta http-equiv="refresh"' in data:
				data_list = re.findall('URL=(.*?)"', data, re.S)
				if data_list:
					videoUrl=data_list[0]
					sts, data = self.getPage(videoUrl)
			if 'AdF' in data:
				printDBG('ffffffffffff1'+data)
				sUrl = self.AdflyDecoder(videoUrl)
				if 'motheregarded' in sUrl:
					data_list = re.findall('href=(.+?)&dp_lp', sUrl, re.S)
					if data_list:
						sUrl = urllib.unquote(''.join(data_list[0])).decode('utf8')
				sts, data = self.getPage(sUrl)
			if sts:
				printDBG('ffffffffffff'+data)
				data_list = re.findall('<b><a href=".+?redirect\/\?url\=(.+?)\&id.+?">', data, re.S)
				if data_list:
					uurl=data_list[0].replace('%3A',':').replace('%2F','/').replace('%0D','/')
					urlTab.append((uurl,'1'))
		return urlTab

	def AdflyDecoder(self,url):
		code=''
		sts, data = self.getPage(url)
		if sts:
			data_list = re.findall("var ysmm = '([^']+)'", data, re.S)
			if data_list:
				from base64 import b64decode
				code = data_list[0]
				A = ''
				B = ''
				#First pass
				for num in enumerate(code):
					if num % 2 == 0:
						A += code[num]
					else:
						B = code[num] + B
				code = A + B

				#Second pass
				m = 0
				code = list(code)
				while m < len(code) :
					if code[m].isdigit() :
						R = m + 1
						while R < len(code):
							if code[R].isdigit() :
								S = int(code[m]) ^ int(code[R])
								if (S < 10):
									code[m] = str(S)
								m = R
								R = len(code)
							R += 1
					m += 1
				code = ''.join(code)
				code = b64decode(code)
				code = code[16:]
				code = code[:-16]
		return code


	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='21':
			self.showmenu2(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelms(cItem)
			
