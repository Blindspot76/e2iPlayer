# -*- coding: utf-8 -*-
###################################################
# LOCAL import 
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit   import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.components.ihost            import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools             import printDBG, printExc, GetTmpDir
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes             import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools      import tunisia_gouv,tscolor

from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper        import getDirectM3U8Playlist
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.urlparser    import urlparser as ts_urlparser
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.resolver     import URLResolver
from Plugins.Extensions.IPTVPlayer.libs.urlparser              import urlparser

###################################################
# FOREIGN import
###################################################
import re
import json
import base64
import inspect
import urllib
from Screens.MessageBox import MessageBox
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from Components.config import config, ConfigText, getConfigListEntry,ConfigYesNo,ConfigSelection
from os import remove as os_remove, path as os_path, system as os_system
from datetime import datetime
import sys
import os

###################################################
#RICH_DESC_PARAMS = ["alternate_title", "original_title", "station", "price", "age_limit", "views", "status", "type", "first_air_date", "last_air_date", "seasons", "episodes", "country", "language", "duration", "quality", "subtitles", "year", "imdb_rating", "tmdb_rating","released", "broadcast", "remaining", "rating", "rated", "genre", "genres", "category", "categories", "production", "director", "directors", "writer", "writers", "creator", "creators", "cast", "actors", "stars", "awards", "budget", "translation",]

config.plugins.iptvplayer.ts_dsn           = ConfigYesNo(default = True)
config.plugins.iptvplayer.vs_meta_view     = ConfigYesNo(default = False)
config.plugins.iptvplayer.dev_mod          = ConfigYesNo(default = False)
config.plugins.iptvplayer.tsi_resolver     = ConfigSelection(default = "tsiplayer", choices = [("tsiplayer", "TSIPlayer"),("e2iplayer", "E2Iplayer")])
config.plugins.iptvplayer.ts_resolver      = ConfigSelection(default = "tsmedia", choices = [("tsmedia", "TSMedia"), ("tsiplayer", "TSIPlayer")])
config.plugins.iptvplayer.xtream_active    = ConfigSelection(default = "Yes", choices = [("Yes", _("Yes")), ("", _("No"))])
config.plugins.iptvplayer.ts_xtream_user   = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_xtream_pass   = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_xtream_host   = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.ts_xtream_ua     = ConfigText(default = '', fixed_size = False)
config.plugins.iptvplayer.use_colors    = ConfigSelection(default = "", choices = [("", _("Auto")), ("yes", _("Yes")), ("no", _("No"))])
config.plugins.iptvplayer.imsakiya_tn      = ConfigSelection(default = '', choices = tunisia_gouv)

def GetConfigList():
	optionList = []
	optionList.append( getConfigListEntry(_("Decrypt Server Name:"), config.plugins.iptvplayer.ts_dsn) )
	#optionList.append( getConfigListEntry(_("Get Meta (VStream):"), config.plugins.iptvplayer.vs_meta_view) )
	optionList.append( getConfigListEntry(_("Display Tools:"), config.plugins.iptvplayer.dev_mod) )
	optionList.append( getConfigListEntry(_("TSIplayer Resolver:"), config.plugins.iptvplayer.tsi_resolver) )	
	optionList.append( getConfigListEntry(_("TSMedia Group Resolver:"), config.plugins.iptvplayer.ts_resolver) )	
	optionList.append( getConfigListEntry(_("Display Xtream:"), config.plugins.iptvplayer.xtream_active) )
	if config.plugins.iptvplayer.xtream_active.value =='Yes':
		optionList.append( getConfigListEntry(_("    Xtream User:"), config.plugins.iptvplayer.ts_xtream_user) )
		optionList.append( getConfigListEntry(_("    Xtream Pass:"), config.plugins.iptvplayer.ts_xtream_pass) )
		optionList.append( getConfigListEntry(_("    Xtream Host:"), config.plugins.iptvplayer.ts_xtream_host) )	
		optionList.append( getConfigListEntry(_("    Xtream User Agent:"), config.plugins.iptvplayer.ts_xtream_ua) )
	optionList.append( getConfigListEntry(_("Use colors:"), config.plugins.iptvplayer.use_colors) )			
	optionList.append( getConfigListEntry(_("Imsakiya:"), config.plugins.iptvplayer.imsakiya_tn) )			
	return optionList


