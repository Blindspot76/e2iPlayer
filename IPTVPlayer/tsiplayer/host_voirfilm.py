# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor

import re


###################################################
#01# HOST http://www.voirfilm.mx/
###################################################	
def getinfo():
	info_={}
	info_['name']='Voirfilms.ws'
	info_['version']='1.3 11/03/2020'
	info_['dev']='RGYSoft'
	info_['cat_id']='301'
	info_['desc']='Films, Series & Animes VF'
	info_['icon']='https://www.voirfilm.me/static/images/logo56.png'
	info_['update']='New Template'	
	info_['recherche_all']='1'
	return info_
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'voirfilm.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.voirfilm.me'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
			 
	def showmenu0(self,cItem):
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Films','icon':cItem['icon'],'mode': '20','sub_mode':'1'})
		self.addDir({'import':cItem['import'],'category' :'host2','title':'Series','icon':cItem['icon'],'mode':'20','sub_mode':'2'})	
		#self.addDir({'import':cItem['import'],'category' :'host2','title':'Animes','icon':cItem['icon'],'mode':'20','sub_mode':'3'})		
		self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})

	def showmenu1(self,cItem):
		sub_mode=cItem.get('sub_mode', '0')
		if sub_mode=='1':
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Films'    ,'url':self.MAIN_URL+'/lesfilms','icon':cItem['icon'],'mode':'30'})
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Par Titre','icon':cItem['icon'],'mode':'21','sub_mode':'1'})	
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Par Année','icon':cItem['icon'],'mode':'21','sub_mode':'2'})	
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Par Genre','icon':cItem['icon'],'mode':'21','sub_mode':'3'})			
		elif sub_mode=='2':	
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Series'   ,'url':self.MAIN_URL+'/series/','icon':cItem['icon'],'mode':'30'})
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Par Titre','icon':cItem['icon'],'mode':'21','sub_mode':'4'})	
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Par Année','icon':cItem['icon'],'mode':'21','sub_mode':'5'})
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Par Genre','icon':cItem['icon'],'mode':'21','sub_mode':'6'})				
		elif sub_mode=='3':	
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Animes'             ,'url':self.MAIN_URL+'/animes/'          ,'icon':cItem['icon'],'mode':'30'})
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Les plus populaires','url':self.MAIN_URL+'/animes/populaire/','icon':cItem['icon'],'mode':'30'})	
			self.addDir({'import':cItem['import'],'category' :'host2','title':'Par Titre'          ,'icon':cItem['icon'],'mode':'21','sub_mode':'7'})

	def showmenu2(self,cItem):
		sub_mode=cItem.get('sub_mode', '0')
		if sub_mode=='1':
			url=self.MAIN_URL+'/film-en-streaming'
			ind_=0
		elif sub_mode=='2':
			url=self.MAIN_URL+'/film-en-streaming'
			ind_=1	
		elif sub_mode=='3':
			url=self.MAIN_URL+'/film-en-streaming'
			ind_=2	
		elif sub_mode=='4':
			url=self.MAIN_URL+'/series-tv-streaming/'
			ind_=0		
		elif sub_mode=='5':
			url=self.MAIN_URL+'/series-tv-streaming/'
			ind_=1			
		elif sub_mode=='6':
			url=self.MAIN_URL+'/series-tv-streaming/'
			ind_=2			
		elif sub_mode=='7':
			url=self.MAIN_URL+'/animes/'
			ind_=0					
		sts, data = self.getPage(url)
		if sts:			
			data1=re.findall('class="options(.*?)</div>', data, re.S)
			if data1:
				data2=re.findall('<a href="(.*?)".*?>(.*?)<', data1[ind_], re.S)
				for (URL,titre) in data2:
					if (URL!='/animes/dernier/') and (URL!='/animes/populaire/'):
						if not URL.startswith('http'):
							URL=self.MAIN_URL+URL
						self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':URL,'icon':cItem['icon'],'mode':'30'})

		else:
			self.addMarker({'title':yellow+'Erreur','icon':cItem['icon']})

	def showitms(self,cItem):
		page = cItem.get('page', 1)
		url=cItem['url']	
		if '/lesfilms' in url: url=url+str(page)
		elif url.endswith('/series/') or url.endswith('/animes/') or url.endswith('/populaire/'):
			url=url+'page-'+str(page)				
		elif page>1:
			if url.endswith('_1'):
				url=url.replace('_1','_')+str(page)		
			else:
				url=url+'/'+str(page)
		sts, data = self.getPage(url)
		if sts:
			count=0				
			Liste_films = re.findall('class="imagefilm">.*?href="(.*?)".*?title="(.*?)"(.*?)<img src="(.*?)".*?<div class="opt">(.*?)</div>', data, re.S)
			for (url1,name_eng,vf,image,desc) in Liste_films:
				if not url1.startswith('http'): url1=self.MAIN_URL+url1
				if not image.startswith('http'): image=self.MAIN_URL+image
				name_eng=name_eng.replace('Serie ','').replace('film ','').replace(' en streaming','').replace(' en Streaming','')
				vf = vf.lower()
				if 'vf' in vf: version='VF'
				elif 'vostfr' in vf: version='VOSTFR'
				else: version=''
				if 	ph.clean_html(desc)!='': desc=tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+ph.clean_html(desc)+'\\n'
				else: desc=''
				if version!='': desc=desc+tscolor('\c00????00')+'Version: '+tscolor('\c00??????')+version
				self.addDir({'import':cItem['import'],'category' : 'host2','title':name_eng.strip(),'url':url1,'desc':desc,'icon':image,'mode':'31','good_for_fav':True,'EPG':True,'hst':'tshost'})
				count=count+1
			if count>15:
				self.addDir({'import':cItem['import'],'category' : 'host2','title':'Page Suivante','url':cItem['url'],'page':page+1,'mode':'30'})

	def showelms(self,cItem):
		url=cItem['url']
		if not url.startswith('http'): url = self.MAIN_URL + url
		sts, data = self.getPage(url)
		if sts:
			Liste_films_data = re.findall('data-trailer="(.*?)"', data, re.S)
			if Liste_films_data:
				self.addVideo({'import':cItem['import'],'category' : 'host2','title':'TRAILER','url':Liste_films_data[0],'desc':'','icon':cItem['icon'],'hst':'none'})	
				
			Liste_films_data = re.findall('unepetitesaisons">.*?href="(.*?)".*?src="(.*?)".*?title="(.*?)"', data, re.S)
			if Liste_films_data:
				for (url1,image,titre) in Liste_films_data:			
					if not url1.startswith('http'): url1=self.MAIN_URL+url1
					if not image.startswith('http'): image=self.MAIN_URL+image					
					self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'desc':cItem['desc'],'icon':image,'mode':'31','good_for_fav':True,'EPG':True,'hst':'tshost'})
					
			else:
				Liste_films_data = re.findall('class="n_episode2".*?title="(.*?)".*?href="(.*?)">(.*?)</a>', data, re.S)
				if Liste_films_data:
					for (desc,url1,titre) in Liste_films_data:
						if not url1.startswith('http'): url1=self.MAIN_URL+'/'+url1	
						titre=ph.clean_html(titre).replace('épisode','Episode')
						self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'desc':desc,'icon':cItem['icon'],'hst':'tshost','good_for_fav':True})	
				else:
					self.addVideo({'import':cItem['import'],'category' : 'host2','title':cItem['title'],'url':cItem['url'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost','good_for_fav':True,'EPG':True,'hst':'tshost'})	

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/recherche/'+str_ch+'/'+str(page)
		sts, data = self.getPage(url_)
		if sts:
			Liste_films = re.findall('class="imagefilm">.*?href="(.*?)".*?title="(.*?)"(.*?)<img src="(.*?)"', data, re.S)
			for (url1,name_eng,type_,image) in Liste_films:
				if not url1.startswith('http'):
					url1=self.MAIN_URL+url1
				if not image.startswith('http'): image=self.MAIN_URL+image
				name_eng=name_eng.replace('Serie ','').replace('film ','').replace(' en streaming','').replace(' en Streaming','')
				if 'type serie' in type_: version='Serie'
				elif 'type anime' in type_: version='Anime'
				else: version='Film'
				name_eng=name_eng+tscolor('\c00????00')+' ('+version+')'	
				self.addDir({'import':extra,'name':'search','category' : 'host2','title':name_eng,'url':url1,'desc':'','icon':image,'mode':'31','good_for_fav':True,'EPG':True,'hst':'tshost'})
		
			
	def get_links(self,cItem): 	
		urlTab = []
		URL=cItem['url']	
		sts, data = self.getPage(URL)
		if sts:
			Liste_Hostes_data = re.findall('class="link_list"(.*?)Copyright', data, re.S)
			if Liste_Hostes_data:
				Liste_Hostes = re.findall('data-src="(.*?)"(.*?)class="gras">(.*?)</span>', Liste_Hostes_data[0], re.S)
				for (url,vf,host) in Liste_Hostes:
					if '"vfL"' in vf: VF='VF'
					elif '"vostfrL"' in vf: VF='VOSTFR'
					elif '"voL"' in vf: VF='VO'
					else: VF=''
					if 'voirfilms.' in url:
						titre = ph.clean_html(host)
						Name_host='|'+tscolor('\c0000????')+VF+tscolor('\c00??????')+'| '+titre	
						urlTab.append({'name':Name_host, 'url':'hst#tshost#'+url+'|'+URL, 'need_resolve':1})
					else:
						titre = self.up.getDomain(url)
						Name_host='|'+tscolor('\c0000????')+VF+tscolor('\c00??????')+'| '+titre					
						urlTab.append({'name':Name_host, 'url':url, 'need_resolve':1})
		return urlTab	

	def getVideos(self,videoUrl):
		urlTab=[]
		url_,refer=videoUrl.split('|')
		#printDBG('f111fffffffffff'+url_+'r111rrrrrrrrrrrrrr'+refer)
		HTTP_HEADER= {'Referer':refer,"User-Agent": "Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:66.0) Gecko/20100101 Firefox/66.0","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3","Connection": "keep-alive","Upgrade-Insecure-Requests": "1"}
		sts, data = self.getPage(url_,HTTP_HEADER)
		if sts:
			printDBG('eeeeeeeee'+data)
			get_url = re.findall('url=(.*?)"', data, re.S)
			if get_url: url=get_url[0]
			else:
				get_url2 = re.findall('src="(.*?)"', data, re.S)
				if get_url2: url=get_url2[0]	
				else: url='ERROR'
			urlTab.append((url,'1'))	
		return urlTab	
		
	def getPage(self,baseUrl, addParams = {}, post_data = None):
		while True:
			if addParams == {}: addParams = dict(self.defaultParams)
			origBaseUrl = baseUrl
			baseUrl = self.cm.iriToUri(baseUrl)
			addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
			sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
			
			if sts and 'class="loading"' in data:
				GetIPTVSleep().Sleep(5)
				continue
			break
		return sts, data		 

	def getArticle(self,cItem):
		otherInfo1 = {}
		desc = cItem.get('desc','')
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('class="listen(.*?)</ul>', data, re.S)
			if lst_dat: 
				lst_dat2=re.findall('<li>(.*?)</span>(.*?)</li>', lst_dat[0], re.S)
				for (x1,x2) in lst_dat2:
					if 'Origine' in x1: otherInfo1['country'] = ph.clean_html(x2)
					if 'Réalisateur' in x1: otherInfo1['director'] = ph.clean_html(x2)
					if 'Acteur' in x1: otherInfo1['actors'] = ph.clean_html(x2)
					if 'Genre' in x1: otherInfo1['genres'] = ph.clean_html(x2)			
					if 'Durée' in x1: otherInfo1['duration'] = ph.clean_html(x2)
					if 'Date de sortie' in x1: otherInfo1['first_air_date'] = ph.clean_html(x2)			
					if 'Qualité' in x1: otherInfo1['quality'] = ph.clean_html(x2)			
					if 'Format' in x1: otherInfo1['type'] = ph.clean_html(x2)
					if 'Langue' in x1: otherInfo1['language'] = ph.clean_html(x2)			
					if 'Sous-titres' in x1: otherInfo1['subtitles'] = ph.clean_html(x2)
					if 'Catégorie' in x1: otherInfo1['genres'] = ph.clean_html(x2)				
					if 'Année' in x1: otherInfo1['year'] = ph.clean_html(x2)					
					if 'Studio' in x1: otherInfo1['production'] = ph.clean_html(x2)				
					if 'Titre' in x1: otherInfo1['original_title'] = ph.clean_html(x2)				
					if 'Auteur' in x1: otherInfo1['writers'] = ph.clean_html(x2)	
					
			lst_dat=re.findall('itemprop="description">(.*?)</div>', data, re.S)
			if lst_dat: desc = ph.clean_html(lst_dat[0])
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
		return True

