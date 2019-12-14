# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG,byteify
from Plugins.Extensions.IPTVPlayer.libs import ph

from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.tools.e2ijs import js_execute
###################################################

try:    import json
except Exception: import simplejson as json

import re
import base64

def getinfo():
	info_={}
	info_['name']='Streamlord.Com'
	info_['version']='1.0 30/05/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'#'401'
	info_['desc']='Films & Series'
	info_['icon']='http://www.streamlord.com/images/logo.png'
	info_['recherche_all']='0'
	info_['update']='New Host'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'streamlord1.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'http://www.streamlord.com'
		self.HTTP_HEADER = {'User-Agent': self.USER_AGENT, 'DNT':'1', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'with_metadata':True,'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}



	def getPage(self, url, addParams={}, post_data=None):
		if addParams == {}:
			addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file': self.COOKIE_FILE, 'User-Agent': self.HTTP_HEADER['User-Agent']}
		sts,data = self.cm.getPageCFProtection(url, addParams, post_data)
		if sts:
			if 'sucuri_cloudproxy' in data:
				cookieItems = {}
				jscode = self.cm.ph.getDataBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)[1]
				if 'eval' in jscode:
					jscode = '%s\n%s' % (base64.b64decode('''dmFyIGlwdHZfY29va2llcz1bXSxkb2N1bWVudD17fTtPYmplY3QuZGVmaW5lUHJvcGVydHkoZG9jdW1lbnQsImNvb2tpZSIse2dldDpmdW5jdGlvbigpe3JldHVybiIifSxzZXQ6ZnVuY3Rpb24obyl7bz1vLnNwbGl0KCI7IiwxKVswXS5zcGxpdCgiPSIsMiksb2JqPXt9LG9ialtvWzBdXT1vWzFdLGlwdHZfY29va2llcy5wdXNoKG9iail9fSk7dmFyIHdpbmRvdz10aGlzLGxvY2F0aW9uPXt9O2xvY2F0aW9uLnJlbG9hZD1mdW5jdGlvbigpe3ByaW50KEpTT04uc3RyaW5naWZ5KGlwdHZfY29va2llcykpfTs='''), jscode)
					ret = js_execute( jscode )
					if ret['sts'] and 0 == ret['code']:
						cookies = byteify(json.loads(ret['data'].strip()))
						for cookie in cookies: cookieItems.update(cookie)
				self.defaultParams['cookie_items'] = cookieItems
				addParams = dict(self.defaultParams)
				addParams['cloudflare_params'] = {'cookie_file': self.COOKIE_FILE, 'User-Agent': self.HTTP_HEADER['User-Agent']}
				removeCookieItems = False
				sts,data = self.cm.getPageCFProtection(url, addParams, post_data)
		
		return sts,data


		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']	
		#self.addVideo({'import':cItem['import'],'EPG':True,'category' : 'host2','url': 'http://www.streamlord.com/watch-movie-despicable-me-2-60.html','title':'test','desc':'','icon':'','hst':'tshost','good_for_fav':True})	
									
		Cat_TAB = [
					{'category':hst,'title': 'Movies', 'mode':'20','sub_mod':0},
					{'category':hst,'title': 'Tv Series', 'mode':'20','sub_mod':1},			
					#{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})
			
				
	def showmenu1(self,cItem):
		hst='host2'
		img_=cItem['icon']	
		gnr=cItem['sub_mod']
		if gnr==0:
			Cat_TAB = [
						{'category':hst,'title': 'NEWEST', 'mode':'30','url':'http://www.streamlord.com/movies.php'},
						{'category':hst,'title': 'RATING', 'mode':'30','url':'http://www.streamlord.com/movies.php?sortby=rating'},					
						{'category':hst,'title': 'By ABC', 'mode':'20','sub_mod':2,'url':'http://www.streamlord.com/movies.php'},
						{'category':hst,'title': 'By Genre', 'mode':'20','sub_mod':3},			
						]
			self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})			
		elif gnr==1:
			Cat_TAB = [
						{'category':hst,'title': 'NEWEST', 'mode':'30','url':'http://www.streamlord.com/series.php'},
						{'category':hst,'title': 'RATING', 'mode':'30','url':'http://www.streamlord.com/series.php?sortby=rating'},					
						{'category':hst,'title': 'By ABC', 'mode':'20','sub_mod':2,'url':'http://www.streamlord.com/series.php'},		
						]
			self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})				
		elif gnr==2:		
			sts, data = self.getPage(cItem['url'])
			if sts:
				data_list = re.findall('<div id="alphabet"(.*?)</div>', data, re.S)
				if data_list:
					data_list2 = re.findall('href="(.*?)".*?>(.*?)<', data_list[0], re.S)
					for (url,titre) in data_list2:
						url=url.replace('./',self.MAIN_URL+'/')
						self.addDir({'import':cItem['import'],'category' : hst,'url': url,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
		elif gnr==3:		
			sts, data = self.getPage('http://www.streamlord.com/movies.php')
			if sts:
				data_list = re.findall('<ul class="fallback">(.*?)</ul', data, re.S)
				if data_list:
					data_list2 = re.findall('href="(.*?)".*?>(.*?)<', data_list[0], re.S)
					for (url,titre) in data_list2:
						url=url.replace('./',self.MAIN_URL+'/')
						self.addDir({'import':cItem['import'],'category' : hst,'url': url,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
			
		
	def showitms(self,cItem):
		url1=cItem['url']
		urlo=cItem['url']
		page=cItem.get('page',1)
		if 'php' in url1:
			if '?' in url1:
				url1=url1+'&page='+str(page)
			else:
				url1=url1+'?page='+str(page)
		else:
			sts, data = self.getPage(url1)
			if sts:			
				data_list = re.findall('id="pagination".*?href="(.*?)&page=', data, re.S)
				if data_list:
					urlo=self.MAIN_URL+data_list[0].replace('./','/')
					url1=urlo+'&page='+str(page)
			
		sts, data = self.getPage(url1)
		if sts:
	#		data_list = re.findall('class="movie">.*?href="(.*?)".*?src=\'(.*?)\'.*?grid-title">(.*?)<.*?runtime">(.*?)<.*?year">(.*?)<.*?rating">(.*?)</.*?description">(.*?)<div', data, re.S)
			data_list = re.findall('class="movie">.*?href="(.*?)".*?src=\'(.*?)\'.*?grid-title">(.*?)<(.*?)description">(.*?)<div', data, re.S)
			i=0
			for (url,image,titre,x1,desc) in data_list:
				i=i+1
				inf=''
				datax=re.findall('runtime">(.*?)<', x1, re.S)
				if  datax: inf=inf+tscolor('\c00????00')+'Runtime:'+tscolor('\c00??????')+' '+datax[0]+'\\n'
				datax=re.findall('year">(.*?)<', x1, re.S)
				if  datax:
					if datax[0].strip() != '':
						inf=inf+tscolor('\c00????00')+'Year:'+tscolor('\c00??????')+' '+datax[0]+'\\n'			
				datax=re.findall('rating">(.*?)</p', x1, re.S)
				if  datax: 
					if 'ended' in datax[0]:
						inf=inf+tscolor('\c00????00')+'Statut:'+tscolor('\c00??????')+' Ended\\n'
						inf=inf+tscolor('\c00????00')+'Rating:'+tscolor('\c00??????')+' '+datax[0].replace('ended','')+'\\n'
					elif 'returning series' in datax[0]:
						inf=inf+tscolor('\c00????00')+'Statut:'+tscolor('\c00??????')+' Returning Series\\n'
						inf=inf+tscolor('\c00????00')+'Rating:'+tscolor('\c00??????')+' '+datax[0].replace('returning series','')+'\\n'				
					else:
						inf=inf+tscolor('\c00????00')+'Rating:'+tscolor('\c00??????')+' '+datax[0]+'\\n'					
							
				desc=inf+tscolor('\c00????00')+'Description:'+tscolor('\c00??????')+' '+desc
				
				image=self.MAIN_URL+'/'+image
				url=self.MAIN_URL+'/'+url
				self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre.strip(),'desc':ph.clean_html(desc),'icon':image,'hst':'tshost','good_for_fav':True,'mode':'31'})	
			if i>11:
				self.addDir({'import':cItem['import'],'title':tscolor('\c0000????')+'Page Suivante','page':page+1,'category' : 'host2','url':urlo,'icon':cItem['icon'],'mode':'30'} )									


	def showelms(self,cItem):
		url1=cItem['url']
		sts, data = self.getPage(url1)
		if sts:
			data_list = re.findall('"season-headline">(.*?)<(.*?)</ul>', data, re.S)
			for (seas_titre,data1) in data_list:
				self.addMarker({'title':tscolor('\c0000????')+seas_titre,'desc':'','icon':cItem['icon']})	
				data_list1 = re.findall('<li>(.*?)</a>.*?href="(.*?)".*?src="(.*?)".*?>(.*?)</li>', data1, re.S)
				for (titre,url,image,desc) in data_list1:
					url=self.MAIN_URL+'/'+url
					titre=ph.clean_html(titre)
					titre=titre.replace('Ep isode','Episode')
					self.addVideo({'import':cItem['import'],'category' : 'host2','url': url,'title':titre,'desc':ph.clean_html(desc),'icon':image,'hst':'tshost','good_for_fav':True})	
			else:
				self.addVideo({'import':cItem['import'],'category' : 'host2','url': url1,'title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost','good_for_fav':True})	
				
	
	def SearchResult(self,str_ch,page,extra):
		url_post = self.MAIN_URL+'/searchapi2.php'
		post_data = {'searchapi2':str_ch}
		param = dict(self.defaultParams)
		param['header']['Referer']='http://www.streamlord.com/searchapi2.php'
		param['header']['Content-Type']='application/x-www-form-urlencoded'
		param['header']['Upgrade-Insecure-Requests']='1'

		sts, data = self.getPage(url_post,param,post_data)
		if sts:
			printDBG('dddddddddddddddataaaaaaa'+data)
			data_list = re.findall('item movie">.*?href.*?href="(.*?)".*?src="(.*?)"', data, re.S)
			for (url,image) in data_list:
				titre=image
				if 'watch-movie-' in url:
					titre=image.replace('watch-movie-','').replace('-','')
				elif 'watch-tvshow-' in url:
					titre=image.replace('watch-tvshow-','').replace('-','')
				self.addVideo({'import':extra,'category' : 'video','url': url,'title':titre,'desc':'','icon':image,'hst':'tshost','good_for_fav':True})	
		

	def get_links(self,cItem):
		urlTab = []
		#urlTab.append({'name':'ttttttt', 'url':'hkhhk', 'need_resolve':0})
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			#d1 = re.findall('''["']sources['"]\s*:\s*\[(.*?)\]''', data)
			d1 = re.findall('''["']sources['"]\s*:\s*\[(.*?)\]''', data, re.S)
			if d1:
				if 'eval' in d1[0]:
					d3 = re.findall('eval\((.*)', data, re.S)
					if d3:
						#tab_dec=[SAWLIVETV_decryptPlayerParams,VIDEOWEED_decryptPlayerParams, VIDEOWEED_decryptPlayerParams2,TEAMCASTPL_decryptPlayerParams,VIDUPME_decryptPlayerParams,KINGFILESNET_decryptPlayerParams]
						data = unpackJSPlayerParams('eval('+d3[0]+')', SAWLIVETV_decryptPlayerParams, 0)
						printDBG(data)
						urlTab.append({'name':'Direct Link', 'url':data.replace('"','').replace("'",''), 'need_resolve':0,'type':'local'})
				else:
					d1 = re.findall('''['"]*file['"]*\s*:\s*([^\(]+)''', d1[0])[0]		
					d2 = re.findall('function\s+%s[^{]+{\s*([^}]+)' % d1, data)[0]		
					
					data_list = re.findall('return.*?"(.*?)"', d2, re.S)
					if data_list:
						URL1=data_list[0]
						urlTab.append({'name':'Direct Link', 'url':URL1, 'need_resolve':0,'type':'local'})
						
					data_list = re.findall('<iframe src="(.*?)"', data, re.S)
					if data_list:
						URL1=data_list[0]
						urlTab.append({'name':gethostname(URL1), 'url':URL1, 'need_resolve':1})			

		return urlTab	



		 

	
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