def gettytul():
	return 'TS IPlayer'

class TSIPlayer(CBaseHostClass):
	#tsiplayerversion = "2019.08.17.0"  
	#tsiplayerremote  = "0.0.0.0"
	def __init__(self,item={}):
		self.startitem_=item
		CBaseHostClass.__init__(self, {'cookie':'TSIPlayer.cookie1'})
		self.USER_AGENT = self.cm.getDefaultHeader()['User-Agent']	
		self.HEADER = {'User-Agent': self.USER_AGENT, 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate', 'Referer':'', 'Origin':''}
		self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
		self.DEFAULT_ICON_URL = 'https://i.ibb.co/Q8ZRP0X/yaq9y3ab.png'
		self.import_str	=''
		if config.plugins.iptvplayer.tsi_resolver.value=='tsiplayer':
			self.ts_up = ts_urlparser()
		else:
			self.ts_up = urlparser()
					

###################################################
# MAIN CATEGORY
###################################################	
	def MainCat(self):
		self.tsiplayer_host({'cat_id':'901','ordre':0})
		self.addDir({'name':'cat','category' : 'FilmsSeriesAr','title':'Arabic Section','desc':'Arabic section','icon':'https://i.ibb.co/Fgk8Yq4/tsiplayer-films.png'} )	
		self.addDir({'name':'cat','category' : 'FilmsSeriesFr','title':'French Section','desc':'Films, Series et Animes en Vf et Vostfr','icon':'https://i.ibb.co/Fgk8Yq4/tsiplayer-films.png'} )	
		self.addDir({'name':'cat','category' : 'FilmsSeriesEn','title':'English section','desc':'Films, Series & Animes (Eng)','icon':'https://i.ibb.co/Fgk8Yq4/tsiplayer-films.png'} )	
		self.addDir({'name':'cat','category' : 'Live','title':'Live Tv & Replay','desc':'Live Tv & Replay','icon':'https://1.bp.blogspot.com/-PHYAba3vvI0/WDroJDScJdI/AAAAAAAABuY/SfwAZRpThoIF-IFAaijBZNWThAn0KXU9QCLcB/s320/Ligtvkafe%2B%25C4%25B0le%2BKumanda%2BSende.jpg'} )
		if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/tsiplayer/addons/'):
			self.addDir({'name':'cat','category' : 'Addons','title':'Addons','desc':'','icon':'https://i.ibb.co/cv2fZ8y/add-ons-icon-11.png'} )
		if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/TSmedia'):
			self.tsiplayer_host({'cat_id':'903'})
		if config.plugins.iptvplayer.dev_mod.value:
			self.addDir({'name':'cat','category' : 'Devmod','title':'Tools','desc':'','icon':'http://www.mezganisaid.com/z-include/images/code-dev.png'} )

		self.tsiplayer_host({'cat_id':'901','ordre':1})






#		self.addDir({'name':'cat','category' : 'vstream','title':'Vstream','desc':'desc','icon':''} )
#1:Ar,2:Live,3:Kids,4:Ramadan,6:Ar+In,10:dev,101:EN,102:FR,
#Live sport: 100,replay Sport: 110
#Live all: 120, replay all:130
#All:  101  
#Dev:  102
#Dev Touls :103
#Sys: update:901,emu:902,tsmedia:903,search:904
#not work: 104
#Arabic: 201:Films 202:Anim 203:kids 204:Islamic
#French: 301,302,303
#Eng:    401,402,403
#
	def FilmCatFr(self):
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Films & Series |★●-----','desc':'Films, Series & Animes en VF et VOSTFR'})	
		self.tsiplayer_host({'cat_id':'101'})	
		self.tsiplayer_host({'cat_id':'301'})
		#self.addDir({'name':'search','category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'ALLFR','icon':''})
		self.tsiplayer_host({'cat_id':'904','gnr':'fr'})		
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Animes & Dessins animés |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'302'})
		self.tsiplayer_host({'cat_id':'303'})

	def FilmCatEn(self):
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Films & Series |★●-----','desc':'Films, Series & Animes'})	
		self.tsiplayer_host({'cat_id':'101'})	
		self.tsiplayer_host({'cat_id':'401'})
		self.tsiplayer_host({'cat_id':'904','gnr':'en'})
		#self.addDir({'name':'search','category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'ALLEN','icon':''})


				
	def FilmCatAr(self):
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Films & Series |★●-----','desc':'Films, Series & Animes en VF et VOSTFR'})			
		self.tsiplayer_host({'cat_id':'101'})	
		self.tsiplayer_host({'cat_id':'201'})	
		self.tsiplayer_host({'cat_id':'904','gnr':'ar'})	
		#self.addDir({'name':'search','category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'ALLAR','icon':''})	
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Animes & Dessins animés |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'202'})
		self.tsiplayer_host({'cat_id':'203'})
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Islamic |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'204'})
						
	def IptvCat(self):
		self.tsiplayer_host({'cat_id':'100'})
		self.tsiplayer_host({'cat_id':'110'})
		self.tsiplayer_host({'cat_id':'120'})		
		
	def AddonsCat(self):
		self.tsiplayer_host({'cat_id':'902'})		
								
	def DevCat(self):
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Tools |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'103'})
		#params = {'category' : 'update_now','title':tscolor('\c0000????')+' +++++++ FORCE UPDATE & RESTART (Tar method) +++++++ ','name':'update_restart'} 
		#self.addDir(params)		
		#params = {'category' : 'update_now2','title':tscolor('\c0000????')+' +++++++ FORCE UPDATE & RESTART (Zip method) +++++++ ','name':'update_restart'} 
		#self.addDir(params)			
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Hosts en développement |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'102'})	
		self.addMarker({'category' :'marker','title':tscolor('\c00????00')+' -----●★| Hosts Out |★●-----','desc':'Dessins animés & Animes en VF et VOSTFR'})
		self.tsiplayer_host({'cat_id':'104'})	


	def PrintExTs(self,e):
		exc_type, exc_obj, exc_tb = sys.exc_info()
		fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
		inf_ = str(fname)+' ('+ str(exc_tb.tb_lineno)+')\n'+str(type(e).__name__)+' ('+str(e)+')\n'
		frm = inspect.trace()[-1]
		mod = inspect.getmodule(frm[0])
		(filename, line_number,function_name, lines, index) = inspect.getframeinfo(frm[0])			
		filename = filename.replace('/usr/lib/enigma2/python/Plugins/Extensions/','>> ')
		inf_ = inf_+'FileName: '+str(filename)+' ('+str(line_number)+')\n'
		inf_ = inf_+'Function: '+str(function_name)+'\n'
		try:
			inf_ = inf_+'Line: '+str(lines[index]).strip()
		except:
			pass
		self.addMarker({'title':tscolor('\c00????00')+'----> Erreur <----','icon':'','desc':inf_})

