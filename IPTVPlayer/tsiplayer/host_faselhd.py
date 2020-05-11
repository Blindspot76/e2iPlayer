# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Components.config import config
import base64,urllib
import re



def getinfo():
	info_={}
	info_['name']='Faselhd.Co'
	info_['version']='1.3 06/10/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='201'
	info_['desc']='أفلام و مسلسلات اسياوية و اجنبية'
	info_['icon']='https://i.ibb.co/jw33PcN/logo.png'
	info_['recherche_all']='1'
	info_['update']='Add Local M3u8 and T7meel servers '	
	return info_
	
	
class TSIPHost(TSCBaseHostClass):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'faselhd.cookie'})
		self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
		self.MAIN_URL = 'https://www.faselhd.co'
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.getPage = self.cm.getPage
		 
	def showmenu0(self,cItem):
		hst='host2'
		img=cItem['icon']			
		Fasel_TAB=[ {'category':hst,'title': 'الأحدث'               ,'mode':'30'  ,'icon':img ,'url':'https://www.faselhd.co/most_recent','page':1},			
					{'category':hst,'title': 'الأفلام'               ,'mode':'20' ,'icon':img ,'sub_mode':0},
					{'category':hst,'title': 'المسلسلات'            ,'mode':'20' ,'icon':img ,'sub_mode':1},
					{'category':hst,'title': 'الأنمي'               ,'mode':'20' ,'icon':img ,'sub_mode':3},	
					{'category':hst,'title': 'البرامج التلفزيونية' ,'mode':'20' ,'icon':img ,'sub_mode':2},						  
					{'category':'search'  ,'title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':img},
					]
		self.listsTab(Fasel_TAB, {'import':cItem['import'],'name':hst})			

	def showmenu1(self,cItem):
		hst='host2'
		img=cItem['icon']
		gnr2=cItem['sub_mode']			 
		sts, data = self.getPage('https://www.faselhd.co/')
		if sts:
			if gnr2==0:
				pat='menu-item-has-children.*?href="(.*?)">(.*?)<(.*?)المسلسلات'
			else:
				pat='menu-item-has-children.*?href="(.*?)">(.*?)<(.*?)</ul>'			
			if gnr2==4:
				self.addDir({'import':cItem['import'],'category' :'host2', 'url':'https://www.faselhd.co/movies', 'title':'جميع الأفلام الأجنبية', 'desc':'الأفلام الأجنبية', 'icon':img, 'mode':'30','page':1})
				lst_data = re.findall('>الأفلام الأجنبية</a>(.*?)</ul>',data, re.S)
				if lst_data:
					data1=lst_data[0]							
					lst_data1 = re.findall('href="(.*?)">(.*?)<',data1, re.S)
					for (url,titre) in lst_data1:
						self.addDir({'import':cItem['import'],'category' :hst, 'url':url, 'title':titre, 'desc':titre, 'icon':img, 'mode':'30','page':1})
			else:
				lst_data = re.findall(pat,data, re.S)
				if lst_data:
					url1=lst_data[gnr2][0]
					titre1=lst_data[gnr2][1]
					data1=lst_data[gnr2][2]							
					lst_data1 = re.findall('href="(.*?)">(.*?)<',data1, re.S)
					for (url,titre) in lst_data1:
						if not '/movies-cats/' in url:
							if titre=='الأفلام الأجنبية':
								self.addDir({'import':cItem['import'],'category' :hst, 'url':url, 'title':titre, 'desc':titre, 'icon':img, 'mode':'20','sub_mode':4})						
							else:
								self.addDir({'import':cItem['import'],'category' :hst, 'url':url, 'title':titre, 'desc':titre, 'icon':img, 'mode':'30','page':1})	
		if gnr2==1:
			self.addDir({'import':cItem['import'],'category' :hst, 'url':'https://www.faselhd.co/asian-series', 'title':'المسلسلات الآسيوية', 'desc':'المسلسلات الآسيوية', 'icon':img, 'mode':'30','page':1})	
		if gnr2==0:
			self.addDir({'import':cItem['import'],'category' :hst, 'url':'https://www.faselhd.co/oscars-winners', 'title':'جوائز الأوسكار', 'desc':'جوائز الأوسكار', 'icon':img, 'mode':'31'})	
	
	def showitms1(self,cItem):
		url0=cItem['url']
		img=cItem['icon']
		page=cItem['page']
		if '?' in url0:
			link,flt=url0.split('?')
			link=link+'/page/'+str(page)+'?'+flt
		elif 'movies_collections' in url0:
			link=url0+'?page_num='+str(page)
		else:
			link=url0+'/page/'+str(page)		
		sts, data = self.cm.getPage(link)
		if sts:
			lst_data=re.findall('class="movie-wrap">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?<span>(.*?)</span>(.*?)<h1>', data, re.S)			
			for (url1,image,name_eng,desc1,desc2) in lst_data:
				desc=''
				if self.cleanHtmlStr(desc1)!='':
					desc='Rate:'+self.cleanHtmlStr(desc1)+'\n'
				desc=desc+self.cleanHtmlStr(desc2)+'\n'
				name_eng=self.cleanHtmlStr(name_eng)
				name_eng=name_eng.replace('فيلم ','')
				name_eng=name_eng.replace('مسلسل ','')
				name_eng=name_eng.replace('أنمي ','')	
				name_eng=name_eng.replace('&#8211;','-')				
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':str(name_eng), 'desc':desc, 'icon':image, 'mode':'32'} )	
			self.addDir({'import':cItem['import'],'category':'host2', 'url':url0, 'title':tscolor('\c0000??00')+'Page Suivante', 'page':page+1, 'desc':'Page Suivante', 'icon':img, 'mode':'30'})					

	def showitms2(self,cItem):
		url0=cItem['url']			 
		sts, data = self.cm.getPage(url0)
		if sts:
			lst_data=re.findall('class="oscars-winner-item".*?href="(.*?)".*?src="(.*?)".*?href.*?">(.*?)<.*?story">(.*?)<', data, re.S)			
			for (url1,image,name_eng,desc) in lst_data:				
				self.addDir({'import':cItem['import'],'good_for_fav':True,'category':'host2', 'url':url1, 'title':name_eng, 'desc':desc, 'icon':image, 'mode':'32'} )							
		
	def showitms3(self,cItem):		
		url0=cItem['url']
		desc=''
		if url0.startswith('/'):
			url0='https://www.faselhd.co'+url0
		if '/anime/' in url0:
			url0=url0+'?display=normal'
		titre0=cItem['title']
		titre0=titre0.replace('|'+tscolor('\c0060??60')+'FaselHD'+tscolor('\c00??????')+'| ','')				
		sts, data = self.cm.getPage(url0)
		if sts:
			if 'http-equiv="refresh"' in data:
				data0=re.findall('http-equiv="refresh".*?URL=\'(.*?)\'', data, re.S)			
				if 	data0:
					sts, data = self.cm.getPage(data0[0])
			if 'class="fa fa-download">' not in data:
				lst_data=re.findall('class="movie-wrap">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?<span>(.*?)</span>(.*?)<h1.*?>(.*?)<', data, re.S)			
				for (url1,image,name_eng1,desc1,desc2,name_eng) in lst_data:
					desc=''
					if self.cleanHtmlStr(desc1)!='':
						desc='Rate:'+self.cleanHtmlStr(desc1)+'\n'
					if name_eng.strip()=='':
						name_eng=name_eng1
					name_eng=name_eng.replace('&#8211;','-')
					self.addDir({'import':cItem['import'],'good_for_fav':True, 'category':'host2', 'url':url1, 'title':name_eng.strip(), 'desc':desc, 'icon':image, 'mode':'32'} )							
			else:
				data1=re.findall('class="movie-details.*?">(.*?)</div>', data, re.S)
				if data1:
					desc=data1[0].replace('<i class="fa','  |  <i class="fa')
					desc=self.cleanHtmlStr(desc)+'\n'
				data1=re.findall('class="movie-story.*?">(.*?)</div>', data, re.S)
				if data1:
					desc=desc+self.cleanHtmlStr(data1[0])
				
				self.addVideo({'import':cItem['import'],'good_for_fav':True,'category':'video', 'url':url0, 'title':titre0, 'desc':desc, 'icon':cItem['icon'], 'hst':'tshost'} )					
		
	def SearchResult(self,str_ch,page,extra):
		url_='https://www.faselhd.co/page/'+str(page)+'/?s='+str_ch
		sts, data = self.cm.getPage(url_)
		if sts:
			lst_data=re.findall('class="movie-wrap">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?<span>(.*?)</span>(.*?)<h1>', data, re.S)			
			for (url1,image,name_eng,desc1,desc2) in lst_data:
				desc=''
				if self.cleanHtmlStr(desc1)!='':
					desc='Rate:'+self.cleanHtmlStr(desc1)+'\n'
				desc=desc+self.cleanHtmlStr(desc2)+'\n'	
				name_eng=name_eng.replace('&#8211;','-')				
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':str(name_eng), 'desc':desc, 'icon':image, 'mode':'32'} )	

	def MediaBoxResult(self,str_ch,year_,extra):
		urltab=[]
		str_ch_o = str_ch
		str_ch = urllib.quote(str_ch_o+' '+year_)
		url_='https://www.faselhd.co/page/1/?s='+str_ch
		sts, data = self.cm.getPage(url_)
		if sts:
			lst_data=re.findall('class="movie-wrap">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?<span>(.*?)</span>(.*?)<h1>', data, re.S)			
			for (url1,image,name_eng,desc1,desc2) in lst_data:
				desc=''
				if self.cleanHtmlStr(desc1)!='':
					desc='Rate:'+self.cleanHtmlStr(desc1)+'\n'
				desc=''
				
				name_eng=str(name_eng).replace('&#8211;','-')
				
				x1,titre0=self.uniform_titre(name_eng,year_op=1)
				desc=x1+desc				
				
				if str_ch_o.lower().replace(' ','') == titre0.replace('-',' ').replace(':',' ').lower().replace(' ',''):
					trouver = True
				else:
					trouver = False
				name_eng='|'+tscolor('\c0060??60')+'FaselHD'+tscolor('\c00??????')+'| '+titre0				
				if trouver:
					urltab.insert(0,{'titre':titre0,'import':extra,'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':name_eng, 'desc':desc, 'icon':image, 'mode':'32'} )					
				else:
					urltab.append({'titre':titre0,'import':extra,'good_for_fav':True,'EPG':True, 'hst':'tshost', 'category':'host2', 'url':url1, 'title':name_eng, 'desc':desc, 'icon':image, 'mode':'32'} )	
		return urltab	
		
	def get_links(self,cItem): 	
		urlTab = []	
		URL=cItem['url']
		sts, data0 = self.cm.getPage(URL)
		if sts:
			Liste_els0 = re.findall('class="movie-btns-single clearfix">(.*?)</div>', data0, re.S)
			if Liste_els0:
				Liste_els1 = re.findall('<a href="(.*?)".*?</i>(.*?)<', Liste_els0[0], re.S)
				for (url5,titre5) in Liste_els1:
					if not 'download=true' in url5:
						if 'إعلان' in titre5: titre5 = '[ Trailer ]'
						urlTab.append({'name':titre5, 'url':url5, 'need_resolve':1})
					else:
						sts, data = self.cm.getPage(url5)
						Liste_els_3 = re.findall('download_wrapper">.*?href="(.*?)"', data.lower(), re.S)			
						if Liste_els_3:	
							sts, data = self.cm.getPage(Liste_els_3[0])
							if sts:
								Liste_els_4 = re.findall('<div class="other_servers">(.*?)</div>', data, re.S)			
								if Liste_els_4:
									Liste_els_5 = re.findall('href="(.*?)".*?">(.*?)<', Liste_els_4[0], re.S)
									for (url_,titre_)in Liste_els_5 :				
										urlTab.append({'name':'|Download Server| '+titre_, 'url':url_, 'need_resolve':1})
						
								Liste_els_6 = re.findall('dl-link">.*?href="(.*?)"', data, re.S)
								if Liste_els_6 :				
									urlTab.append({'name':'|Download Server| T7meel', 'url':Liste_els_6[0], 'need_resolve':0,'type':'local'})
							
										
			Liste_els = re.findall('onclick="player_iframe.*?\'(.*?)\'">(.*?)</a>', data0, re.S)
			for(url,name) in Liste_els:	
				if config.plugins.iptvplayer.ts_dsn.value:
					sts, data = self.cm.getPage(url) 
					if '/video_player?' in url:
						urlTab.append({'name':'|M3u8 v1| Faselhd', 'url':'hst#tshost#'+url, 'need_resolve':1,'type':'local'})					
					elif '/player.php?' in url:
						urlTab.append({'name':'|M3u8 v2| Faselhd', 'url':'hst#tshost#'+url, 'need_resolve':1,'type':'local'})							
					else:
						Liste_els_3 = re.findall('<iframe.*?src="(.*?)"', data, re.S)	
						if Liste_els_3:
							URL_=Liste_els_3[0]
							urlTab.append({'name':self.up.getDomain(URL_).title(), 'url':URL_, 'need_resolve':1})	
				else:
					urlTab.append({'name':self.cleanHtmlStr(name), 'url':'hst#tshost#'+url, 'need_resolve':1})					
		return urlTab
		 
	def getVideos(self,videoUrl):
		urlTab = []	
		sts, data = self.cm.getPage(videoUrl)
		if sts:			
			if 'adilbo_HTML_encoder' in data:
				printDBG('ttttttttttttttttttttttttttt'+data)
				t_script = re.findall('<script.*?;.*?\'(.*?);', data, re.S)	
				t_int = re.findall('/g.....(.*?)\)', data, re.S)	
				if t_script and t_int:
					script = t_script[0].replace("'",'')
					script = script.replace("+",'')
					script = script.replace("\n",'')
					sc = script.split('.')
					page = ''
					for elm in sc:
						#printDBG('decode'+elm)
						c_elm = base64.b64decode(elm+'==')
						t_ch = re.findall('\d+', c_elm, re.S)
						if t_ch:
							nb = int(t_ch[0])+int(t_int[0])
							page = page + chr(nb)
					t_url = re.findall('file":"(.*?)"', page, re.S)	
					if t_url:	
						urlTab.append((t_url[0].replace('\\',''),'3'))
			else:
				Liste_els_3 = re.findall('<iframe.*?src="(.*?)"', data, re.S)	
				if Liste_els_3:
					urlTab.append((Liste_els_3[0],'1'))
				else:
					Liste_els_3 = re.findall('file: "(.*?)"', data, re.S)	
					if Liste_els_3:			
						meta = {'iptv_proto':'m3u8','Referer':videoUrl}
						url_=strwithmeta(Liste_els_3[0], meta)
						urlTab.append((url_,'3'))
		return urlTab
		
	def getArticle(self, cItem):
		printDBG("FaselhdCOM.getArticleContent [%s]" % cItem)
		retTab = []
		otherInfo = {}
		title = ''
		desc = ''
		icon = ''
		sts, data = self.cm.getPage(cItem['url'])
		if sts:
			url = self.cm.ph.getDataBeetwenNodes(data, ('<meta', '>', 'refresh'), ('<', '>'))[1]
			url = self.getFullUrl(self.cm.ph.getSearchGroups(url, '''url=['"]([^'^"]+?)['"]''', 1, True)[0])

			if self.cm.isValidUrl(url):
				sts, tmp = self.getPage(url)
				if sts: data = tmp

			data = self.cm.ph.getDataBeetwenNodes(data, ('<header', '>'), ('<style', '>'))[1]
			desc = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<p', '</p>')[1])
			title = self.cleanHtmlStr(self.cm.ph.getDataBeetwenMarkers(data, '<h1', '</h1>')[1])
			icon  = self.getFullIconUrl(self.cm.ph.getSearchGroups(data, '''\ssrc=['"]([^'^"]+?)['"]''')[0])

			keysMap = {'دولة المسلسل':   'country',
					   'حالة المسلسل':   'status',
					   'اللغة':          'language',
					   'توقيت الحلقات':  'duration',
					   'الموسم':         'seasons',
					   'الحلقات':        'episodes',

					   'تصنيف الفيلم':   'genres',
					   'مستوى المشاهدة': 'age_limit',
					   'سنة الإنتاج':     'year',
					   'مدة الفيلم':     'duration',
					   'تقييم IMDB':     'imdb_rating',
					   'بطولة':          'actors',
					   'جودة الفيلم':    'quality'}
			data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<i', '>', 'fa-'), ('</span', '>'))
			for item in data:
				tmp = self.cleanHtmlStr(item).split(':')
				marker = tmp[0].strip()
				value  = tmp[-1].strip().replace(' , ', ', ')
				
				printDBG(">>>>>>>>>>>>>>>>>> marker[%s] -> value[%s]" % (marker, value))
				
				#marker = self.cm.ph.getSearchGroups(item, '''(\sfa\-[^'^"]+?)['"]''')[0].split('fa-')[-1]
				#printDBG(">>>>>>>>>>>>>>>>>> " + marker)
				if marker not in keysMap: continue
				if value == '': continue
				otherInfo[keysMap[marker]] = value

		if title == '': title = cItem['title']
		if desc == '':  desc = cItem.get('desc', '')
		if icon == '':  icon = cItem.get('icon', self.DEFAULT_ICON_URL)

		return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self.getFullUrl(icon)}], 'other_info':otherInfo}]

	
	def start(self,cItem):      
		mode=cItem.get('mode', None)
		if mode=='00':
			self.showmenu0(cItem)
		if mode=='20':
			self.showmenu1(cItem)
		if mode=='30':
			self.showitms1(cItem)			
		if mode=='31':
			self.showitms2(cItem)
		if mode=='32':
			self.showitms3(cItem)
