# -*- coding: utf-8 -*-
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG
from Plugins.Extensions.IPTVPlayer.libs import ph
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.tstools import TSCBaseHostClass,tscolor
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, SAWLIVETV_decryptPlayerParams
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.packer import cPacker
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads
try:
    from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.config import GestionCookie
    from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.vstream.requestHandler import cRequestHandler
except:
    pass
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from binascii import unhexlify
from hashlib import md5
import base64
import re
import time
import urllib
from Plugins.Extensions.IPTVPlayer.tsiplayer.libs.urlparser  import urlparser as ts_urlparser

def getinfo():
    info_={}
    info_['name']='Movs4u.Tv'
    info_['version']='1.9.1 23/02/2020'
    info_['dev']='RGYSoft'
    info_['cat_id']='99'
    info_['desc']='أفلام و مسلسلات اجنبية'
    info_['icon']='https://i.ibb.co/8Pgs99g/Sans-titre.png'
    info_['recherche_all']='1'
    info_['update']='Fixe trailer'	
    return info_
    
def cryptoJS_AES_decrypt(encrypted, password, salt):
    def derive_key_and_iv(password, salt, key_length, iv_length):
        d = d_i = ''
        while len(d) < key_length + iv_length:
            d_i = md5(d_i + password + salt).digest()
            d += d_i
        return d[:key_length], d[key_length:key_length+iv_length]
    bs = 16
    key, iv = derive_key_and_iv(password, salt, 32, 16)
    cipher = AES_CBC(key=key, keySize=32)
    return cipher.decrypt(encrypted, iv)
    