###################################################
# HOST tsiplayer
###################################################	
	def tsiplayer_get_host(self,cItem,type_):
		ordre = -1
		if type_ == 'private' :
			folder='/usr/lib/enigma2/python/Plugins/tsiplayer/'
			import_ = 'from Plugins.tsiplayer.'	
			color_ = tscolor('\c0000????')		
		elif type_ == 'public' :
			folder='/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/tsiplayer/'
			import_ = 'from Plugins.Extensions.IPTVPlayer.tsiplayer.'
			color_ = tscolor('\c00??????')
		elif type_ == 'addons' :
			folder='/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/tsiplayer/addons/'
			import_ = 'from Plugins.Extensions.IPTVPlayer.tsiplayer.addons.'
			ordre = cItem.get('ordre',-1)
			color_ = tscolor('\c00??????')
		elif type_ == 'system' :
			folder='/usr/lib/enigma2/python/Plugins/Extensions/IPTVPlayer/tsiplayer/modules/'
			import_ = 'from Plugins.Extensions.IPTVPlayer.tsiplayer.modules.'
			ordre = cItem.get('ordre',-1)
			color_ = tscolor('\c00??????')
			
		gnr_=cItem.get('gnr','')					
		cat_id=cItem.get('cat_id','')
		devmod=cItem.get('devmod','')

		lst=[]
		if os.path.exists(folder):
			lst=os.listdir(folder)
			lst.sort()
			for (file_) in lst:
				if (file_.endswith('.py'))and((file_.startswith('host_')) or ((file_.startswith('hide_')))):
					path_=folder+'/'+file_
					import_str=import_+file_.replace('.py',' import ')
					try:
						exec (import_str+'getinfo')
						info=getinfo()
					except Exception, e:
						info={}
						info['warning']=' >>>>>>> Problem in this host <<<<<<<'
						info['desc']=str(e)
						info['name']=file_
						info['icon']=''
						info['version']=''
						info['cat_id']='104'
						info['dev']=''
					desc=''
					icon_ = info['icon']
					param_ = 'oui'
					name_ = info['name']
					if (info.get('filtre', '')!=''):
						try:
							cmd_='param_ = config.plugins.iptvplayer.'+info.get('filtre', '')+'.value'
							exec(cmd_)
						except:
							param_ = ''
					if param_!='': 
						if cat_id==info['cat_id']:
							if cat_id=='10':
								desc=desc+tscolor('\c00????00')+' -----> !!!!!!!!! Not Working (Dev Mod) !!!!!!!!! <-----\\n'
							if info.get('warning', '')!='':
								desc=desc+tscolor('\c00????00')+' '+info.get('warning', '')+'\\n'
							desc=desc+tscolor('\c00????00')+' Info: '+tscolor('\c00??????')+info['desc']+'\\n '+tscolor('\c00????00')+'Version: '+tscolor('\c00??????')+info['version']+'\\n '+tscolor('\c00????00')+'Developpeur: '+tscolor('\c00??????')+info['dev']+'\\n'
							if info.get('update', '')!='':
								desc=desc+tscolor('\c00????00')+' Last Update: '+tscolor('\c00??????')+info.get('update', '')+'\\n'
								
							show = True	
							if ordre >-1:
								show = False
								exec (import_str+'TSIPHost as UpdateHost')
								updateHost_ = UpdateHost()								
								updateHost_.GetVersions()
								if (updateHost_.tsiplayerversion != updateHost_.tsiplayerremote) and ordre==0:
									color_ = tscolor('\c00????00')
									name_= info.get('name2','Update')
									icon_ = info.get('icon2',icon_)
									desc=color_+'TSIPLayer Version: '+tscolor('\c0000????')+updateHost_.tsiplayerversion+'\n'
									desc=color_+'TSIPLayer Remote Version: '+tscolor('\c0000????')+updateHost_.tsiplayerremote+'\n'+desc
									show = True
								elif (updateHost_.tsiplayerversion == updateHost_.tsiplayerremote) and ordre==1:
									desc=tscolor('\c00????00')+'TSIPLayer Version: '+tscolor('\c000????')+updateHost_.tsiplayerversion+'\n'									
									show = True
							if show:
								self.addDir({'category' : 'host2','title':color_+name_,'desc':desc,'icon':icon_,'mode':'00','import':import_str,'gnr':gnr_})

		
	def tsiplayer_host(self,cItem):
		self.tsiplayer_get_host(cItem,'private')
		self.tsiplayer_get_host(cItem,'public')
		self.tsiplayer_get_host(cItem,'addons')
		self.tsiplayer_get_host(cItem,'system')

						
	def host2_host(self,cItem):
		mode_=cItem.get('mode','00')
		import_str = cItem.get('import',self.import_str)
		if self.import_str!=import_str:
			'''file_=import_str.replace('from Plugins.Extensions.IPTVPlayer.tsiplayer.','').replace(' import ','')
			try:
				_url='http://86.105.212.206/tsiplayer/stat.php?host='+file_+'&cat=Main_'
				self.cm.getPage(_url)
			except:
				printDBG('erreur')'''
			exec (import_str+'TSIPHost')
			self.import_str=import_str
			self.host_ = TSIPHost()	
		self.host_.currList=[]
		self.host_.start(cItem)
		self.currList=self.host_.currList
	
