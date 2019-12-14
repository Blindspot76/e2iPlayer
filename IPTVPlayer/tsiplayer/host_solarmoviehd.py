# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
###################################################


import re
import base64

def getinfo():
	info_={}
	info_['name']='Solarmoviehd.Ru'
	info_['version']='1.0 01/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'
	info_['desc']='Watch Movies & TV shows'
	info_['icon']='https://solarmoviehd.ru/assets/images/logo.png'
	info_['recherche_all']='1'
	info_['update']='New Host'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'solarmoviehd.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://solarmoviehd.ru'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.HEADER1 = {'User-Agent': self.USER_AGENT,'Accept':'*/*', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.defaultParams1 = {'header':self.HEADER1, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):

		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'MOVIES',  'mode':'20'},
					{'category':hst,'title': 'TV-SERIES','url': self.MAIN_URL+'/movie/filter/series/latest/all/all/all/all/all/', 'mode':'30'},
					{'category':hst,'title': tscolor('\c00????00')+'Filter', 'mode':'21'},													
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})				


	def showmenu1(self,cItem):
		self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/movie/filter/movies/latest/all/all/all/all/all/','title':'All Movies','desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
		self.addDir({'import':cItem['import'],'category' : 'host2','url': self.MAIN_URL+'/top-imdb/movie/','title':'Top IMDB','desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
		sts, data = self.getPage(self.MAIN_URL+'/movie/filter/movies.html')
		if sts:
			films_list = re.findall('class="sub-menu">(.*?)</ul', data, re.S)		
			if films_list:
				self.addMarker({'title':tscolor('\c0000??00')+'Genre','desc':'','icon':cItem['icon']})
				films_list1 = re.findall('<li>.*?href="(.*?)".*?title.*?">(.*?)<', films_list[0], re.S)
				for (url,titre) in films_list1:
					self.addDir({'import':cItem['import'],'category' : 'host2','url': url.replace('.html','/'),'title':titre,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})		
				self.addMarker({'title':tscolor('\c0000??00')+'Country','desc':'','icon':cItem['icon']})		
				films_list1 = re.findall('<li>.*?href="(.*?)".*?title.*?">(.*?)<', films_list[-1], re.S)
				for (url,titre) in films_list1:
					self.addDir({'import':cItem['import'],'category' : 'host2','url': url.replace('.html','/'),'title':titre,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	


	def showfilter(self,cItem):
		count=cItem.get('count',0)
		data=cItem.get('data',[])
		url=cItem.get('url',self.MAIN_URL+'/movie/filter/')
		if count==0:
			sts, data = self.getPage(self.MAIN_URL+'/movie/filter/movies.html')
			if sts:
				films_list = re.findall('<ul class="fc(.*?)</ul', data, re.S)		
				if films_list:
					data=films_list
					self.addMarker({'title':tscolor('\c0000??00')+'Film Type:','desc':'','icon':cItem['icon']})		
					elm_list = re.findall('<li>.*?value="(.*?)".*?">(.*?)<', data[1], re.S)
					for (url1,titre) in elm_list:
						urlo=url+url1+'/'
						self.addDir({'import':cItem['import'],'count':1,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	
		elif count==1:			
			self.addMarker({'title':tscolor('\c0000??00')+'Sort by:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?href.*?movies/(.*?)/.*?">(.*?)</li>', data[0], re.S)
			for (url1,titre) in elm_list:
				urlo=url+url1+'/'
				titre=self.cleanHtmlStr(titre)
				self.addDir({'import':cItem['import'],'count':2,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

		elif count==2:			
			self.addMarker({'title':tscolor('\c0000??00')+'Genre:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?value="(.*?)".*?>(.*?)<', data[3], re.S)
			self.addDir({'import':cItem['import'],'count':3,'data':data,'category' : 'host2','url': url+'all/','title':'All','desc':url+'all/','icon':cItem['icon'],'hst':'tshost','mode':'21'})			
			for (url1,titre) in elm_list:
				urlo=url+url1+'/'
				self.addDir({'import':cItem['import'],'count':3,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

		elif count==3:			
			self.addMarker({'title':tscolor('\c0000??00')+'Country:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?value="(.*?)".*?>(.*?)<', data[4], re.S)
			self.addDir({'import':cItem['import'],'count':4,'data':data,'category' : 'host2','url': url+'all/','title':'All','desc':url+'all/','icon':cItem['icon'],'hst':'tshost','mode':'21'})			
			for (url1,titre) in elm_list:
				urlo=url+url1+'/'
				self.addDir({'import':cItem['import'],'count':4,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

		elif count==4:			
			self.addMarker({'title':tscolor('\c0000??00')+'Release:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?value="(.*?)".*?>(.*?)<', data[5], re.S)
			for (url1,titre) in elm_list:
				urlo=url+url1+'/'
				self.addDir({'import':cItem['import'],'count':5,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

		elif count==5:			
			self.addMarker({'title':tscolor('\c0000??00')+'Quality:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('<li>.*?value="(.*?)".*?>(.*?)<', data[2], re.S)
			for (url1,titre) in elm_list:
				urlo=url+'all/'+url1+'/'
				self.addDir({'import':cItem['import'],'category' : 'host2','url': urlo,'title':titre.strip(),'desc':urlo,'icon':cItem['icon'],'hst':'tshost','mode':'30'})	


		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		url1=url1+'page-'+str(page)+'.html'
		sts, data = self.getPage(url1)
		if sts:
			films_list = re.findall('ml-item">.*?href="(.*?)".*?title="(.*?)".*?class="mli-.*?">(.*?)</.*?original="(.*?)"', data, re.S)		
			for (url,titre,desc,image) in films_list:
				titre=titre+tscolor('\c0000??00')+' '+ph.clean_html(desc)
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':ph.clean_html(desc),'icon':image,'hst':'tshost','mode':'31'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	def showelms(self,cItem):
		urlo=cItem['url']
		img_=cItem['icon']
		sts, data = self.getPage(urlo)
		
		if sts:
			films_list0 = re.findall('(youtube.com/embed/.*?)["\']', data, re.S)
			if films_list0:
				self.addVideo({'import':cItem['import'],'category' : 'host2','url': 'https://www.'+films_list0[0],'title':'Watch trailer','desc':cItem['desc'],'icon':img_,'hst':'none'} )				
			self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': urlo,'title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'} )
			films_list = re.findall('ml-item">.*?href="(.*?)".*?title="(.*?)".*?class="mli-.*?">(.*?)</.*?original="(.*?)"', data, re.S)
			if films_list:
				self.addMarker({'title':tscolor('\c00????00')+'You May Also Like','category' : 'host2','icon':img_} )
				for (url,titre,desc,image) in films_list:
					titre=titre+tscolor('\c0000??00')+' '+ph.clean_html(desc)
					self.addVideo({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':ph.clean_html(desc),'icon':image,'hst':'tshost'})	

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/search/'+str_ch+'/page-'+str(page)+'.html'
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('ml-item">.*?href="(.*?)".*?title="(.*?)".*?class="mli-.*?">(.*?)</.*?original="(.*?)"', data, re.S)		
			for (url,titre,desc,image) in films_list:
				titre=titre+tscolor('\c0000??00')+' '+ph.clean_html(desc)
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url,'title':titre,'desc':ph.clean_html(desc),'icon':image,'hst':'tshost','mode':'31'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url'].replace('.html','/watching.html')
		sts, data = self.getPage(URL)
		if sts:
			Tab_els = re.findall('onclick="favorite\((.*?),', data, re.S)
			if Tab_els:
				url2='https://solarmoviehd.ru/ajax/v4_movie_episodes/'+Tab_els[0]
				sts, data = self.getPage(url2)
				if sts:
					data=data.replace('\\"','"')
					Tab_els = re.findall('class="ep-item".*?data-server="(.*?)".*?data-id="(.*?)".*?title="(.*?)"', data, re.S)
					if Tab_els:
						Tab_els = sorted(Tab_els, key = lambda x: (x[2]))
						for (server,id_,titre) in Tab_els:
							if server=='16':server='Vidcloud'
							if server=='15':server='Openload'
							if server=='14':server='Streamango'
							if server=='6':server='VIP'
							urlTab.append({'name':'|'+titre+'| '+server, 'url':'hst#tshost#'+id_, 'need_resolve':1})	
						
		return urlTab
		
		
	def getVideos(self,videoUrl):
		urlTab = []	
		url=self.MAIN_URL+'/ajax/movie_embed/'+videoUrl
		sts, data = self.getPage(url)
		if sts:
			Tab_els = re.findall('src":"(.*?)"', data, re.S)
			if Tab_els:
				urlTab.append((Tab_els[0].replace('\\',''),'1'))

		return urlTab		
		
		
		
		
		
			
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc= cItem.get('desc','')	
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('mvic-info">(.*?)Keywords', data, re.S)
			if lst_dat:
				lst_dat2=re.findall('<strong>(.*?)</strong>(.*?)</p>', lst_dat[0], re.S)
				for (x1,x2) in lst_dat2:
					if 'Country'   in x1: otherInfo1['country']     = ph.clean_html(x2)
					if 'Duration'  in x1: otherInfo1['duration']    = ph.clean_html(x2)				
					if 'Release'   in x1: otherInfo1['year']        = ph.clean_html(x2)						
					if 'Genres'    in x1: otherInfo1['genres']      = ph.clean_html(x2)
					if 'IMDb'      in x1: otherInfo1['imdb_rating'] = ph.clean_html(x2)
					if 'Directors' in x1: otherInfo1['directors']   = ph.clean_html(x2)
					if 'Actors'    in x1: otherInfo1['actors']      = ph.clean_html(x2)
					if 'Quality'   in x1: otherInfo1['quality']     = ph.clean_html(x2)		
			
				
			lst_dat2=re.findall('class="desc">(.*?)<div', data , re.S)
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
			
