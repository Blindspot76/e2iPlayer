# -*- coding: utf-8 -*-
###################################################
# 2019-12-19 by Alec - modified NonstopMozi
###################################################
HOST_VERSION = "1.1"
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, rm, GetTmpDir, GetIPTVPlayerVerstion, MergeDicts
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs import ph
###################################################

###################################################
# FOREIGN import
###################################################
import urlparse
import re
import urllib
import random
import os
import datetime
import time
import zlib
import cookielib
import base64
import traceback
from copy import deepcopy
try:
    import json
except Exception:
    import simplejson as json
from Components.config import config, ConfigText, ConfigYesNo, getConfigListEntry
from Tools.Directories import resolveFilename, fileExists, SCOPE_PLUGINS
from datetime import datetime
from hashlib import sha1
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################
config.plugins.iptvplayer.nonstopmozi_id = ConfigYesNo(default = False)
config.plugins.iptvplayer.boxtipus = ConfigText(default = "", fixed_size = False)
config.plugins.iptvplayer.boxrendszer = ConfigText(default = "", fixed_size = False)

def GetConfigList():
    optionList = []
    optionList.append(getConfigListEntry("id:", config.plugins.iptvplayer.nonstopmozi_id))
    return optionList
###################################################

def gettytul():
    return 'https://nonstopmozi.com/'

