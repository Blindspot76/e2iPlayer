# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost
try:
    from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
    from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
except:
    pass 
import urllib
import re,os
import time,cookielib
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta

def getinfo():
    info_={}
    name = 'Cima4u.Tv'
    hst = tshost(name)	
    if hst=='': hst = 'http://w1.cima4u.io'
    info_['host']= hst
    info_['name']=name
    info_['version']='1.1.01 05/07/2020' 
    info_['dev']='RGYSoft'
    info_['cat_id']='21'
    info_['desc']='أفلام, مسلسلات و انمي عربية و اجنبية'
    info_['icon']='https://i.ibb.co/4FCCKvf/cima4u.png'
    info_['recherche_all']='1'
    #info_['update']='change to w.cima4u.tv'
    return info_
    
    
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'cima4u2.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0'
        self.MAIN_URL   =  getinfo()['host']
        self.MAIN_URL2  = 'http://live.cima4u.io'
        self.SiteName   = 'Cima4u'
        self.HEADER     = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.defaultParams = {'header':self.HEADER, 'with_metadata':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        #self.getPage = self.cm.getPage
            
    def getPage(self, baseUrl, addParams = {}, post_data = None):
        baseUrl=self.std_url(baseUrl)
        if addParams == {}: addParams = dict(self.defaultParams)
        addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)			

    def getPage1(self,baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams) 
        sts, data = self.cm.getPage(baseUrl,addParams,post_data)
        if not data: data=strwithmeta('',{})
        printDBG('ddddaaattttaaaa'+str(data.meta))
        #printDBG('ddddaaattttaaaa'+data)
        if ('!![]+!![]' in data) or (data.meta.get('status_code',0)==503):
            try:
                if os.path.exists(self.COOKIE_FILE):
                    os.remove(self.COOKIE_FILE)
                    printDBG('cookie removed')
                printDBG('Start CLoudflare  Vstream methode')
                oRequestHandler = cRequestHandler(baseUrl)
                if post_data:
                    post_data_vstream = ''
                    for key in post_data:
                        if post_data_vstream=='':
                            post_data_vstream=key+'='+post_data[key]
                        else:
                            post_data_vstream=post_data_vstream+'&'+key+'='+post_data[key]					
                    oRequestHandler.setRequestType(cRequestHandler.REQUEST_TYPE_POST)
                    oRequestHandler.addParametersLine(post_data_vstream)					
                data = oRequestHandler.request()
                sts = True
                printDBG('cook_vstream_file='+self.up.getDomain(baseUrl).replace('.','_'))
                cook = GestionCookie().Readcookie(self.up.getDomain(baseUrl).replace('.','_'))
                printDBG('cook_vstream='+cook)
                #printDBG('cook_vstream='+data)
                if ';' in cook: cook_tab = cook.split(';')
                else: cook_tab = cook
                cj = self.cm.getCookie(self.COOKIE_FILE)
                for item in cook_tab:
                    if '=' in item:	
                        printDBG('item='+item)		
                        cookieKey, cookieValue = item.split('=')
                        cookieItem = cookielib.Cookie(version=0, name=cookieKey, value=cookieValue, port=None, port_specified=False, domain='.'+self.cm.getBaseUrl(baseUrl, True), domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=time.time()+3600*48, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
                        cj.set_cookie(cookieItem)
                cj.save(self.COOKIE_FILE, ignore_discard = True)
            except Exception, e:
                printDBG('ERREUR:'+str(e))
                printDBG('Start CLoudflare  E2iplayer methode')
                addParams['cloudflare_params'] = {'domain':self.up.getDomain(baseUrl), 'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
                sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)	
        return sts, data	

         
    def showmenu0(self,cItem):
        hst='host2'
        img_=cItem['icon']
        Cima4u_TAB = [
                    {'category':hst,'title': 'أفلام', 'mode':'20','sub-mode':0},
                    {'category':hst,'title': 'مسلسلات','mode':'20','sub-mode':1},
                    {'category':hst,'title': 'مصارعة حرة','url':self.MAIN_URL+'/category/%d9%85%d8%b5%d8%a7%d8%b1%d8%b9%d8%a9-%d8%ad%d8%b1%d8%a9-wwe/','mode':'30','page':1},
                    {'category':hst,'title': 'برامج تلفزيونية','url':self.MAIN_URL+'/category/مسلسلات-series/برامج-تليفزيونية-tv-shows/','mode':'30','page':1},							
                    {'category':hst,'title': 'افلام و مسلسلات Netflix','url':self.MAIN_URL+'/netflix/','mode':'30','page':1},							
                    {'category':hst,'title': 'افلام النجوم','url':self.MAIN_URL+'/actors/','mode':'30','page':1,'sub-mode':1},							
                    {'category':'search','title': _('Search'), 'search_item':True,'page':1,'hst':'tshost'},
                    ]
        self.listsTab(Cima4u_TAB, {'import':cItem['import'],'icon':img_})						

    def showmenu1(self,cItem):
        hst='host2'
        img_=cItem['icon']
        gnr=cItem['sub-mode']
        sts, data = self.getPage(self.MAIN_URL)
        if sts:
            cat_film_data=re.findall('<ul class="sub-menu">(.*?)</ul>', data, re.S) 
            if cat_film_data:
                data2=re.findall('<li.*?href="(.*?)">(.*?)<', cat_film_data[gnr], re.S)
                for (url,titre) in data2:
                    if not url.startswith('http'): url=self.MAIN_URL+url
                    self.addDir({'import':cItem['import'],'category' : 'host2','url': url,'title':titre,'desc':'','icon':cItem['icon'],'mode':'30'})	
    
    def showitms(self,cItem):
        url = cItem['url']
        page = cItem.get('page',1)	
        if page > 1: url = url +'page/'+str(page)+'/'
        sts, data = self.getPage(url)
        if sts:
            if '/actors/' in url:		
                Liste_els = re.findall('class="ActorsItems">(.*?)(</ul|<ul)'	, data, re.S)
                if Liste_els: 
                    Liste_els = re.findall('<li.*?href="(.*?)".*?title="(.*?)".*?url\((.*?)\).*?>(.*?)</a>'	, Liste_els[0][0], re.S)
                    for (url,titre,image,desc) in Liste_els:
                        titre = ph.clean_html(titre)
                        
                        desc = ph.clean_html(desc.replace('</div>','\\n').replace('</i>','\\n')).strip()
                        #desc = tscolor('\c00????00')+'Genre: '+ tscolor('\c00??????') +ph.clean_html(genre)+'\n'+tscolor('\c00????00')+'Views: '+tscolor('\c00??????')+ph.clean_html(view)+' | '+ tscolor('\c00????00')+'Cat: '+tscolor('\c00??????')+ph.clean_html(cat)
                        self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'mode':'30','hst':'tshost'})	
            else:
                pat = 'class="MovieBlock">.*?href="(.*?)".*?image:url\((.*?)\)(.*?)</li>'
                films_list = re.findall(pat, data, re.S)		
                if films_list:
                    for (url,image,data0) in films_list:
                        titre_ = re.findall('BoxTitleInfo">.*?</div>(.*?)</a>', data0, re.S)
                        if titre_: titre = ph.clean_html(titre_[0])
                        else: titre = '!!'
                        genre_ = re.findall('class="Genres">(.*?)</div>', data0, re.S)
                        if genre_: genre = ph.clean_html(genre_[0])
                        else: genre = '!!'	
                        
                        cat_ = re.findall('class="Category">(.*?)</div>', data0, re.S)
                        if cat_: cat = ph.clean_html(cat_[0])
                        else: cat = '!!'               
                        
                        desc = tscolor('\c00????00')+'Genre: '+ tscolor('\c00??????') +ph.clean_html(genre)+'\n'+ tscolor('\c00????00')+'Cat: '+tscolor('\c00??????')+ph.clean_html(cat)

                        desc0,titre = self.uniform_titre(titre)
                        if desc.strip()!='':
                            desc = tscolor('\c00????00')+'Info: '+tscolor('\c00??????')+desc
                        self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'mode':'31','EPG':True,'hst':'tshost'})	
                
            
            self.addDir({'import':cItem['import'],'title':tscolor('\c0000??00')+'Page '+str(page+1),'page':page+1,'category' : 'host2','url':cItem['url'],'icon':cItem['icon'],'mode':'30'} )									

    def showelms(self,cItem):
        url = cItem['url']
        sts, data0 = self.getPage(url)
        if sts:
            Liste_els = re.findall('class="StatsMain">.*?</ul>.*?href="(http.*?)".*?WatchIcon">', data0, re.S)
            if Liste_els:
                URL = Liste_els[0]
                sts, data = self.getPage(URL)
                if sts:
                    if ('/tag/' in URL) or ('/packs/' in URL):
                        pat = 'class="MovieBlock">.*?href="(.*?)".*?image:url\((.*?)\)(.*?)</li>'
                        films_list = re.findall(pat, data, re.S)		
                        if films_list:
                            for (url,image,data0) in films_list:
                                titre_ = re.findall('BoxTitleInfo">.*?</div>(.*?)</a>', data0, re.S)
                                if titre_: titre = ph.clean_html(titre_[0])
                                else: titre = '!!'
                                
                                genre_ = re.findall('class="Genres">(.*?)</div>', data0, re.S)
                                if genre_: genre = ph.clean_html(genre_[0])
                                else: genre = '!!'	
                                
                                cat_ = re.findall('class="Category">(.*?)</div>', data0, re.S)
                                if cat_: cat = ph.clean_html(cat_[0])
                                else: cat = '!!'               
                                
                                desc = tscolor('\c00????00')+'Genre: '+ tscolor('\c00??????') +ph.clean_html(genre)+'\n'+ tscolor('\c00????00')+'Cat: '+tscolor('\c00??????')+ph.clean_html(cat)
                                self.addDir({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'mode':'31','EPG':True,'hst':'tshost'})	
                    else:
                        Liste_tr = re.findall('<iframe.*?src="(.*?)"', data0, re.S)
                        if Liste_tr:
                            self.addVideo({'import':cItem['import'],'category' : 'video','url': Liste_tr[0],'title':'Trailer','desc':cItem['desc'],'icon':cItem['icon'],'hst':'none'})	
                        if '/episode/' in URL.lower():
                            films_list = re.findall('EpisodeItem.*?href="(.*?)".*?>(.*?)</a>', data, re.S)		
                            if films_list:
                                for (url,titre) in films_list:
                                    titre = ph.clean_html(titre)
                                    self.addVideo({'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'})	
                        elif  '/video/' in URL.lower():
                            self.addVideo({'import':cItem['import'],'good_for_fav':True,'good_for_fav':True,'category' : 'video','url': URL,'title':cItem['title'],'desc':cItem['desc'],'icon':cItem['icon'],'hst':'tshost'})	
               
    def SearchResult(self,str_ch,page,extra):
        elms = []  
        url_='http://cima4u.io'+'/search/'+str_ch+'/page/'+str(page)+'/'
        sts, data = self.getPage(url_)
        if sts:
            pat = 'class="MovieBlock">.*?href="(.*?)".*?image:url\((.*?)\)(.*?)</li>'
            films_list = re.findall(pat, data, re.S)		
            if films_list:
                for (url,image,data0) in films_list:
                    titre_ = re.findall('BoxTitleInfo">.*?</div>(.*?)</a>', data0, re.S)
                    if titre_: titre = ph.clean_html(titre_[0])
                    else: titre = '!!'
                    
                    genre_ = re.findall('class="Genres">(.*?)</div>', data0, re.S)
                    if genre_: genre = ph.clean_html(genre_[0])
                    else: genre = '!!'	
                    
                    cat_ = re.findall('class="Category">(.*?)</div>', data0, re.S)
                    if cat_: cat = ph.clean_html(cat_[0])
                    else: cat = '!!'                    
                    
                    desc = tscolor('\c00????00')+'Genre: '+ tscolor('\c00??????') +ph.clean_html(genre)+'\n'+ tscolor('\c00????00')+'Cat: '+tscolor('\c00??????')+ph.clean_html(cat)
                    desc0,titre = self.uniform_titre(titre,1)
                    desc = desc0 + desc
                    elm = {'import':extra,'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':desc,'icon':image,'mode':'31','EPG':True,'hst':'tshost'}	
                    elms.append(elm)
                    self.addDir(elm)
        return elms
        
    def get_links(self,cItem):
        urlTab = []	
        url=cItem['url']
        #URL = urllib.quote(URL).replace('%3A//','://')
        sts, data = self.getPage(url)
        if sts:	
            Liste_els =  re.findall('data-link="(.*?)".*?>(.*?)</a>', data, re.S)
            for (code,host_) in Liste_els:
                host_ = ph.clean_html(host_).strip()
                if 'thevids'   in host_.lower(): host_= 'thevideobee'
                if 'up-stream' in host_.lower(): host_= 'uptostream'
                urlTab.append({'name':host_, 'url':'hst#tshost#'+code, 'need_resolve':1})						
        return urlTab
        
         
    def getVideos(self,videoUrl):
        urlTab = []	
        sUrl = self.MAIN_URL2+'/structure/server.php?id='+videoUrl
        post_data = {'id':videoUrl}
        sts, data = self.getPage(sUrl, post_data=post_data)
        if sts:
            Liste_els_3 = re.findall('src="(.*?)"', data, re.S)	
            if Liste_els_3:
                urlTab.append((Liste_els_3[0].replace('\r',''),'1'))
        return urlTab
        
    def getArticle(self, cItem):
        printDBG("cima4u.getArticle [%s]" % cItem) 
        otherInfo1 = {}
        desc= cItem['desc']
        sts, data = self.getPage(cItem['url'])
        if sts:
            lst_dat=re.findall('InformationList">(.*?)</ul', data, re.S)
            if lst_dat:
                lst_dat2=re.findall('<li>(.*?)">(.*?)</li>', lst_dat[0], re.S)
                for (x1,x2) in lst_dat2:
                    if 'النوع'  in x1: otherInfo1['genres'] = ph.clean_html(x2)
                    if 'القسم'  in x1: otherInfo1['categories'] = ph.clean_html(x2)			
                    if 'الجودة'  in x1: otherInfo1['quality'] = ph.clean_html(x2)					
                    if 'السنة'  in x1: otherInfo1['year'] = ph.clean_html(x2)					
            lst_dat=re.findall('class="Story">(.*?)</div>', data, re.S)
            if lst_dat:		
                desc=ph.clean_html(lst_dat[0])
                
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
        if mode=='32':
            self.showepisodes(cItem)
            
