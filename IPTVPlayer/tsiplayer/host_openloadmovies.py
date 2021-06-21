# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,gethostname
import re
from Plugins.Extensions.IPTVPlayer.libs import ph
###################################################
def getinfo():
    info_={}
    info_['name']='OpenloadMovies'
    info_['version']='1.0 03/03/2021'
    info_['dev']='RGYSoft'
    info_['cat_id']='99'
    info_['desc']='Watch Movies & TV shows'
    info_['icon']='https://openloadmovies.ch/file/logo.png'
    info_['recherche_all']='1'
    return info_
      
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'momomesh.cookie'})
        self.MAIN_URL = 'https://openloadmovies.ch'

    def showmenu0(self,cItem):
        hst='host2'
        img_=cItem['icon']								
        Cat_TAB = [
                    {'category':hst,'title': 'Latest Movies',     'url': self.MAIN_URL+'/movies/',      'mode':'30'},
                    {'category':hst,'title': 'Latest Series',     'url': self.MAIN_URL+'/tvshows/',     'mode':'30'},
                    {'category':hst,'title': 'Kids & Family',     'url': self.MAIN_URL+'/genre/family/','mode':'30'},
                    {'category':hst,'title': 'Trending',          'url': self.MAIN_URL+'/trending-2/',  'mode':'30'},					
                    {'category':hst,'title': tscolor('\c0000????')+'Genre | Year',                   'mode':'20'},																	
                    {'category':'search','name':'search','title': _('Search'), 'search_item':True,'hst':'tshost'},
                    ]
        self.listsTab(Cat_TAB, {'import':cItem['import'],'icon':img_,'desc':''})	

    def showmenu1(self,cItem):
        sts, data = self.getPage(self.MAIN_URL)
        if sts:
            films_list = re.findall('<ul class=(.*?)</ul', data, re.S)		
            if films_list:
                if len(films_list)>1:
                    #self.addMarker({'title':tscolor('\c0000??00')+'Glossary:','desc':'','icon':cItem['icon']})
                    #films_list1 = re.findall('<li>.*?data-glossary="(.*?)".*?>(.*?)<', films_list[0], re.S)
                    #for (titre,url) in films_list1:
                    #    self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre.strip(),'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})		
                    self.addMarker({'title':tscolor('\c0000??00')+'Genre:','desc':'','icon':cItem['icon']})		
                    films_list1 = re.findall('<li.*?href="(.*?)".*?>(.*?)<', films_list[1], re.S)
                    for (url,titre) in films_list1:
                        self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre.strip(),'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	
                    self.addMarker({'title':tscolor('\c0000??00')+'Release:','desc':'','icon':cItem['icon']})		
                    films_list1 = re.findall('<li.*?href="(.*?)".*?>(.*?)<', films_list[-1], re.S)
                    for (url,titre) in films_list1:
                        self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre.strip(),'desc':'','icon':cItem['icon'],'hst':'tshost','mode':'30'})	

    def showitms(self,cItem):
        desc = [('Rating','class="rating">(.*?)</div>','',''),('Info','class="featu">(.*?)</div>','',''),('Year','</h3>(.*?)</div>','','')]
        if '?' in cItem['url']:
            next = ['class=\'arrow_pag\'.*?href="(.*?)"','30']
        else:
            next = ['rel="next.*?href="(.*?)"','30']
        self.add_menu(cItem,'','class="item .*?src="(http.*?)"(.*?)<h3>.*?href="(.*?)".*?>(.*?)<(.*?)</article>','','31',ord=[2,3,0,1,4],Desc=desc,Next=next)		

    def showelms(self,cItem):
        desc = [('Date','date\'>(.*?)</span>','','')]
        self.add_menu(cItem,'','class=\'numerando\'>(.*?)<.*?href=\'(.*?)\'.*?>(.*?)<(.*?)img src=\'(.*?)\'','','video',ord=[1,0,4,2,3],Desc=desc)		


    def SearchResult(self,str_ch,page,extra):
        url = self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
        desc = [('Type','<span class="(tvshows|movies)"','',''),('Rating','class="rating">(.*?)</span>','',''),('Year','class="year">(.*?)</span>','',''),
                ('Story','contenido">(.*?)</div>','\n','')]
        self.add_menu({'import':extra,'url':url},'','result-item">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)"(.*?)</article>','','31',ord=[0,2,1,3],Desc=desc)


    def get_links(self,cItem):
        URL=cItem['url']
        urlTab = []
        sts, data = self.getPage(URL)
        if sts:
            Tab_els = re.findall('<iframe.*?src="(.*?)"', data, re.S)
            for elm in Tab_els:
                printDBG('link------------->'+elm)
                if 'www.2embed' in elm:
                    urls = self.get_2embed(elm)
                    for url in urls:
                        urlTab.append({'name':'|2Embed| '+gethostname(url), 'url':url, 'need_resolve':1})
                elif 'database.gdriveplayer' in elm:
                    urls = self.get_gdriveplayer(elm)
                    for url in urls:
                        urlTab.append({'name':'|GdrivePlayer| '+gethostname(url), 'url':url, 'need_resolve':1})
                else:
                    urlTab.append({'name':gethostname(elm), 'url':elm, 'need_resolve':1})
        return urlTab

    def get_2embed(self,URL):
        main_url = 'https://www.2embed.ru'
        urlTab = []
        sts, data = self.getPage(URL)
        if sts:
            Tab_els = re.findall('item-server.*?data-id="(.*?)".*?>(.*?)<', data, re.S)
            for (id,name) in Tab_els:
                url = main_url+'/ajax/embed/play?id='+id+'&_token='
                sts, data = self.getPage(url)
                if sts: 
                    Tab_els = re.findall('"link":"(.*?)"', data, re.S)
                    urlTab.append(Tab_els[0])                    
        return urlTab

    def get_gdriveplayer(self,URL):
        #main_url = 'https://www.2embed.ru'
        urlTab = []
        sts, data = self.getPage(URL,self.defaultParams)
        if sts:
            printDBG('0001')
            serv_string  = re.findall('Main Server.*?href="(.*?)"', data, re.S)
            if serv_string: 
                printDBG('0002')
                link_ = serv_string[0]
                if link_.startswith('//'): link_= 'http:'+link_
                sts1, data1 = self.getPage(link_,self.defaultParams)
                if sts1:
                    printDBG('0003')
                    serv_string  = re.findall('class="linkserver".*?data-video="(.*?)"', data1, re.S)
                    for elm in serv_string:
                        printDBG('0004')
                        if elm.startswith('//'): elm = 'http:'+elm
                        urlTab.append(elm)                  
        return urlTab


    def getVideos(self,videoUrl):
        urlTab = []	
        videoUrl,x1=videoUrl.split('|')
        return ''
           
    def start(self,cItem):      
        mode=cItem.get('mode', None)
        if mode=='00':
            self.showmenu0(cItem)
        if mode=='20':
            self.showmenu1(cItem)
        if mode=='30':
            self.showitms(cItem)			
        if mode=='31':
            self.showelms(cItem)
            