class NonstopMozi(CBaseHostClass):
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'nonstopmozi', 'cookie':'nonstopmozi.cookie'})
        self.DEFAULT_ICON_URL = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c/LzysuyS/Iza/KjM/JT8/XK8hLBwDdxxNq'))
        self.USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'
        self.HEADER = self.cm.getDefaultHeader()
        self.AJAX_HEADER = dict(self.HEADER)
        self.AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
        self.MAIN_URL = 'https://nonstopmozi.com'
        self.vivn = GetIPTVPlayerVerstion()
        self.porv = self.gits()
        self.pbtp = '-'
        self.btps = config.plugins.iptvplayer.boxtipus.value
        self.brdr = config.plugins.iptvplayer.boxrendszer.value
        self.aid = config.plugins.iptvplayer.nonstopmozi_id.value
        self.aid_ki = ''
        self.ilk = False
        self.defaultParams = {'header':self.HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE}        

    def getFullIconUrl(self, url):
        return CBaseHostClass.getFullIconUrl(self, url.replace('&amp;', '&'))
        
    def getStringToLowerWithout(self, szoveg):
        bv = ''
        if szoveg != '':
            szoveg = szoveg.replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ö','o').replace('ő','o').replace('ú','u').replace('ü','u').replace('ű','u')
            szoveg = szoveg.replace('Á','a').replace('É','e').replace('Í','i').replace('Ó','o').replace('Ö','o').replace('Ő','o').replace('Ú','u').replace('Ü','u').replace('Ű','u')
            bv = szoveg.lower()
        return bv

    def getPage(self, baseUrl, addParams = {}, post_data = None):
        if addParams == {}: addParams = dict(self.defaultParams)
        addParams['cloudflare_params'] = {'cookie_file':self.COOKIE_FILE, 'User-Agent':self.USER_AGENT}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
        
    def listMainMenu(self, cItem):
        try:
            if not self.ebbtit(): return
            if self.btps != '' and self.brdr != '': self.pbtp = self.btps.strip() + ' - ' + self.brdr.strip()
            tab_movies = 'nonstopmozi_filmek'
            desc_movies = self.getdvdsz(tab_movies, 'Filmek megjelenítése...')
            tab_series = 'nonstopmozi_sorozatok'
            desc_series = self.getdvdsz(tab_series, 'Sorozatok megjelenítése...')
            tab_ajanlott = 'nonstopmozi_ajanlott'
            desc_ajanlott = self.getdvdsz(tab_ajanlott, 'Ajánlott, nézett tartalmak megjelenítése...')
            tab_keresett = 'nonstopmozi_keresett_tartalom'
            desc_keresett = self.getdvdsz(tab_keresett, 'Keresett tartalmak megjelenítése...')
            tab_search = 'nonstopmozi_kereses'
            desc_search = self.getdvdsz(tab_search, 'Keresés...')
            tab_search_hist = 'nonstopmozi_kereses_elozmeny'
            desc_search_hist = self.getdvdsz(tab_search_hist, 'Keresés az előzmények között...')
            MAIN_CAT_TAB = [
                            {'category':'list_movies', 'title': _('Movies'), 'url': self.MAIN_URL, 'tps':'1', 'tab_id':tab_movies, 'desc':desc_movies },
                            {'category':'list_series', 'title': _('Series'), 'url': self.MAIN_URL, 'tps':'2', 'tab_id':tab_series, 'desc':desc_series },
                            {'category':'list_main', 'title': 'Ajánlott, nézett tartalmak', 'tab_id':tab_ajanlott, 'desc':desc_ajanlott },
                            {'category':'list_main', 'title': 'Keresett tartalmak', 'tab_id':tab_keresett, 'desc':desc_keresett },
                            {'category':'search', 'title': _('Search'), 'search_item':True, 'tps':'0', 'tab_id':tab_search, 'desc':desc_search },
                            {'category':'search_history', 'title': _('Search history'), 'tps':'0', 'tab_id':tab_search_hist, 'desc':desc_search_hist } 
                           ]
            self.listsTab(MAIN_CAT_TAB, {'name':'category'})
            vtb = self.malvadnav(cItem, '7', '14', '0', '14')
            if len(vtb) > 0:
                for item in vtb:
                    item['category'] = 'list_third'
                    self.addVideo(item)
            self.ilk = True
        except Exception:
            return
            
    def _listCategories(self, cItem, nextCategory, mode):
        try:
            sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
            if not sts: return
            if len(data) == 0: return
            if mode == 'movie':
                data = self.cm.ph.getDataBeetwenMarkers(data, '<a href="/online-filmek" class="dropdown-toggle', '<div class="clearfix"></div>', False)[1]
                if len(data) == 0: return
            if mode == 'series':
                data = self.cm.ph.getDataBeetwenMarkers(data, '<a href="/online-sorozatok" class="dropdown-toggle', '<div class="clearfix"></div>', False)[1]
                if len(data) == 0: return
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<li><a', '/li>')
            if len(data) == 0: return
            for item in data:
                url = self.getFullUrl(self.cm.ph.getSearchGroups(item, 'href=[\'"]([^"^\']+?)[\'"]')[0])
                if not self.cm.isValidUrl(url):
                    continue
                title = self.cm.ph.getDataBeetwenMarkers(item, '">', '</a', False)[1]
                params = dict(cItem)
                params['desc'] = ''
                params.update({'category':nextCategory, 'title':title, 'url':url, 'md':mode})
                self.addDir(params)
        except Exception:
            return
        
    def listMovies(self, cItem, nextCategory):
        tabID = cItem['tab_id']
        if tabID != '':
            self.susn('2', '14', tabID)
        self._listCategories(cItem, nextCategory, 'movie')
        
    def listSeries(self, cItem, nextCategory):
        tabID = cItem['tab_id']
        if tabID != '':
            self.susn('2', '14', tabID)
        self._listCategories(cItem, nextCategory, 'series')
        
    def listItems(self, cItem, nextCategory):
        nextPage = False        
        try:
            tuhe = cItem['url']
            page = cItem.get('page', 1)
            tumd = cItem['md']
            if tuhe != '':
                tuhe = tuhe + '/oldal/' + str(page)
                sts, data = self.cm.getPage(tuhe, self.defaultParams)
                if not sts: return
                if len(data) == 0: return
                Pgntr = self.cm.ph.getDataBeetwenMarkers(data, '<div class="blog-pagenat-wthree">', '</div>')[1]
                if 'Következő' in Pgntr:
                    nextPage = True
                else:
                    nextPage = False
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, "<div class='col-md-2 w3l-movie-gride-agile'", "div class='clearfix'>")
                if len(data) == 0: return
                for item in data:
                    url = self.getFullUrl(self.cm.ph.getSearchGroups(item, 'href=[\'"]([^"^\']+?)[\'"]')[0])
                    if not self.cm.isValidUrl(url):
                        continue
                    title = self.cm.ph.getSearchGroups(item, '<a title=[\'"]([^"^\']+?)[\'"]')[0].strip()
                    if title == '': continue
                    icon = self.cm.ph.getSearchGroups(item, 'src=[\'"]([^"^\']+?)[\'"]')[0].strip()
                    tmp_ny = self.cm.ph.getDataBeetwenMarkers(item, '<img src=', '>')[1]
                    nyelv = self.cm.ph.getSearchGroups(tmp_ny, 'title=[\'"]([^"^\']+?)[\'"]')[0].strip()
                    if nyelv == '': nyelv = ' '
                    kev = self.cm.ph.getDataBeetwenMarkers(item, "<div class='mid-2'>(", ")<", False)[1]
                    if kev == '': kev = ' '
                    desc = nyelv + '\nKiadás éve:  ' + kev
                    params = MergeDicts(cItem, {'category':nextCategory, 'title':title, 'url':url, 'desc':desc, 'icon':icon, 'nylv':nyelv, 'md':tumd})
                    self.addDir(params)
                if nextPage and len(self.currList) > 0:
                    params = dict(cItem)
                    params.update({'title':_("Next page"), 'page':page+1, 'desc':'Nyugi...\nVan még további tartalom, lapozz tovább!!!'})
                    self.addDir(params)
        except Exception:
            return
            
    def exploreItem(self, cItem):
        desc = ''
        try:
            if len(cItem) > 0:
                tumd = cItem['md']
                sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
                if not sts: return
                if len(data) == 0: return
                tmp_kat = self.cm.ph.getDataBeetwenMarkers(data, '<h4 id="b">Kategória:</h4>', '</div>')[1]
                if tmp_kat != '':
                    kat = self.cleanHtmlStr(tmp_kat)
                tmp_kev = self.cm.ph.getDataBeetwenMarkers(data, '<h4 id="b">Kiadás éve:</h4>', '</a>')[1]
                if tmp_kev != '':
                    kev = self.cleanHtmlStr(tmp_kev)
                nyelv = cItem["nylv"]    
                imdb = self.cm.ph.getDataBeetwenMarkers(data, "itemprop='ratingValue'>", '</span>', False)[1]
                if imdb == 'N/A':
                    imdb = ' '
                leiras = self.cm.ph.getDataBeetwenMarkers(data, "itemprop='description'>", '</p>', False)[1]
                if leiras != '':
                    leiras = re.sub(r'^(.{600}).*$', '\g<1>...', leiras.replace('\n','').strip())
                if nyelv != '':
                    desc = nyelv + '\n'
                if kev != '':
                    desc = desc + kev
                    if kat != '':
                        desc = desc + '  |  ' + kat
                    if imdb != '':
                        desc = desc + '  |  IMDB pont: ' + imdb
                else:
                    if kat != '':
                        desc = desc + kat
                    if imdb != '':
                        desc = desc + '  |  IMDB pont: ' + imdb
                if desc != '':
                    desc = desc + '\n\n' + leiras
                else:
                    desc = leiras
                if tumd == 'series':
                    temp_s = self.cm.ph.getDataBeetwenMarkers(data, '<div class="blog-pagenat-wthree">', '</div>')[1]
                    if temp_s != '':
                        data_s = self.cm.ph.getAllItemsBeetwenMarkers(temp_s, '<li>', '</li>')
                        if len(data_s) > 0:
                            for item_s in data_s:
                                epizod = self.cleanHtmlStr(item_s)
                                epizod_u = self.getFullUrl(self.cm.ph.getSearchGroups(item_s, '''href=['"]([^"^']+?)['"]''')[0])
                                if not self.cm.isValidUrl(epizod_u): continue
                                params = MergeDicts(cItem, {'good_for_fav': True, 'title':cItem['title'] + ' :: ' + epizod + '. epizód', 'url':epizod_u, 'desc':desc, 'icon':cItem['icon']})
                                self.addVideo(params)
                else:
                    params = MergeDicts(cItem, {'good_for_fav': True, 'title':cItem['title'], 'url':cItem['url'], 'desc':desc, 'icon':cItem['icon']})
                    self.addVideo(params)
        except Exception:
            return
            
    def getLinksForVideo(self, cItem):
        url_tmb = []
        retTab = []
        nyelv = ''
        minoseg = ''
        nez = ''
        try:
            sts, data = self.cm.getPage(cItem['url'], self.defaultParams)
            if not sts: return []
            if len(data) == 0: return []
            data = self.cm.ph.getDataBeetwenMarkers(data, '<table', '/table>')[1]
            if len(data) == 0: return []
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, "<tr class='sor'", "</tr>")
            if len(data) == 0: return []
            for item in data:
                url_name = ''
                temp_url = self.getFullUrl(self.cm.ph.getSearchGroups(item, '<a id=\'kat\' href=[\'"]([^"^\']+?)[\'"]')[0])
                if not self.cm.isValidUrl(temp_url): continue
                sts_t, data_t = self.cm.getPage(temp_url, self.defaultParams)
                if not sts_t: continue
                if len(data_t) == 0: continue
                temp_turl = self.cm.ph.getDataBeetwenMarkers(data_t, '<iframe', '/iframe>', caseSensitive=False)[1]
                if len(temp_turl) == 0: continue
                url = self.cm.ph.getSearchGroups(temp_turl, '''src=['"]([^"^']+?)['"]''', ignoreCase=True)[0]
                if self.cm.isValidUrl(url):
                    if url in url_tmb:
                        continue
                    else:
                        url_tmb.append(url)
                    url_name = self.cm.getBaseUrl(url)
                    url_name = self.name_find(url_name,'//','/')
                else:
                    continue
                dtc = self.cm.ph.getAllItemsBeetwenMarkers(item, "<td align = 'center'>", "</td>", False)
                if len(dtc) == 0: continue
                db = 1
                for itc in dtc:
                    if db == 1:
                        nyelv = self.cm.ph.getSearchGroups(itc, '''title = ['"]([^"^']+?)['"]''')[0].replace('!','').strip()
                    if db == 2:
                        minoseg = itc.strip()
                    if db == 6:
                        nez = itc.strip() + ' nézés'
                    db = db + 1    
                name = url_name
                if nyelv != '':
                    name = name + ' | ' + nyelv
                if minoseg != '':
                    name = name + ' | ' + minoseg
                if nez != '':
                    name = name + ' | ' + nez
                if name != '' and url != '':
                    retTab.append({'name':name, 'url':url, 'need_resolve':1})
            if len(retTab) > 0:
                if cItem['category'] != 'list_third':
                    self.susmrgts('2', '14', cItem['tps'], cItem['url'], cItem['title'], cItem['icon'], cItem['desc'], 'mnez')
                return retTab
            else:
                return []
        except Exception:
            return []
            
    def name_find(self, string='', start='', end=''):
        if string != '' and start !='':
            if end != '':
                return string[string.find(start) + len(start):string.rfind(end)]
            else:
                return string[string.find(start) + len(start):]
        else:
            return ''
        
    def getVideoLinks(self, videoUrl=''):
        urlTab = []
        if videoUrl != '' and self.cm.isValidUrl(videoUrl):
            urlTab = self.up.getVideoLinkExt(videoUrl)
        return urlTab
        
    def listMainItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'nonstopmozi_ajanlott':
                self.Fzkttm(cItem, tabID)
            elif tabID == 'nonstopmozi_keresett_tartalom':
                self.Vdakstmk({'name':'history', 'category': 'search', 'tab_id':''}, 'desc', _("Type: "), tabID)
            else:
                return
        except Exception:
            return
            
    def Fzkttm(self, cItem, tabID):
        try:
            self.susn('2', '14', tabID)
            tab_ams = 'nonstopmozi_ajnlt_musor'
            desc_ams = self.getdvdsz(tab_ams, 'Ajánlott, nézett tartalmak megjelenítése műsorok szerint...')
            tab_adt = 'nonstopmozi_ajnlt_datum'
            desc_adt = self.getdvdsz(tab_adt, 'Ajánlott, nézett tartalmak megjelenítése dátum szerint...')
            tab_anzt = 'nonstopmozi_ajnlt_nezettseg'
            desc_anzt = self.getdvdsz(tab_anzt, 'Ajánlott, nézett tartalmak megjelenítése nézettség szerint...')
            A_CAT_TAB = [{'category':'list_third', 'title': 'Dátum szerint', 'tab_id':tab_adt, 'desc':desc_adt},
                         {'category':'list_third', 'title': 'Nézettség szerint', 'tab_id':tab_anzt, 'desc':desc_anzt},
                         {'category':'list_third', 'title': 'Műsorok szerint', 'tab_id':tab_ams, 'desc':desc_ams} 
                        ]
            self.listsTab(A_CAT_TAB, cItem)
        except Exception:
            return
        
    def listThirdItems(self, cItem):
        try:
            tabID = cItem.get('tab_id', '')
            if tabID == 'nonstopmozi_ajnlt_musor':
                self.Vajnltmsr(cItem)
            elif tabID == 'nonstopmozi_ajnlt_datum':
                self.Vajnltdtm(cItem)
            elif tabID == 'nonstopmozi_ajnlt_nezettseg':
                self.Vajnltnztsg(cItem)
            else:
                return
        except Exception:
            return
            
    def Vajnltmsr(self,cItem):
        try:
            self.susn('2', '14', 'nonstopmozi_ajnlt_musor')
            vtb = self.malvadnav(cItem, '3', '14', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return
            
    def Vajnltdtm(self,cItem):
        vtb = []
        try:
            self.susn('2', '14', 'nonstopmozi_ajnlt_datum')
            vtb = self.malvadnav(cItem, '4', '14', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return
            
    def Vajnltnztsg(self,cItem):
        try:
            self.susn('2', '14', 'nonstopmozi_ajnlt_nezettseg')
            vtb = self.malvadnav(cItem, '5', '14', '0')
            if len(vtb) > 0:
                for item in vtb:
                    self.addVideo(item)
        except Exception:
            return

    def listSearchResult(self, cItem, searchPattern, searchType):
        uagnt = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0'
        phdre = {'User-Agent':uagnt, 'DNT':'1', 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Encoding':'gzip, deflate, br', 'Accept-Language':'hu-HU,hu;q=0.8,en-US;q=0.5,en;q=0.3', 'Host':'nonstopmozi.com', 'Upgrade-Insecure-Requests':'1', 'Connection':'keep-alive', 'Content-Type':'application/x-www-form-urlencoded', 'Referer':'https://nonstopmozi.com'}
        phdr = {'header':phdre, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': self.COOKIE_FILE} 
        db = 0
        try:
            cItem = dict(cItem)
            if searchPattern != '':
                self.suskrbt('2', '14', searchPattern)
                krsstr = searchPattern
                krsstr_lnk = self.getStringToLowerWithout(searchPattern.replace(' ', '-'))
                uhe = zlib.decompress(base64.b64decode('eJzLKCkpKLbS18/LzysuyS/Iza/K1EvOz9XPz8vJzEvVTcvMyU3N1s9OLUotTi3WBwCjDBGy')) + krsstr_lnk
                pstd = {'keres':krsstr, 'submit':'Keresés'}
                sts, data = self.cm.getPage(uhe, phdr, pstd)
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, "<div class='col-md-2 w3l-movie-gride-agile'", "div class='clearfix'>")
                if len(data) == 0: return
                for item in data:
                    url = self.getFullUrl(self.cm.ph.getSearchGroups(item, 'href=[\'"]([^"^\']+?)[\'"]')[0])
                    if not self.cm.isValidUrl(url):
                        continue
                    if 'online-sorozatok' in url:
                        tumd = 'series'
                    else:
                        tumd = 'movie'
                    title = self.cm.ph.getSearchGroups(item, '<a title=[\'"]([^"^\']+?)[\'"]')[0].strip()
                    if title == '': continue
                    icon = self.cm.ph.getSearchGroups(item, 'src=[\'"]([^"^\']+?)[\'"]')[0].strip()
                    tmp_ny = self.cm.ph.getDataBeetwenMarkers(item, '<img src=', '>')[1]
                    nyelv = self.cm.ph.getSearchGroups(tmp_ny, 'title=[\'"]([^"^\']+?)[\'"]')[0].strip()
                    if nyelv == '': nyelv = ' '
                    kev = self.cm.ph.getDataBeetwenMarkers(item, "<div class='mid-2'>(", ")<", False)[1]
                    if kev == '': kev = ' '
                    desc = nyelv + '\nKiadás éve:  ' + kev
                    db += 1
                    params = MergeDicts(cItem, {'category':'explore_item', 'title':title, 'url':url, 'desc':desc, 'icon':icon, 'nylv':nyelv, 'md':tumd})
                    self.addDir(params)
                    if db > 60:
                        break
        except Exception:
            return

    def getFavouriteData(self, cItem):
        params = {'type':cItem['type'], 'category':cItem.get('category', ''), 'title':cItem['title'], 'url':cItem['url'], 'desc':cItem['desc'], 'icon':cItem['icon']}
        return json_dumps(params) 
  
    def suskrbt(self, i_md='', i_hgk='', i_mpsz=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzwbywERxYklKkl5BRgEAD/4T/Q=='))
        try:
            if i_mpsz != '' and len(i_mpsz) > 1:
                if len(i_mpsz) > 80:
                    i_mpsz = i_mpsz[:78]
                i_mpsz = base64.b64encode(i_mpsz).replace('\n', '').strip()
                if i_hgk != '':
                    i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                    pstd = {'md':i_md, 'hgk':i_hgk, 'mpsz':i_mpsz}
                    if i_md != '' and i_hgk != '' and i_mpsz != '':
                        sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
            
    def susmrgts(self, i_md='', i_hgk='', i_mptip='', i_mpu='', i_mpt='', i_mpi='', i_mpdl='', i_mpnzs=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzy0tSQQTxYklKUl6BRkFABGoFBk='))
        try:
            if i_hgk != '': i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
            if i_mptip != '': i_mptip = base64.b64encode(i_mptip).replace('\n', '').strip()
            if i_mpu != '': i_mpu = base64.b64encode(i_mpu).replace('\n', '').strip()
            if i_mpt != '': i_mpt = base64.b64encode(i_mpt).replace('\n', '').strip()
            if i_mpi == '':
                i_mpi = base64.b64encode('-')
            else:
                i_mpi = base64.b64encode(i_mpi).replace('\n', '').strip()
            if i_mpdl == '':
                i_mpdl = base64.b64encode('-')
            else:
                i_mpdl = base64.b64encode(i_mpdl).replace('\n', '').strip()
            if i_mpnzs != '': i_mpnzs = base64.b64encode(i_mpnzs).replace('\n', '').strip()
            pstd = {'md':i_md, 'hgk':i_hgk, 'mptip':i_mptip, 'mpu':i_mpu, 'mpt':i_mpt, 'mpi':i_mpi, 'mpdl':i_mpdl, 'mpnzs':i_mpnzs}
            if i_md != '' and i_hgk != '' and i_mptip != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
    
    def getdvdsz(self, pu='', psz=''):
        bv = ''
        if pu != '' and psz != '':
            n_atnav = self.malvadst('1', '14', pu)
            if n_atnav != '' and self.aid:
                if pu == 'nonstopmozi_filmek':
                    self.aid_ki = 'ID: ' + n_atnav + '  |  NonstopMozi  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = 'ID: ' + n_atnav + '\n'
            else:
                if pu == 'nonstopmozi_filmek':
                    self.aid_ki = 'NonstopMozi  v' + HOST_VERSION + '\n'
                else:
                    self.aid_ki = ''
            bv = self.aid_ki + psz
        return bv
        
    def malvadst(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu}
        t_s = ''
        temp_vn = ''
        temp_vni = ''
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a_div', '</div>')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '/>')
                if len(data) == 0: return t_s
                for item in data:
                    t_i = self.cm.ph.getSearchGroups(item, 'id=[\'"]([^"^\']+?)[\'"]')[0]
                    if t_i == 'vn':
                        temp_vn = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                    elif t_i == 'vni':
                        temp_vni = self.cm.ph.getSearchGroups(item, 'value=[\'"]([^"^\']+?)[\'"]')[0]
                if temp_vn != '':
                    t_s = temp_vn
            return t_s
        except Exception:
            return t_s
            
    def malvadnav(self, cItem, i_md='', i_hgk='', i_mptip='', i_mpdb=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzy0tSQQTxYklKUl6BRkFABGoFBk='))
        t_s = []
        try:
            if i_md != '' and i_hgk != '' and i_mptip != '':
                if i_hgk != '': i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                if i_mptip != '': i_mptip = base64.b64encode(i_mptip).replace('\n', '').strip()
                if i_mpdb != '': i_mpdb = base64.b64encode(i_mpdb).replace('\n', '').strip()
                pstd = {'md':i_md, 'hgk':i_hgk, 'mptip':i_mptip, 'mpdb':i_mpdb}
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
                if not sts: return t_s
                if len(data) == 0: return t_s
                data = self.cm.ph.getDataBeetwenMarkers(data, '<div id="div_a1_div"', '<div id="div_a2_div"')[1]
                if len(data) == 0: return t_s
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div class="d_sor_d"', '</div>')
                if len(data) == 0: return t_s
                for temp_item in data:
                    temp_data = self.cm.ph.getAllItemsBeetwenMarkers(temp_item, '<span', '</span>')
                    if len(temp_data) == 0: return t_s
                    for item in temp_data:
                        t_vp = self.cm.ph.getSearchGroups(item, 'class=[\'"]([^"^\']+?)[\'"]')[0]
                        if t_vp == 'c_sor_u':
                            temp_u = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_u">', '</span>', False)[1]
                            if temp_u != '': temp_u = base64.b64decode(temp_u)
                        if t_vp == 'c_sor_t':
                            temp_t = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_t">', '</span>', False)[1]
                            if temp_t != '': temp_t = base64.b64decode(temp_t)
                        if t_vp == 'c_sor_i':
                            temp_i = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_i">', '</span>', False)[1]
                            if temp_i != '': temp_i = base64.b64decode(temp_i)
                        if t_vp == 'c_sor_l':
                            temp_l = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_l">', '</span>', False)[1]
                            if temp_l != '': temp_l = base64.b64decode(temp_l)
                        if t_vp == 'c_sor_n':
                            temp_n = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_n">', '</span>', False)[1]
                            if temp_n != '': temp_n = base64.b64decode(temp_n)
                        if t_vp == 'c_sor_tip':
                            temp_tp = self.cm.ph.getDataBeetwenMarkers(item, '<span class="c_sor_tip">', '</span>', False)[1]
                            if temp_tp != '': temp_tp = base64.b64decode(temp_tp)
                    if temp_u == '' and temp_t =='': continue
                    if temp_n == '': temp_n = '1'
                    params = MergeDicts(cItem, {'good_for_fav': True, 'url':temp_u, 'title':temp_t, 'icon':temp_i, 'desc':temp_l, 'nztsg':temp_n, 'tps':temp_tp})
                    t_s.append(params)       
            return t_s
        except Exception:
            return []
            
    def susn(self, i_md='', i_hgk='', i_mpu=''):
        uhe = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUL04sSdQvS8wD0ilJegUZBQD8FROZ'))
        pstd = {'md':i_md, 'hgk':i_hgk, 'mpu':i_mpu, 'hv':self.vivn, 'orv':self.porv, 'bts':self.pbtp}
        try:
            if i_md != '' and i_hgk != '' and i_mpu != '':
                sts, data = self.cm.getPage(uhe, self.defaultParams, pstd)
            return
        except Exception:
            return
    
    def ebbtit(self):
        try:
            if '' == self.btps.strip() or '' == self.brdr.strip():
                msg = 'A Set-top-Box típusát és a használt rendszer (image) nevét egyszer meg kell adni!\n\nA kompatibilitás és a megfelelő használat miatt kellenek ezek az adatok a programnak.\nKérlek, a helyes működéshez a valóságnak megfelelően írd be azokat.\n\nA "HU Telepítő" keretrendszerben tudod ezt megtenni.\n\nKilépek és megyek azt beállítani?'
                ret = self.sessionEx.waitForFinishOpen(MessageBox, msg, type=MessageBox.TYPE_YESNO, default=True)
                return False
            else:
                return True
        except Exception:
            return False
    
    def gits(self):
        bv = '-'
        tt = []
        try:
            if fileExists(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE'))):
                fr = open(zlib.decompress(base64.b64decode('eJzTTy1J1s8sLi5NBQATXQPE')),'r')
                for ln in fr:
                    ln = ln.rstrip('\n')
                    if ln != '':
                        tt.append(ln)
                fr.close()
                if len(tt) == 1:
                    bv = tt[0].strip()[:-6].capitalize()
                if len(tt) == 2:
                    bv = tt[1].strip()[:-6].capitalize()
            return bv
        except:
            return '-'
            
    def malvadkrttmk(self, i_md='', i_hgk=''):
        bv = []
        ukszrz = zlib.decompress(base64.b64decode('eJzLKCkpsNLXLy8v10vLTK9MzclNrSpJLUkt1sso1c9IzanUzwbywERxYklKkl5BRgEAD/4T/Q=='))
        try:
            if i_md != '' and i_hgk != '':
                i_hgk = base64.b64encode(i_hgk).replace('\n', '').strip()
                pstd = {'md':i_md, 'hgk':i_hgk}
                sts, data = self.cm.getPage(ukszrz, self.defaultParams, pstd)
                if not sts: return []
                if len(data) == 0: return []
                data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<div>', '</div>', False)
                if len(data) == 0: return []
                for item in data:
                    if item != '':
                        bv.append(base64.b64decode(item))
            return bv
        except Exception:
            return []
        
    def Vdakstmk(self, baseItem={'name': 'history', 'category': 'search'}, desc_key='plot', desc_base=(_("Type: ")), tabID='' ):
        if tabID != '':
            self.susn('2', '14', tabID)
            
        def _vdakstmk(data,lnp=50):
            ln = 0
            for histItem in data:
                plot = ''
                try:
                    ln += 1
                    if type(histItem) == type({}):
                        pattern = histItem.get('pattern', '')
                        search_type = histItem.get('type', '')
                        if '' != search_type: plot = desc_base + _(search_type)
                    else:
                        pattern = histItem
                        search_type = None
                    params = dict(baseItem)
                    params.update({'title': pattern, 'search_type': search_type,  desc_key: plot, 'tps':'0'})
                    self.addDir(params)
                    if ln >= lnp:
                        break
                except Exception: return
            
        try:
            list = self.malvadkrttmk('1','14')
            if len(list) > 0:
                _vdakstmk(list,2)
            if len(list) > 0:
                list = list[2:]
                random.shuffle(list)
                _vdakstmk(list,48)
        except Exception:
            return
    
    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)
        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        mode     = self.currItem.get("mode", '')
        self.currList = []
        if name == None:
            self.listMainMenu( {'name':'category'} )
        elif category == 'list_movies':
            self.listMovies(self.currItem, 'list_items')
        elif category == 'list_series':
            self.listSeries(self.currItem, 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem, 'explore_item')
        elif category == 'explore_item':
            self.exploreItem(self.currItem)
        elif category == 'list_main':
            self.listMainItems(self.currItem)
        elif category == 'list_third':
            self.listThirdItems(self.currItem)
        elif category in ["search", "search_next_page"]:
            if self.currItem['tab_id'] == 'nonstopmozi_kereses':
                self.susn('2', '14', 'nonstopmozi_kereses')
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'})
            self.listSearchResult(cItem, searchPattern, searchType)
        elif category == "search_history":
            if self.currItem['tab_id'] == 'nonstopmozi_kereses_elozmeny':
                self.susn('2', '14', 'nonstopmozi_kereses_elozmeny')
            self.listsHistory({'name':'history', 'category': 'search', 'tab_id':'', 'tps':'0'}, 'desc', _("Type: "))
        else:
            return
        CBaseHostClass.endHandleService(self, index, refresh)

class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, NonstopMozi(), True, [])
        
    def withArticleContent(self, cItem):
        if (cItem['type'] != 'video' and cItem['category'] != 'explore_item'):
            return False
        return True
