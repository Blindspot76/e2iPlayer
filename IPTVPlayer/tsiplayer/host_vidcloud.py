# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.packer import cPacker
###################################################


import re
import base64
import time

def getinfo():
	info_={}
	info_['name']='Vidcloud.Icu'
	info_['version']='1.0 10/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='104'#'401'
	info_['desc']='Movies & TV shows'
	info_['icon']='https://vidcloud.icu/img/logo_vid.png?1'
	info_['recherche_all']='1'
	info_['update']='New Host'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'vidcloud.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0'
		self.MAIN_URL = 'https://vidcloud.biz/'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):

		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'MOVIES',        'url': self.MAIN_URL+'/movies', 'mode':'30'},
					{'category':hst,'title': 'Cinema Movies', 'url': self.MAIN_URL+'/cinema-movies', 'mode':'30'},
					{'category':hst,'title': 'TV Series',     'url': self.MAIN_URL+'/series', 'mode':'30'},
					{'category':hst,'title': 'Featured Series', 'url': self.MAIN_URL+'/recommended-series', 'mode':'30'},																					
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_,'desc':''})				

	
	def showitms(self,cItem):
		url=cItem['url']
		page=cItem.get('page',1)
		url_=url+'?page='+str(page)
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('video-block ">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?meta">(.*?)</div', data, re.S)		
			for (url,image,titre,desc1) in films_list:
				desc = ph.clean_html(desc1)
				url=self.MAIN_URL+url
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url':url,'title':ph.clean_html(titre),'desc':desc,'icon':image,'hst':'tshost'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/search.html?keyword='+str_ch+'&page='+str(page)
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('video-block ">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?meta">(.*?)</div', data, re.S)		
			for (url,image,titre,desc1) in films_list:
				desc = ph.clean_html(desc1)
				url=self.MAIN_URL+url
				self.addVideo({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url':url,'title':ph.clean_html(titre),'desc':desc,'icon':image,'hst':'tshost'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url']
		url=URL
		if 'load.php' not in URL:
			sts, data = self.getPage(URL)
			if sts:		
				Tab_els = re.findall('<iframe src="(.*?)"', data, re.S)
				if Tab_els:
					url = Tab_els[0]
		if url.startswith('//'): url = 'http:'+url
		sts, data = self.getPage(url)
		if sts:
			printDBG('rrrrrrrr'+data)
			#if 'tracks' in data:
			#	printDBG('1')
			#	Tab_els = re.findall('playerInstance.setup.*?sources:\[(.*?)\].*?tracks.*?\[(.*?)\]', data, re.S)
			#else:
			#	printDBG('2')
			Tab_els = re.findall('playerInstance.setup.*?sources:\[(.*?)\]', data, re.S)
			url_tabs=[]
			for url_data in Tab_els:
				printDBG('3'+url_data)
				Tab_ = re.findall('file.*?\'(.*?)\'.*?label.*?\'(.*?)\'', url_data, re.S)
				for (url_,label_) in Tab_:
					printDBG('4')
					if url_ not in url_tabs:
						url_tabs.append(url_)
						urlTab.append({'name':'|HLS 1| Vidcloud', 'url':'hst#tshost#'+url_+'|XXVIC', 'need_resolve':1,'type':'local'})

			Tab_els = re.findall('window.urlVideo.*?\'(.*?)\'', data, re.S)
			for url_data in Tab_els:
				urlTab.append({'name':'|HLS 2| Vidcloud', 'url':'hst#tshost#'+url_data+'|XXVIC', 'need_resolve':1,'type':'local'})



			Tab_els = re.findall('server-items">(.*?)</ul>', data, re.S)
			if Tab_els:
				Tab_els = re.findall('<li.*?data-video="(.*?)">(.*?)<', Tab_els[0], re.S)
				for (url,host) in Tab_els:
					if (url!='') and ('vidcloud.icu/load.php' not in url):
						urlTab.append({'name':host, 'url':'hst#tshost#'+url+'|XXVIC', 'need_resolve':1})

		return urlTab
		
		
	def getVideos(self,videoUrl):
		urlTab = []	
		videoUrl,x1=videoUrl.split('|')
		if '/v/' in videoUrl:
			url_post=videoUrl.replace('/v/','/api/source/')
			data_post = {'r':'','d':'gcloud.live'}
			sts, data = self.getPage(url_post,post_data=data_post)
			if sts:
				printDBG('ffffffffffff'+data)
				Tab_els0 = re.findall('"file":"(.*?)".*?label":"(.*?)".*?type":"(.*?)"', data, re.S)
				for (url,label,type_) in Tab_els0:
					name = type_+' ['+label+']'
					urlTab.append((name+'|'+url.replace('\\',''),'4'))
		elif 'api.vidnode' in videoUrl:
			param = dict(self.defaultParams)
			param['with_metadata']  = True,
			param['no_redirection'] = True
			sts, data = self.getPage(videoUrl,param)
			if sts:
				videoUrl=self.cm.meta.get('location', '')
				urlTab.append((videoUrl,'1'))
			
		elif 'm3u8' in videoUrl:
			videoUrl = strwithmeta(videoUrl,{'Referer':'https://vidcloud.icu/'})
			urlTab.append((videoUrl,'3'))
		elif 'mp4':
			videoUrl = strwithmeta(videoUrl,{'Referer':'https://vidcloud.icu/'})
			urlTab.append((videoUrl,'0'))	
			 				
		return urlTab		
	
	def getArticle(self, cItem):
		otherInfo1 = {}
		desc= cItem.get('desc','')	
		sts, data = self.getPage(cItem['url'])
		if sts:
			lst_dat=re.findall('<div class="quads.*?<p><strong>(.*?)<a', data, re.S)
			if lst_dat:
				desc=lst_dat[0].replace('<strong>','\\n'+tscolor('\c00????00'))
				desc=desc.replace('</strong>',tscolor('\c00??????'))
				desc=ph.clean_html(desc)
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
		if mode=='30':
			self.showitms(cItem)			
			
