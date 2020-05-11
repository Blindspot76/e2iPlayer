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
	info_['name']='Vidlink.Org'
	info_['version']='1.0 10/09/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'
	info_['desc']='Movies & TV shows'
	info_['icon']='https://i.ibb.co/bJwn22Q/vidlink.png'
	info_['recherche_all']='1'
	info_['update']='New Host'
	info_['warning']='---->  !! Only for Search  !! <----'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'vidlink.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0'
		self.MAIN_URL = 'https://vidlink.org'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

		self.getPage = self.cm.getPage
		 





	def showmenu0(self,cItem):

		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'MOVIES',       'url': self.MAIN_URL, 'mode':'30'},				
					{'category':hst,'title': tscolor('\c0000????')+'By Genre',  'mode':'20'},																	
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_,'desc':''})				


	def showmenu1(self,cItem):
		elms = ['Action','Romance','Fantasy','Sci-Fi','Horror','Adventure','Comedy','Drama','Mystery',
		' Biography','Music','Musical','Horror','Thriller','Romance','Animation','Family','War']
		for elm in elms:
			Url=self.MAIN_URL+'/?q='+elm
			self.addDir({'import':cItem['import'],'category' : 'host2','url': Url,'title':elm,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})		
	
	def showitms(self,cItem):
		url=cItem['url']
		sts, data = self.getPage(url)
		if sts:
			films_list = re.findall('p-thumb">.*?href="(.*?)".*?src="(.*?)".*?title="(.*?)".*?a-line">(.*?)</div>.*?a-line".*?>(.*?)</div>', data, re.S)		
			for (url,image,titre,desc1,desc2) in films_list:
				desc = ph.clean_html(desc1)+'\n'+ph.clean_html(desc2)
				if image.startswith('//'): image = 'http:'+image
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url':self.MAIN_URL+url,'title':titre,'desc':desc,'icon':image,'hst':'tshost'})	

	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/results?q='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			films_list = re.findall('p-thumb">.*?href="(.*?)".*?src="(.*?)".*?title="(.*?)".*?a-line">(.*?)</div>.*?a-line".*?>(.*?)</div>', data, re.S)		
			for (url,image,titre,desc1,desc2) in films_list:
				desc = ph.clean_html(desc1)+'\n'+ph.clean_html(desc2)
				if image.startswith('//'): image = 'http:'+image
				self.addVideo({'import':extra,'good_for_fav':True,'category' : 'video','url':self.MAIN_URL+url,'title':titre,'desc':desc,'icon':image,'hst':'tshost'})	


	def get_links(self,cItem):
		urlTab = []	
		URL=cItem['url'].replace('/post/','/embed/')
		x1,id_=URL.split('/embed/')
		URL = 'https://vidlink.org/embed/update_views'
		post_data = {'postID':id_}
		sts, data = self.getPage(URL,post_data=post_data)
		if sts:
			printDBG('data='+data)
			data = cPacker().unpack(data.strip())
			printDBG('dataaaaa'+data)
			ol_data = re.findall('var.*?oploadID="(.*?)"', data, re.S)
			gitURL_data = re.findall('var.*?gitURL="(.*?)"', data, re.S)
			sub_data = re.findall('var.*?subs=\[(.*?)\]', data, re.S)						
			file1_data = re.findall('var.*?file1="(.*?)"', data, re.S)

			if ol_data:
				if ol_data[0]!='':
					urlTab.append({'name':'Openload', 'url':'https://openload.co/embed/'+ol_data[0], 'need_resolve':1})
			if file1_data:
				if file1_data[0]!='':
					urlTab.append({'name':'HLS', 'url':'hst#tshost#'+file1_data[0]+'|0||XXVID', 'need_resolve':1,'type':'local'})		
			if gitURL_data:
				if gitURL_data[0]!='':
					sts, data = self.getPage(gitURL_data[0])
					if sts:	
						sub_data = re.findall('URI="/sub/vtt/(.*?)/.*?LANGUAGE="(.*?)"', data, re.S)
						for (vtt,lng) in sub_data:
							if file1_data:
								if file1_data[0]!='':							
									urlTab.append({'name':'|'+lng+' Sub| HLS', 'url':'hst#tshost#'+file1_data[0]+'|'+vtt+'|'+lng+'|XXVID', 'need_resolve':1,'type':'local'})	
						
		return urlTab
		
		
	def getVideos(self,videoUrl):
		urlTab = []	
		videoUrl,vtt,lng,x1=videoUrl.split('|')
		if vtt =='0':
			urlTab.append((videoUrl,'3'))
		else:
			vtt_url='https://opensubtitles.co/sub/'+vtt+'.vtt'+'|'+lng+'|'+videoUrl
			urlTab.append((vtt_url,'6'))	
			
		return urlTab		
	

	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='30':
			self.showitms(cItem)			
			
