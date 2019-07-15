# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.tstools import TSCBaseHostClass,gethostname
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
###################################################


import re
import base64

def getinfo():
	info_={}
	info_['name']='Official-Film-Illimite.Ws'
	info_['version']='1.0 30/05/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='301'
	info_['desc']='Films & Series HD et UHD'
	info_['icon']='https://ww2.official-film-illimite.ws/wp-content/uploads/2016/10/official-film-illimite.png'
	info_['recherche_all']='1'
	info_['update']='New Host'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'officialfilmillimite.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://ww2.official-film-illimite.ws'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.HEADER1 = {'User-Agent': self.USER_AGENT,'Accept':'*/*', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip'}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.defaultParams1 = {'header':self.HEADER1, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.cacheLinks = {}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'Films', 'mode':'20'},
					{'category':hst,'title': 'Series', 'mode':'30','url':'https://ww2.official-film-illimite.ws/serie-tv/'},
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})	
				
	def showmenu1(self,cItem):
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'Tous', 'mode':'30','url':'https://ww2.official-film-illimite.ws/films/'},
					{'category':hst,'title': 'Par Genre', 'mode':'21','sub_mode':0},
					{'category':hst,'title': 'Par Qualité', 'mode':'21','sub_mode':1},
					{'category':hst,'title': 'Par Année', 'mode':'21','sub_mode':2},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})			


	def showmenu2(self,cItem):
		gnr=cItem['sub_mode']
		sts, data = self.getPage(self.MAIN_URL)
		if sts:
			if gnr==0:
				pat='<ul class="sub-menu">(.*?)</ul>'
				pat1='href="(.*?)">(.*?)<'
			elif gnr==1:
				pat='filter-content-quality clearfix">(.*?)<script>'
				pat1='href="(.*?)">(.*?)<'
			elif gnr==2:
				pat='class="filter-content-slider">(.*?)<div class="filter-slide'	
				pat1='href="(.*?)">(.*?)<'		
				
			films_list = re.findall(pat, data, re.S)
			if films_list:
				films_list2 = re.findall(pat1, films_list[0], re.S)	
				for (url,titre) in films_list2:
					if not url.startswith('http'): url=self.MAIN_URL+url
					self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre.strip(),'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
			
		
		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		if '?' in url1:
			x1,x2=url1.split('?',1)
			url1=x1+'page/'+str(page)+'/?'+x2
		else:
			url1=url1+'page/'+str(page)+'/'
		sts, data = self.getPage(url1)
		if sts:
			if 'paginador' in data: data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'mt-'), ('<div', '>', 'paginador'))[1]
			else: data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'mt-'), ('<style', '>'))[1]
			data = self.cm.ph.rgetAllItemsBeetwenNodes(data, ('</div', '>'), ('<div', '>', 'mt-'))
			i=0
			for item in data:
				i=i+1
				films_list = re.findall('href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?class="imdb">(.*?)</span>.*?class="ttx">(.*?)</span>.*?class="year">(.*?)<.*?calidad2">(.*?)<', item, re.S)		
				if films_list:
					for (url,image,titre,rate,desc,year_,qual) in films_list:
						desc1='\c00??????Rating: \c00????00'+ph.clean_html(rate)+'\c00?????? | Date: \c00????00'+year_+'\c00?????? | Qualitée: \c00????00'+qual
						desc=desc1+'\\n\c00??????Synopsis: \c0000????'+ph.clean_html(desc)			
						self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':self.cleanHtmlStr(titre.replace(' Streaming HD','')),'desc':desc,'icon':image,'hst':'tshost','mode':'31'})	
				else:
					films_list = re.findall('href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?class="imdb">(.*?)</span>.*?class="ttx">(.*?)</span>.*?<.*?calidad2">(.*?)<', item, re.S)		
					if films_list:
						for (url,image,titre,rate,desc,qual) in films_list:
							desc1='\c00??????Rating: \c00????00'+ph.clean_html(rate)+'\c00?????? | Qualitée: \c00????00'+qual
							desc=desc1+'\\n\c00??????Synopsis: \c0000????'+ph.clean_html(desc)			
							self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':self.cleanHtmlStr(titre.replace(' Streaming HD','')),'desc':desc,'icon':image,'hst':'tshost','mode':'31'})		
					
			if i>19:
				self.addDir({'import':cItem['import'],'title':'\c0000????Page Suivante','page':page+1,'category' : 'host2','url':cItem['url'],'icon':image,'mode':'30'} )									

	def showelms(self,cItem):
		urlo=cItem['url']
		img_=cItem['icon']
		desc=cItem['desc']
		sts, data = self.getPage(cItem['url'])
		if not sts: return
		cUrl = self.cm.meta['url']
		self.setMainUrl(cUrl)


		self.cacheLinks[cUrl] = []
		playerData = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'player'), ('</ul', '>'), False)[1]
		tmp = self.cm.ph.getAllItemsBeetwenMarkers(playerData, '<li', '</li>')
		for item in tmp:
			link = self.cm.ph.getSearchGroups(item, '''href=['"]#([^"^']+?)['"]''')[0]
			if link == '': continue
			name = self.cleanHtmlStr(item)
			link = self.cm.ph.getDataBeetwenNodes(playerData, ('<div', '>', link), ('</div', '>'), False)[1]
			url = self.getFullUrl(self.cm.ph.getSearchGroups(link, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
			if url != '': self.cacheLinks[cUrl].append({'name':name, 'url':strwithmeta(url, {'Referer':cUrl}), 'need_resolve':1})

		if len(self.cacheLinks[cUrl]):
			params = dict(cItem)
			params.update({'good_for_fav': False, 'url':cUrl, 'desc':desc, 'prev_url':cItem['url']})
			self.addVideo(params)
		else:
			playerData = self.cm.ph.rgetAllItemsBeetwenNodes(data, ('</iframe', '>'), ('<div', '>', 'id'), caseSensitive=False)
			for item in playerData:
				frameId = self.cm.ph.getSearchGroups(item, '''<div[^>]+?id=['"]([^"^']+?)['"]''', 1, True)[0]
				url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0])
				if url == '': continue
				name = self.cleanHtmlStr( self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', '#' + frameId), ('</a', '>'), False)[1] )
				self.cacheLinks[url] = [{'name':name, 'url':strwithmeta(url, {'Referer':cUrl}), 'need_resolve':1}]
				params = dict(cItem)
				params.update({'good_for_fav': False, 'url':url, 'title':cItem['title'] + ': ' + name, 'desc':desc, 'prev_url':cItem['url']})
				self.addVideo(params)
		
	
	def SearchResult(self,str_ch,page,extra):
		url_='https://www.moviflex.net/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('class="result-item.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)"', data, re.S)		
			for (url,image,titre) in films_list:
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':'','icon':image,'hst':'tshost','mode':'31'})	


	def get_links(self,cItem):
		urlTab = []
		url=cItem['url']
		printDBG('uuuuuuuuuuurrrrrrlllllllll'+str(self.cacheLinks.get(url, [])))
		for elm in self.cacheLinks.get(url, []):
			if 'upvid.me' in elm['url']:
				Url=elm['url']
				printDBG('uuuuuuuuuuurrrrrrlllllllll'+url)
				URL = 'https://' + Url.split('/')[2] + '/hls/'+Url.split('id=')[1]+'/'+Url.split('id=')[1]+'.playlist.m3u8'
				URL = strwithmeta(URL, {'Referer':Url})
				urlTab.extend(getDirectM3U8Playlist(URL, checkExt=True, checkContent=True, sortWithMaxBitrate=999999999))	
			elif 'film-hd.vip' in elm['url']:
				if 'hst#tshost#' not in elm['url']:
					elm['url']='hst#tshost#'+elm['url']
					elm['name']=elm['name']+' (film-hd.vip)'
				urlTab.append(elm)
			elif 'clickopen.win' in elm['url']:
				if 'hst#tshost#' not in elm['url']:
					elm['url']='hst#tshost#'+elm['url']
					elm['name']=elm['name']+' (clickopen.win)'
				urlTab.append(elm)
			elif 'hdss.to' in elm['url']:
				if 'work ftom hdss.to' not in elm['name']:
					elm['name']=elm['name']+' (not work from hdss.to !!!)'
				urlTab.append(elm)
			else:
				urlTab.append(elm)
		
		return urlTab
	
	
	def getVideos(self,videoUrl):
		urlTab=[]
		Url=videoUrl
		id_ = Url.split('/v/',1)[1]
		if 'film-hd.vip' in Url:
			post_data = {'r':'', 'd':'film-hd.vip'} 
			url1= 'https://film-hd.vip/api/source/'+id_
		else:
			post_data = {'r':'', 'd':'clickopen.win'} 
			url1= 'https://clickopen.win/api/source/'+id_			
		sts, data = self.getPage(url1, post_data=post_data)
		if sts:
			data = json_loads(data)
			for elm in data['data']:
				printDBG('rrrrrrrrrrrrrrrrr'+str(elm))		
				titre=elm['type']+ ' (' +elm['label']+')'
				urlTab.append((titre+'|'+elm['file'],'4'))	
		return urlTab			
	
		
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc= cItem.get('desc','')	
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat2=re.findall('class="costum_info">(.*?)(valor">|tag">)(.*?)</div>', data, re.S)
			if lst_dat2:
				for (x1,x0,x2) in lst_dat2:
					if 'اشراف' in x1: otherInfo1['age_limit'] = ph.clean_html(x2)
					if 'بلد'  in x1: otherInfo1['country'] = ph.clean_html(x2)
					if 'مدة'  in x1: otherInfo1['duration'] = ph.clean_html(x2)				
					if 'تاريخ' in x1: otherInfo1['year'] = ph.clean_html(x2)						
					if 'sgeneros'  in x1: otherInfo1['genres'] = ph.clean_html(x2)					
			else:
				lst_dat2=re.findall('class="sgeneros">(.*?)<div', data , re.S)
				if lst_dat2:
					otherInfo1['genres'] = ph.clean_html(lst_dat2[0])			
		
		
			
			lst_dat2=re.findall('wp-content">(.*?)<div', data , re.S)
			if lst_dat2:
				desc=ph.clean_html(lst_dat2[0])			
		icon = cItem.get('icon')
		title = cItem['title']		
		return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]

		 

	
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
			
