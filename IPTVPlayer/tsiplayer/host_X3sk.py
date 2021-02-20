# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor,tshost
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
from Plugins.Extensions.IPTVPlayer.libs import ph
import re,urllib,base64
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes                 import strwithmeta

def getinfo():
    info_={}
    name = 'Esheeq.Com'
    hst = tshost(name)	
    if hst=='': hst = 'https://esheeq.com'
    info_['host']= hst
    info_['name']=name
    info_['name']='Esheeq.Com'
    info_['version']='1.2.02 27/08/2020'
    info_['dev']='RGYSoft'
    info_['cat_id']='201'
    info_['desc']='أفلام و مسلسلات تركية'
    info_['icon']='https://i.ibb.co/dBxJK7F/esseq.png'
    info_['recherche_all']='1'
    #info_['update']='Fix Links extractor'	

    return info_
    
    
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'_3sk.cookie'})
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        self.MAIN_URL = getinfo()['host']
        self.HEADER = {'User-Agent': self.USER_AGENT, 'Connection': 'keep-alive', 'Accept-Encoding':'gzip', 'Content-Type':'application/x-www-form-urlencoded','Referer':self.getMainUrl(), 'Origin':self.getMainUrl()}
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}
        #self.getPage = self.cm.getPage

    def getPage(self, baseUrl, addParams = {}, post_data = None):
        baseUrl=self.std_url(baseUrl)
        if addParams == {}: addParams = dict(self.defaultParams)
        addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
        return self.cm.getPageCFProtection(baseUrl, addParams, post_data)
         
    def showmenu0(self,cItem):
        self.addDir({'import':cItem['import'],'category' : 'host2','title':'اخر الحلقات'  ,'icon':cItem['icon'],'mode':'30','url':self.MAIN_URL+'/episodes/'})
        self.addDir({'import':cItem['import'],'category' : 'host2','title':'افلام'     ,'icon':cItem['icon'],'mode':'30','url':self.MAIN_URL+'/category/الأفلام-التركية/'})			
        self.addDir({'import':cItem['import'],'category' : 'host2','title':'جميع المسلسلات','icon':cItem['icon'],'mode':'30','url':self.MAIN_URL+'/series/'})
        self.addDir({'import':cItem['import'],'category' :'search','title': _('Search'),'search_item':True,'page':1,'hst':'tshost','icon':cItem['icon']})

    def showitms(self,cItem):
        url=cItem.get('url', '')
        page = cItem.get('page', 1)
        if page>1:
            if '/series/' in url:
                url = url+'/page/'+str(page)+'/'
            else:
                url = url+'?page='+str(page)+'/'
        sts, data = self.getPage(url)
        if sts:		
            if True:# ('/episodes/' in  url) or ('/category/' in  url):
                #pat = '<li class="EpisodeBlock.*?href="(.*?)".*?Title">(.*?)<.*?bg="(.*?)"'
                #pat = '<li class="EpisodeBlock.*?href="(.*?)".*?Title">(.*?)<.*?url\((.*?)\)'
                pat = 'class="block-post.*?href="(.*?)".*?title="(.*?)".*?url\((.*?)\)'
                lst_data=re.findall(pat, data, re.S)
                for (url1,titre,image) in lst_data:
                    titre = ph.clean_html(titre)
                    image=self.std_url(image)
                    if 'post.php?url=' in url1:
                        url_tmp = url1.split('post.php?url=')[-1].replace('%3D','=')
                        #try:
                        url1 = base64.b64decode(url_tmp)
                        #except:
                        #    printDBG('error base64:url1='+url_tmp)
                    if '/series/' in url1:
                        self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'desc':'','icon':image,'hst':'tshost','good_for_fav':True,'mode':'30'})			
                    else:
                        self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'desc':'','icon':image,'hst':'tshost','good_for_fav':True})	
                #if '/series/' not in url:
                self.addDir({'import':cItem['import'],'category' : 'host2','title':tscolor('\c00????00')+_("Next page"),'url':cItem['url'],'page':page+1,'mode':'30'})			
            else:
                pat = 'class="SerieBox".*?href="(.*?)".*?bg="(.*?)".*?>(.*?)</a>'
                pat = 'class="SerieBox".*?href="(.*?)".*?url\((.*?)\).*?>(.*?)</a>'
                lst_data=re.findall(pat, data, re.S)
                for (url1,image,titre) in lst_data:
                    image=self.std_url(image)
                    titre = ph.clean_html(titre)
                    if '/packs/' in url:
                        self.addVideo({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'desc':'','icon':image,'hst':'tshost','good_for_fav':True})	
                    else:
                        self.addDir({'import':cItem['import'],'category' : 'host2','title':titre,'url':url1,'desc':'','icon':image,'hst':'tshost','good_for_fav':True,'mode':'30'})			
                
    def get_links(self,cItem): 	
        urlTab = []
        baseUrl=cItem['url']
        if '/vid/post.php?' in baseUrl:
            sts, data = self.getPage(baseUrl)
            if sts:	
                lst_data = re.findall('top_banner">.*?href="(.*?)"',data, re.S)			
                if lst_data:
                    baseUrl = lst_data[0]
        sts, data = self.getPage(baseUrl)
        if sts:	
            lst_data = re.findall('data-server="(.*?)"(.*?)</li>',data, re.S)
            if lst_data:
                for host,url in lst_data:
                    if '<em>ok</em>' in url: 
                        url = 'https://www.ok.ru/videoembed/'+host
                        host = 'OK.RU'
                    elif '<em>tune</em>' in url:
                        url = 'https://tune.pk/js/open/embed.js?vid='+host+'&userid=827492&_=1601112672793'
                        host = 'TUNE.PK'
                    elif '<em>turk</em>' in url:
                        url = 'https://arabveturk.com/embed-'+host+'.html'
                        host = 'ARABVETURK'
                    elif '<em>now</em>' in url:
                        url = 'https://extremenow.net/embed-'+host+'.html'
                        host = 'EXTREAMENOW'
                    elif '<em>youtube</em>' in url:
                        url = 'https://www.youtube.com/watch?v='+host
                        host = 'YOUTUBE'                         
                    elif '<em>daily</em>' in url:
                        lst_data0 = re.findall('href="(.*?)"',url, re.S)	
                        if lst_data0:
                            url = lst_data0[0]
                            #if '?' in url: url = url.split('?',1)[0]
                            #url = url.replace('www.dailymotion.com/video/','www.dailymotion.com/embed/video/')
                        host = 'DAILYMOTION'
                    urlTab.append({'url':url, 'name':host, 'need_resolve':1,type:''})
            else:
                lst_data = re.findall('iframe.*?src="(.*?)"',data, re.S)
                if lst_data: urlTab.append({'url':lst_data[0], 'name':'Iframe', 'need_resolve':1,type:''})	
        return urlTab	

    def getVideos(self,videoUrl):
        printDBG(videoUrl)
        urlTab = []	
        sts, data = self.getPage(videoUrl)
        if sts:	
            lst_url = re.findall('src=["\'](.*?)["\']',data, re.S|re.IGNORECASE)
            if lst_url:
                Url = lst_url[0]
                if Url.startswith('//'): Url='http:'+Url
                Url = strwithmeta(Url,{'Referer':''})
                urlTab.append((Url,'1'))
        return urlTab		 

    def SearchResult(self,str_ch,page,extra):
        url=self.MAIN_URL+'/search/'+str_ch+'/?page='+str(page)+'/'
        sts, data = self.getPage(url)
        if sts:
            lst_data=re.findall('class="block-post.*?href="(.*?)".*?title="(.*?)".*?url\((.*?)\)', data, re.S)
            for (url,titre,image) in lst_data:
                image=self.std_url(image)
                titre = ph.clean_html(titre)
                if '/series/' in url:
                    self.addDir({'import':extra,'category' : 'host2','title':titre,'url':url,'desc':'','icon':image,'hst':'tshost','good_for_fav':True,'mode':'30'})			
                else:
                    self.addVideo({'import':extra,'category' : 'host2','title':titre,'url':url,'desc':'','icon':image,'hst':'tshost','good_for_fav':True})	
            
    def start(self,cItem):      
        mode=cItem.get('mode', None)
        if mode=='00':
            self.showmenu0(cItem)
        if mode=='20':
            self.showmenu1(cItem)
        if mode=='30':
            self.showitms(cItem)			

