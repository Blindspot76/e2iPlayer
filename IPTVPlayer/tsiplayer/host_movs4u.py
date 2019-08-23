# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
import re

def getinfo():
	info_={}
	info_['name']='Movs4u.To'
	info_['version']='1.4 18/08/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات اجنبية'
	info_['icon']='https://www.movs4u.tv/wp-content/uploads/2019/01/Logo-header.png'
	info_['recherche_all']='1'
	info_['update']='add movs4u servers'	
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'movs4u.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.movs4u.to'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		#self.getPage = self.cm.getPage
		
	def getPage(self, baseUrl, addParams = {}, post_data = None):
		if addParams == {}: addParams = dict(self.defaultParams)
		addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']
		Movs4u_TAB =  [{'category':'host2' ,       'title': 'Films',                  'url':self.MAIN_URL+'/movie/'      ,'icon':img_,'mode':'20'},
						{'category':'host2',       'title': 'Series','sub_mode':'serie'  ,'Url':self.MAIN_URL+'/tvshows/'    ,'icon':img_,'page':1,'mode':'30'},
						{'category':'search',      'title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'       ,'icon':img_},
						]
		self.listsTab(Movs4u_TAB, {'import':cItem['import'],'name':'host2'})
	def showmenu1(self,cItem):
		Movs4u_Film_CAT_TAB = [{'category':'host2','title': 'Films','Url':self.MAIN_URL+'/movie/','sub_mode':'film','page':1,'mode':'30'},
							{'category':'host2','title': 'Collection Films','Url':self.MAIN_URL+'/collection/','sub_mode':'Film_coll','page':1,'mode':'30'},
							{'category':'host2','title': 'Films Par Genre','sub_mode':'film','mode':'21'},
							{'category':'host2','title': 'Films Par Qualité','sub_mode':'Film_qual','mode':'21'},
							]
		self.listsTab(Movs4u_Film_CAT_TAB, {'import':cItem['import'],'name':'host2','icon':cItem['icon']})					

	def showmenu2(self,cItem):		
		gnr=cItem['sub_mode']
		img_=cItem['icon']		
		sUrl=self.MAIN_URL
		sts, data = self.getPage(sUrl) 
		if sts:
			Liste_films_data = re.findall('class="sub-menu">(.*?)\/ul', data, re.S)
			if Liste_films_data :
				if gnr=='Film_qual':
					films_data=Liste_films_data[1]
				else:
					films_data=Liste_films_data[0]		
				Liste_films_data = re.findall('<a href="(.*?)">(.*?)<', films_data, re.S)	
				for (url,titre) in Liste_films_data:
					params = {'import':cItem['import'],'good_for_fav':True,'category' : 'host2','Url': url,'title':titre,'desc':titre,'page':1,'icon':img_,'sub_mode':gnr,'mode':'30'} 
					self.addDir(params)	
		
	def showitms(self,cItem):
		page=cItem.get('page',1)
		url_=cItem['Url']
		if '?' in url_:
			x1,x2=url_.split('?',1)
			url_=x1+'page/'+str(page)+'/?'+x2
		else:
			url_=cItem['Url']+'page/'+str(page)+'/'
		printDBG('list_items_movs4u='+url_)	
		gnr=cItem['sub_mode']		
		img_=cItem['icon']
		sts, data = self.getPage(url_) 
		if sts:
			Liste_films_data = re.findall('<h1(.*?)(pagination">|<div class="copy">)', data, re.S)
			if Liste_films_data :
				films_data=Liste_films_data[0][0]	
				if gnr=='film':
					if 'trending' not in cItem['Url']:
						Liste_films_data = re.findall('<article id=.*?src="(.*?)".*?alt="(.*?)".*?quality">(.*?)<.*?href="(.*?)".*?metadata">(.*?)</div>.*?texto">(.*?)<', films_data, re.S)	
						for (image,name_eng,qual,url,meta,desc) in Liste_films_data:
							meta_=''
							meta_data = re.findall('<span.*?>(.*?)<', meta, re.S)	
							for (mt) in meta_data:
								if meta_=='':
									meta_= mt 
								else:
									meta_= meta_ + ' | ' + mt
							desc = meta_ +'\n'+ desc
							params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +'\c0000???? ('+qual+')','desc':desc,'icon':image,'hst':'tshost'} 
							self.addVideo(params)	
					else:
						Liste_films_data = re.findall('<article id=.*?src="(.*?)".*?alt="(.*?)".*?quality">(.*?)<.*?href="(.*?)"', films_data, re.S)	
						for (image,name_eng,qual,url) in Liste_films_data:
							params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +'\c0000???? ('+qual+')','desc':'','icon':image,'hst':'tshost'} 
							self.addVideo(params)						
				elif gnr=='Film_qual':
					Liste_films_data = re.findall('class="item".*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?type">(.*?)<', films_data, re.S)	
					for (url,image,name_eng,nat) in Liste_films_data:
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +'\c0000???? ('+nat+')','desc':'','icon':image,'hst':'tshost'} 
						self.addVideo(params)					
				elif gnr=='serie':
					Liste_films_data = re.findall('article id.*?src="(.*?)".*?alt="(.*?)".*?href="(.*?)".*?"texto">(.*?)<', films_data, re.S)	
					for (image,name_eng,url,desc) in Liste_films_data:
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'host2','Url': url,'title':name_eng,'desc':desc,'icon':image,'sub_mode':'serie_ep','page':1,'mode':'30'} 
						self.addDir(params)			 
				elif gnr=='Film_coll':
					Liste_films_data = re.findall('class="item.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)"', films_data, re.S)	
					for (url,image,name_eng) in Liste_films_data:
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'host2','Url': url,'title':name_eng,'desc':'','icon':image,'hst':'tshost','sub_mode':'one_film_col','page':1,'mode':'30'} 
						self.addDir(params)					
				elif gnr=='one_film_col':
					Liste_films_data = re.findall('class="item.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?quality">(.*?)<', films_data, re.S)	
					for (url,image,name_eng,qual) in Liste_films_data:
						params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +'\c0000???? ('+qual+')','desc':'','icon':image,'hst':'tshost'} 
						self.addVideo(params)
				elif gnr=='serie_ep':
					Liste_films_data1 = re.findall('<h2>Video trailer.*?src="(.*?)"', data, re.S)
					if Liste_films_data1:			
						params = {'import':cItem['import'],'category' : 'video','url': Liste_films_data1[0],'title':'Trailer','desc':'','icon':img_,'hst':'none'} 
						self.addVideo(params)			
					Liste_films_data = re.findall('<div id=\'seasons\'>(.*?)</script>', data, re.S)
					if Liste_films_data:
						films_data=Liste_films_data[0]
						Liste_films_data = re.findall("<span class='title'>(.*?)<(.*?)<\/ul>", films_data, re.S)
						for (season,data_s) in Liste_films_data:
							params = {'name':'categories','category' : 'video','title':'\c00????00'+season.replace('الموسم',''),'desc':'','icon':img_} 
							self.addMarker(params)
							films_data = re.findall("<li.*?src='(.*?)'.*?numerando'>(.*?)<.*?href='(.*?)'>(.*?)<", data_s, re.S)
							for (image,name_eng,url,name2) in films_data:
								params = {'import':cItem['import'],'good_for_fav':True,'category' : 'video','url': url,'title':name_eng +'\c0000????  # '+name2,'desc':'','icon':image,'hst':'tshost'} 
								self.addVideo(params)
				if gnr!='serie_ep':
					params = {'import':cItem['import'],'category':'host2','title': 'Next Page','Url':cItem['Url'],'sub_mode':gnr,'page':page+1,'icon':img_,'mode':'30'}
					self.addDir(params)							

	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			Liste_films_data = re.findall('"result-item">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?">(.*?)<', data, re.S)
			for (url,image,name_eng,type_) in Liste_films_data:
				if type_=='Movie':
					params = {'import':extra,'good_for_fav':True,'category' : 'video','url': url,'title':name_eng,'desc':'','icon':image,'hst':'tshost'} 
					self.addVideo(params)
				else:
					params = {'import':extra,'good_for_fav':True,'category' : 'host2','Url': url,'title':name_eng,'desc':'','icon':image,'sub_mode':'serie_ep','page':1,'mode':'30'} 
					self.addDir(params)	
		
		
	def get_links(self,cItem): 	
		urlTab = []	
		URL=cItem['url']
		sts, sHtmlContent = self.getPage(URL)
		if sts:
			_data0 = re.findall("'trailer'>.*?'title'>(.*?)<.*?server'>(.*?)<.*?data-post='(.*?)'",sHtmlContent, re.S)
			if _data0:
				urlTab.append({'name':_data0[0][0].replace('- تريلر الفلم',':')+' ' +'\c0000????('+_data0[0][1]+')', 'url':'hst#tshost#'+_data0[0][2], 'need_resolve':1})					
			_data = re.findall("data-url='(.*?)'.*?title'>(.*?)<.*?server'>(.*?)<",sHtmlContent, re.S)
			for (data_url,titre1,srv) in _data:
				titre1=titre1.replace('سيرفر مشاهدة رقم','Server:') 
				urlTab.append({'name':titre1+' ' +'\c0000????('+srv+')', 'url':'hst#tshost#'+data_url, 'need_resolve':1})		
		return urlTab
		
		
	def extractLink(self,videoUrl):
		url_out='None'
		if 'gdriveplayer' in videoUrl:
			_data3 = re.findall('link=(.*?)&',videoUrl, re.S)
			if _data3: 
				url_out = _data3[0]
		else:
			sts, data = self.getPage(videoUrl)
			if sts:
				_data2 = re.findall('<iframe.*?src="(.*?)"',data, re.S)		 		
				if _data2:			
					url_out = _data2[0]
				else:
					_data4 = re.findall('javascript">eval(.*?)</script>',data, re.S)
					if _data4:
						script_eval='eval'+_data4[0].strip()
						printDBG(script_eval)
						datau = unpackJSPlayerParams(script_eval, SAWLIVETV_decryptPlayerParams, 0)
						printDBG(datau)
						_data5 = re.findall('<iframe.*?src="(.*?)"',datau.replace('\\',''), re.S)
						if _data5:
							url_out = _data5[0]
					else:
						_data2 = re.findall('<meta.*?url=(.*?)"',data, re.S)		 		
						if _data2:			
							url_out = _data2[0]					
						else:
							_data4 = re.findall('"file".*?"(.*?)"',data, re.S)
							if _data4:
								url_out = _data4[0]
		return url_out	
	def getVideos(self,videoUrl):
		urlTab = []	
		url_ref=videoUrl
		printDBG("1")
		if videoUrl.startswith('http'):
			i=0
			while True:
				i=i+1
				printDBG(str(i)+">>>>Start<<<< "+videoUrl)
				oldURL=videoUrl
				videoUrl = self.extractLink(videoUrl)
				printDBG(str(i)+">>>>End<<<< "+videoUrl)
				if videoUrl == 'None': 
					printDBG('1') 
					urlTab.append((oldURL,'1'))
					break 
				elif '.m3u8' in videoUrl:
					printDBG('2')
					URL1=strwithmeta(videoUrl, {'Referer':url_ref})
					urlTab.append((URL1,'3'))
					break
				elif (self.up.checkHostSupport(videoUrl) == 1):	
					printDBG('3')
					urlTab.append((videoUrl,'1'))
					break
				printDBG('4')								 									
							 					
		else:
			printDBG("2")
			post_data = {'action':'doo_player_ajax','post':videoUrl,'nume':'trailer','type':'movie'}
			sts, data2 = self.getPage(self.MAIN_URL+'/wp-admin/admin-ajax.php', post_data=post_data)
			if sts:
				printDBG("20")
				_data0 = re.findall('<iframe.*?src="(.*?)"',data2, re.S)
				if _data0:	
					urlTab.append((_data0[0],'1'))	
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

