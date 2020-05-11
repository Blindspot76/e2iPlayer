# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
###################################################


import re
import base64
import time

def getinfo():
	info_={}
	info_['name']='Chillax.To'
	info_['version']='1.1 23/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'
	info_['desc']='Watch Movies & TV shows'
	info_['icon']='https://i.ibb.co/r2kKX5s/chillax.png'
	info_['recherche_all']='1'
	info_['update']='Change Host name and fix link extractor'
	info_['warning']='---->  !! Work only in Eplayer3 WITH BUFFERING  !! <----'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'chillax.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0'
		self.MAIN_URL = 'https://ww1.9movies.yt'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.HEADER1 = {'User-Agent': self.USER_AGENT,'Accept':'*/*', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.defaultParams1 = {'header':self.HEADER1, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

		#self.getPage = self.cm.getPage
		 

	def getPage(self,baseUrl, addParams = {}, post_data = None):
		sts = False
		try:
			oRequestHandler = cRequestHandler(baseUrl)
			if post_data:
				oRequestHandler.setRequestType(cRequestHandler.REQUEST_TYPE_POST)
				oRequestHandler.addParametersLine(post_data)			
			if addParams!={}:
				oRequestHandler.addParameters(addParams)
			sHtmlContent    = oRequestHandler.request()
			sts = True	
		except Exception, e:
			sHtmlContent='ERREUR:'+str(e)	
		return sts, sHtmlContent




	def showmenu0(self,cItem):

		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'MOVIES',       'url': self.MAIN_URL+'/latest/movies', 'mode':'30'},
					{'category':hst,'title': 'TV SERIES',    'url': self.MAIN_URL+'/latest/series', 'mode':'30'},
					{'category':hst,'title': 'Top IMDB',     'url': self.MAIN_URL+'/top-imdb',      'mode':'30'},
					{'category':hst,'title': 'Most Watched', 'url': self.MAIN_URL+'/most-watched',  'mode':'30'},					
					{'category':hst,'title': tscolor('\c0000????')+'By Genre | Country | Release',  'mode':'20'},					
					{'category':hst,'title': tscolor('\c00????00')+'Filter',           'mode':'21'},													
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_,'desc':'---- >  '+tscolor('\c00????00')+'Work only in eplayer3 '+tscolor('\c0000??00')+'WITH BUFFERING '+tscolor('\c00??????')+'<----'})				


	def showmenu1(self,cItem):
		sts, data = self.getPage(self.MAIN_URL)
		if sts:
			films_list = re.findall('class="sub-menu(.*?)</ul', data, re.S)		
			if films_list:
				if len(films_list)>1:
					self.addMarker({'title':tscolor('\c0000??00')+'Genre:','desc':'','icon':cItem['icon']})
					films_list1 = re.findall('<li>.*?href="(.*?)".*?title.*?">(.*?)<', films_list[0], re.S)
					for (url,titre) in films_list1:
						self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+url,'title':titre.strip(),'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})		
					self.addMarker({'title':tscolor('\c0000??00')+'Country:','desc':'','icon':cItem['icon']})		
					films_list1 = re.findall('<li>.*?href="(.*?)".*?title.*?">(.*?)<', films_list[1], re.S)
					for (url,titre) in films_list1:
						self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+url,'title':titre.strip(),'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
					self.addMarker({'title':tscolor('\c0000??00')+'Release:','desc':'','icon':cItem['icon']})		
					films_list1 = re.findall('<li>.*?href="(.*?)".*?title.*?">(.*?)<', films_list[-1], re.S)
					for (url,titre) in films_list1:
						self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+url,'title':titre.strip(),'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	


	def showfilter(self,cItem):
		count=cItem.get('count',0)
		data=cItem.get('data',[])
		url=cItem.get('url',self.MAIN_URL+'/index.php/filter/')
		if count==0:
			sts, data = self.getPage(self.MAIN_URL+'/latest/movies')
			if sts:
				films_list = re.findall('class="filter.*?<ul(.*?)</ul', data, re.S)		
				if films_list:
					data=films_list
					self.addMarker({'title':tscolor('\c0000??00')+'Sort by:','desc':'','icon':cItem['icon']})		
					elm_list = re.findall('<li.*?value="(.*?)".*?">(.*?)</li>', data[0], re.S)
					for (url1,titre) in elm_list:
						urlo=url+url1+'/'
						self.addDir({'import':cItem['import'],'count':1,'data':data,'category' : 'host2','url': urlo,'title':ph.clean_html(titre).strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	
		elif count==1:			
			self.addMarker({'title':tscolor('\c0000??00')+'Genre:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?value="(.*?)".*?">(.*?)<', data[1], re.S)
			self.addDir({'import':cItem['import'],'count':2,'data':data,'category' : 'host2','url': url+'all/','title':'All','desc':url+'all/','icon':cItem['icon'],'hst':'tshost','mode':'21'})				
			for (url1,titre) in elm_list:
				urlo=url+url1+'/'
				titre=self.cleanHtmlStr(titre)
				self.addDir({'import':cItem['import'],'count':2,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

		elif count==2:			
			self.addMarker({'title':tscolor('\c0000??00')+'Country:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?value="(.*?)".*?">(.*?)<', data[2], re.S)
			self.addDir({'import':cItem['import'],'count':3,'data':data,'category' : 'host2','url': url+'all/','title':'All','desc':url+'all/','icon':cItem['icon'],'hst':'tshost','mode':'21'})				
			for (url1,titre) in elm_list:
				urlo=url+url1+'/'
				self.addDir({'import':cItem['import'],'count':3,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

		elif count==3:			
			self.addMarker({'title':tscolor('\c0000??00')+'Type:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?value="(.*?)".*?">(.*?)<', data[3], re.S)
			self.addDir({'import':cItem['import'],'count':4,'data':data,'category' : 'host2','url': url+'all/','title':'All','desc':url+'all/','icon':cItem['icon'],'hst':'tshost','mode':'21'})				
			for (url1,titre) in elm_list:
				urlo=url+url1+'/'
				self.addDir({'import':cItem['import'],'count':4,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

		elif count==4:			
			self.addMarker({'title':tscolor('\c0000??00')+'Release:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?value="(.*?)".*?">(.*?)<', data[4], re.S)
			self.addDir({'import':cItem['import'],'category' : 'host2','url': url+'all','title':'All','desc':url+'all','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
			for (url1,titre) in elm_list:
				urlo=url+url1
				self.addDir({'import':cItem['import'],'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'30'})	


		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		url1=url1+'?p='+str(page)
		sts, data = self.getPage(url1)
		if sts:
			films_list = re.findall('class="item.*?class=".*?>(.*?)</div>.*?href="(.*?)".*?src="(.*?)".*?name".*?">(.*?)<', data, re.S)		
			for (desc,url,image,titre) in films_list:
				if '<!--' in desc:
					titre=titre+tscolor('\c0000??00')+' '+ph.clean_html(desc)				
				elif 'fa-star' in desc:
					titre=titre
					desc = 'Imdb: '+desc					
				else:
					titre=titre+tscolor('\c0000??00')+' (Serie)'
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url':self.MAIN_URL+url,'title':titre,'desc':tscolor('\c0000??00')+ph.clean_html(desc),'icon':image,'hst':'tshost','mode':'31'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	def showelms(self,cItem):
		urlo=cItem['url']
		#urlo=urlo.replace('/film/','/watch/')
		img_=cItem['icon']
		sts, data = self.getPage(urlo)
		
		if sts:
			self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': urlo,'title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'} )
			films_list = re.findall('class="item.*?class=".*?>(.*?)</div>.*?href="(.*?)".*?src="(.*?)".*?name".*?">(.*?)<', data, re.S)
			if films_list:
				self.addMarker({'title':tscolor('\c00????00')+'You May Also Like','category' : 'host2','icon':img_} )
				for (desc,url,image,titre) in films_list:
					if not 'mdb' in desc:
						titre=titre.strip()+tscolor('\c0000??00')+' '+ph.clean_html(desc)
					else:
						titre=titre.strip()+tscolor('\c0000??00')+' (Serie)'
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': self.MAIN_URL+url,'title':titre,'desc':tscolor('\c0000??00')+ph.clean_html(desc),'icon':image,'hst':'tshost'})	

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/movie/search?keyword='+str_ch+'&p='+str(page) 
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('class="item.*?class=".*?>(.*?)</div>.*?href="(.*?)".*?src="(.*?)".*?name".*?">(.*?)<', data, re.S)		
			for (desc,url,image,titre) in films_list:
				if not 'mdb' in desc:
					titre=titre+tscolor('\c0000??00')+' '+ph.clean_html(desc)
				else:
					titre=titre+tscolor('\c0000??00')+' (Serie)'
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url':self.MAIN_URL+url,'title':titre,'desc':tscolor('\c0000??00')+ph.clean_html(desc)+'\\n'+'---- >  '+tscolor('\c00????00')+'Work only in eplayer3 '+tscolor('\c0000??00')+'WITH BUFFERING '+tscolor('\c00??????')+'<----','icon':image,'hst':'tshost','mode':'31'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url'].replace('/film/','/watch/').replace('https://chillax.to',self.MAIN_URL)
		sts, data = self.getPage(URL)
		if sts:
			Tab_els = re.findall('onclick="favorite\((.*?),', data, re.S)
			if Tab_els:
				url2=self.MAIN_URL+'/ajax/movie_episodes/'+Tab_els[0]
				sts, data = self.getPage(url2)
				if sts:
					data=data.replace('\\','')
					Tab_els0 = re.findall('class="fa fa-server.*?">(.*?)<ul(.*?)</ul>', data, re.S)
					if Tab_els0:
						for (saison,data1) in Tab_els0:
							Tab_els = re.findall('<li>.*?data-id="(.*?)".*?data-server="(.*?)".*?class="ep-item">(.*?)<', data1, re.S)
							if not Tab_els: 
								Tab_els = re.findall('<li>.*?data-id="(.*?)".*?data-server="(.*?)".*?ep-item">(.*?)<', data1, re.S)
							if Tab_els:
								#Tab_els = sorted(Tab_els, key = lambda x: (x[2]))
								for (id_,server,titre) in Tab_els:
									urlTab.append({'name':ph.clean_html(saison)+' | '+ titre, 'url':'hst#tshost#'+id_+'|'+URL+'?ep='+id_+'|XXCHI', 'need_resolve':1})	
							
		return urlTab
		
		
	def getVideos(self,videoUrl):
		urlTab = []	
		videoUrl,referer,x1=videoUrl.split('|')
		url=self.MAIN_URL+'/ajax/movie_sources/'
		#post_data = {'eid':videoUrl}
		post_data = 'eid='+videoUrl
		sts, data = self.getPage(url,post_data=post_data)
		if sts:
			Tab_els = re.findall('file":"(.*?)".*?label":"(.*?)"', data, re.S)
			if Tab_els:
				hdrm3u8={
					'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
					'Accept':'*/*',
					'Accept-Language':'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
					'Referer':referer,
					'Origin':self.MAIN_URL,
					'Connection':'keep-alive',
					'Accept-Encoding':'gzip, deflate'}
				vtt_url=''
				for (url_,label) in Tab_els:
					if False:#'.vtt' in url_:
						subTrack = [{'title':label, 'url':url_.replace('\\',''), 'lang':label, 'format':'vtt'}]
						hdrm3u8['external_sub_tracks']=subTrack
						#vtt_url=url_+'|'+label+'|'
				for (url_,label) in Tab_els:
					url = url_.replace('\\','')
					url = strwithmeta(url, hdrm3u8)
					if 'm3u8' in url_:
						#if vtt_url!='':
						#	urlTab.append((vtt_url+url,'6'))
						#else:
						urlTab.append((url,'3'))
					elif '.vtt' not in url_:
						urlTab.append((label+'|'+url,'4'))
					
						

		return urlTab		
		
		
		
		
		
			
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc= cItem.get('desc','')	
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('class="meta(.*?)</div>', data, re.S)
			if lst_dat:
				lst_dat2=re.findall('class="(.*?)">(.*?)</span>', lst_dat[0], re.S)
				for (x1,x2) in lst_dat2:
					if 'imdb'      in x1: otherInfo1['imdb_rating'] = ph.clean_html(x2)
					if 'clock'  in x1: otherInfo1['duration']       = ph.clean_html(x2)	
					if 'calendar'   in x1: otherInfo1['year']       = ph.clean_html(x2)	
				lst_dat2=re.findall('<dt>(.*?)</dt>(.*?)</dd>', lst_dat[1], re.S)
				for (x1,x2) in lst_dat2:					
					if 'Genre'    in x1: otherInfo1['genres']      = ph.clean_html(x2)
					if 'Stars'    in x1: otherInfo1['actors']      = ph.clean_html(x2)
					if 'Director' in x1: otherInfo1['directors']   = ph.clean_html(x2)
					if 'Country'   in x1: otherInfo1['country']     = ph.clean_html(x2)

			lst_dat2=re.findall('fullcontent">(.*?)<div', data , re.S)
			if lst_dat2:
				desc=ph.clean_html(lst_dat2[0])
			else:
				desc= cItem['desc']				
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
			self.showfilter(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelms(cItem)
			
