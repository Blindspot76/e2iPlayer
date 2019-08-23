# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,gethostname
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
###################################################


import re
import base64

def getinfo():
	info_={}
	info_['name']='Hdss.To'
	info_['version']='1.1 08/07/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='301'
	info_['desc']='Films & Series'
	info_['icon']='https://i.ibb.co/f1Tw4M7/j73buveq.png'
	info_['recherche_all']='1'
	info_['update']='fix Films-Tous category'
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'hdss.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://hdss.to'
		self.HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
		self.defaultParams = {'with_metadata':True,'header':self.HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}

	def getPage(self,baseUrl, addParams = {}, post_data = None):
		while True:
			if addParams == {}: addParams = dict(self.defaultParams)
			origBaseUrl = baseUrl
			baseUrl = self.cm.iriToUri(baseUrl)
			addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
			sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
			printDBG(str(sts))
			if sts and 'class="loading"' in data:
				GetIPTVSleep().Sleep(5)
				continue
			break
		return sts, data
		 
	def showmenu0(self,cItem):
		hst='host2'
		img_=cItem['icon']								
		Cat_TAB = [
					{'category':hst,'title': 'Films', 'mode':'20','sub_mode':0},
					{'category':hst,'title': 'Series', 'mode':'20','sub_mode':1},
					{'category':hst,'title': 'Par Lettre', 'mode':'20','sub_mode':2},				
					{'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
					]
		self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})	
				
	def showmenu1(self,cItem):
		hst='host2'
		img_=cItem['icon']	
		gnr=cItem['sub_mode']
		if gnr==0:						
			Cat_TAB = [
						{'category':hst,'title': 'Tous',                'mode':'30','url':'https://hdss.to/films/'},
						{'category':hst,'title': 'Les Plus Populaires', 'mode':'30','url':'https://hdss.to/populaires/'},
						{'category':hst,'title': 'Les Mieux Notés',     'mode':'30','url':'https://hdss.to/mieux-notes/'},
						{'category':hst,'title': 'Par Genre',           'mode':'20','sub_mode':3},
						]
			self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})
			
		elif gnr==1:
			Cat_TAB = [
						{'category':hst,'title': 'Tous',                'mode':'30','url':'https://hdss.to/tv-seriess/'},
						{'category':hst,'title': 'Par Genre',           'mode':'20','sub_mode':4},
						]			
			self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_})
			
		elif gnr==2:
			sts, data = self.getPage(self.MAIN_URL)
			if sts:
				data_list = re.findall('class="AZList">(.*?)</ul>', data, re.S)
				if data_list:
					data_list2 = re.findall('<li.*?href="(.*?)">(.*?)<', data_list[0], re.S)
					for (url,titre) in data_list2:
						self.addDir({'import':cItem['import'],'category' : hst,'url': url,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
		else :
			sts, data = self.getPage(self.MAIN_URL)
			if sts:
				data_list = re.findall('<ul class="sub-menu">(.*?)</ul>', data, re.S)
				if data_list:
					if gnr==3: add_='?tr_post_type=1'
					else: add_='?tr_post_type=2'
					data_list2 = re.findall('<li.*?href="(.*?)">(.*?)<', data_list[-1], re.S)
					for (url,titre) in data_list2:
						self.addDir({'import':cItem['import'],'category' : hst,'url': url+add_,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
					
			
			
			
					
		
	'''	
		sts, data = self.getPage('https://hdss.to/bumblebe-r/')
		data_list = re.findall('class="TPlayerTb.*?trembed=(.*?)("|&quot;)', data, re.S)
		for (url,x1) in data_list:
			url=url.replace('&amp;','&')
			url='https://hdss.to/'+'?trembed='+url.replace('&#038;','&')
			sts, data2 = self.getPage(url,self.defaultParams)
			printDBG(data2)
			data_list2 = re.findall('src.*?["\'](.*?)["\']', data2, re.S)
			if data_list2:
				url=data_list2[0]
				sts, data3 = self.getPage(url,self.defaultParams)
				printDBG('data222'+data3)
				data_list3 = re.findall("var id.+?'(.+?)'", data3, re.S)
				if data_list3:
					url1='https://hdss.to/?trhidee=1&trfex='+data_list3[0][::-1]
					paramsUrl = dict(self.defaultParams)
					paramsUrl['header']['Referer'] = url
					sts, data3 = self.getPage(url1,paramsUrl)
					printDBG('dataeta'+str(data3.meta))
					Url=data3.meta['url']
					if self.up.checkHostSupport(Url)==1:
						self.addVideo({'import':cItem['import'],'category' : 'host2','url': Url,'title':Url,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
					elif 'hdsto' in Url:
						URL = 'https://' + Url.split('/')[2] + '/hls/'+Url.split('id=')[1]+'/'+Url.split('id=')[1]+'.playlist.m3u8'
						self.addVideo({'import':cItem['import'],'category' : 'host2','url': URL,'title':'Direct','desc':URL,'icon':cItem['icon'],'hst':'tshost','mode':'30'})	

			
'''


		
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
			if not '/letters/' in url1:
				data_list = re.findall('class="TPost C">(.*?)</li>', data, re.S)
				i=0
				for data1 in data_list:
					i=i+1
					data_list1 = re.findall('href="(.*?)".*?src="(.*?)".*?Title">(.*?)<', data1, re.S)
					if data_list1:
						url=data_list1[0][0]
						image=data_list1[0][1]
						titre=data_list1[0][2]
						desc=''
						data_listi = re.findall('class="Year">(.*?)<', data1, re.S)
						if data_listi: desc='\c00??????Year: \c00????00'+data_listi[0]+' \c00??????| '
						data_listi = re.findall('star">(.*?)<', data1, re.S)
						if data_listi: desc=desc+'\c00??????Rate: \c00????00'+data_listi[0]+' \c00??????| '				
						data_listi = re.findall('Qlty">(.*?)<', data1, re.S)
						if data_listi: desc=desc+'\c00??????Qualité: \c00????00'+data_listi[0]+' \c00??????| '
						data_listi = re.findall('Description">(.*?)</p>', data1, re.S)							
						if data_listi: desc=desc+'\\n\c00??????Résumé: \c0000????'+ph.clean_html(data_listi[0])							
						data_listi = re.findall('Genre:(.*?)</p>', data1, re.S)							
						if data_listi: desc=desc+'\\n\c00??????Genre: \c00????00'+ph.clean_html(data_listi[0])				
						data_listi = re.findall('Director:(.*?)</p>', data1, re.S)							
						if data_listi: desc=desc+'\\n\c00??????Director: \c00????00'+ph.clean_html(data_listi[0])				
						data_listi = re.findall('Cast:(.*?)</p>', data1, re.S)							
						if data_listi: desc=desc+'\\n\c00??????Cast: \c00????00'+ph.clean_html(data_listi[0])					
						
						self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':self.cleanHtmlStr(titre),'desc':desc,'icon':image,'mode':'31'})	
				if i>19:
					self.addDir({'import':cItem['import'],'title':'\c0000????Page Suivante','page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									
			else:
				data_list = re.findall('class="Num">.*?href="(.*?)".*?src="(.*?)"(.*?)<strong>(.*?)<.*?class="Info">(.*?)</tr>', data, re.S)
				i=0
				for (url,image,type_,titre,desc1) in data_list:
					i=i+1
					if 'Qlty">TV' in type_:
						type_='  \c0000????(Serie)'
					else: type_=''
					desc=''
					data_listi = re.findall('Qlty">(.*?)<', desc1, re.S)							
					if data_listi: desc=desc+'\c00??????Qualité: \c00????00'+ph.clean_html(data_listi[0])+' \c00??????| '					
					data_listi = re.findall('<td>(.*?)</td', desc1, re.S)							
					if data_listi: 
						desc=desc+'\c00??????Durée: \c00????00'+ph.clean_html(data_listi[0])+' \c00??????| Genre: \c00????00'+ph.clean_html(data_listi[1])
					self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':self.cleanHtmlStr(titre)+type_,'desc':desc,'icon':image,'mode':'31'})	
				if i>19:
					self.addDir({'import':cItem['import'],'title':'\c0000????Page Suivante','page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	def showelms(self,cItem):
		urlo=cItem['url']
		img_=cItem['icon']
		desc=cItem['desc']
		sts, data = self.getPage(urlo)
		if sts:
			data_list = re.findall('AA-Season.*?">(.*?)<table>(.*?)</table>', data, re.S)
			if data_list:
				for (name,data1) in data_list:
					data1=data1.replace('&quot;','"')
					self.addMarker({'title':'\c00????00'+ph.clean_html(name),'icon':cItem['icon']})
					data_list1 = re.findall('class="Num">(.*?)<a.*?href="(.*?)".*?src="(.*?)".*?href="(.*?)">(.*?)</a>(.*?)</td>', data1, re.S)
					for (num,url,image,x1,titre,date) in data_list1:
						titre='Episode \c00????00'+ph.clean_html(num)+'\c00??????: '+titre+' \c0000????('+ph.clean_html(date)+')'
						self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url,'desc':desc,'icon':image,'hst':'tshost','good_for_fav':True})	
			else:
				self.addVideo({'import':cItem['import'],'category' : 'host2','title':cItem['title'],'url':urlo,'desc':desc,'icon':img_,'hst':'tshost','good_for_fav':True})	
		
	
	def SearchResult(self,str_ch,page,extra):
		url_=self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
		sts, data = self.getPage(url_)
		if sts:
			data_list = re.findall('class="TPost C">(.*?)</li>', data, re.S)
			i=0
			for data1 in data_list:
				i=i+1
				data_list1 = re.findall('href="(.*?)".*?src="(.*?)".*?Title">(.*?)<', data1, re.S)
				if data_list1:
					url=data_list1[0][0]
					image=data_list1[0][1]
					titre=data_list1[0][2]
					desc=''
					data_listi = re.findall('class="Year">(.*?)<', data1, re.S)
					if data_listi: desc='\c00??????Year: \c00????00'+data_listi[0]+' \c00??????| '
					data_listi = re.findall('star">(.*?)<', data1, re.S)
					if data_listi: desc=desc+'\c00??????Rate: \c00????00'+data_listi[0]+' \c00??????| '				
					data_listi = re.findall('Qlty">(.*?)<', data1, re.S)
					if data_listi: 
						desc=desc+'\c00??????Qualité: \c00????00'+data_listi[0]+' \c00??????| '
						if data_listi[0]=='TV': titre=titre+' \c0000????(Serie)'
					data_listi = re.findall('Description">(.*?)</p>', data1, re.S)							
					if data_listi: desc=desc+'\\n\c00??????Résumé: \c0000????'+ph.clean_html(data_listi[0])							
					data_listi = re.findall('Genre:(.*?)</p>', data1, re.S)							
					if data_listi: desc=desc+'\\n\c00??????Genre: \c00????00'+ph.clean_html(data_listi[0])				
					data_listi = re.findall('Director:(.*?)</p>', data1, re.S)							
					if data_listi: desc=desc+'\\n\c00??????Director: \c00????00'+ph.clean_html(data_listi[0])				
					data_listi = re.findall('Cast:(.*?)</p>', data1, re.S)							
					if data_listi: desc=desc+'\\n\c00??????Cast: \c00????00'+ph.clean_html(data_listi[0])					
					
					self.addDir({'name':'sherch','import':extra,'category' : 'host2','url': url,'title':self.cleanHtmlStr(titre),'desc':desc,'icon':image,'mode':'31'})	


	def get_links(self,cItem):
		urlTab = []
		URL=cItem['url']
		sts, data = self.getPage(URL)
		if sts:
			data_list = re.findall('class="TPlayerTb.*?trembed=(.*?)("|&quot;)', data, re.S)
			for (url,x1) in data_list:
				url=url.replace('&amp;','&')
				url=self.MAIN_URL+'/?trembed='+url.replace('&#038;','&')
				sts, data2 = self.getPage(url,self.defaultParams)
				printDBG(data2)
				data_list2 = re.findall('src.*?["\'](.*?)["\']', data2, re.S)
				if data_list2:
					url=data_list2[0]
					sts, data3 = self.getPage(url,self.defaultParams)
					printDBG('data222'+data3)
					data_list3 = re.findall("var id.+?'(.+?)'", data3, re.S)
					if data_list3:
						url1=self.MAIN_URL+'/?trhidee=1&trfex='+data_list3[0][::-1]
						paramsUrl = dict(self.defaultParams)
						paramsUrl['header']['Referer'] = url
						sts, data3 = self.getPage(url1,paramsUrl)
						printDBG('dataeta'+str(data3.meta))
						Url=data3.meta['url']
						if self.up.checkHostSupport(Url)==1:
							urlTab.append({'name':gethostname(Url), 'url':Url, 'need_resolve':1})
						elif 'hdsto' in Url:
							URL = 'https://' + Url.split('/')[2] + '/hls/'+Url.split('id=')[1]+'/'+Url.split('id=')[1]+'.playlist.m3u8'
							URL = strwithmeta(URL, {'Referer':Url})	
							urlTab.extend(getDirectM3U8Playlist(URL, checkExt=True, checkContent=True, sortWithMaxBitrate=999999999))

			#urlTab = getDirectM3U8Playlist(URL, checkExt=True, checkContent=True, sortWithMaxBitrate=999999999)		
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
			