class TSIPHost(TSCBaseHostClass):
    def __init__(self):
        TSCBaseHostClass.__init__(self,{'cookie':'movs4u.cookie'})
        self.MAIN_URL = 'https://movs4u.vip'

    def showmenu(self,cItem):
        TAB = [('الافلام','','10',0),('المسلسلات','','10',1),('سلاسل الافلام','/collection/','20',''),('انواع افلام','','10',2)]
        self.add_menu(cItem,'','','','','',TAB=TAB,search=True)

    def showmenu1(self,cItem):
        self.add_menu(cItem,'<ul(.*?)</ul>','<li.*?href="(.*?)".*?name">(.*?)<','','20',del_=['url:#'],ind_0 = cItem['sub_mode'],ord=[0,1])		

    def showitms(self,cItem):
        desc  = [('Genre','class="genres">(.*?)</span>','',''),('Imdb','box-imdb">(.*?)</div>','',''),('Year','</path>(.*?)</span>','',''),('Quality','class="quality">(.*?)</span>','','')]
        next  = ['class=\'arrow_pag\'.{1,5}href="(.*?)"','20']
        #next  = ['<link rel="next".*?href="(.*?)"','20']
        mode_ = 'video'
        if '/tvshows/'        in cItem['url']    : mode_ = '21'
        if 'trending/?get=tv' in cItem['url']    : mode_ = '21'        
        if cItem['url'].endswith('/collection/') : mode_ = '20'
        if '/seasons/'        in cItem['url']    : mode_ = '20'
        #self.add_menu(cItem,'class="colsbox(.*?)<footer','col-post-movie">.*?href="(.*?)".*?src="(.*?)"(.*?)<h3>(.*?)</h3>(.*?)</div>.{1,10}</div>','',mode_,ord=[0,3,1,2,4],Desc=desc,Next=next,u_titre=True,EPG=True)		
        self.add_menu(cItem,'class="colsbox(.*?)(?:<footer|loop-episode)','col-post-movie">.*?src="(.*?)"(.*?)<h3.*?href="(.*?)".*?>(.*?)</h3>(.*?)</div>.{1,50}</div>','',mode_,ord=[2,3,0,1,4],Next=next,Desc=desc,u_titre=True,EPG=True)		

    def showelms(self,cItem):
        sUrl=cItem['url']
        sts, data = self.getPage(sUrl) 
        if sts:
            Liste_films_data0 = re.findall('class="senumb">.*?</i>(.*?)<(.*?)(?:<h2>|<h5>)', data, re.S)
            if Liste_films_data0 :
                for (tt,data) in Liste_films_data0:
                    self.addMarker({'title':tscolor('\c0000??00')+tt,'desc':'','icon':cItem['icon'],'desc':cItem['desc']})
                    Liste_films_data = re.findall('<a href="(.*?)".*?titlepisode">(.*?)<.*?numepisode">(.*?)<', data, re.S)	
                    for (url,titre,ep) in Liste_films_data:
                        titre = tscolor('\c00????00') + ep + tscolor('\c00??????') + ' - ' + titre
                        params = {'import':cItem['import'],'good_for_fav':True,'category' : 'host2','url': url,'title':titre,'desc':cItem['desc'],'page':1,'icon':cItem['icon'],'hst':'tshost'} 
                        self.addVideo(params)	

    def getArticle(self,cItem):
            printDBG("movs4u.getVideoLinks [%s]" % cItem) 
            otherInfo1 = {}
            desc = cItem.get('desc','')
            sts, data = self.getPage(cItem['url'])
            if sts:
                lst_dat=re.findall('class="post-content.*?>(.*?)</p>', data, re.S)
                if lst_dat: desc = tscolor('\c00????00')+'Story: '+tscolor('\c00??????')+ph.clean_html(lst_dat[0])
            icon = cItem.get('icon')
            title = cItem['title']		
            return [{'title':title, 'text': desc, 'images':[{'title':'', 'url':icon}], 'other_info':otherInfo1}]




    def showmenu2(self,cItem):		
        gnr=cItem['sub_mode']
        img_=cItem['icon']		
        sUrl=self.MAIN_URL
        sts, data = self.getPage(sUrl) 
        if sts:
            Liste_films_data = re.findall('class="sub-menu">(.*?)\/ul', data, re.S)
            if Liste_films_data :
                if gnr=='Film_qual':
                    films_data=Liste_films_data[3]
                else:
                    films_data=Liste_films_data[2]		
                Liste_films_data = re.findall('<a href="(.*?)">(.*?)<', films_data, re.S)	
                for (url,titre) in Liste_films_data:
                    titre=self.cleanHtmlStr(titre)
                    params = {'import':cItem['import'],'good_for_fav':True,'category' : 'host2','Url': url,'title':titre,'desc':titre,'page':1,'icon':img_,'sub_mode':gnr,'mode':'30'} 
                    self.addDir(params)	


    
    def SearchResult(self,str_ch,page,extra):
        url = self.MAIN_URL+'/page/'+str(page)+'/?search='+str_ch
        desc  = [('Genre','class="genres">(.*?)</span>','',''),('Imdb','box-imdb">(.*?)</div>','',''),('Year','</path>(.*?)</span>','',''),('Quality','class="quality">(.*?)</span>','','')]
        self.add_menu({'import':extra,'url':url+'&post_type=movies','icon':''},'class="colsbox(.*?)(?:<footer|loop-episode)','col-post-movie">.*?src="(.*?)"(.*?)<h3.*?href="(.*?)".*?>(.*?)</h3>(.*?)</div>.{1,50}</div>','','video',Titre='Movies',ord=[2,3,0,1,4],Desc=desc,u_titre=True,EPG=True,add_vid=False)		
        self.add_menu({'import':extra,'url':url+'&post_type=tvshows','icon':''},'class="colsbox(.*?)(?:<footer|loop-episode)','col-post-movie">.*?src="(.*?)"(.*?)<h3.*?href="(.*?)".*?>(.*?)</h3>(.*?)</div>.{1,50}</div>','','21',Titre='TV Shows',ord=[2,3,0,1,4],Desc=desc,u_titre=True,EPG=True,add_vid=False)		

    def MediaBoxResult(self,str_ch,year_,extra):
        urltab=[]
        str_ch_o = str_ch
        str_ch = urllib.quote(str_ch_o)
        url_=self.MAIN_URL+'/page/1/?s='+str_ch
        sts, data = self.getPage(url_)
        if sts:
            Liste_films_data = re.findall('"result-item">.*?href="(.*?)".*?src="(.*?)".*?alt="(.*?)".*?">(.*?)<', data, re.S)
            for (url,image,name_eng,type_) in Liste_films_data:
                type_ = type_.strip()
                name_eng=ph.clean_html(name_eng.strip())
                desc0,titre0 = self.uniform_titre(name_eng,1)
                if str_ch_o.lower().replace(' ','') == titre0.replace('-',' ').replace(':',' ').lower().replace(' ',''):
                    trouver = True
                else:
                    trouver = False
                name_eng='|'+tscolor('\c0060??60')+'Movs4U'+tscolor('\c00??????')+'| '+titre0
                if type_=='Movie':
                    params = {'titre':titre0,'import':extra,'good_for_fav':True,'category' : 'video','url': url,'title':name_eng,'desc':'','icon':image,'hst':'tshost'} 
                    if trouver: urltab.insert(0,params)
                    else: urltab.append(params)
                else:
                    params = {'titre':titre0,'import':extra,'good_for_fav':True,'category' : 'host2','Url': url,'title':name_eng,'desc':'','icon':image,'sub_mode':'serie_ep','page':1,'mode':'30'} 
                    if trouver: urltab.insert(0,params)
                    else: urltab.append(params)	
        return urltab

    def get_links(self,cItem): 	
        urlTab = []	
        URL=cItem['url']
        sts, sHtmlContent = self.getPage(URL)
        if sts:
            data0 = re.findall('<ul class="postserv(.*?)</ul>',sHtmlContent, re.S)
            if data0:
                data = re.findall('<li.*?url="(.*?)".*?>(.*?)<',data0[0], re.S)
                for (url,titre) in data:                
                    urlTab.append({'name':titre, 'url':'hst#tshost#'+url+'|'+cItem['url'], 'need_resolve':1,'type':''})		
        return urlTab     
        

    def getVideos(self,videoUrl):
        urlTab = []	
        refer=''
        if '|' in videoUrl:
            url_ref,refer=videoUrl.split('|')
            videoUrl = url_ref
        printDBG("1")
        params = dict(self.defaultParams)
        params['header']['Referer'] = self.std_url(refer)
        sts, data = self.getPage(videoUrl,params)
        if sts:
            result = re.findall('<iframe.*?src="(.*?)"',data, re.S)	
            if result:
                URL = result[0]
                if '=http' in URL: URL = 'http' + URL.split('=http',1)[1]
                urlTab.append((URL,'1'))
                
        return urlTab



        
    def get_links1(self,cItem): 	
        urlTab = []	
        URL=cItem['url']
        sts, sHtmlContent = self.getPage(URL)
        if sts:
            _data0 = re.findall("'trailer'>.*?'title'>(.*?)<.*?server'>(.*?)<.*?data-post='(.*?)'",sHtmlContent, re.S)
            if _data0:
                urlTab.append({'name':_data0[0][0].replace('- تريلر الفلم',''), 'url':'hst#tshost#'+_data0[0][2], 'need_resolve':1})					
            _data = re.findall("data-url='(.*?)'.*?title'>(.*?)<.*?server'>(.*?)<",sHtmlContent, re.S)
            for (data_url,titre1,srv) in _data:
                titre1=titre1.replace('سيرفر مشاهدة رقم','Server:') 
                local=''
                if 'movs' in srv.lower(): local='local'
                srv=srv.lower().replace('openload.com','openload.co')
                tag = ''
                if '/player_c.php'  in data_url:
                    tag  = ' [Aflamyz M3U8 (Mail.Ru)]'
                    local='local'
                if '/main_player1.php'  in data_url:
                    tag  = ' [Arabramadan MAIN]'
                    local='local'	
                if '/main_player.php'  in data_url:
                    tag  = ' [M3U8 MAIN (GOOGLE)]'
                    local='local'					
                if '/player_y.php'  in data_url:
                    tag  = ' [Aflamyz M3U8 (YANDEX)]'
                    local='local'
                if '/player_ok.php' in data_url:
                    tag  = ' [Aflamyz MP4 (OK.RU)]'
                    local='local'
                if '/player_m.php' in data_url:
                    tag  = ' [Aflamyz MP4 (MEGA)]'
                    local='local'
                if '/player_j.php'  in data_url:
                    tag  = ' [Arabramadan MP4 (GOOGLE)]'
                    local='local'
                if '/player_e1.php'  in data_url:
                    tag  = ' [Gdrive]'
                    local='local'
                if '/e1.php' in data_url:
                    tag  = ' [Arabramadan MP4 (GOOGLE)]'
                    local='local'					
                if '/e2.php' in data_url:
                    tag  = ' [Arabramadan MP4 (GOOGLE)]'
                    local='local'
                if '/or/index.php' in data_url:
                    tag  = ' [Aflamys MP4 ]'
                    local='local'					

                urlTab.append({'name':'|'+titre1+'| '+srv+tag, 'url':'hst#tshost#'+data_url+'|'+cItem['url'], 'need_resolve':1,'type':local})		
        return urlTab

    
    def extractLink(self,videoUrl,refer):
        url_out='None'
        printDBG('a1')
        if 'juicy.php?url=' in videoUrl:
            printDBG('a3')
            _data3 = re.findall('url=(.*)',videoUrl, re.S)
            if _data3: 
                url_out = _data3[0]
        else:
            printDBG('a4')
            Params = dict(self.defaultParams)
            Params['header']['Referer']=refer
            sts, data = self.getPage(videoUrl,Params)
            if sts:
                printDBG('a5')
                _data2 = re.findall('<iframe.*?src="(.*?)"',data, re.S)		 		
                if _data2:			
                    url_out = _data2[0]
                else:
                    printDBG('a6')
                    _data4 = re.findall('javascript">eval(.*?)</script>',data, re.S)
                    if _data4:
                        script_eval='eval'+_data4[0].strip()
                        printDBG(script_eval)
                        datau = unpackJSPlayerParams(script_eval, SAWLIVETV_decryptPlayerParams, 0)
                        printDBG(datau)
                        _data5 = re.findall('<iframe.*?src="(.*?)"',datau.replace('\\',''), re.S)
                        if _data5:
                            url_out = _data5[0]
                        else:
                            _data5 = re.findall('sources:(\[.*?])',datau.replace('\\',''), re.S)
                            if _data5:
                                url_out = _data5[0]						
                    else:
                        printDBG('a7='+data)
                        _data4 = re.findall('"file".*?"(.*?)"',data, re.S)
                        if _data4:
                            printDBG('a9')
                            url_out = _data4[0]						
                        else:
                            _data2 = re.findall('<meta.*?url=(.*?)"',data, re.S)		 		
                            if _data2:			
                                url_out = _data2[0]					
        return url_out	

    def getVideos1(self,videoUrl):
        urlTab = []	
        refer=''
        if '|' in videoUrl:
            url_ref,refer=videoUrl.split('|')
            videoUrl = url_ref
        printDBG("1")
        if videoUrl.startswith('http'):
            i=0
            while True:
                i=i+1
                printDBG(str(i)+">>>>Start<<<< "+videoUrl)
                oldURL=videoUrl
                videoUrl = self.extractLink(videoUrl,refer)
                printDBG(str(i)+">>>>End<<<< "+videoUrl)
                if videoUrl.startswith('['):
                    _data3 = re.findall('label":"(.*?)".*?file":"(.*?)"',videoUrl, re.S)	
                    for (label,uurl) in _data3:
                        urlTab.append((label+'|'+uurl,'4'))	
                    break	
                elif videoUrl == 'None': 
                    printDBG('1') 			
                    urlTab.append((oldURL,'1'))
                    break 				
                elif '.m3u8' in videoUrl:
                    printDBG('2')
                    URL1=strwithmeta(videoUrl, {'Referer':url_ref})
                    urlTab.append((URL1,'3'))
                    break
                elif 'arabramadan' in videoUrl:
                    params = dict(self.defaultParams)
                    params['header']['Referer'] = oldURL
                    sts, data = self.getPage(videoUrl,params)
                    if sts:
                        _data3 = re.findall('JuicyCodes.Run\("(.*?)"\)',data, re.S)	
                        if _data3:
                            packed = base64.b64decode(_data3[0].replace('"+"',''))
                            printDBG('packed'+packed)
                            Unpacked = cPacker().unpack(packed)
                            printDBG('packed'+Unpacked)
                            meta_ = {'Referer':'https://arabramadan.com/embed/L00w0FyU0if4mHD/'}
                            _data3 = re.findall('src".*?"(.*?)".*?label":"(.*?)"',Unpacked, re.S)	
                            for (uurl,ttitre) in _data3:
                                uurl = strwithmeta(ttitre+'|'+uurl,meta_)
                                urlTab.append((uurl,'4'))
                    break	
                elif 'gdriveplayer' in videoUrl:
                    params = dict(self.defaultParams)
                    params['header']['Referer'] = oldURL
                    sts, data = self.getPage(videoUrl,params)
                    if sts:
                        result = re.findall('(eval\(function\(p.*?)</script>',data, re.S)	
                        if result:
                            data = result[0].strip()
                            printDBG('eval trouver='+result[0].strip()+'#')
                            data0 = cPacker().unpack(result[0].strip())
                            printDBG('data0='+data0+'#')
                            result = re.findall('data=.*?(\{.*?}).*?null.*?[\'"](.*?)[\'"]',data0, re.S)
                            if result:
                                code_ = json_loads(result[0][0])
                                printDBG('Code='+str(code_))
                                data1 = result[0][1].strip().replace('\\','')									
                                printDBG('data1='+data1)
                                lst = re.compile("[A-Za-z]{1,}").split(data1)
                                printDBG('lst='+str(lst))
                                script = ''
                                for elm in lst:
                                    script = script+chr(int(elm))
                                printDBG('script='+script)
                                result = re.findall('pass.*?[\'"](.*?)[\'"]',script, re.S)
                                if result:
                                    pass_ = result[0]								
                                    printDBG('pass_='+pass_)
                                    ciphertext = base64.b64decode(code_['ct'])
                                    iv = unhexlify(code_['iv'])
                                    salt = unhexlify(code_['s'])
                                    b = pass_
                                    decrypted = cryptoJS_AES_decrypt(ciphertext, b, salt)
                                    printDBG('decrypted='+decrypted)
                                    data2 = decrypted[1:-1]
                                    #data2 = decrypted.replace('"','').strip()
                                    printDBG('data2='+data2)									
                                    data2 = cPacker().unpack(data2)
                                    printDBG('data2='+data2)								
                                    url_list = re.findall('sources:(\[.*?\])',data2, re.S)	
                                    #for data3 in url_list:
                                    data3= url_list[0]
                                    data3 = data3.replace('\\','').replace('"+countcheck+"','')
                                    printDBG('data3='+data3+'#')
                                    src_lst = json_loads(data3)
                                    printDBG('src_lst='+str(src_lst)+'#')
                                    for elm in src_lst:
                                        _url   = elm['file']
                                        _label = elm.get('label','Google')
                                        if 'm3u8' in _url:
                                            urlTab.append((_url,'3'))	
                                        else:
                                            urlTab.append(('Google ('+_label+')|'+_url,'4'))															
                    break
                 
                elif 'aflamyz' in videoUrl:
                    params = dict(self.defaultParams)
                    params['header']['Referer'] = oldURL
                    sts, data = self.getPage(videoUrl,params)
                    if sts:
                        result = re.findall('data-en="(.*?)".*?data-p="(.*?)"',data, re.S)	
                        if result:
                            code_ = json_loads(urllib.unquote(result[0][0]))
                            pass_ = result[0][1]
                            printDBG('Code='+str(code_))
                            printDBG('Pass='+pass_)
                            ciphertext = base64.b64decode(code_['ct'])
                            iv = unhexlify(code_['iv'])
                            salt = unhexlify(code_['s'])
                            b = pass_
                            decrypted = cryptoJS_AES_decrypt(ciphertext, b, salt)
                            printDBG('decrypted='+decrypted)
                            URL = decrypted.replace('\/','/').replace('"','')
                            printDBG('URL='+URL)
                            params['header']['Referer'] = videoUrl
                            sts, data = self.getPage(URL,params)							
                            if sts:
                                url_list = re.findall('"sources":(\[.*?\])',data, re.S)	
                                if url_list:
                                    src_lst = json_loads(url_list[0])
                                    printDBG('src_lst='+str(src_lst)+'#')
                                    for elm in src_lst:
                                        _url   = elm['file']
                                        _label = elm.get('label','Aflamyz')
                                        if 'm3u8' in _url:
                                            urlTab.append((_url,'3'))	
                                        else:
                                            urlTab.append(('Aflamyz ('+_label+')|'+_url,'4'))										
                    break

                elif (self.up.checkHostSupport(videoUrl) == 1) or (ts_urlparser().checkHostSupport(videoUrl) == 1):	
                    printDBG('3')
                    urlTab.append((videoUrl,'1'))
                    break
                printDBG('4')								 									
                                                
        else:
            printDBG("2")
            post_data = {'action':'doo_player_ajax','post':videoUrl,'nume':'trailer','type':'movie'}		
            sts, data2 = self.getPage(self.MAIN_URL+'/wp-admin/admin-ajax.php', post_data=post_data)
            if sts:
                printDBG("20")
                _data0 = re.findall('<iframe.*?src="(.*?)"',data2, re.S)
                if _data0:	
                    urlTab.append((_data0[0],'1'))	
        return urlTab



