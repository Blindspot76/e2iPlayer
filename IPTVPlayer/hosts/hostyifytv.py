# -*- coding: utf-8 -*-
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _, SetIPTVPlayerLastHostError
from Plugins.Extensions.IPTVPlayer.components.ihost import CHostBase, CBaseHostClass, CDisplayListItem, RetHost, CUrlItem, ArticleContent
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSearchHistoryHelper, remove_html_markup, GetLogoDir, GetCookieDir, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common, CParsingHelper
import Plugins.Extensions.IPTVPlayer.libs.urlparser as urlparser
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.jsinterp import JSInterpreter
###################################################

###################################################
# FOREIGN import
###################################################
from datetime import datetime
import string
import re
import urllib
import base64
try:    import json
except: import simplejson as json
from Components.config import config, ConfigSelection, ConfigYesNo, ConfigText, getConfigListEntry
###################################################

###################################################
# E2 GUI COMMPONENTS 
###################################################
from Plugins.Extensions.IPTVPlayer.components.asynccall import MainSessionWrapper
from Screens.MessageBox import MessageBox
###################################################

###################################################
# Config options for HOST
###################################################

def GetConfigList():
    optionList = []
    return optionList
###################################################


def gettytul():
    return 'yify.tv'

class YifyTV(CBaseHostClass):
    HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html'}
    AJAX_HEADER = dict(HEADER)
    AJAX_HEADER.update( {'X-Requested-With': 'XMLHttpRequest'} )
    MAIN_URL    = 'http://yify.tv/'
    SRCH_URL    = MAIN_URL + '?s='
    
    MAIN_CAT_TAB = [{'category':'list_items',            'title': _('Releases'),          'url':MAIN_URL+'files/releases/'                                                 },
                    {'category':'list_items',            'title': _('Popular'),           'url':MAIN_URL+'popular/'                                                        },
                    {'category':'list_items',            'title': _('Top +250'),          'url':MAIN_URL+'files/movies/?meta_key=imdbRating&orderby=meta_value&order=desc' },
                    {'category':'list_genres_filter',    'title': _('Genres'),            'url':MAIN_URL+'files/movies/'                                                   },
                    {'category':'list_languages_filter', 'title': _('Languages'),         'url':MAIN_URL+'languages/'                                                      },
                    {'category':'list_countries_filter', 'title': _('Countries'),         'url':MAIN_URL+'countries/'                                                      },
                    {'category':'search',                'title': _('Search'), 'search_item':True},
                    {'category':'search_history',        'title': _('Search history')} ]
 
    def __init__(self):
        CBaseHostClass.__init__(self, {'history':'YifyTV', 'cookie':'alltubetv.cookie'})
        self.filterCache = {}
        
    def _getFullUrl(self, url):
        if url.startswith('//'):
            return 'http:' + url
        if url.startswith('/'):
            url = url[1:]
        if 0 < len(url) and not url.startswith('http'):
            url =  self.MAIN_URL + url
        if not self.MAIN_URL.startswith('https://'):
            url = url.replace('https://', 'http://')
        return url

    def listsTab(self, tab, cItem, type='dir'):
        printDBG("YifyTV.listsTab")
        for item in tab:
            params = dict(cItem)
            params.update(item)
            params['name']  = 'category'
            if type == 'dir':
                self.addDir(params)
            else: self.addVideo(params)
            
    def fillFiltersCache(self):
        printDBG("YifyTV.fillFiltersCache")
        # Fill genres, years, orderby
        if 0 == len(self.filterCache.get('genres', [])):
            sts, data = self.cm.getPage(self.MAIN_URL + 'files/movies/')
            if sts:
                # genres
                genres = self.cm.ph.getDataBeetwenMarkers(data, '<select name="genre', '</select>', False)[1]
                genres = re.compile('<option[^>]+?value="([^"]+?)"[^>]*?>([^<]+?)</option>').findall(genres)
                self.filterCache['genres'] = []
                for item in genres:
                    value = item[0]
                    if value == 'Genre':
                        value = ''
                    self.filterCache['genres'].append({'title': self.cleanHtmlStr(item[1]), 'genre':value})
               
                # orderby
                orderby = self.cm.ph.getDataBeetwenMarkers(data, '<select id="orderby"', '</select>', False)[1]
                orderby = re.compile('<option[^>]+?value="([^"]+?)"[^>]*?>([^<]+?)</option>').findall(orderby)
                self.filterCache['orderby'] = []
                for item in orderby:
                    for val in [(_('descending'), '&order=desc'), (_('ascending'), '&order=asc')]:
                        self.filterCache['orderby'].append({'title': self.cleanHtmlStr(item[1]) + ' [%s]' % val[0], 'orderby':item[0]+val[1]})
                
                # years
                self.filterCache['years'] = [{'title': _('Any')}]
                year = datetime.now().year
                while year >= 1920:
                    self.filterCache['years'].append({'title': str(year), 'year':year})
                    year -= 1
                    
        if 0 == len(self.filterCache.get('languages', [])):
            sts, data = self.cm.getPage(self.MAIN_URL + 'languages/')
            if sts:
                #languages
                languages = self.cm.ph.getDataBeetwenMarkers(data, '<tbody><tr><td>', '</table>', False)[1]
                languages = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(languages)
                self.filterCache['languages'] = []
                for item in languages:
                    self.filterCache['languages'].append({'title': self.cleanHtmlStr(item[1]), 'url':self._getFullUrl(item[0])})
                    
        if 0 == len(self.filterCache.get('countries', [])):
            sts, data = self.cm.getPage(self.MAIN_URL + 'countries/')
            if sts:
                #countries
                countries = self.cm.ph.getDataBeetwenMarkers(data, '<tbody>', '</tbody>', False)[1]
                countries = re.compile('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>').findall(countries)
                self.filterCache['countries'] = []
                for item in countries:
                    self.filterCache['countries'].append({'title': self.cleanHtmlStr(item[1]), 'url':self._getFullUrl(item[0])})
                    
    def listFilters(self, cItem, filter, category):
        printDBG("YifyTV.listFilters")
        tab = self.filterCache.get(filter, [])
        if 0 == len(tab):
            self.fillFiltersCache()
            tab = self.filterCache.get(filter, [])
        cItem = dict(cItem)
        cItem['category'] = category
        self.listsTab(tab, cItem)
                    
    def listItems(self, cItem):
        printDBG("YifyTV.listItems")
        
        tmp     = cItem['url'].split('?')
        baseUrl = tmp[0]
        getArgs = []
        if 2 == len(tmp):
            getArgs.append(tmp[1])
        # page
        page = cItem.get('page', 1)
        if page > 1:
            baseUrl += 'page/%s/' % page
        # year
        if '' != cItem.get('year', ''):
            getArgs.append('years=%s' % cItem['year'])
        # genre
        if '' != cItem.get('genre', ''):
            getArgs.append('genre=%s' % cItem['genre'])
        # orderby
        if '' != cItem.get('orderby', ''):
            getArgs.append(cItem['orderby'])
        url = baseUrl + '?' + '&'.join(getArgs)
        
        sts, data = self.cm.getPage(url)
        if not sts: return 
        
        if ('/page/%s/' % (page + 1)) in data:
            nextPage = True
        else: nextPage = False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'var posts = {', '};', False)[1]
        try:
            data = byteify(json.loads('{' + data + '}'))
            for item in data['posts']:
                item['url']   = self._getFullUrl(item['link'])
                item['title'] = self.cleanHtmlStr(item['title'])
                item['desc']  = self.cleanHtmlStr(item['post_content'])
                item['icon']  = self._getFullUrl(item['image'])
                self.addVideo(item)
        except:
            printExc()
        
        if nextPage:
            params = dict(cItem)
            params.update( {'title':_('Next page'), 'page':page+1} )
            self.addDir(params)
        
    def listSearchResult(self, cItem, searchPattern, searchType):
        printDBG("YifyTV.listSearchResult cItem[%s], searchPattern[%s] searchType[%s]" % (cItem, searchPattern, searchType))
        
        currItem = dict(cItem)
        currItem['url'] = self.SRCH_URL + urllib.quote_plus(searchPattern)
        self.listItems(currItem)
        
    def unpackJS(self, data, name):
        data = data.replace('Math.min', 'min').replace(' + (', ' + str(').replace('String.fromCharCode', 'chr').replace('return b[a]', 'return saveGet(b, a)')
        def saveGet(b, a):
            try:
                return b[a]
            except:
                return 'pic'
        try:
            paramsAlgoObj = compile(data, '', 'exec')
        except:
            printExc('unpackJS compile algo code EXCEPTION')
            return ''
        vGlobals = {"__builtins__": None, 'string': string, 'str':str, 'chr':chr, 'decodeURIComponent':urllib.unquote, 'unescape':urllib.unquote, 'min':min, 'saveGet':saveGet}
        vLocals = { name: None }

        try:
            exec( data, vGlobals, vLocals )
        except:
            printExc('unpackJS exec code EXCEPTION')
            return ''
        try:
            return vLocals[name]
        except:
            printExc('decryptPlayerParams EXCEPTION')
        return ''
        
    def getLinksForVideo(self, cItem):
        printDBG("YifyTV.getLinksForVideo [%s]" % cItem)
        urlTab = []
        
        sts, data = self.cm.getPage(cItem['url'])
        if not sts: return urlTab
        
        #data = self.cm.ph.getSearchGroups(data, 'var[^"]*?parametros[^"]*?=[^"]*?"([^"]+?)"')[0]
        dat1 = self.cm.ph.getSearchGroups(data, '\}([^\{^\}]+?)var mouse_and_cat_playing_for_ever')[0].replace('var ', '')
        
        parametros = self.cm.ph.getDataBeetwenMarkers(data, 'var mouse_and_cat_playing_for_ever', ';', False)[1]
        data = self.cm.ph.getDataBeetwenMarkers(data, 'sourcesConfigMod', 'var mouse_and_cat_playing_for_ever', False)[1]
        
        globalTabCode = []
        tmp = re.compile('var([^;]+?)=[^;]*?(\[[^\]]+?\]);').findall(data)
        for item in tmp:
            var = item[0].strip()
            val = item[1].strip()
            if var == '': continue
            if val == '': continue
            globalTabCode.append('%s = %s' % (var, val))
        globalTabCode = '\n'.join( globalTabCode )
        
        data2 = data.split('\n')
        data = []
        for item in data2:
            if 'try{' in item: continue
            if '}catch' in item: continue
            data.append(item)
        data = '\n'.join(data)
        funData = re.compile('function ([^\(]*?\([^\)]*?\))[^\{]*?\{([^\{]*?)\}').findall(data)
        
        pyCode = ''
        for item in funData:
            funHeader = item[0]
            
            funBody = item[1]
            funIns = funBody.split(';')
            funBody = ''
            for ins in funIns:
                ins = ins.replace('var', ' ').strip()
                if len(ins) and ins[-1] not in [')', ']']:
                    ins += '()'
                funBody += '\t%s\n' % ins
            if '' == funBody.replace('\t', '').replace('\n', '').strip():
                continue
            pyCode += 'def %s:' % funHeader.strip() + '\n' + funBody
        
        pyCode = dat1.strip() + '\n' +  pyCode  + 'parametros ' + parametros.strip()
        pyCode = 'def retA():\n\t' + globalTabCode.replace('\n', '\n\t') + '\n' + pyCode.replace('\n', '\n\t') + '\n\treturn parametros\n' + 'param = retA()'
        #printDBG(pyCode)
        data = self.unpackJS(pyCode, 'param')
        #printDBG(pyCode)
        printDBG(data)
        
        subLangs = self.cm.ph.getSearchGroups(data, '&sub=([^&]+?)&')[0]
        subID    = self.cm.ph.getSearchGroups(data, '&id=(tt[^&]+?)&')[0]
        if subID == '':
            subID    = self.cm.ph.getSearchGroups(data, '&pic=(tt[^&]+?)&')[0]
        subLangs = subLangs.split(',')
        sub_tracks = []
        for lang in subLangs:
            if subID != '':
                sub_tracks.append({'title':lang, 'url':'http://yify.tv/player/bajarsub.php?%s_%s' % (subID, lang), 'lang':lang, 'format':'srt'})
        
        data = data.split('&')
        idx = 1
        for item in data:
            tmp = item.split('=')
            if len(tmp)!= 2: continue
            if tmp[1].endswith('enc'):
                url = strwithmeta(tmp[1], {'external_sub_tracks':sub_tracks})
                url.meta['Referer'] = cItem['url']
                url.meta['sou'] = tmp[0]
                urlTab.append({'name':_('Mirror') + ' %s' % idx, 'url':url, 'need_resolve':1})
                idx += 1
        return urlTab
        
    def getVideoLinks(self, baseUrl):
        printDBG("Movie4kTO.getVideoLinks [%s]" % baseUrl)
        urlTab = []
        sub_tracks = strwithmeta(baseUrl).meta.get('external_sub_tracks', [])
        
        header = dict(self.AJAX_HEADER)
        header['Referer'] = baseUrl.meta['Referer']
        post_data = {'fv':'18', 'url':baseUrl, 'sou':baseUrl.meta.get('sou', '')}
        url = self._getFullUrl('/player/pk/pk/plugins/player_p2.php')
        sts, data = self.cm.getPage(url, {'header':header}, post_data)
        if not sts: return []
        #printDBG(data)
        try:
            data = byteify(json.loads(data))
            for item in data:
                if item.get('type', '').startswith('video/') and item.get('url', '').startswith('http'):
                    urlTab.append({'name':'{0}x{1}'.format(item.get('height', ''), item.get('width', '')), 'url':item['url'], 'need_resolve':0})
        except:
            SetIPTVPlayerLastHostError('The Mirror is broken.\nIf available you can choose other source.')
            printExc()
        
        if False: 
            videoUrl = url
            if url.startswith('//'):
                videoUrl = 'http:' + videoUrl
            urlTab = self.up.getVideoLinkExt(videoUrl)
        for idx in range(len(urlTab)):
            urlTab[idx]['url'] = strwithmeta(urlTab[idx]['url'], {'external_sub_tracks':sub_tracks})
        
        return urlTab
        
    def getFavouriteData(self, cItem):
        return cItem['url']
        
    def getLinksForFavourite(self, fav_data):
        return self.getLinksForVideo({'url':fav_data})
        
    def getArticleContent(self, cItem):
        printDBG("MoviesHDCO.getArticleContent [%s]" % cItem)
        
        title = cItem['title']
        icon  = cItem['image']
        desc  = cItem['post_content']
        otherInfo = {}
        otherInfo['year']     = cItem['year']
        otherInfo['duration'] = cItem['runtime']
        otherInfo['genre']    = cItem['genre']
        otherInfo['director'] = cItem['director']
        otherInfo['actors']   = cItem['actors']
        return [{'title':self.cleanHtmlStr( title ), 'text': self.cleanHtmlStr( desc ), 'images':[{'title':'', 'url':self._getFullUrl(icon)}], 'other_info':otherInfo}]

    def handleService(self, index, refresh = 0, searchPattern = '', searchType = ''):
        printDBG('handleService start')
        
        CBaseHostClass.handleService(self, index, refresh, searchPattern, searchType)

        name     = self.currItem.get("name", '')
        category = self.currItem.get("category", '')
        printDBG( "handleService: |||||||||||||||||||||||||||||||||||| name[%s], category[%s] " % (name, category) )
        self.currList = []
        
    #MAIN MENU
        if name == None:
            self.listsTab(self.MAIN_CAT_TAB, {'name':'category'})
    #MOVIES
        elif category == 'list_countries_filter':
            self.listFilters(self.currItem, 'countries', 'list_genres_filter')
        elif category == 'list_languages_filter':
            self.listFilters(self.currItem, 'languages', 'list_genres_filter')
        elif category == 'list_genres_filter':
            self.listFilters(self.currItem, 'genres', 'list_year_filter')
        elif category == 'list_year_filter':
            self.listFilters(self.currItem, 'years', 'list_orderby_filter')
        elif category == 'list_orderby_filter':
            self.listFilters(self.currItem, 'orderby', 'list_items')
        elif category == 'list_items':
            self.listItems(self.currItem)
    #SEARCH
        elif category in ["search", "search_next_page"]:
            cItem = dict(self.currItem)
            cItem.update({'search_item':False, 'name':'category'}) 
            self.listSearchResult(cItem, searchPattern, searchType)
    #HISTORIA SEARCH
        elif category == "search_history":
            self.listsHistory({'name':'history', 'category': 'search'}, 'desc', _("Type: "))
        else:
            printExc()
        
        CBaseHostClass.endHandleService(self, index, refresh)
