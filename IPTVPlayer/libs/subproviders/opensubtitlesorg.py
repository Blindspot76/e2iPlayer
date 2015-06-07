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
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, iptv_system, RemoveDisallowedFilenameChars, rm
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
        params = [self.loginToken, title]
        self._methodCall(self._doSearchMovieCallback, "SearchMoviesOnIMDB", params)
    
    def _doSearchMovieCallback(self, sts, data):
        list = []
        for item in data:
            if 'title' in item and 'id' in item:
                list.append({'title':item['title'], 'private_data':item['id']})
        self.outerCallback(sts, list)
        
    def doSearchSubtitle(self, callback, imdbid, langItem):
        self.outerCallback = callback
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
        list = []
        for item in data:
            link = item.get('SubDownloadLink', '')
            if item.get('SubFormat', '') in self.subFormats and link.startswith('http') and link.endswith('.gz'):
                title = self._getSubtitleTitle(item)
                list.append({'title':title, 'private_data':item})
        self.outerCallback(sts, list)
        
    def doGetLanguages(self, callback, lang):
        if len(self.langsCache):
            self._doGetLanguagesCallback(True, self.langsCache)
            return
        
        self.outerCallback = callback
        self.defaultLanguage = lang
        subParams = [{'name':'sublanguageid', 'value':lang}]
        params = [self.loginToken, self._getArraryParam(subParams)]
        self._methodCall(self._doGetLanguagesCallback, "GetSubLanguages", params)
        
    def _doGetLanguagesCallback(self, sts, data):
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
        #if sts and len(list):
        #    self.langsCache = data
        self.outerCallback(sts, list)
        
    def doDowanloadSubtitle(self, callback, subItem, tmpDir, subDir):
        self.tmpData = {'subItem':subItem, 'tmpDir':tmpDir, 'subDir':subDir}
        self.outerCallback = callback
        
        params = {'User-Agent': OpenSubOrgProvider.USER_AGENT}
            
        url     = " '{0}' ".format(subItem['SubDownloadLink'])
        tmpFile = tmpDir + OpenSubOrgProvider.TMP_FILE_NAME
        self.filesToRemove.append(tmpFile)
        self.tmpData['tmpFile'] = tmpFile
        
        tmpFile = " '{0}' ".format(tmpFile)
        
        cmd = DMHelper.getBaseWgetCmd(params) + url + ' -O ' + tmpFile + ' > /dev/null 2>&1 '
        printDBG('doDowanloadSubtitle cmd[%s]' % cmd)

        self.iptv_sys = iptv_system(cmd, self._doDowanloadSubtitleCallback)
        
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
                    fileName = "{0}_{1}_0_{2}_{3}".format(title, subItem['ISO639'], subItem['IDSubtitle'], subItem['IDMovieImdb'])
                    fileName = self.tmpData['subDir'] + fileName + '.' + subItem['SubFormat']
                    try:
                        with open(fileName, 'w') as f:
                            f.write(data)
                    except: 
                        self.lastApiError = {'code':-999, 'message':_('write error')}
                        printExc()
                    sts = True
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
        
        
        
        
        
        
    