###################################################
# Main
###################################################	
						
	def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
		CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
		if self.startitem_!={}:
			self.currItem=self.startitem_
			self.startitem_={}
		name     = self.currItem.get("name", '')
		category = self.currItem.get("category", '')
		printDBG( "handleService: || name[%s], category[%s] " % (name, category) )
		self.currList = []
		self.cacheLinks = {}
		if name == None:
			self.MainCat()
		elif category == 'search':
			self.listSearchResult(self.currItem,searchPattern, searchType)	
		elif category == '_next_page':
			self.listSearchResult(self.currItem,'', '')				
		elif category == 'FilmsSeriesAr':
			self.FilmCatAr()
		elif category == 'FilmsSeriesFr':
			self.FilmCatFr()
		elif category == 'FilmsSeriesEn':
			self.FilmCatEn()
		elif category == 'Live':
			self.IptvCat()
		elif category == 'Devmod':
			self.DevCat()
		elif category == 'Addons':
			self.AddonsCat()
		else:
			exec('self.'+category+'_host(self.currItem)')

		CBaseHostClass.endHandleService(self, index, refresh)
		
	def listSearchResult(self, cItem, searchPattern, searchType):		
		hst=cItem['hst']
		cat=cItem['category']
		page=cItem.get('page',1)
		if cat=='_next_page':
			str_ch = cItem['searchPattern']
		else:
			str_ch = searchPattern
		if hst=='tshost':		
			img = cItem['icon']
			self.host_.currList=[]
			self.host_.SearchResult(str_ch,page,extra=cItem['import'])
			self.currList=self.host_.currList
			if page>0:
				self.addDir({'import':cItem['import'],'category':'_next_page','title': tscolor('\c0000??00')+'Page Suivante','icon':img, 'search_item':False,'page':page+1,'searchPattern':str_ch,'hst':hst})	
		else:
			exec('self.'+hst+'_search(str_ch,page)')
			if page>0:
				self.addDir({'category':'_next_page','title': tscolor('\c0000??00')+'Page Suivante', 'search_item':False,'page':page+1,'searchPattern':str_ch,'hst':hst})	
		
	def getVideoLinks(self, videoUrl):
		printDBG("getVideoLinks [%s]" % videoUrl)
		urlTab = []
		if videoUrl.startswith('hst'):
			_data = re.findall('hst#(.*?)#(.*?)#', videoUrl+'#', re.S)	
			hst=_data[0][0]
			videoUrl=_data[0][1]
		else:
			hst='none'
		if hst=='none':
			urlTab = self.TSgetVideoLinkExt(videoUrl)
		elif hst=='host':
			import_str,videoUrl=videoUrl.split('||')
			exec (import_str+'getVideos')
			urlTab1=getVideos(videoUrl)
			for (url_,type_) in urlTab1:
				if 	type_=='1':
					urlTab = self.TSgetVideoLinkExt(url_)
				else:
					urlTab.append({'name':'Direct', 'url':url_})
		elif hst=='tshost':
			urlTab1=self.host_.getVideos(videoUrl)
			urlTab=[]
			for (url_,type_) in urlTab1:
				if 	type_=='1':
					urlTab = self.TSgetVideoLinkExt(url_)
				elif type_=='3':	
					urlTab = getDirectM3U8Playlist(url_, False, checkContent=True, sortWithMaxBitrate=999999999)
				elif type_=='0':
					urlTab.append({'name':'Direct', 'url':url_})
				elif type_=='4':
					meta =''
					try:
						meta = url_.meta
					except:
						pass
					if meta != '':
						urlTab.append({'name':url_.split('|')[0], 'url':strwithmeta(url_.split('|')[1],meta)})
					else:
						urlTab.append({'name':url_.split('|')[0], 'url':url_.split('|')[1]})
				elif type_=='5':
					name = url_.split('|')[0]
					URL  = url_.split('|')[1]
					urltabout = self.TSgetVideoLinkExt(URL)
					if urltabout !=[]:
						for elm in urltabout:
							elm['name']=name+' ['+elm['name']+']'
							urlTab.append(elm)	
				elif type_=='6':	
					vtt,lng,URL = url_.split('|',2)
					subTrack = [{'title':lng, 'url':vtt, 'lang':lng, 'format':'vtt'}]
					URL=strwithmeta(URL,{'external_sub_tracks':subTrack})					
					urlTab = getDirectM3U8Playlist(URL, False, checkContent=True, sortWithMaxBitrate=999999999)
					print			
				else:
					urlTab.append({'name':'Direct', 'url':url_})
		else:
			exec('urlTab = self.'+hst+'_videos(videoUrl)')
		return urlTab
		
	def getLinksForVideo(self, cItem):
		printDBG("TVProart.getLinksForVideo [%s]" % cItem)
		name=cItem['title']
		hst=cItem['hst']
	
		urlTab = []
		if hst=='direct':	
			urlTab.append({'name':name, 'url':cItem['url'], 'need_resolve':0})		
		elif hst=='none':
			urlTab.append({'name':name, 'url':cItem['url'], 'need_resolve':1})
		elif hst=='tshost':	
			import_str = cItem.get('import',self.import_str)
			if self.import_str!=import_str:
				exec (import_str+'TSIPHost')
				self.import_str=import_str
				self.host_ = TSIPHost()	
			urlTab0=self.host_.get_links(cItem)
			urlTab=[]
			for elm in urlTab0:
				name_ = elm.get('name','XXXX')
				type_ = elm.get('type','XXXX')
				color =''
				if type_=='local':
					color = tscolor('\c0060??60')
				elif ts_urlparser().checkHostSupportbyname(name_):
					color = tscolor('\c0090??20')
				elif ts_urlparser().checkHostNotSupportbyname(name_):
					color = tscolor('\c00??3030')						
				if '|' in name_:
					name_=name_.replace(name_.split('|')[-1],color+name_.split('|')[-1].lower().replace('www.','').title())
				else:
					name_=color+name_.lower().replace('www.','').title()					
				elm ['name']= name_					
				urlTab.append(elm)	
				
		else:
			exec('urlTab = self.'+hst+'_links(cItem[\'url\'])')		
		return urlTab
		
	def getArticleContent(self, cItem):
		printDBG("getArticleContent [%s]" % cItem) 
		retTab = []
		hst=cItem['hst']
		if hst=='direct':			
			data=cItem.get('category', '')
			if data=='host2':
				retTab=self.host_.getArticle(cItem)
		elif hst=='tshost':		
			retTab=self.host_.getArticle(cItem)			
		else:	
			exec ('retTab=self.'+hst+'_getArticleContent(cItem)')
		return retTab


		 
	def TSgetVideoLinkExt(self,videoUrl): 
		urlTab=[]
		try:
			urlTab = URLResolver(videoUrl).getLinks()
		except:
			urlTab=[]
		return urlTab
	

class IPTVHost(CHostBase): 

	def __init__(self,item={}):  
		#item['title']  = 'eeeeee'
		CHostBase.__init__(self, TSIPlayer(item=item), False, []) 
		
	def withArticleContent(self, cItem):
		if cItem.get('EPG', False): return True
		else: return False
		