class IPTVHost(CHostBase):

    def __init__(self):
        CHostBase.__init__(self, YifyTV(), True, [CDisplayListItem.TYPE_VIDEO, CDisplayListItem.TYPE_AUDIO])

    def getLogoPath(self):
        return RetHost(RetHost.OK, value = [GetLogoDir('yifytvlogo.png')])
    
    def getLinksForVideo(self, Index = 0, selItem = None):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): return RetHost(retCode, value=retlist)
        
        urlList = self.host.getLinksForVideo(self.host.currList[Index])
        for item in urlList:
            retlist.append(CUrlItem(item["name"], item["url"], item['need_resolve']))

        return RetHost(RetHost.OK, value = retlist)
    # end getLinksForVideo
    
    def getResolvedURL(self, url):
        # resolve url to get direct url to video file
        retlist = []
        urlList = self.host.getVideoLinks(url)
        for item in urlList:
            need_resolve = 0
            retlist.append(CUrlItem(item["name"], item["url"], need_resolve))

        return RetHost(RetHost.OK, value = retlist)

    def getArticleContent(self, Index = 0):
        retCode = RetHost.ERROR
        retlist = []
        if not self.isValidIndex(Index): 
            return RetHost(retCode, value=retlist)

        cItem = self.host.currList[Index]
        if cItem.get('type') == 'video':
            hList = self.host.getArticleContent(cItem)
            for item in hList:
                title      = item.get('title', '')
                text       = item.get('text', '')
                images     = item.get("images", [])
                othersInfo = item.get('other_info', '')
                retlist.append( ArticleContent(title = title, text = text, images =  images, richDescParams = othersInfo) )
                retCode = RetHost.OK
        return RetHost(retCode, value = retlist)
    
    def converItem(self, cItem):
        hostList = []
        searchTypesOptions = [] # ustawione alfabetycznie
        #searchTypesOptions.append((_("Movies"), "movies"))
        #searchTypesOptions.append((_("Series"), "series"))
    
        hostLinks = []
        type = CDisplayListItem.TYPE_UNKNOWN
        possibleTypesOfSearch = None

        if 'category' == cItem['type']:
            if cItem.get('search_item', False):
                type = CDisplayListItem.TYPE_SEARCH
                possibleTypesOfSearch = searchTypesOptions
            else:
                type = CDisplayListItem.TYPE_CATEGORY
        elif cItem['type'] == 'video':
            type = CDisplayListItem.TYPE_VIDEO
        elif 'more' == cItem['type']:
            type = CDisplayListItem.TYPE_MORE
        elif 'audio' == cItem['type']:
            type = CDisplayListItem.TYPE_AUDIO
            
        if type in [CDisplayListItem.TYPE_AUDIO, CDisplayListItem.TYPE_VIDEO]:
            url = cItem.get('url', '')
            if '' != url:
                hostLinks.append(CUrlItem("Link", url, 1))
            
        title       =  cItem.get('title', '')
        description =  cItem.get('desc', '')
        icon        =  cItem.get('icon', '')
        
        return CDisplayListItem(name = title,
                                    description = description,
                                    type = type,
                                    urlItems = hostLinks,
                                    urlSeparateRequest = 1,
                                    iconimage = icon,
                                    possibleTypesOfSearch = possibleTypesOfSearch)
    # end converItem

    def getSearchItemInx(self):
        try:
            list = self.host.getCurrList()
            for i in range( len(list) ):
                if list[i]['category'] == 'search':
                    return i
        except:
            printDBG('getSearchItemInx EXCEPTION')
            return -1

    def setSearchPattern(self):
        try:
            list = self.host.getCurrList()
            if 'history' == list[self.currIndex]['name']:
                pattern = list[self.currIndex]['title']
                search_type = list[self.currIndex]['search_type']
                self.host.history.addHistoryItem( pattern, search_type)
                self.searchPattern = pattern
                self.searchType = search_type
        except:
            printDBG('setSearchPattern EXCEPTION')
            self.searchPattern = ''
            self.searchType = ''
        return
