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
	info_['name']='123Movies'
	info_['version']='1.0 06/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'
	info_['desc']='Watch Movies & TV shows'
	info_['icon']='https://i.ibb.co/kQGDxLc/x123.png'
	info_['recherche_all']='1'
	info_['update']='Change Host url and fix HLS srver'
	#info_['warning']='---->  !! Work only in Eplayer3 WITH BUFFERING  !! <----'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'123movies.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0'
		self.MAIN_URL = 'https://w3.d123movies.com/'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):

		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'MOVIES',       'url': self.MAIN_URL+'/movies/',      'mode':'30'},
					{'category':hst,'title': 'TV SERIES',    'url': self.MAIN_URL+'/tv-series/',   'mode':'30'},
					{'category':hst,'title': 'Just Updated', 'url': self.MAIN_URL+'/just-updated/','mode':'30'},
					{'category':hst,'title': 'Most Viewed',  'url': self.MAIN_URL+'/most-viewed/', 'mode':'30'},				
					{'category':hst,'title': tscolor('\c00????00')+'Filter',           'mode':'21'},													
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_,'desc':''})				

	def showfilter(self,cItem):
		count=cItem.get('count',0)
		data=cItem.get('data',[])
		desc1=cItem.get('desc','')
		#https://w2.0123moviesback.com/most-viewed/page/2/?tax_category%5B0%5D=action&tax_country%5B0%5D=usa&wpas=1
		url=cItem.get('url',self.MAIN_URL)
		if count==0:
			sts, data = self.getPage(self.MAIN_URL+'/movies/')
			if sts:
				films_list1 = re.findall('class="filter.*?<ul(.*?)</ul', data, re.S)	
				films_list2 = re.findall('tax_category">(.*?)wpas-tax_country', data, re.S)
				films_list3 = re.findall('tax_country">(.*?)clearfix"', data, re.S)
				if films_list1 and films_list2 and films_list3:
					data=[films_list1[0],films_list2[0],films_list3[0]]
					self.addMarker({'title':tscolor('\c0000??00')+'Sort by:','desc':'','icon':cItem['icon']})		
					elm_list = re.findall('<li.*?href="(.*?)".*?">(.*?)</li>', data[0], re.S)
					for (url1,titre) in elm_list:
						desc = ph.clean_html(titre).strip()
						urlo=url+url1.replace('https://dwatchseries.org','')+'page/1/'
						self.addDir({'import':cItem['import'],'count':1,'data':data,'category' : 'host2','url': urlo,'title':ph.clean_html(titre).strip(),'desc':desc,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	
		elif count==1:			
			self.addMarker({'title':tscolor('\c0000??00')+'Genre:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('class="wpas-tax_category.*?value="(.*?)".*?">(.*?)<', data[1], re.S)
			self.addDir({'import':cItem['import'],'count':2,'data':data,'category' : 'host2','url': url,'title':'All','desc': desc1 + ' | All category','icon':cItem['icon'],'hst':'tshost','mode':'21'})				
			for (url1,titre) in elm_list:
				urlo=url+'?tax_category%5B0%5D='+url1
				desc = desc1 + ' | '+ph.clean_html(titre).strip()
				titre=self.cleanHtmlStr(titre)
				self.addDir({'import':cItem['import'],'count':2,'data':data,'category' : 'host2','url': urlo,'title':titre.strip(),'desc':desc,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	

		elif count==2:			
			self.addMarker({'title':tscolor('\c0000??00')+'Country:','desc':'','icon':cItem['icon']})		
			elm_list = re.findall('class="wpas-tax_country.*?value="(.*?)".*?">(.*?)<', data[2], re.S)
			self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':'All','desc':desc1 + ' | All country','icon':cItem['icon'],'hst':'tshost','mode':'30'})				
			for (url1,titre) in elm_list:
				if '?tax' in url:
					urlo=url+'&tax_country%5B0%5D='+url1+'&wpas=1'
				else:
					urlo=url+'?tax_country%5B0%5D='+url1+'&wpas=1'
				desc = desc1 + ' | '+ph.clean_html(titre).strip()
				self.addDir({'import':cItem['import'],'category' : 'host2','url': urlo,'title':titre.strip(),'desc':desc,'icon':cItem['icon'],'hst':'tshost','mode':'30'})	



		
	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		
		if '/page/1/' in url1:
			url1=url1.replace('/page/1/','/page/'+str(page)+'/')
		else:
			url1=url1+'page/'+str(page)+'/'
		sts, data = self.getPage(url1)
		if sts:
			films_list = re.findall('ml-item">.*?href="(.*?)".*?title="(.*?)".*?original="(.*?)".*?imdb">(.*?)<.*?desc">(.*?)<div.*?Genre:.*?(<.*?)</div>', data, re.S)		
			for (url,titre,image,imdb,desc,genre) in films_list:
				desc_ = ''
				if 'N/A' not in imdb: desc_ = tscolor('\c0000??00')+imdb+'\n'
				desc_ = desc_+tscolor('\c0000??00')+' Genre: '+tscolor('\c00????00')+ph.clean_html(genre)+'\n'
				desc  = desc_+tscolor('\c0000??00')+' Story: '+tscolor('\c00????00')+ph.clean_html(desc)+'\n'
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url':url,'title':ph.clean_html(titre),'desc':desc,'icon':self.MAIN_URL+image,'hst':'tshost','mode':'31'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	def showelms(self,cItem):
		urlo=cItem['url']
		img_=cItem['icon']
		sts, data = self.getPage(urlo)	
		if sts:
			films_list0 = re.findall('server mr5">(.*?)</ul', data, re.S)
			if films_list0:
				films_list = re.findall('href="(.*?)".*?title="(.*?)">(.*?)</', films_list0[0], re.S)
				for (url,titre,titre2) in films_list:
					if titre2 != '0':
						titre = 'Ep: '+titre2

					self.addVideo({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': self.MAIN_URL+url,'title':titre,'desc':'HLS Servers must execute in Buffering Mode\\n'+cItem['desc'],'icon':cItem['icon'],'hst':'tshost'})	

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('ml-item">.*?href="(.*?)".*?title="(.*?)".*?original="(.*?)".*?imdb">(.*?)<.*?desc">(.*?)<div.*?Genre:.*?(<.*?)</div>', data, re.S)		
			for (url,titre,image,imdb,desc,genre) in films_list:
				desc_ = ''
				if 'N/A' not in imdb: desc_ = tscolor('\c0000??00')+imdb+'\n'
				desc_ = desc_+tscolor('\c0000??00')+' Genre: '+tscolor('\c00????00')+ph.clean_html(genre)+'\n'
				desc  = desc_+tscolor('\c0000??00')+' Story: '+tscolor('\c00????00')+ph.clean_html(desc)+'\n'
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url':url,'title':ph.clean_html(titre),'desc':desc,'icon':self.MAIN_URL+image,'hst':'tshost','mode':'31'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		
		# From mediabox
		if ('all123movies.com' in URL):
			x1,URL=URL.split('all123movies.com')
			URL=self.MAIN_URL+URL
			URL,prefix=URL.split('-eps-')
			ep,srv=prefix.replace('/','').split('-server-')
			URL=URL+'/?sv='+srv+'&ep='+ep
		
		sts, data = self.getPage(URL)
		if sts:
			link_data   = re.findall('jQuery.ajax.*?url.*?"(.*?)"', data, re.S)
			action_data = re.findall('jQuery.ajax.*?data.*?action.*?\'(.*?)\'', data, re.S)
			nonce_data = re.findall('jQuery.ajax.*?data.*?nonce.*?\'(.*?)\'', data, re.S)
			Player_data = re.findall('jQuery\(document\).*?Player\((.*?)\)', data, re.S)			
			if (link_data and action_data and nonce_data and Player_data):
				link   = link_data[0]
				action = action_data[0]
				nonce  = nonce_data[0]
				Player = Player_data[0]
				episode,server,postid,ep_link,episodei = Player.replace('"','').split(',')
				
				url_post  = self.MAIN_URL+link
				post_data = {'action':action, 'nonce':nonce,'episode':episode,'episodei':'','server':server,'postid':postid}
				sts, data = self.getPage(url_post,post_data=post_data)
				if sts:
					server_data = re.findall('vb_json_data.*?\'(.*?)\'', data, re.S)
					if server_data:
						server_json = json_loads(server_data[0])
						for server in server_json[1]:
							name = server['s'].replace('Picasaweb ','')
							url  = server['u']
							local=''
							if url !='':
								url = base64.b64decode(url)
								if not url.startswith('http'):
									url = self.MAIN_URL+url
								if 'vredirect.php' in url:
									if ('HLS' in name) or ('High' in name):
										name = '|'+	name +'| 123Movies'
										local='local'
									urlTab.append({'name':name, 'url':'hst#tshost#'+url+'|XX123', 'need_resolve':1,'type':local})
								else:
									if ('mp4' in url) or ('m3u8' in url):
										name = '|'+	name +'| Direct Link'
										urlTab.append({'name':name, 'url':url, 'need_resolve':0,'type':'local'})								 								
									else:
										urlTab.append({'name':name, 'url':url, 'need_resolve':1})
									
										
								
		return urlTab
		
		
	def getVideos(self,videoUrl):
		urlTab = []	
		videoUrl,mode=videoUrl.split('|')
		#if mode=='XX123':
		params = dict(self.defaultParams)
		params['no_redirection'] = True
		sts, data = self.getPage(videoUrl,params)
		if sts:
			url1 = self.cm.meta.get('location', 'non')
			if url1=='non':
				url_data = re.findall('href=[\'"](.*?)[\'"]', data, re.S)
				if url_data:
					url1=url_data[0]	
			if 'driveproxy' in url1:
				sts, data = self.getPage(url1)
				if sts:
					url_data2 = re.findall('file:[\'"](.*?)[\'"]', data, re.S)						
					if url_data2:
						link=strwithmeta(url_data2[0],{'Referer' : url1,'Origin':'http://driveproxy.net'})
						urlTab.append((link,'0'))					
			elif self.up.checkHostSupport(url1):
				urlTab.append((url1,'1'))
			else:
				urlTab.append((url1,'0'))
		
		return urlTab		
		
			
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc= cItem.get('desc','')	
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
			
