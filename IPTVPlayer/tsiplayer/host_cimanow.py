# -*- coding: utf8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Components.config import config
import re
import base64,urllib

def getinfo():
    info_={}
    info_['name']='CimaNow'
    info_['version']='2.0 13/04/2021'
    info_['dev']='RGYSoft'
    info_['cat_id']='21'
    info_['desc']='افلام و مسلسلات'
    info_['icon']='https://i.ibb.co/F5GycyM/logo.png'
    info_['recherche_all']='0'
    return info_


class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'cimanow.cookie'})
        self.MAIN_URL = 'https://en.cimanow.cc'		

    def showmenu(self,cItem):
        del_ = ['قريبا','قائمتي']        
        self.add_menu(cItem,'<ul>(.*?)</ul>','<li.*?href="(.*?)".*?>(.*?)</li>','','10',ord=[0,1],del_=del_,search=True)		

    def showmenu1(self,cItem):
        del_ = ['قريبا','أختر وجهتك المفضلة','الاكثر مشاهدة','الاكثر اعجا','احدث الحفلات']
        self.add_menu(cItem,'','<section>.*?<span>(.*?)<.*?href="(.*?)"','','20',ord=[1,0],del_=del_)
           
    def showitms(self,cItem):
        desc = [('Info','Ribbon">(.*?)</li>','',''),('Year','year">(.*?)</li>','',''),('Genre','<em>(.*?)</em>','','')]
        next = [1,'20']
        self.add_menu(cItem,'','<article .*?href="(.*?)"(.*?)title">(.*?)(<em>.*?)</li>.*?src="(.*?)"','','21',ord=[0,2,4,1,3],Desc=desc,Next=next,u_titre=True,EPG=True,del_titre='<t class="fa fa-eye">.*?</em>')		

    def showelms(self,cItem):
        self.addVideo({'category':'host2','good_for_fav':True, 'title': cItem['title'],'url':cItem['url'], 'desc':cItem.get('desc',''),'import':cItem['import'],'icon':cItem['icon'],'hst':'tshost'})						
        self.add_menu(cItem,'<ul class.{,30}?id="eps">(.*?)</ul>','<li.*?href="(.*?)".*?(?:alt="logo"|</h3>).*?src="(.*?)".*?alt="(.*?)"','','video',ord=[0,2,1],Titre='Episodes',EPG=True,add_vid=False)

    def get_links(self,cItem): 	
        urlTab = []
        url = cItem['url']
        referer = url
        sts, data = self.getPage(url)
        if sts:
            Liste_els = re.findall('class="shine".*?href="(.*?)"', data, re.S)
            if 	Liste_els:
                Link = Liste_els[0]
                if 'redirect=' in Link:
                    try:
                        printDBG('redirect= in link !!!!!!!!!!')
                        Link = base64.b64decode(Link.split('redirect=',1)[1])
                        referer = Link.split('redirect=',1)[0]
                    except:
                        printDBG('erreur in link !!!!!!!!!!')
                else:
                    printDBG('redirect not in link:'+Link)
                addParams = dict(self.defaultParams)
                addParams['header']['Referer'] = referer
                sts, data = self.getPage(Link)
                if sts:                
                    printDBG('Data.meta='+str(data.meta))
                    printDBG('Data='+data)
                    Liste_els = re.findall('<li.*?data-index="(.*?)".*?data-id="(.*?)".*?>(.*?)</li>', data, re.S)
                    for (url0,id_,titre) in Liste_els:
                        local_=''
                        if 'cn server'   in titre.lower(): titre='fembed'
                        elif 'vidbob'    in titre.lower(): titre='jawcloud'
                        elif 'Cima Now'  in titre: local_='local'
                        titre = self.cleanHtmlStr(titre).strip()
                        urlTab.append({'name':'|Watch Server| '+titre, 'url':'hst#tshost#'+url0+'|'+id_, 'need_resolve':1,'type':local_})  
                    Liste_els = re.findall('id="download">(.*?)</ul>', data, re.S)
                    for elm in Liste_els:
                        Tag    = '|Download Server| '
                        L_els = re.findall('href="(.*?)".*?</i>(.*?)</a>', elm, re.S)
                        for (url0,titre) in L_els:
                            local_ = 'non'
                            resolve = 1                            
                            if url0.endswith('.mp4'):
                                local_ = 'local'
                                url0 = strwithmeta(url0, {'Referer':url})
                                resolve = 0
                            urlTab.append({'name':Tag+self.cleanHtmlStr(titre), 'url':url0, 'need_resolve':resolve,'type':local_})		       
        return urlTab	


    def getVideos(self,videoUrl):
        urlTab = []	
        code,id_ = videoUrl.split('|',1)
        if id_ == 'DOWN':
            sts, data = self.getPage(code,self.defaultParams)
            printDBG('data='+data)
            Liste_els = re.findall('id="downloadbtn".*?href="(.*?)"', data, re.S|re.IGNORECASE)			
            if Liste_els:
                url_ = Liste_els[0]
                if url_.endswith('mp4'):
                    host = url_.split('.net/',1)[0]+'.net'
                    URL_= strwithmeta('MP4|'+url_, {'Referer':host})
                    urlTab.append((URL_,'4'))	
                else:
                    urlTab.append((url_,'1'))
        else:	
            url = self.MAIN_URL+'/wp-content/themes/CimaNow/Interface/server.php'
            post_data = {'id':id_, 'server':code}
            sts, data = self.getPage(url,post_data=post_data)
            if sts:
                Liste_els_3 = re.findall('src="(.+?)"', data, re.S|re.IGNORECASE)	
                if Liste_els_3:
                    URL = Liste_els_3[0]
                    if URL.startswith('//'): URL='http:'+URL
                    if 'cimanow.net/' in URL:
                        host = URL.split('.net/',1)[0]+'.net'
                        printDBG('host='+host)
                        sts, data = self.getPage(URL,self.defaultParams)
                        if sts:
                            printDBG('data='+data)
                            Liste_els = re.findall('source.*?src="(.*?)".*?size="(.*?)"', data, re.S|re.IGNORECASE)
                            for elm in Liste_els:
                                url_ = elm[0]
                                if not(url_.startswith('http')): url_ = host + urllib.quote(url_)
                                URL_= strwithmeta(elm[1]+'|'+url_, {'Referer':host})
                                urlTab.append((URL_,'4'))
                    else:
                        urlTab.append((URL,'1'))
        return urlTab	

    def SearchResult(self,str_ch,page,extra):
        desc = [('Info','Ribbon">(.*?)</li>','',''),('Year','year">(.*?)</li>','',''),('Genre','<em>(.*?)</em>','',''),('Episode','episode">(.*?)</li>','','')]
        url = self.MAIN_URL+'/page/'+str(page)+'/?s='+str_ch
        self.add_menu({'import':extra,'url':url},'','<article .*?href="(.*?)"(.*?)title">(.*?)(<em>.*?)</li>.*?src="(.*?)"','','21',ord=[0,2,4,1,3],Desc=desc,u_titre=True,EPG=True,del_titre='<t class="fa fa-eye">.*?</em>')

    def getArticle(self,cItem):
        Desc = [('Quality','fa-play"></i>الجودة.*?<a>(.*?)</a>','',''),('Time','fa-clock">.*?<a>(.*?)</a>','',''),
                ('Story','fa-info-circle">(.*?)</li>','\n','')]
        desc = self.add_menu(cItem,'','','','desc',Desc=Desc)	
        if desc =='': desc = cItem.get('desc','')
        return [{'title':cItem['title'], 'text': desc, 'images':[{'title':'', 'url':cItem.get('icon','')}], 'other_info':{}}]
                
