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

def getinfo():
	info_={}
	info_['name']='Official-Film-Illimite'
	info_['version']='1.2 02/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='301'
	info_['desc']='Films & Series HD et UHD'
	info_['icon']='https://www.official-film-illimite.to/wp-content/uploads/2016/10/official-film-illimite.png'
	info_['recherche_all']='1'
	info_['update']='Fix streamax.club Servers & fix Search'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'officialfilmillimite.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.official-film-illimite.to'
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
					{'category':hst,'title': 'Series', 'mode':'30','url':self.MAIN_URL+'/serie-tv/'},
					{'category':hst,'title': 'Animes', 'mode':'22'},
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})
	def showmenu1(self,cItem):
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'Tous', 'mode':'30','url':self.MAIN_URL+'/films/'},
					{'category':hst,'title': 'Saga', 'mode':'30','url':self.MAIN_URL+'/films/sagas/'},					
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
			
	def showmenu3(self,cItem):
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'Tous', 'mode':'30','url':self.MAIN_URL+'/animes/'},
					{'category':hst,'title': 'Animes VF', 'mode':'30','url':self.MAIN_URL+'/animes/vf/'},					
					{'category':hst,'title': 'Animes VO', 'mode':'30','url':self.MAIN_URL+'/animes/vo/'},									
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})			
		
		
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
				films_list = re.findall('href="(.*?)".*?-src="(.*?)".*?alt="(.*?)".*?class="imdb">(.*?)</span>.*?class="ttx">(.*?)</span>.*?class="year">(.*?)<.*?calidad2">(.*?)<', item, re.S)		
				if films_list:
					for (url,image,titre,rate,desc,year_,qual) in films_list:
						desc1=tscolor('\c00??????')+'Rating: '+tscolor('\c00????00')+ph.clean_html(rate)+tscolor('\c00??????')+' | Date: '+tscolor('\c00????00')+year_+tscolor('\c00??????')+' | Qualitée: '+tscolor('\c00????00')+qual
						desc=desc1+'\\n'+tscolor('\c00??????')+'Synopsis: '+tscolor('\c0000????')+ph.clean_html(desc)			
						self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':self.cleanHtmlStr(titre.replace(' Streaming HD','')),'desc':desc,'icon':image,'hst':'tshost','mode':'31'})	
				else:
					films_list = re.findall('href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?class="imdb">(.*?)</span>.*?class="ttx">(.*?)</span>.*?<.*?calidad2">(.*?)<', item, re.S)		
					for (url,image,titre,rate,desc,qual) in films_list:
						desc1=tscolor('\c00??????')+'Rating: '+tscolor('\c00????00')+ph.clean_html(rate)+tscolor('\c00??????')+' | Qualitée: '+tscolor('\c00????00')+qual
						desc=desc1+'\\n'+tscolor('\c00??????')+'Synopsis: '+tscolor('\c0000????')+ph.clean_html(desc)			
						self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':self.cleanHtmlStr(titre.replace(' Streaming HD','')),'desc':desc,'icon':image,'hst':'tshost','mode':'31'})		
					
			if i>12:
				self.addDir({'import':cItem['import'],'title':tscolor('\c0000????')+'Page Suivante','page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

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
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('class="item">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?class="imdb">(.*?)</span>.*?class="ttx">(.*?)</span>.*?<.*?calidad2">(.*?)<', data, re.S)		
			for (url,image,titre,rate,desc,qual) in films_list:
				desc1=tscolor('\c00??????')+'Rating: '+tscolor('\c00????00')+ph.clean_html(rate)+tscolor('\c00??????')+' | Qualitée: '+tscolor('\c00????00')+qual
				desc=desc1+'\\n'+tscolor('\c00??????')+'Synopsis: '+tscolor('\c0000????')+ph.clean_html(desc)			
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':self.cleanHtmlStr(titre.replace(' Streaming HD','')),'desc':desc,'icon':image,'hst':'tshost','mode':'31'})		

	def get_links(self,cItem):
		urlTab = []
		url=cItem['url']
		printDBG('uuuuuuuuuuurrrrrrlllllllll'+str(self.cacheLinks.get(url, [])))
		for elm in self.cacheLinks.get(url, []):
			if ('upvid.me' in elm['url']) or ('streamax.club' in elm['url']):
				Url=elm['url']
				URL = 'https://' + Url.split('/')[2] + '/hls/'+Url.split('id=')[1]+'/'+Url.split('id=')[1]+'.playlist.m3u8'
				URL = strwithmeta(URL, {'Referer':Url})
				tmp = getDirectM3U8Playlist(URL, checkExt=True, checkContent=True, sortWithMaxBitrate=999999999)
				for elm0 in tmp:
					elm0['type'] = 'local'
					elm0['name'] = '|HLS| '+elm0['name'] 
					urlTab.append(elm0)
			elif 'film-hd.vip' in elm['url']:
				if 'hst#tshost#' not in elm['url']:
					elm['url']='hst#tshost#'+elm['url']
					elm['name']='|film-hd.vip| '+elm['name']
					elm['type'] = 'local'
				urlTab.append(elm)
			elif 'd0stream' in elm['url']:
				if 'hst#tshost#' not in elm['url']:
					elm['url']='hst#tshost#'+elm['url'].replace('#','')+'||'+cItem['url']
					elm['name']='|d0stream| '+elm['name']+' > Marche pas :( <'
					elm['type'] = 'local'
				urlTab.append(elm)
			elif 'clickopen.' in elm['url']:
				if 'hst#tshost#' not in elm['url']:
					elm['url']='hst#tshost#'+elm['url']
					elm['name']='|clickopen| '+elm['name']
					elm['type'] = 'local'
				urlTab.append(elm)
				
			elif 'hdss.to' in elm['url']:
				printDBG('hdss link')
				#urlTab.append(elm)
			else:
				urlTab.append(elm)
		
		return urlTab
	
	
	def getVideos(self,videoUrl):
		urlTab=[]
		referer=''
		printDBG('||||||||||||||||||:'+videoUrl)
		if '||' in videoUrl:
			Url,referer=videoUrl.split('||')
		else:
			Url=videoUrl
		id_ =''
		if '/v/' in Url:
			id_ = Url.split('/v/',1)[1]
		elif '/x/embed/' in Url:
			id_ = Url.split('/x/embed/',1)[1]
			id_ = id_.replace('/','')	
		
		if 'd0stream' in Url:
			url_='https://v.d0stream.com/'
			printDBG('refererrefererrefererrefererrefererrefererrefererrefererreferer='+referer)
			Params = dict(self.defaultParams) 
			Params['header']['Referer']=referer
			sts, data = self.getPage(url_,Params)
			if sts:
				printDBG('data_films='+data)
				films_list = re.findall('video-pr\'>(.*?)<',data, re.S)		
				if films_list:
					id_2 = films_list[0]
					id_1 = Url.split('/')[-1]
					URL = 'https://v.d0stream.com/krade.io/we/'+id_1+'/'+id_2+'#/'+id_1
					Params['header']['Referer']='https://v.d0stream.com/'
					sts, data = self.getPage(URL,Params)
					if sts:				
						printDBG('data_films2='+data)
						films_list = re.findall('HlsSources.*?url":"(.*?)"',data, re.S)		
						if films_list:
							src = films_list[0]
							printDBG('src='+src)
							urlTab.append(('https://v.d0stream.com'+src,'3'))
							return urlTab
			return []
					
		elif 'film-hd.vip' in Url:
			post_data = {'r':'', 'd':'film-hd.vip'} 
			url1= 'https://film-hd.vip/api/source/'+id_
		else:
			post_data = {'r':'', 'd':'clickopen.club'} 
			url1= 'https://clickopen.club/api/source/'+id_			
		sts, data = self.getPage(url1, post_data=post_data)
		if sts:
			try:
				data = json_loads(data)
				for elm in data['data']:
					printDBG('rrrrrrrrrrrrrrrrr'+str(elm))		
					titre=elm['type']+ ' (' +elm['label']+')'
					urlTab.append((titre+'|'+elm['file'],'4'))
			except:
				printDBG('eurreur post page')		
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
		if mode=='22':
			self.showmenu3(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelms(cItem)
			
