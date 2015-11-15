# -*- coding: utf-8 -*-

"""
Implementation of the opensubtitles.org api
@author samsamsam@o2.pl based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/vevo.py
@version 0.1

Download subtitles from OpenSubtitles.org
http://www.opensubtitles.org/upload

"""


###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, iptv_system, RemoveDisallowedFilenameChars, rm, GetDefaultLang, GetPolishSubEncoding, byteify
from Plugins.Extensions.IPTVPlayer.libs.pCommon import common
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import hex_md5
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import clean_html
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
###################################################

###################################################
# FOREIGN import
###################################################
from Components.config import config
from binascii import hexlify
import urllib
import math 
import random
import base64
import re
try:    import simplejson as json
except: import json

try:
    try: from cStringIO import StringIO
    except: from StringIO import StringIO 
    import gzip
except: pass

###################################################

def printDBG2(data):
    pass
    #printDBG("%s" % data)

class OpenSubOrgProvider:
    #USER_AGENT       = 'IPTVPlayer v1'
    NAPISY24_USER_AGENT = 'DMnapi 13.1.30'
    USER_AGENT       = 'Subliminal v0.3' #'OSTestUserAgent'
    HTTP_HEADER      = {'User-Agent':USER_AGENT, 'Accept':'gzip'}#, 'Accept-Language':'pl'}
    MAIN_URL         = 'http://api.opensubtitles.org/xml-rpc'
    #MAIN_URL         = 'https://api.opensubtitles.org/xml-rpc'
    
    TMP_FILE_NAME    = '.iptv_subtitles.org'
    
    
    def __init__(self):
        printDBG("OpenSubOrgProvider.__init__")
        self.cm = common()
        self.doInit()
        
    def doInit(self):
        self.cm.HEADER   = OpenSubOrgProvider.HTTP_HEADER
        self.lastApiError = {'code':0, 'message':''}
        
        self.loginToken = ''
        self.subFormats = ['srt', 'mpl']
        
        self.outerCallback   = None
        self._methodCallBack = None
        self.iptv_sys        = None
        
        self.login = ''
        self.langsCache = []
        self.defaultLanguage = 'en'
        self.tmpData = {}
        
        self.filesToRemove = []
        
    def cancelRequest(self):
        if None != self.iptv_sys: self.iptv_sys.terminate()
        
    def terminate(self):
        self.cancelRequest()
        self.doInit() # to eventually break circular references
        for item in self.filesToRemove:
            rm(item)
        
    def getName(self):
        return "OpenSubtitles.org"
        
    def getLastApiError(self):
        return self.lastApiError
        
    def doLogin(self, callback, login, password, lang='en'):
        self.outerCallback = callback
        self.tmpData = {}
        self.login = login
        params = [login, hex_md5(password), lang, OpenSubOrgProvider.USER_AGENT]
        self._methodCall(self.doLoginCallback, "LogIn", params)

    def doLoginCallback(self, sts, data):
        if sts:
            try:
                if ('' != self.login and self._checkStatus(data, 0)) or '' == self.login: 
                    self.loginToken = data[0]['token']
                else: sts = False
            except: sts = False
        self.outerCallback(sts)
        
    def doSearchMovie(self, callback, title):
        self.outerCallback = callback
        self.tmpData = {'title':title, 'list':[]}
        if GetDefaultLang() == 'pl':
            self._doSearchMovieNapisy24()
        else:
            self._RealDoSearchMovie()
            
    def _mapNapisy24Item(self, data):
        keys = ['id', 'title', 'altTitle', 'imdb', 'year', 'release', 'language', 'cd', 'time', 'size', 'fps', 'resolution', 'author', 'rating']
        private_data = {}
        for key in keys:
            private_data[key] = self.cm.ph.getDataBeetwenMarkers(data, '<%s>' % key, '</%s>' % key, False)[1]
        return private_data
    
    def _doSearchMovieNapisy24(self):
        params = {'User-Agent': self.NAPISY24_USER_AGENT, 'Referer':'http://napisy24.pl/'}
        query = 'title={0}'.format(urllib.quote(self.tmpData['title']))
        url     = "'http://napisy24.pl/libs/webapi.php?{0}'".format(query)
        cmd = DMHelper.getBaseWgetCmd(params) + url + ' -O - 2> /dev/null '
        printDBG('_doSearchMovieNapisy24 cmd[%s]' % cmd)
        self.iptv_sys = iptv_system(cmd, self._doSearchMovieNapisy24Callback)
    
    def _doSearchMovieNapisy24Callback(self, code, data):
        if code == 0:
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<subtitle>', '</subtitle>', False)
            imdbs = []
            for item in data:
                private_data = self._mapNapisy24Item(item)
                if private_data['imdb'] != '' and private_data['imdb'] not in imdbs:
                    imdbs.append(private_data['imdb'])
                    title = self._getSubtitleNapisy24Title(private_data)
                    self.tmpData['list'].append({'title':title, 'private_data':{'napisy_24':True, 'id':private_data['imdb'][2:], 'title':title}})
        self._RealDoSearchMovie()
        
    def _RealDoSearchMovie(self):
        params = [self.loginToken, self.tmpData['title']]
        self._methodCall(self._doSearchMovieCallback, "SearchMoviesOnIMDB", params)
    
    def _doSearchMovieCallback(self, sts, data):
        list = self.tmpData.get('list', [])
        for item in data:
            if 'title' in item and 'id' in item:
                list.append({'title':item['title'], 'private_data':{'id':item['id'], 'title':item['title']}})
        self.outerCallback(sts, list)
        
    def doGetItemType(self, callback, privateData):
        self.outerCallback = callback
        self.tmpData = {}
        self.itemTypeCache = {'type':'movie'}        
        url     = "'http://www.omdbapi.com/?i=tt{0}&plot=short&r=json'".format(privateData['id'])
        cmd = DMHelper.getBaseWgetCmd({}) + url + ' -O - 2> /dev/null '
        printDBG('doGetItemType cmd[%s]' % cmd)
        self.iptv_sys = iptv_system(cmd, self._doGetItemTypeCallback)
        
    def _doGetItemTypeCallback(self, code, data):
        sts = False
        itemType = 'movie'
        if code == 0:
            try:
                data = byteify(json.loads(data))
                if data["Type"] == 'series':
                    itemType = 'series'
                year = data["Year"][0:4]
                self.itemTypeCache = {'type':itemType, 'title':data["Title"], 'year':year}
                sts = True
            except:
                printExc()
                self.lastApiError = {'code':-999, 'message':_('json load error')}
        self.outerCallback(sts, itemType)
        
    def doGetEpisodes(self, callback, privateData):
        self.outerCallback = callback
        self.tmpData = {'private_data':privateData}
        
        year = self.itemTypeCache.get('year', '')
        if year != '':
            year = '&year=%s' % year
        else:
            year = ''
        
        url     = "'http://imdbapi.poromenos.org/js/?name={0}{1}'".format(urllib.quote(self.itemTypeCache.get('title', '')), year)
        cmd = DMHelper.getBaseWgetCmd({}) + url + ' -O - 2> /dev/null '
        printDBG('doGetEpisodes cmd[%s]' % cmd)
        self.iptv_sys = iptv_system(cmd, self._doGetEpisodesCallback)
        
    def _doGetEpisodesCallback(self, code, data):
        sts = False
        list = []
        if code == 0:
            try:
                data = byteify(json.loads(data))
                key, value = data.popitem()
                for item in value["episodes"]:
                    params = dict(self.tmpData['private_data'])
                    params.update({"season": item["season"], "episode_title":item["name"], "episode":item["number"]})
                    title = 's{0}e{1} {2}'.format(str(item["season"]).zfill(2), str(item["number"]).zfill(2), item['name'])
                    list.append({'title':title, 'private_data':params})
                sts = True
            except:
                printExc()
                self.lastApiError = {'code':-999, 'message':_('json load error 2')}
        self.tmpData = {}
        self.outerCallback(sts, list)
        
    def doSearchSubtitle(self, callback, privateData, langItem):       
        self.outerCallback = callback
        self.tmpData = {}
        if 'episode' in privateData and 'season' in privateData :
            self.tmpData = {'private_data':privateData, 'langItem':langItem}
            self.goGetEpisodeType(privateData)
        else:
            self.doSearchSubtitleNext(privateData, langItem)
            
    def goGetEpisodeType(self, privateData):
        url  = "'http://www.imdb.com/title/tt{0}/episodes/_ajax?season={1}'".format(privateData['id'], privateData['season'])
        grep =  '?ref_=ttep_ep{0}"'.format(privateData['episode'])
        grep = " | grep '{0}'".format(grep)
        cmd  = DMHelper.getBaseWgetCmd({}) + url + ' -O - 2>/dev/null ' + grep
        printDBG('doGetEpisodes cmd[%s]' % cmd)
        self.iptv_sys = iptv_system(cmd, self._goGetEpisodeTypeCallback)
        
    def _goGetEpisodeTypeCallback(self, code, data):
        privateData = self.tmpData['private_data']
        langItem    = self.tmpData['langItem']
        self.tmpData = {}
        if 0 == code:
            id = self.cm.ph.getSearchGroups(data, '/tt([0-9]+?)/')[0]
            if id != '': privateData['id'] = id
        self.doSearchSubtitleNext(privateData, langItem)
    
    def doSearchSubtitleNext(self, privateData, langItem):       
        if 'pol' == langItem.get('SubLanguageID', ''):
            imdbid = privateData['id']
            title  = privateData['title']
            # we will first check subttiles on napisy24.pl
            self.tmpData = {'langItem':langItem, 'imdbid':imdbid, 'title':title, 'list':[]}
            self._doSearchSubtitleNapisy24()
        else:
            self._realDoSearchSubtitle(privateData['id'], langItem)
            
    def _doSearchSubtitleNapisy24(self, type='imdb'):
        self.tmpData['type'] = type
        params = {'User-Agent': self.NAPISY24_USER_AGENT, 'Referer':'http://napisy24.pl/'}
        
        if type == 'imdb':
            query = 'imdb=tt{0}'.format(self.tmpData['imdbid'])
        else:
            query = 'title={0}'.format(urllib.quote(self.tmpData['title']))
        
        url     = "'http://napisy24.pl/libs/webapi.php?{0}'".format(query)
        cmd = DMHelper.getBaseWgetCmd(params) + url + ' -O - 2> /dev/null '
        printDBG('_doSearchSubtitleNapisy24Callback cmd[%s]' % cmd)
        self.iptv_sys = iptv_system(cmd, self._doSearchSubtitleNapisy24Callback)
            
    def _doSearchSubtitleNapisy24Callback(self, code, data):
        list = self.tmpData.get('list', [])
        if code == 0:
            printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            printDBG(data)
            printDBG('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
            keys = ['id', 'title', 'altTitle', 'imdb', 'year', 'release', 'language', 'cd', 'time', 'size', 'fps', 'resolution', 'author', 'rating']
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<subtitle>', '</subtitle>', False)
            for item in data:
                private_data = self._mapNapisy24Item(item)
                if private_data['id'] != '' and 'pl' == private_data['language']:
                    private_data['napisy_24'] = True
                    title = self._getSubtitleNapisy24Title(private_data)
                    self.tmpData['list'].append({'title':title, 'private_data':private_data})
        
        if 0 == len(self.tmpData['list']) and 'imdb' == self.tmpData.get('type', ''):
            self._doSearchSubtitleNapisy24('title')
        else:
            self._realDoSearchSubtitle(self.tmpData.get('imdbid', ''), self.tmpData.get('langItem', ''))
        
    def _getSubtitleNapisy24Title(self, item):
        title = '[Napisy24.pl] %s.%s.%s.' % (item.get('title', ''), item.get('altTitle', ''), item.get('year', ''))
        title += item.get('resolution', '')
        
        cd = item.get('cd', '1')
        title += ' CD[{0}]'.format(cd)
        
        time = item.get('time', '')
        if '' != time: title += ' [{0}]'.format(time)
        
        return RemoveDisallowedFilenameChars(title)
        
    def _realDoSearchSubtitle(self, imdbid, langItem):
        sublanguageid = langItem.get('SubLanguageID', '')
        subParams = [{'name':'sublanguageid', 'value':sublanguageid}, {'name':'imdbid', 'value':imdbid}]
        params = [self.loginToken, self._getArraryParam(subParams)]
        self._methodCall(self._doSearchSubtitleCallback, "SearchSubtitles", params)
        
    def _getSubtitleTitle(self, item):
        title = item.get('MovieReleaseName', '')
        if '' == title: title = item.get('SubFileName', '')
        if '' == title: title = item.get('MovieName', '')
        
        cdMax = item.get('SubSumCD', '1')
        cd    = item.get('SubActualCD', '1')
        if cdMax != '1': title += ' CD[{0}/{1}]'.format(cdMax, cd)
        
        lastTime = item.get('SubLastTS', '')
        if '' != lastTime: title += ' [{0}]'.format(lastTime)
        
        return RemoveDisallowedFilenameChars(title)
        
    def _doSearchSubtitleCallback(self, sts, data):
        list = self.tmpData.get('list', [])
        for item in data:
            link = item.get('SubDownloadLink', '')
            if item.get('SubFormat', '') in self.subFormats and link.startswith('http') and link.endswith('.gz'):
                title = self._getSubtitleTitle(item)
                list.append({'title':title, 'private_data':item})
        self.tmpData = {}
        self.outerCallback(sts, list)
        
    def doGetLanguages(self, callback, lang):        
        self.outerCallback = callback
        self.tmpData = {}
        self.defaultLanguage = lang
        if len(self.langsCache):
            self._dummyCall(self._doGetLanguagesCallback)
        else:
            subParams = [{'name':'sublanguageid', 'value':lang}]
            params = [self.loginToken, self._getArraryParam(subParams)]
            self._methodCall(self._doGetLanguagesCallback, "GetSubLanguages", params)
        
    def _doGetLanguagesCallback(self, sts, data):
        if '' == data and len(self.langsCache):
            data = self.langsCache
            sts  = True
        
        list = []
        defaultLanguageItem = {}
        for item in data:
            if 'LanguageName' in item and 'SubLanguageID' in item and 'ISO639' in item :
                if self.defaultLanguage !=  item['ISO639']:
                    list.append({'title':'{0} [{1}]'.format(item['LanguageName'], item['SubLanguageID']), 'private_data':item})
                else:
                    defaultLanguageItem = item
        if {} != defaultLanguageItem:
            list.insert(0, {'title':'{0} [{1}]'.format(defaultLanguageItem['LanguageName'], defaultLanguageItem['SubLanguageID']), 'private_data':defaultLanguageItem})
        if sts and len(list):
            self.langsCache = data
        self.outerCallback(sts, list)
        
    def doDowanloadSubtitle(self, callback, subItem, tmpDir, subDir):
        self.outerCallback = callback
        self.tmpData = {'subItem':subItem, 'tmpDir':tmpDir, 'subDir':subDir}
        # subItem === private_data
        
        tmpFile = tmpDir + OpenSubOrgProvider.TMP_FILE_NAME
        self.filesToRemove.append(tmpFile)
        self.tmpData['tmpFile'] = tmpFile
        tmpFile = " '{0}' ".format(tmpFile)
        
        if not subItem.get('napisy_24', False):
            params = {'User-Agent': OpenSubOrgProvider.USER_AGENT}
            url     = " '{0}' ".format(subItem['SubDownloadLink'])
            cmd = DMHelper.getBaseWgetCmd(params) + url + ' -O ' + tmpFile + ' > /dev/null 2>&1 '
            printDBG('doDowanloadSubtitle cmd[%s]' % cmd)
            self.iptv_sys = iptv_system(cmd, self._doDowanloadSubtitleCallback)
        else:
            tmpFileZip = self.tmpData['tmpFile'] + '.zip'
            self.tmpData['tmpFileZip'] = tmpFileZip
            self.filesToRemove.append(tmpFileZip)
            tmpFileZip = " '{0}' ".format(tmpFileZip)
            params = {'User-Agent': self.NAPISY24_USER_AGENT, 'Referer':'http://napisy24.pl/'}
            url     = "'http://napisy24.pl/run/pages/download.php?napisId={0}&typ=sr'".format(subItem['id'])
            cmd = DMHelper.getBaseWgetCmd(params) + url + ' -O ' + tmpFileZip + ' > /dev/null 2>&1 '
            printDBG('_doSearchSubtitleNapisy24Callback cmd[%s]' % cmd)
            self.iptv_sys = iptv_system(cmd, self._doDowanloadSubtitle24Callback)
        
    def _doDowanloadSubtitle24Callback(self, code, data):
        if 0 == code:
            tmpFileZip = self.tmpData['tmpFileZip']
            tmpFile    = self.tmpData['tmpFile']
            # unzip file
            cmd = "unzip -po '{0}' -x Napisy24.pl.url > '{1}' 2>/dev/null".format(tmpFileZip, tmpFile)
            self.iptv_sys = iptv_system(cmd, self._doUnzipSubtitle24Callback)
        else:
            self.lastApiError = {'code':code, 'message':_('Download subtitles error.\nwget error code[%d].') % code}
            self.outerCallback(False, '')
    
    def _doUnzipSubtitle24Callback(self, code, data):
        if 0 == code:
            # unzip file
            cmd = '%s "%s"' % (config.plugins.iptvplayer.uchardetpath.value, self.tmpData['tmpFile'])
            self.iptv_sys = iptv_system(cmd, self._doGetEncodingSubtitle24Callback)
        else:
            self.lastApiError = {'code':-999, 'message':_('unzip error - please check if utitlity unzip is available')}
            self.outerCallback(False, self.tmpData.get('tmpFileZip', ''))
            
    def _doGetEncodingSubtitle24Callback(self, code, data):
        encoding = data
        if 0 != code or 'unknown' in encoding:
            encoding = ''
        else:
            encoding = encoding.strip()
        
        if GetDefaultLang() == 'pl' and encoding == 'iso-8859-2':
            encoding = GetPolishSubEncoding(self.tmpData['tmpFile'])
        elif '' == encoding:
            encoding = 'utf-8'
        fileName = ''
        sts = False
        try:
            f = open(self.tmpData['tmpFile'])
            data = f.read()
            f.close()
            subItem = self.tmpData['subItem']
            try:
                data = data.decode(encoding).encode('UTF-8')
                title = self._getSubtitleNapisy24Title(subItem).replace('_', '.').replace('.srt', '').replace(' ', '.')
                match = re.search(r'[^.]', title)
                if match: title = title[match.start():]

                fileName = "{0}_{1}_0_{2}_{3}".format(title, 'pl', subItem['id'][2:], subItem['imdb'])
                fileName = self.tmpData['subDir'] + fileName + '.srt'
                try:
                    with open(fileName, 'w') as f:
                        f.write(data)
                    sts = True
                except: 
                    self.lastApiError = {'code':-999, 'message':_('write error')}
                    printExc()
            except:
                self.lastApiError = {'code':-999, 'message':_('decode error')}
                printExc()  
        except:
            self.lastApiError = {'code':-999, 'message':_('read error')}
            printExc()
        self.outerCallback(sts, fileName)
        
    def _doDowanloadSubtitleCallback(self, code, data):
        fileName = ''
        sts      = False
        if 0 == code:
            # uncompress
            try:
                f = gzip.open(self.tmpData['tmpFile'])
                data = f.read()
                f.close()
                subItem = self.tmpData['subItem']
                
                try: 
                    data = data.decode(subItem['SubEncoding']).encode('UTF-8')
                    title = self._getSubtitleTitle(subItem).replace('_', '.').replace('.'+subItem['SubFormat'], '').replace(' ', '.')
                    match = re.search(r'[^.]', title)
                    if match: title = title[match.start():]
    
                    fileName = "{0}_{1}_0_{2}_{3}".format(title, subItem['ISO639'], subItem['IDSubtitle'], subItem['IDMovieImdb'])
                    fileName = self.tmpData['subDir'] + fileName + '.' + subItem['SubFormat']
                    try:
                        with open(fileName, 'w') as f:
                            f.write(data)
                        sts = True
                    except: 
                        self.lastApiError = {'code':-999, 'message':_('write error')}
                        printExc()
                except: 
                    self.lastApiError = {'code':-999, 'message':_('decode error')}
                    printExc()
            except: 
                self.lastApiError = {'code':-999, 'message':_('gzip error')}
                printExc()
        else:
            self.lastApiError = {'code':code, 'message':_('Download subtitles error.\nwget error code[%d].') % code}
            
            
        printDBG("_doDowanloadSubtitleCallback >>>>>> sts[%r], fileName[%s]" % (sts, fileName))
        self.outerCallback(sts, fileName)
    
    def _getPage(self, callback, url, params={}, post_data=None):
        if 'User-Agent' not in params: params['User-Agent'] =OpenSubOrgProvider.USER_AGENT
        
        if None != post_data:
            post_data = " --post-data '{0}' ".format(post_data)
        else: post_data = ''
            
        url = " '{0}' ".format(url)
        cmd = DMHelper.getBaseWgetCmd(params) + post_data + url + ' -O - 2> /dev/null'

        self.iptv_sys = iptv_system(cmd, callback)
    
    def _resp2Json(self, data):
        retJson = []
        
        stage = 'none'
        tagsStack = []
        tagName   = ''
        startTag  = False
        endTag    = False
        codingTag = False
        
        value = None
        name  = None
        obj = {}
        
        for idx in range(len(data)):
            it = data[idx]
            if it == '<':
                if stage in ['text', 'none']: 
                    stage = 'tag'
                    tagName   = ''
                    startTag  = False
                    endTag    = False
                    codingTag = False
                else: 
                    raise BaseException("Not expected < stage[%s] idx[%d]\n========================%s\n" % (stage, idx, data[idx:]))
            elif 'tag' == stage:
                if True not in [startTag, endTag, codingTag]:
                    if '/' == it:
                        endTag = True
                    elif '?' == it:
                        codingTag = True
                    else:
                        startTag = True
                        tagName = it
                else:
                    if '>' == it:
                        if startTag:
                            if 0 == len(tagName): 
                                raise BaseException("Empty tag name detected")
                            tagsStack.append(tagName)
                            text = ''
                            if  '/' != tagName[-1]:
                                stage = 'text'
                                continue
                            else:
                                endTag = True
                        if endTag:
                            if tagName != tagsStack[-1]: 
                                raise BaseException("End not existing start tag [%s][%s]" % (tagName, tagsStack[-1]))
                            del tagsStack[-1]
                            #printDBG("[%s]" % tagName)
                            if tagName == 'name':
                                name  = text
                            elif tagName == 'value':
                                value  = text
                            elif 'double' == tagName:
                                text = float(text)
                            elif 'member' == tagName:
                                if name != None:
                                    obj[name] = value
                                    name  = None
                                    value = None
                            elif 'struct' == tagName:
                                retJson.append(obj)
                                obj = {}
                        stage = 'none'
                    else:
                        tagName += it
                        
            elif 'text' == stage:
                text += it
                
        if 0 != len(tagsStack): 
            raise BaseException("Some tags have not been ended")
        return retJson
    
    def _dummyCall(self, callback):
        self._methodCallBack = callback
        cmd = 'sleep 0 > > /dev/null 2>&1'
        self.iptv_sys = iptv_system(cmd, callback)
        
    def _dummyCallback(self, code, data):
        self._methodCallBack(code, data)
        
    def _methodCall(self, callback, method, paramsList=[]):
        self._methodCallBack = callback
        
        requestData = "<methodCall><methodName>{0}</methodName><params>".format(method)
        for item in paramsList:
            requestData += "<param>"
            requestData += "<value>"
            if item.startswith('<'):
                requestData += item
            else:
                requestData += "<string>{0}</string>".format(item)
            requestData += "</value>"
            requestData += "</param>"
        requestData += "</params></methodCall>"
        
        printDBG("_methodCall requestData[%s]" % requestData)
        self._getPage(self._getPagCallback, OpenSubOrgProvider.MAIN_URL, {}, requestData)
        
    def _getPagCallback(self, code, data):
        sts = False
        if 0 == code:
            #printDBG2(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            #printDBG2(data)
            #printDBG2("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
            try:
                data = self._resp2Json(data)
                printDBG2(data)
                sts = True
            except: 
                printExc()
                data = {}
                sts = False
        else:
            data = {}
        self._methodCallBack(sts, data)
        
    def _serializeValue(self, item):
        param = '<value>'
        if isinstance(item, float):
            param += '<double>{0}</double>'.format(item)
        elif isinstance(item, str):
            param += '<string>{0}</string>'.format(item)
        param += '</value>'
        return param
        
    def _getArraryParam(self, array=[]):
        param = '<array><data><value><struct>'
        for item in array:
            param += '<member>'
            param += '<name>{0}</name>'.format(item['name'])
            param += self._serializeValue(item['value'])
            param += '</member>'
        param += '</struct></value></data></array>'
        return param
        
    def _checkStatus(self, data, idx=None):
        try:
            if None == idx:
                for idx in range(len(data)):
                    if 'status' in data[idx]:
                        item = data[idx]
                        break
            else: item = data[idx]
            code = int(item['status'].split(' ')[0])
            if code >= 200 and code < 300: return True
            self.lastApiError = {'code':code, 'message':item['status']}
            
        except:
            printExc()
            self.lastApiError = {'code':-999, 'message':_('_checkStatus except error')}
        return False
        
        
    '''
    def logOut(self):
        printDBG("OpenSubOrgProvider.logOut")
        params = [self.loginToken]
        sts, data = self._methodCall("LogOut", params)
        if not sts or not self._checkStatus(data, 0): return False
        return sts
    
    def noOperation(self):
        printDBG("OpenSubOrgProvider.noOperation user")
        params = [self.loginToken]
        sts, data = self._methodCall("NoOperation", params)
        if not sts or not self._checkStatus(data, 0): return False
        return sts
    '''
        
        
        
        
        
        
    