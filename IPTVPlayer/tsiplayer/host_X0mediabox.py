# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from tsiplayer.libs.tstools import TSCBaseHostClass,gethostname,tscolor
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.components.recaptcha_v2helper import CaptchaHelper
from tsiplayer.libs.packer import cPacker
###################################################

import re
import base64
import difflib

def getinfo():
	info_={}
	info_['name']='MediaBox HD'
	info_['version']='2.0 23/11/2019'
	info_['dev']='RGYSoft'
	info_['cat_id']='401'
	info_['desc']='Watch Movies & TV shows'
	info_['icon']='https://i.ibb.co/HGnvGvy/Screen-Shot-2018-10-08-at-3-39-11-PM.png'
	info_['recherche_all']='1'
	info_['update']='Add Arabic links'
	return info_
	
	
class TSIPHost(TSCBaseHostClass,CaptchaHelper):
	def __init__(self):
		TSCBaseHostClass.__init__(self,{'cookie':'mediabox.cookie'})
		self.USER_AGENT = 'Mediabox/2.4.6 (Linux;Android 7.1.1) ExoPlayerLib/2.10.1'
		self.MAIN_URL = 'https://qazwsxedcrfvtgb.info'
		self.HEADER = {'User-Agent': self.USER_AGENT,'Accept':'*/*','X-Requested-With':'XMLHttpRequest', 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Pragma':'no-cache'}
		self.defaultParams = {'timeout':9,'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.hdr_pers={'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 7.1.1; E6633 Build/32.4.A.1.54)',
		'Accept-Encoding': 'gzip',
		'Content-Type': 'application/json',
		'trakt-api-key': '86c9567d7ed44aba1f9cdeb107b309fe8fb7ebb71f2df79b353ea5ec4497e3ad',
		'trakt-api-version': '2'}

	def getPage(self, baseUrl, params={}, post_data=None):
		if params == {}: params = dict(self.defaultParams)
		params['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
		return self.cm.getPageCFProtection(baseUrl, params, post_data)

		 
	def showmenu0(self,cItem):

		self.addDir({'import':cItem['import'],'category' : 'host2','title':'MENU','desc':'','icon':cItem['icon'],'hst':'tshost','mode':'20'})	
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'Movies','url': '/movies/XXVV?genre=&sort=trending','desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
		self.addDir({'import':cItem['import'],'category' : 'host2','title':'TV Shows','url': '/shows/XXVV?genre=&sort=trending','desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
		self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c00????00')+'Filter','desc':'','icon':cItem['icon'],'hst':'tshost','mode':'21'})	
		self.addDir({'import':cItem['import'],'category':'search','name':'search','title': _('Search'), 'search_item':True,'icon':cItem['icon'],'hst':'tshost'})	

	def showmenu1(self,cItem):
		url = self.MAIN_URL+'/discovers'
		sts, data = self.getPage(url,self.defaultParams)
		if sts:
			data = json_loads(data)
			self.addMarker({'title':tscolor('\c0000??00')+'Showcases','desc':'','icon':cItem['icon']})
			data1=data['showcases']
			for elm in data1:
				titre = elm['title']
				id_   = elm['data']
				image = elm['image']
				self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url': id_,'desc':'','icon':image,'hst':'tshost','mode':'22'})	
			
			self.addMarker({'title':tscolor('\c0000??00')+'Articles','desc':'','icon':cItem['icon']})
			data1=data['articles']
			for elm in data1:
				titre = elm['title']
				id_   = elm['contents']
				if id_!=[]:
					self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url': id_,'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'23'})	


	def showfilter(self,cItem):
		count=cItem.get('count',0)
		url=cItem.get('url','')
		if count==0:
			self.addMarker({'title':tscolor('\c0000??00')+'Type:','desc':'','icon':cItem['icon']})	
			self.addDir({'import':cItem['import'],'count':1,'category' : 'host2','url': url+'/movies/XXVV','title':'Movies','desc':'Movies','icon':cItem['icon'],'hst':'tshost','mode':'21'})	
			self.addDir({'import':cItem['import'],'count':1,'category' : 'host2','url': url+'/shows/XXVV','title':'TV Shows','desc':'TV Shows','icon':cItem['icon'],'hst':'tshost','mode':'21'})	
		elif count==1:
			self.addMarker({'title':tscolor('\c0000??00')+'Genre:','desc':'','icon':cItem['icon']})	
			Genre  = ('All','action','adventure','animation','biography','comedy','crime','documentary','drama','family','fantasy','game-show','history','horror','music','musical','mystery','romance','sci-fi','short','sport','thriller','war','western')
			for elm in Genre:
				titre = elm.capitalize()
				if elm =='All': elm=''
				self.addDir({'import':cItem['import'],'count':2,'category' : 'host2','url': url+'?genre='+elm,'title':titre,'desc':cItem['desc']+' | '+titre,'icon':cItem['icon'],'hst':'tshost','mode':'21'})	
		elif count==2:
			self.addMarker({'title':tscolor('\c0000??00')+'Sort by:','desc':'','icon':cItem['icon']})					
			Sort = ('trending','seeds','rating','last%20added','year')
			for elm in Sort:
				titre = elm.replace('%20',' ')
				titre = titre.capitalize()
				self.addDir({'import':cItem['import'],'category' : 'host2','url': url+'&sort='+elm,'title':titre,'desc':cItem['desc']+' | '+titre,'icon':cItem['icon'],'hst':'tshost','mode':'30'})	




	def showitms_00(self,cItem):
		page=cItem.get('page',1)
		url=self.MAIN_URL+'/movie/'+cItem['url']+'?page='+str(page)+'&aa=596bdda60b2d41fcd95a8eb9bb1cace1'
		sts, data = self.getPage(url,self.defaultParams)
		if sts:
			data = json_loads(data)
			for elm in data['items']:
				desc  = self.get_inf(elm)
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','year':elm.get('year',''),'url': elm['imdb_id'],'title':elm['title'],'desc':desc,'icon':elm['images']['poster'],'hst':'tshost','mode':'31'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'22'} )									
			 
	def showitms_01(self,cItem):
			mode_='31'
			if cItem['title']=='Collection': mode_='22'
			for elm in cItem['url']:
				desc  = self.get_inf(elm)
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','year':elm.get('year',''),'url': elm['imdb_id'],'title':elm['title'],'desc':desc,'icon':elm['images']['poster'],'hst':'tshost','mode':mode_})	
		
	def showitms_02(self,cItem):
			mode_='31'
			sts, data = self.getPage(cItem['url'],self.defaultParams)
			if sts:
				data = json_loads(data)
				id_ = data.get('imdb_id','')
				if id_:
					if id_!='':
						url_=''
						mmdl = "E6633"
						url = 'https://api.trakt.tv/people/'+id_+'/movies?extended=full'
						sts, data = self.getPage(url,{'header':self.hdr_pers})
						if sts:
							data = json_loads(data)
							for elm in data.get('cast',[]):
								printDBG('dddddddddddddddddd11'+str(elm))
								elm1 = elm.get('movie',[])
								printDBG('dddddddddddddddddd'+str(elm1))
								id_mo_ = elm1['ids']['imdb']
								if id_mo_:
									url_=url_+id_mo_+','
						if url_!='':
							url = self.MAIN_URL+'/imdbs/'+url_
							sts, data = self.getPage(url,self.defaultParams)
							if sts:
								data = json_loads(data)
								for elm in data:
									desc  = self.get_inf(elm)
									self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','year':elm.get('year',''),'url': elm['imdb_id'],'title':elm['title'],'desc':desc,'icon':elm['images']['poster'],'hst':'tshost','mode':'31'})	
			
	def showitms_03(self,cItem):
		url='https://api.trakt.tv/movies/'+cItem['url'].replace('S00E000','')+'/people'
		url_=''
		sts, data = self.getPage(url,{'header':self.hdr_pers})
		if sts:
			try:
				data = json_loads(data)
			except:
				data = {}
			i=0
			for elm in data.get('cast',[]):
				#printDBG('dddddddddddddddddd11'+str(elm))
				elm1 = elm.get('person',[])
				#printDBG('dddddddddddddddddd'+str(elm1))
				id_mo_ = elm1['ids']['tmdb']
				name_ = elm1['name']
				url_ = 'https://api.themoviedb.org/3/person/'+str(id_mo_)+'/external_ids?api_key=9753f7b3b6bac2a279f9e7daf419d124'
				img_=''
				if i<15:
					url_image = 'https://api.themoviedb.org/3/person/'+str(id_mo_)+'/images?api_key=739eed14bc18a1d6f5dacd1ce6c2b29e'
					sts1, data1 = self.getPage(url_image,self.defaultParams)
					if sts1:
						data1 = json_loads(data1)
						i=i+1
						for elm in data1.get('profiles',[]):
							img_=elm.get('file_path','')
							if img_!='': break
						if img_!='': img_='http://image.tmdb.org/t/p/w200/'+img_
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','url': url_,'title':name_,'desc':'','icon':img_,'hst':'tshost','mode':'24'})	
		
		
	def get_inf(self,elm):
		desc      =  ''
		qual      =  elm.get('quality','')
		genre     =  elm.get('genres',[])
		year      =  elm.get('year','')
		cert      =  elm.get('certification','N/A')
		imdb      =  elm.get('rating',{}).get('percentage',0)
		runtime   =  elm.get('runtime','')
		country   =  elm.get('country','null')
		synopsis  =  elm.get('synopsis','')
		if qual     !=''  : desc=desc+tscolor('\c0000??00')+'Qual: '+tscolor('\c00??????') +qual+' | '
		if year     !=''  : desc=desc+tscolor('\c0000??00')+'Year: '+tscolor('\c00??????')      +year+' | '
		if imdb     !=0   : desc=desc+tscolor('\c0000??00')+'Rating: '+tscolor('\c00??????')    +str(imdb)+'% | '
		if runtime  !=''  : desc=desc+tscolor('\c0000??00')+'Runtime: '+tscolor('\c00??????')   +runtime+'mn | '
		if (cert!='N/A') and (cert!='NOT RATED'): desc=desc+tscolor('\c0000??00')+'Cert: \c00??????' +cert+' | '
		if country!='null': desc=desc+tscolor('\c0000??00')+'Country: '+tscolor('\c00??????')   +country+' | '
		if genre    !=[]  : desc=desc+'\n'+tscolor('\c0000??00')+'Genres: '+tscolor('\c00??????')+ str(genre).replace('[','').replace(']','').replace('\'','')		
		if synopsis !=''  : desc=desc+'\n'+tscolor('\c0000??00')+'Synopsis: '+tscolor('\c00??????')+synopsis
		return desc


	def showitms(self,cItem):
		url1=cItem['url']
		page=cItem.get('page',1)
		url1=url1.replace('XXVV',str(page))
		url= self.MAIN_URL+url1
		sts, data = self.getPage(url,self.defaultParams)
		if sts:
			data = json_loads(data)
			for elm in data:
				desc  = self.get_inf(elm)
				trailer      =  elm.get('trailer','')
				img_ = elm.get('images',{}).get('poster',cItem['icon'])
				self.addDir({'import':cItem['import'],'good_for_fav':True,'EPG':True,'category' : 'host2','year':elm.get('year',''),'url': elm['imdb_id'],'trailer':trailer,'title':elm['title'],'desc':desc,'icon':img_,'hst':'tshost','mode':'31'})	
			self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

	def showelms(self,cItem):
		urlo=cItem['url']
		img_=cItem['icon']
		trailer =  cItem.get('trailer','')
		if trailer!='':
			self.addVideo({'import':cItem['import'],'category' : 'host2','url': trailer,'title':'Watch Trailer','desc':cItem['desc'],'icon':img_,'hst':'none'} )				
		URL=self.MAIN_URL+'/movie/'+urlo
		tab_elm =[]		
		sts, data = self.getPage(URL,self.defaultParams)
		if sts:
			data = json_loads(data)
			data_episodes = data.get('episodes',[])
			for elm in data_episodes:
				printDBG('eeeeeeeeeeeeeee'+str(elm))
				titre = elm.get('title','')
				if titre=='Episode 0':
					titre = cItem['title']
					elm['title']=cItem['title']
				imdb_id = elm.get('tvdb_id','')
				ep = elm.get('episode',0)
				se = elm.get('season',0)
				order = elm.get('order','00000')
				if se+ep > 0:
					titre = '>> '+cItem['title']+' S'+str(se).zfill(2)+'E'+str(ep).zfill(2)+' - '+tscolor('\c0000????')+titre
				else:
					titre = '>> '+titre
				img = elm.get('images',{}).get('fanart',cItem['icon'])
				img = img.replace('https:/img','https://img')
				tab_elm.append((order,titre,img,elm)) 
				tab_elm = sorted(tab_elm, key=lambda x: x[0], reverse=False)
		self.addDir({'import':cItem['import'],'good_for_fav':True,'elm':elm,'category' : 'host2','year':cItem.get('year',''),'url': '','title':titre+' [Arabic]','desc':cItem['desc'],'icon':img,'hst':'tshost','mode':'40','lng':'ar'} )
		for (order,titre,img,elm) in tab_elm:
			self.addDir({'import':cItem['import'],'good_for_fav':True,'elm':elm,'category' : 'host2','year':cItem.get('year',''),'url': '','title':titre,'desc':cItem['desc'],'icon':img,'hst':'tshost','mode':'40'} )

		if 'tt' in imdb_id:
			self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': imdb_id,'title':'CAST','desc':cItem['desc'],'icon':img,'hst':'tshost','mode':'25'} )


	def showhosts(self,cItem):
		urlTab = []
		lng=cItem.get('lng','eng')
		elm=cItem['elm']
		if lng=='eng':
			printDBG('start showhosts'+str(elm))
			streams=elm.get('streams',[])
			if streams==[]:
				streams=elm.get('tvdb_id','')	
				URL=self.MAIN_URL+'/episode/'+streams
				sts, data = self.getPage(URL,self.defaultParams)
				if sts:
					data = json_loads(data)
					streams = data.get('streams',[])
				
			Image = cItem['icon']
			stream_lst=[]
			titre_ = cItem['title'].replace('>> ','')
			
			if ' - '+tscolor('\c0000????') in titre_:
				titre_=titre_.split(' - '+tscolor('\c0000????'))[0]
			for elm1 in streams:
				stream = elm1['stream']
				name   = elm1.get('source','!!')
				type_  = elm1.get('type',0)
				if (stream not in stream_lst):
					stream_lst.append(stream)
					if type_ in [98,99]:
						Name  = 'VIP ['+name.replace('VIP','').strip()+']'
						Url   = stream
						Type_ = 'VIP'
						Desc  = 'Direct Links'
						Image = 'https://i.ibb.co/L6vctvL/VIP-1024x672.png'
					elif type_ in [39]:
						Name  = 'Vidcloud [Multi]'
						Url   = stream
						Type_ = 'Vidcloud'
						Desc  = 'Multi Hosts'
						Image = 'https://vidcloud.icu/img/logo_vid.png?1'
					elif type_ in [27,28,29,30,31]:
						Name  = 'Youtube'
						Url   = stream
						Type_ = 'Resolve'
						Desc  = 'Youtube'
					elif type_ in [77]:
						Name  = '123Movies [Multi]'
						Url   = stream
						Type_ = '123Movies'
						Desc  = 'Multi Hosts'					
						Image = 'https://i.ibb.co/kQGDxLc/x123.png'
					elif type_ in [20]:
						Name  = 'Vidlink [Multi]'
						Url   = stream
						Type_ = 'Vidlink'
						Desc  = 'Multi Hosts\nM3u8 server\nWith subs'					
						Image = 'https://i.ibb.co/bJwn22Q/vidlink.png'
					elif type_ in [71]:
						Name  = 'Seehd.pl [Multi]'
						Url   = stream
						Type_ = 'Seehd'
						Desc  = 'Multi Hosts'					
						Image = 'https://i.ibb.co/mJymy06/seehd.png'					
					elif type_ in [73]:
						Name  = 'Chillax [Multi]'
						Url   = stream
						Type_ = 'Chillax'
						Desc  = '---- >  '+tscolor('\c00????00')+'Work only in eplayer3 '+tscolor('\c0000??00')+'WITH BUFFERING '+tscolor('\c00??????')+'<----'
						Desc  = Desc + '\n'+tscolor('\c00??????')+'Good M3u8 Server\nMust wait for cloudflare bypass'					
						Image = 'https://i.ibb.co/r2kKX5s/chillax.png'					
					elif type_ in [61,62,63]:
						Name  = 'Gomostream [Multi]'
						Url   = stream
						Type_ = 'Gomostream'
						Desc  = 'Multi Hosts'
						Image = 'https://i.ibb.co/TH2kJm6/putstream.png'	
					elif type_ in [11]:
						Name  = 'DB-Media [Multi]'
						Url   = stream
						Type_ = 'DB-Media'
						Desc  = 'Multi Hosts, Need To Resolve captcha'
						Image = 'https://i.ibb.co/6tTVtx5/Logo-d-B-Media.png'	
					elif type_ in [2,4,9,6]:
						printDBG('eeeeeeeeeeeeeee'+str(elm1))
						Name  = gethostname(stream).capitalize()
						Url   = stream					
						Type_ = 'Resolve'
						Desc  = stream	
					elif type_ in [53,15,64]:				
						Type_ = 'Non'						
					else:
						printDBG('eeeeeeeeeeeeeee'+str(elm1))
						Name  = '|'+str(type_)+'| '+name
						Url   = stream
						Type_ = 'Non'#'na'
						Desc  = stream
					if 	Type_ != 'Non':				
						self.addVideo({'import':cItem['import'],'category' : 'host2','url': Url,'title':titre_,'desc':tscolor('\c00????00')+Name+tscolor('\c00??????')+'\n'+Desc,'icon':Image,'hst':'tshost','Type_':Type_} )
		elif lng=='ar':
			hsts = ['host_egybest','host_faselhd','host_akoam','host_movs4u']
			for hst in hsts:
				Extra= 'from tsiplayer.'+hst+' import '
				exec (Extra+'TSIPHost')
				host = TSIPHost()				
				printDBG('elm='+str(elm))
				printDBG('citem='+str(cItem))
				str_ch = elm.get('title','')
				urlTab = host.MediaBoxResult(str_ch,cItem.get('year',''),Extra)				
				printDBG('result='+str(urlTab))
				if len(urlTab)>0:
					elm_1 = urlTab[0]
					ratio = difflib.SequenceMatcher(None,elm_1['titre'], str_ch).ratio()
					elm_1['title'] = elm_1['title']+' ('+str(ratio)+')'
					if elm_1.get('category','')=='video':
						self.addVideo(elm_1)
					else: self.addDir(elm_1)
			
					
	def get_links(self,cItem):
		urlTab = []
		Type_ = cItem.get('Type_', 'na')
		Url   = cItem.get('url',   '')
		Name  = cItem.get('title',   '')
		printDBG('Get Links: '+str(cItem))
		if Type_ == 'VIP':
			urlTab = self.Get_VIP_Servers(Url)
		elif Type_ == 'DB-Media':			
			urlTab = self.Get_DBMedia_Servers(Url)
		elif Type_ == 'Gomostream':	
			urlTab = self.Get_Gomostream_Servers(Url)			
		elif Type_ == 'Resolve':	
			urlTab.append({'name':Name, 'url':Url, 'need_resolve':1})			
		elif Type_ == '123Movies':
			from tsiplayer.host_X123movies import TSIPHost
			host = TSIPHost()				
			urlTab.extend(host.get_links({'url': Url}))	
		elif Type_ == 'Vidcloud':
			from tsiplayer.host_vidcloud import TSIPHost
			host = TSIPHost()				
			urlTab.extend(host.get_links({'url': Url}))	
		elif Type_ == 'Vidlink':
			from tsiplayer.host_vidlink import TSIPHost
			host = TSIPHost()				
			urlTab.extend(host.get_links({'url': Url}))	
		elif Type_ == 'Seehd':
			from tsiplayer.host_seehdpl import TSIPHost
			host = TSIPHost()				
			urlTab.extend(host.get_links({'url': Url}))

		elif Type_ == 'Chillax':
			from tsiplayer.host_chillax import TSIPHost
			host = TSIPHost()
			urlTab.extend(host.get_links({'url': Url}))									
		return urlTab
		
		
	def getVideos(self,videoUrl):
		urlTab = []
		videoUrl0,gnr = videoUrl.split('|',1)
		if 'XX123' in gnr:	
			from tsiplayer.host_X123movies import TSIPHost
			host = TSIPHost()
			urlTab = host.getVideos(videoUrl)
		if 'XXVID' in gnr:	
			from tsiplayer.host_vidlink import TSIPHost
			host = TSIPHost()
			urlTab = host.getVideos(videoUrl)
		if 'XXCHI' in gnr:	
			from tsiplayer.host_chillax import TSIPHost
			host = TSIPHost()
			urlTab = host.getVideos(videoUrl)
		if 'XXSEE' in gnr:	
			from tsiplayer.host_seehdpl import TSIPHost
			host = TSIPHost()
			urlTab = host.getVideos(videoUrl)
		if 'XXVIC' in gnr:	
			from tsiplayer.host_vidcloud import TSIPHost
			host = TSIPHost()
			urlTab = host.getVideos(videoUrl)
		if 'XXGOM' in gnr:			
			sts, data = self.getPage(videoUrl0)
			if sts:	
				pack_data = re.findall('text/javascript\'>(.*?)</script>', data, re.S)
				if pack_data:
					data = cPacker().unpack(pack_data[0].strip())
					link_data = re.findall('sources:.*?\[(.*?)\]', data, re.S)
					if link_data:
						printDBG('datakkkkkkkkkkkkkkkkkkk'+	link_data[0])
						link_data = re.findall('{file:"(.*?)"(.*?)}', link_data[0], re.S)
						for (url,label) in link_data:
							if 'm3u8' in url: label='HLS'
							label=label.replace(',label:"','').replace('"','')					
							if 'm3u8' in url:
								urlTab.append((url,'3')) 
							else:
								if not 'manifest.mpd' in url:
									urlTab.append((label+'|'+url,'4'))
						
		elif gnr=='DB-Media':			
			sts, data = self.getPage(videoUrl0)
			printDBG('datakkkkkkkkkkkkkkkkkkk'+	data)	
			if 'data-sitekey' in data:
				getParams = {}
				sitekey = self.cm.ph.getSearchGroups(data, '''data\-sitekey=['"]([^'^"]+?)['"]''')[0]
				if sitekey != '':
					token, errorMsgTab = self.processCaptcha(sitekey, self.cm.meta['url'])
					if token != '':
						getParams['gresponse'] = token

			post_data = {'g-recaptcha-response':token,'hivecaptcha':'1'}
			params = dict(self.defaultParams)
			params['no_redirection'] = True
			sts, data = self.getPage(videoUrl0,params,post_data=post_data)
			if sts:
				URL = self.cm.meta.get('location', 'non')
				if URL!= 'non':
					sts, data = self.getPage(URL)
					if sts:
						params['header']['Referer'] = URL
						sts, data = self.getPage('https://oload.party/watch',params)
						if sts:
							lst_data = re.findall('span.class="source.*?data-id="(.*?)">(.*?)<', data, re.S)
							for (id_,name) in lst_data:
								if name=='verystream':    url_='https://verystream.com/e/'+id_
								elif name=='gounlimited': url_='https://gounlimited.to/embed-'+id_+'.html'
								elif name=='openload':    url_='https://oload.site/embed/'+id_ 									 
								elif name=='vidcloud':    url_='https://vidcloud.icu/load.php?id='+id_ 									 
								elif name=='vidlox':      url_='https://vidlox.me/embed-'+id_+'.html'									 
								elif name=='flix555':     url_='https://flix555.com/embed-'+id_+'.html'								 
								elif name=='onlystream':  url_='https://onlystream.tv/e/'+id_ 
								elif name=='clipwatching':url_='https://clipwatching.com/embed-'+id_+'.html'
								urlTab.append((name+'|'+url_,'5')) 
					
		return urlTab		

	def SearchResult(self,str_ch,page,extra):
		self.addMarker({'title':tscolor('\c0000????')+'Movies & TV:','icon':''})
		url = self.MAIN_URL+'/movies/'+str(page)+'?keywords='+str_ch+'&filter=media'
		sts, data = self.getPage(url,self.defaultParams)
		if sts:
			data = json_loads(data)		
			for elm in data:
				desc  = self.get_inf(elm)
				trailer      =  elm.get('trailer','')
				type_      =  elm.get('type',1)
				imdb_id_      =  elm.get('imdb_id','')
				titre = elm['title']
				if type_==6:
					mode_='22'
				else: mode_='31'
				if type_==2:   titre = elm['title']+' '+tscolor('\c0000????')+'(TV SHOWS)'
				elif type_==5: titre = elm['title']+' '+tscolor('\c0000????')+'(Music Charts)'
				elif type_==3: titre = elm['title']+' '+tscolor('\c0000????')+'(Anime)'
				elif type_==1: titre = elm['title']+' '+tscolor('\c0000????')+'(Film)'				
				elif type_==6: titre = elm['title']+' '+tscolor('\c0000????')+'(Collection)'	
				
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','trailer':trailer,'year':elm.get('year',''),'url': elm['imdb_id'],'title':titre,'desc':desc,'icon':elm['images']['poster'],'hst':'tshost','mode':mode_})	
	
		self.addMarker({'title':tscolor('\c0000????')+'Persons:','icon':''})
		url = 'https://api.themoviedb.org/3/search/person?page='+str(page)+'&api_key=9753f7b3b6bac2a279f9e7daf419d124&query='+str_ch

		sts, data = self.getPage(url,self.defaultParams)
		if sts:
			data = json_loads(data)		
			for elm in data['results']:
				#desc  = self.get_inf(elm)
				name_ = elm['name']
				id_   = elm['id']
				image = elm.get('profile_path','')
				url_  = 'https://api.themoviedb.org/3/person/'+str(id_)+'/external_ids?api_key=9753f7b3b6bac2a279f9e7daf419d124'			
				printDBG('eeee'+name_)
				if not image: image=''
				if image!='': image='http://image.tmdb.org/t/p/w200'+image
				
				self.addDir({'import':extra,'good_for_fav':True,'EPG':True,'category' : 'host2','url': url_,'title':name_,'desc':'','icon':image,'hst':'tshost','mode':'24'})	
	
		
	
	
		
		
	def get_token(self, fn_data,tc):	
		x0,x1,x2,x3='','','',''
		for x in fn_data:
			x0,x1,x2,x3=x[0],x[1],x[2],x[3]
		_token1 = tc[int(x0):int(x1)]
		_token1 = ''.join(reversed(_token1))
		_token1 = ''.join((_token1,x2,x3))
		return _token1	
			
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
		if mode=='22':
			self.showitms_00(cItem)
		if mode=='23':
			self.showitms_01(cItem)
		if mode=='24':
			self.showitms_02(cItem)
		if mode=='25':
			self.showitms_03(cItem)
		if mode=='30':
			self.showitms(cItem)			
		if mode=='31':
			self.showelms(cItem)
		if mode=='40':
			self.showhosts(cItem)
			



	def Get_DBMedia_Servers(self,Url):
		urlTab = []
		sts, data = self.getPage(Url)
		if 'data-sitekey' in data:
			getParams = {}
			sitekey = self.cm.ph.getSearchGroups(data, '''data\-sitekey=['"]([^'^"]+?)['"]''')[0]
			if sitekey != '':
				token, errorMsgTab = self.processCaptcha(sitekey, self.cm.meta['url'])
				if token != '':
					getParams['gresponse'] = token
		post_data = {'g-recaptcha-response':token,'hivecaptcha':'1'}
		params = dict(self.defaultParams)
		params['no_redirection'] = True
		sts, data = self.getPage(Url,params,post_data=post_data)
		if sts:
			URL = self.cm.meta.get('location', 'non')
			if URL!= 'non':
				sts, data = self.getPage(URL)
				if sts:
					params['header']['Referer'] = URL
					printDBG('ddddddaaaaattttta'+data)
					sts, data = self.getPage('https://oload.party/watch',params)
					if sts:
						printDBG(data)
						lst_data = re.findall('span.class="source.*?data-id="(.*?)">(.*?)<', data, re.S)
						for (id_,name) in lst_data:
							if name=='verystream':    url_='https://verystream.com/e/'+id_
							elif name=='gounlimited': url_='https://gounlimited.to/embed-'+id_+'.html'
							elif name=='openload':    url_='https://oload.site/embed/'+id_ 									 
							elif name=='vidcloud':    url_='https://vidcloud.icu/load.php?id='+id_ 									 
							elif name=='vidlox':      url_='https://vidlox.me/embed-'+id_+'.html'									 
							elif name=='flix555':     url_='https://flix555.com/embed-'+id_+'.html'								 
							elif name=='onlystream':  url_='https://onlystream.tv/e/'+id_ 
							elif name=='clipwatching':url_='https://clipwatching.com/embed-'+id_+'.html'
							elif name=='streamango':  url_='https://streamango.com/embed/'+id_ 
							elif name=='mixdrop':     url_='https://mixdrop.co/e/'+id_ 
							elif (name=='xstream'):   url_='https://streamhoe.online/v/'+id_
							elif (name=='streamhoe'): url_='https://streamhoe.online/v/'+base64.b64decode(id_)

							
							else:
								name = '* '+name
								url_= id_
							urlTab.append({'name':name.capitalize(), 'url':url_, 'need_resolve':1})	
		return urlTab

	def Get_Gomostream_Servers(self,Url):
		urlTab = []
		sts, data = self.getPage(Url,self.defaultParams)
		if sts:
			tc_data     = re.findall('var tc.*?[\'"](.*?)[\'"]', data, re.S)
			_token_data = re.findall('_token".*?"(.*?)"', data, re.S)
			fn_data    = re.findall('function _tsd_tsd_ds\(s\) \{.+?slice\((.+?),(.+?)\).+?return _.+? \+ "(.+?)"\+"(.+?)";', data, re.S)
			if (tc_data and _token_data and fn_data):
				tc       = tc_data[0]
				_token   = _token_data[0]
				_token1  = self.get_token(fn_data,tc)
				printDBG('token = '+_token1)

				POST_HEADER={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0',
						'X-Requested-With':'XMLHttpRequest','x-token': _token1,'Referer':Url}
					
				post_data = {'tokenCode':tc,'_token':_token}
				sts, data = self.getPage('https://gomostream.com/decoding_v3.php',{'header':POST_HEADER},post_data)
				if sts:
					srv_data = re.findall('"(.*?)"', data.replace('\\',''), re.S)
					for srv in srv_data:
						if srv!='':
							if 'gomostream.com' not in srv:
								urlTab.append({'name':gethostname(srv).capitalize(), 'url':srv, 'need_resolve':1})
							else:
								urlTab.append({'name':'Viduplayer (Gomostream)', 'url':'hst#tshost#'+srv+'|XXGOM', 'need_resolve':1})
		return urlTab


	def Get_VIP_Servers(self,Url):
		urlTab = []
		URL='http://lb.mbplayer.info/getM3u8Link?driveId='+Url
		sts, data = self.getPage(URL,self.defaultParams)
		if sts:
			if 'No link' not in data:
				urlTab.append({'name':'VIP', 'url':data, 'need_resolve':0})
		return urlTab
				
				
				
