﻿# -*- coding: utf-8 -*-
# Modified by Blindspot # 2022.02.14.
###################################################
# LOCAL import
###################################################
from pCommon import common, CParsingHelper
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import SetIPTVPlayerLastHostError, GetIPTVSleep
from Plugins.Extensions.IPTVPlayer.tools.iptvtypes import strwithmeta
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, CSelOneLink, GetCookieDir, byteify, formatBytes, GetPyScriptCmd, GetTmpDir, rm, \
                                                          GetDefaultLang, GetFileSize, GetPluginDir, MergeDicts, GetJSScriptFile
from Plugins.Extensions.IPTVPlayer.libs.crypto.hash.md5Hash import MD5
from Plugins.Extensions.IPTVPlayer.libs import ph, recaptcha_v3

from Plugins.Extensions.IPTVPlayer.components.captcha_helper import CaptchaHelper

from Plugins.Extensions.IPTVPlayer.libs.recaptcha_v2 import UnCaptchaReCaptcha

from Plugins.Extensions.IPTVPlayer.libs.gledajfilmDecrypter import gledajfilmDecrypter
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes  import AES
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.aes_cbc import AES_CBC
from Plugins.Extensions.IPTVPlayer.libs.crypto.cipher.base import noPadding
from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.utils import unescapeHTML, clean_html
from Plugins.Extensions.IPTVPlayer.libs.urlparserhelper import unpackJSPlayerParams, unpackJS, \
                                                               JS_FromCharCode, \
                                                               JS_toString, \
                                                               VIDUPME_decryptPlayerParams,    \
                                                               SAWLIVETV_decryptPlayerParams,  \
                                                               TEAMCASTPL_decryptPlayerParams, \
                                                               VIDEOWEED_decryptPlayerParams, \
                                                               KINGFILESNET_decryptPlayerParams, \
                                                               captchaParser, \
                                                               getDirectM3U8Playlist, \
                                                               getMPDLinksWithMeta, \
                                                               getF4MLinksWithMeta, \
                                                               decorateUrl, \
                                                               int2base, drdX_fx, \
                                                               unicode_escape
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.components.asynccall import iptv_execute, MainSessionWrapper
from Plugins.Extensions.IPTVPlayer.tools.e2ijs import js_execute, js_execute_ext
from Plugins.Extensions.IPTVPlayer.libs.e2ijson import loads as json_loads, dumps as json_dumps
from Plugins.Extensions.IPTVPlayer.libs.demjson import decode as demjson_loads
from Plugins.Extensions.IPTVPlayer.libs.aadecode import decode as aadecode 
from Plugins.Extensions.IPTVPlayer.libs.powvideo import swapUrl as powvideo_swapUrl

from Screens.MessageBox import MessageBox
###################################################
# FOREIGN import
###################################################
import re
import time
import urllib
import string
import codecs
import base64
import math

from xml.etree import cElementTree
from random import random, randint, randrange, choice as random_choice
from urlparse import urlparse, urlunparse, parse_qs, parse_qsl
from binascii import hexlify, unhexlify, a2b_hex
from hashlib import md5, sha256
from Components.config import config

from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.mtv import GametrailersIE
try:    
    from urlparse import urlsplit, urlunsplit, urljoin
except Exception: 
    printExc()
###################################################

def InternalCipher(data, encrypt=True):
    tmp = sha256('|'.join(GetPluginDir().split('/')[-2:])).digest()
    key = tmp[:16]
    iv  = tmp[16:]
    cipher = AES_CBC(key=key, keySize=16)
    if encrypt:
        return cipher.encrypt(data, iv)
    else:
        return cipher.decrypt(data, iv)

class urlparser:
    def __init__(self):
        self.cm = common()
        self.pp = pageParser()
        self.setHostsMap()
        
    @staticmethod
    def getDomain(url, onlyDomain=True):
        parsed_uri = urlparse( url )
        if onlyDomain:
            domain = '{uri.netloc}'.format(uri=parsed_uri)
        else:
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
        return domain
    
    @staticmethod
    def decorateUrl(url, metaParams={}):
        return decorateUrl(url, metaParams)
        
    @staticmethod
    def decorateParamsFromUrl(baseUrl, overwrite=False):
        printDBG("urlparser.decorateParamsFromUrl ---> %s" % baseUrl)
        tmp        = baseUrl.split('|')
        baseUrl    = strwithmeta(tmp[0].strip(), strwithmeta(baseUrl).meta)
        KEYS_TAB = list(DMHelper.HANDLED_HTTP_HEADER_PARAMS)
        KEYS_TAB.extend(["iptv_audio_url", "iptv_proto", "Host", "Accept", "MPEGTS-Live", "PROGRAM-ID"])
        if 2 == len(tmp):
            baseParams = tmp[1].strip()
            try:
                params  = parse_qs(baseParams)
                printDBG("PARAMS FROM URL [%s]" % params)
                for key in params.keys():
                    if key not in KEYS_TAB: continue
                    if not overwrite and key in baseUrl.meta: continue
                    try: baseUrl.meta[key] = params[key][0]
                    except Exception: printExc()
            except Exception: printExc()
        baseUrl= urlparser.decorateUrl(baseUrl)
        return baseUrl

    def preparHostForSelect(self, v, resolveLink = False):
        valTab = []
        i = 0
        if len(v) > 0:
            for url in (v.values() if type(v) is dict else v):
                if 1 == self.checkHostSupport(url):
                    hostName = self.getHostName(url, True)
                    i=i+1
                    if resolveLink:
                        url = self.getVideoLink( url )
                    if isinstance(url, basestring) and url.startswith('http'):
                        valTab.append({'name': (str(i) + '. ' + hostName), 'url': url})
        return valTab

    def getItemTitles(self, table):
        out = []
        for i in range(len(table)):
            value = table[i]
            out.append(value[0])
        return out

    def setHostsMap(self):
        self.hostMap = {
                       '1fichier.com':          self.pp.parser1FICHIERCOM   ,
                       '1tv.ru':                self.pp.parser1TVRU         ,
                       '2021dogecoin.xyz':      self.pp.parserTXNEWSNETWORK ,
                       '37.220.36.15':          self.pp.parserMOONWALKCC    ,
                       '4snip.pw':              self.pp.parser4SNIP         ,
                       '7cast.net':             self.pp.parser7CASTNET      ,
                       'abcast.biz':            self.pp.parserABCASTBIZ     ,
                       'abcast.net':            self.pp.parserABCASTBIZ     ,
                       'abcvideo.cc':           self.pp.parserABCVIDEO      ,
                       'aflamyz.com':           self.pp.parserAFLAMYZCOM    ,
                       'akvideo.stream':        self.pp.parserAKVIDEOSTREAM ,
                       'albfilm.com':           self.pp.parserALBFILMCOM    ,
                       'aliez.me':              self.pp.parserALIEZME       ,
                       'allcast.is':            self.pp.parserALLCASTIS     ,
                       'allmyvideos.net':       self.pp.parserALLMYVIDEOS   ,
                       'allocine.fr':           self.pp.parserALLOCINEFR    ,
                       'allvid.ch':             self.pp.parserALLVIDCH      ,
                       'anime-shinden.info':    self.pp.parserANIMESHINDEN  ,
                       'anyvideo.org':          self.pp.parserONLYSTREAM    ,
                       'aparat.cam':            self.pp.parserONLYSTREAM    ,
                       'aparat.com':            self.pp.parserAPARAT        ,
                       'api.video.mail.ru':     self.pp.parserVIDEOMAIL     ,
                       'archive.org':           self.pp.parserARCHIVEORG    ,
                       'auroravid.to':          self.pp.parserAURORAVIDTO   ,
                       'backin.net':            self.pp.parserBACKIN,
                       'badutv.xyz':            self.pp.parserTXNEWSNETWORK ,
                       'bbc.co.uk':             self.pp.parserBBC           ,
                       'bestreams.net':         self.pp.parserBESTREAMS     ,
                       'biggestplayer.me':      self.pp.parserBIGGESTPLAYER ,
                       'bitvid.sx':             self.pp.parserVIDEOWEED     ,
                       'bojem3a.info':          self.pp.parserEXASHARECOM   ,
                       'bro.adca.st':           self.pp.parserBROADCAST      ,
                       'bro.adcast.tech':       self.pp.parserBROADCAST      ,
                       'brolel.net':            self.pp.parserTXNEWSNETWORK ,
                       'buckler.link':          self.pp.parserBUCKLER       ,
                       'byetv.org':             self.pp.parserBYETVORG       ,
                       'casacinema.cc':         self.pp.parserCASACINEMACC   ,
                       'cast4u.tv':             self.pp.parserCAST4UTV      ,
                       'castalba.tv':           self.pp.parserCASTALBATV    ,
                       'castamp.com':           self.pp.parserCASTAMPCOM    ,
                       'castasap.pw':           self.pp.parserCASTFLASHPW    ,
                       'castflash.pw':          self.pp.parserCASTFLASHPW    ,
                       'castfree.me':           self.pp.parserCASTFREEME     ,
                       'cricplay2.xyz':         self.pp.parserASSIAORG,
                       'caston.tv':             self.pp.parserCASTONTV       ,
                       'castto.me':             self.pp.parserCASTTOME      ,
                       'cda.pl':                self.pp.parserCDA           ,
                       'cercafilm.net':         self.pp.parserFEMBED        ,
                       'cfiles.net':            self.pp.parserUPLOAD         ,
                       'chefti.info':           self.pp.parserEXASHARECOM   ,
                       'clicknupload.link':     self.pp.parserUPLOAD         ,
                       'clicknupload.org':      self.pp.parserUPLOAD         ,
                       'clickopen.win':         self.pp.parserCLICKOPENWIN   ,
                       'clipwatching.com':      self.pp.parserCLIPWATCHINGCOM,
                       'cloud.mail.ru':         self.pp.parserCOUDMAILRU    ,
                       'cloudcartel.net':       self.pp.parserCLOUDCARTELNET ,
                       'cloudstream.us':        self.pp.parserCLOUDSTREAMUS  ,
                       'cloudtime.to':          self.pp.parserCLOUDTIME     ,
                       'cloudvideo.tv':         self.pp.parserCLOUDVIDEOTV   ,
                       'cloudy.ec':             self.pp.parserCLOUDYEC      ,
                       'cloudyfiles.me':        self.pp.parserUPLOAD         ,
                       'cloudyfiles.org':       self.pp.parserUPLOAD         ,
                       'cloudyvideos.com':      self.pp.parserCLOUDYVIDEOS  ,
                       'content.peteava.ro':    self.pp.parserPETEAVA       ,
                       'coolcast.eu':           self.pp.parserCOOLCASTEU    ,
                       'crichd.tv':             self.pp.parserCRICHDTV      ,
                       'cryptodialynews.com':   self.pp.parserTXNEWSNETWORK , 
                       'daaidaij.com':          self.pp.parserMOONWALKCC    ,
                       'daclips.in':            self.pp.parserFASTVIDEOIN   ,
                       'dailymotion.com':       self.pp.parserDAILYMOTION   ,
                       'dailyuploads.net':      self.pp.parserUPLOAD2        ,
                       'darkomplayer.com':      self.pp.parserDARKOMPLAYER   ,
                       'deltatv.pw':            self.pp.parserDELTATVPW     ,
                       'divxpress.com':         self.pp.parserDIVEXPRESS    ,
                       'divxstage.eu':          self.pp.parserDIVXSTAGE     ,
                       'divxstage.to':          self.pp.parserDIVXSTAGE     ,
                       'donevideo.com':         self.pp.parserLIMEVIDEO     ,
                       'dood.re':               self.pp.parserDOOD          ,
                       'dood.cx':               self.pp.parserDOOD          ,
                       'dood.la':               self.pp.parserDOOD          ,
                       'dood.so':               self.pp.parserDOOD          ,
                       'dood.to':               self.pp.parserDOOD          ,
                       'dood.watch':            self.pp.parserDOOD          ,
                       'dood.ws':               self.pp.parserDOOD          ,
                       'dood.sh':               self.pp.parserDOOD          ,
                       'dood.pm':               self.pp.parserDOOD          ,
                       'dood.wf':               self.pp.parserDOOD          ,
                       'doodstream.com':        self.pp.parserDOOD          ,
                       'dotstream.tv':          self.pp.parserDOTSTREAMTV   ,
                       'droonws.xyz':           self.pp.parserTXNEWSNETWORK , 
                       'dwn.so':                self.pp.parserDWN           ,
                       'easyload.io':           self.pp.parserEASYLOAD      ,
                       'easyvid.org':           self.pp.parserEASYVIDORG    ,
                       'easyvideo.me':          self.pp.parserEASYVIDEOME   ,
                       'easysport2022.xyz':     self.pp.parserTXNEWSNETWORK ,
                       'ebd.cda.pl':            self.pp.parserCDA           ,
                       'educadegree.com':       self.pp.parserEDUCADEGREE,
                       'ekstraklasa.tv':        self.pp.parserEKSTRAKLASATV  ,
                       'emb.aliez.tv':          self.pp.parserALIEZ         ,
                       'embed.trilulilu.ro':    self.pp.parserTRILULILU     ,
                       'embed.mystream.to':     self.pp.parserMSTREAMICU,
                       'embedsb.com':           self.pp.parserSTREAMSB    ,
                       'embedsito.com':         self.pp.parserFEMBED,
                       'embeducaster.com':      self.pp.parserUCASTERCOM     ,
                       'estream.to':            self.pp.parserESTREAMTO     ,
                       'evoload.io':            self.pp.parserEVOLOADIO     ,
                       'exashare.com':          self.pp.parserEXASHARECOM   ,
                       'facebook.com':          self.pp.parserFACEBOOK      ,
                       'fastflash.pw':          self.pp.parserCASTFLASHPW    ,
                       'fastplay.cc':           self.pp.parserFASTPLAYCC     ,
                       'faststream.in':         self.pp.parserVIDSTREAM     ,
                       'fastvideo.in':          self.pp.parserFASTVIDEOIN   ,
                       'favoritegames.xyz':     self.pp.parserTXNEWSNETWORK ,
                       'fcdn.stream':           self.pp.parserFEMBED,
                       'fembed.com':            self.pp.parserFEMBED,
                       'fembed-hd.com':         self.pp.parserFEMBED,
                       'feurl.com':             self.pp.parserFEMBED,
                       'filecandy.net':         self.pp.parserFILECANDYNET   ,
                       'filecloud.io':          self.pp.parserFILECLOUDIO    ,
                       'filefactory.com':       self.pp.parserFILEFACTORYCOM ,
                       'filehoot.com':          self.pp.parserFILEHOOT      ,
                       'filemoon.to':           self.pp.parserONLYSTREAMTV,
                       'filemoon.sx':           self.pp.parserONLYSTREAMTV,
                       'filenuke.com':          self.pp.parserFILENUKE      ,
                       'fileone.tv':            self.pp.parserFILEONETV     ,
                       'filepup.net':           self.pp.parserFILEPUPNET    ,
                       'file-upload.com':       self.pp.parserFILEUPLOADCOM  ,
                       'filez.tv':              self.pp.parserFILEZTV        ,
                       'firedrive.com':         self.pp.parserFIREDRIVE     , 
                       'flashcast.pw':          self.pp.parserCASTFLASHPW    ,
                       'flashlive.pw':          self.pp.parserCASTFLASHPW    ,
                       'flashx.co':             self.pp.parserFLASHXTV      ,
                       'flashx.pw':             self.pp.parserFLASHXTV      ,
                       'flashx.tv':             self.pp.parserFLASHXTV      ,
                       'flashx.net':            self.pp.parserFLASHXTV      ,
                       'fplayer.info':          self.pp.parserFEMBED,
                       'freedisc.pl':           self.pp.parserFREEDISC      ,
                       'fxstream.biz':          self.pp.parserFXSTREAMBIZ   ,
                       'gametrailers.com':      self.pp.parserGAMETRAILERS  , 
                       'gamovideo.com':         self.pp.parserGAMOVIDEOCOM  ,
                       'gcloud.live':           self.pp.parserFEMBED        , 
                       'gdriveplayer.co':       self.pp.parserGDRIVEPLAYER  ,
                       'gdriveplayer.me':       self.pp.parserGDRIVEPLAYER  ,
                       'gdriveplayer.us':       self.pp.parserGDRIVEPLAYER  ,
                       'ginbig.com':            self.pp.parserGINBIG        ,
                       'gloria.tv':             self.pp.parserGLORIATV      ,
                       'gogoanime.to':          self.pp.parserGOGOANIMETO   ,
                       'goldvod.tv':            self.pp.parserGOLDVODTV     ,
                       'goodcast.co':           self.pp.parserGOODCASTCO    ,
                       'goodrtmp.com':          self.pp.parserGOODRTMP      ,
                       'google.com':            self.pp.parserGOOGLE        ,
                       'gorillavid.in':         self.pp.parserFASTVIDEOIN   ,
                       'gosafedomain.eu':       self.pp.parserSTREAMTAPE    ,
                       'gounlimited.to':        self.pp.parserGOUNLIMITEDTO  ,
                       'govod.tv':              self.pp.parserWIIZTV         ,
                       'haxhits.com':           self.pp.parserHAXHITSCOM     ,
                       'hdcast.info':           self.pp.parserHDCASTINFO    ,
                       'hdfilmstreaming.com':   self.pp.parserHDFILMSTREAMING,
                       'hdgo.cc':               self.pp.parserHDGOCC        ,
                       'hdgo.cx':               self.pp.parserHDGOCC        ,
                       'hdpass.online':         self.pp.parserHDPASSONLINE  ,
                       'hdplayer.casa':         self.pp.parserHDPLAYERCASA  ,
                       'hdthevid.online':       self.pp.parserHDVIDTV       ,
                       'hdvid.tv':              self.pp.parserHDVIDTV       ,
                       'hdvid.fun':             self.pp.parserHDVIDTV       ,
                       'highstream.tv':         self.pp.parserCLIPWATCHINGCOM,
                       'hlstester.com':         self.pp.parserHLSTESTER     ,
                       'hofoot.90minkora.com':  self.pp.parserVIUCLIPS      ,
                       'hofoot.allvidview.tk':  self.pp.parserVIUCLIPS      ,
                       'hofoot.koravidup.com':  self.pp.parserVIUCLIPS      ,
                       'hofoot.vidcrt.net':     self.pp.parserVIUCLIPS      ,
                       'hofoot.uprafa.com':     self.pp.parserVIUCLIPS      ,
                       'hqq.none':              self.pp.parserNETUTV         ,
                       'hqq.tv':                self.pp.parserNETUTV         ,
                       'hqq.to':                self.pp.parserNETUTV         ,
                       'hqq.watch':             self.pp.parserNETUTV         ,
                       'netu.wiztube.xyz':      self.pp.parserNETUTV         ,
                       'hxfile.co':             self.pp.parserONLYSTREAM     ,
                       'hxload.io':             self.pp.parserVIDBOMCOM      ,
                       'hydrax.net':            self.pp.parserONLYSTREAM     ,
                       'i.vplay.ro':            self.pp.parserVPLAY         ,
                       'ideoraj.ch':            self.pp.parserCLOUDYEC      ,
                       'indavideo.hu':          self.pp.parserINDAVIDEOHU    ,
                       'interia.tv':            self.pp.parserINTERIATV      ,
                       'jacvideo.com':          self.pp.parserJACVIDEOCOM    ,
                       'jawcloud.co':           self.pp.parserJAWCLOUDCO     ,
                       'jetload.net':           self.pp.parserJETLOAD       ,
                       'junkyvideo.com':        self.pp.parserJUNKYVIDEO    ,
                       'justupload.io':         self.pp.parserJUSTUPLOAD     ,
                       'kabab.lima-city.de':    self.pp.parserKABABLIMA     ,
                       'kingfiles.net':         self.pp.parserKINGFILESNET   ,
                       'kingvid.tv':            self.pp.parserKINGVIDTV      ,
                       'krakenfiles.com':       self.pp.parserKRAKENFILESCOM ,
                       'krask.xyz':             self.pp.parserWSTREAMVIDEO   ,
                       'leton.tv':              self.pp.parserDOTSTREAMTV   ,
                       'letwatch.us':           self.pp.parserLETWATCHUS    ,
                       'life-rtmp.com':         self.pp.parserLIFERTMP      ,
                       'limevideo.net':         self.pp.parserLIMEVIDEO     ,
                       'linkhub.icu':           self.pp.parserLINKHUB,
                       'litcun.net':            self.pp.parserTXNEWSNETWORK ,
                       'live.bvbtotal.de':      self.pp.parserLIVEBVBTOTALDE,
                       'liveall.tv':            self.pp.parserLIVEALLTV      ,
                       'liveleak.com':          self.pp.parserLIVELEAK      ,
                       'liveonlinetv247.info':  self.pp.parserLIVEONLINE247 ,
                       'liveonlinetv247.info':  self.pp.parserLIVEONLINETV247,
                       'liveonlinetv247.net':   self.pp.parserLIVEONLINE247 ,
                       'livestream.com':        self.pp.parserLIVESTREAMCOM,
                       'live-stream.tv':        self.pp.parserLIVESTRAMTV   ,
                       'livetvspecial.top':     self.pp.parserTXNEWSNETWORK ,
                       'lookhd.xyz':            self.pp.parserTXNEWSNETWORK ,
                       'lookmovie.ag' :         self.pp.parserLOOKMOVIE     ,
                       'm2list.com':            self.pp.parserM2LIST        ,
                       'm0.vidcloudpng.com':    self.pp.parserVIDCLOUD    ,
                       'mastarti.com':          self.pp.parserMOONWALKCC    ,
                       'matchat.online':        self.pp.parserMATCHATONLINE  ,
                       'maxupload.tv':          self.pp.parserTOPUPLOAD     ,
                       'mcloud.to':             self.pp.parserMYCLOUDTO     ,
                       'mcloud2.to':            self.pp.parserMYCLOUDTO     ,
                       'mediafire.com':         self.pp.parserMEDIAFIRECOM  ,
                       'mediasetplay.mediaset.it': self.pp.parserMEDIASET   ,
                       'megadrive.co':          self.pp.parserMEGADRIVECO    ,
                       'megadrive.tv':          self.pp.parserMEGADRIVETV    ,
                       'megom.tv':              self.pp.parserMEGOMTV        ,
                       'megustavid.com':        self.pp.parserMEGUSTAVID    ,
                       'melbil.net':            self.pp.parserTXNEWSNETWORK ,
                       'membed.net':            self.pp.parserMEMBED        ,
                       'mightyupload.com':      self.pp.parserMIGHTYUPLOAD  ,
                       'miplayer.net':          self.pp.parserMIPLAYERNET   ,
                       'mirrorace.com':         self.pp.parserMIRRORACE     ,
                       'mixdrop.bz':            self.pp.parserMIXDROP       ,
                       'mixdrop.co':            self.pp.parserMIXDROP       ,
                       'mixdrop.ch':            self.pp.parserMIXDROP       ,
                       'mixdrop.club':          self.pp.parserMIXDROP       ,
                       'mixdrop.to':            self.pp.parserMIXDROP       ,
                       'moevideo.net':          self.pp.parserPLAYEREPLAY   ,
                       'moonwalk.cc':           self.pp.parserMOONWALKCC    ,
                       'moshahda.net':          self.pp.parserMOSHAHDANET   ,
                       'movcloud.net':          self.pp.parserMOVCLOUD      ,
                       'movdivx.com':           self.pp.parserMODIVXCOM     ,
                       'movpod.in':             self.pp.parserFASTVIDEOIN   ,
                       'movreel.com':           self.pp.parserMOVRELLCOM    ,
                       'movshare.net':          self.pp.parserWHOLECLOUD    ,
                       'mp4upload.com':         self.pp.parserMP4UPLOAD     ,
                       'mstream.fun':           self.pp.parserMSTREAMICU    ,
                       'mstream.icu':           self.pp.parserMSTREAMICU    ,
                       'mstream.press':         self.pp.parserMSTREAMICU    ,
                       'mstream.website':       self.pp.parserMSTREAMICU    ,
                       'mstream.xyz':           self.pp.parserMSTREAMICU    ,
                       'multikland.net':        self.pp.parserMULTIKLAND,
                       'my.mail.ru':            self.pp.parserVIDEOMAIL     ,
                       'mycloud.to':            self.pp.parserMYCLOUDTO     ,
                       'mystream.la':           self.pp.parserMYSTREAMLA    ,
                       'mystream.to':           self.pp.parserMYSTREAMTO    ,
                       'mystream.press':        self.pp.parserMYSTREAMTO   ,
                       'mystream.nuovo-indirizzo.com':  self.pp.parserMSTREAMICU   ,
                       'premiumserver.club':    self.pp.parserMSTREAMICU    ,
                       'mystream.streamango.to': self.pp.parserMSTREAMICU   ,
                       'myvi.ru':               self.pp.parserMYVIRU        ,
                       'myvi.tv':               self.pp.parserMYVIRU        ,
                       'myvideo.de':            self.pp.parserMYVIDEODE     ,
                       'nadaje.com':            self.pp.parserNADAJECOM      ,
                       'neodrive.co':           self.pp.parserNEODRIVECO    ,
                       'netu.tv':               self.pp.parserNETUTV         ,
                       'netu.to':               self.pp.parserNETUTV         ,
                       'ninjastream.to':        self.pp.parserNINJASTREAMTO   ,
                       'nonlimit.pl':           self.pp.parserIITV          ,
                       'nosvideo.com':          self.pp.parserNOSVIDEO      ,
                       'novamov.com':           self.pp.parserNOVAMOV       ,
                       'nowlive.pw':            self.pp.parserNOWLIVEPW      ,
                       'nowlive.xyz':           self.pp.parserNOWLIVEPW      ,
                       'nowvideo.ch':           self.pp.parserNOWVIDEOCH    ,
                       'nowvideo.co':           self.pp.parserNOWVIDEO      ,
                       'nowvideo.eu':           self.pp.parserNOWVIDEO      ,
                       'nowvideo.sx':           self.pp.parserNOWVIDEO      ,
                       'nowvideo.to':           self.pp.parserNOWVIDEO      ,
                       'ntv.ru':                self.pp.parserNTVRU          ,
                       'nuovo-indirizzo.com':   self.pp.parserHDPLAYERCASA   ,
                       'nxload.com':            self.pp.parserNXLOADCOM      ,
                       'ok.ru':                 self.pp.parserOKRU          ,
                       'ocubel.net':            self.pp.parserTXNEWSNETWORK ,
                       'oload.cloud':           self.pp.parserOPENLOADIO    ,
                       'oload.co':              self.pp.parserOPENLOADIO    ,
                       'oload.download':        self.pp.parserOPENLOADIO    ,
                       'oload.io':              self.pp.parserOPENLOADIO    ,
                       'oload.site':            self.pp.parserOPENLOADIO    ,
                       'oload.stream':          self.pp.parserOPENLOADIO    ,
                       'oload.tv':              self.pp.parserOPENLOADIO    ,
                       'player.veuclips.com':   self.pp.parserVIUCLIPS     ,   
                       'player.streamkora.com': self.pp.parserVIUCLIPS     ,
                       'onet.pl':               self.pp.parserONETTV        ,
                       'onet.tv':               self.pp.parserONETTV        ,
                       'onlystream.tv':         self.pp.parserONLYSTREAM    ,    
                       'opendrive.top':         self.pp.parserOPENDRIVE     ,
                       'openlive.org':          self.pp.parserOPENLIVEORG   ,
                       'openload.co':           self.pp.parserOPENLOADIO    ,
                       'openload.info':         self.pp.parserEXASHARECOM   ,
                       'openload.io':           self.pp.parserOPENLOADIO    ,
                       'openloads.co':          self.pp.parserOPENLOADIO    ,
                       'ovva.tv':               self.pp.parserOVVATV         ,
                       'owndrives.com':         self.pp.parserUPLOAD         ,
                       'p2pcast.tv':            self.pp.parserP2PCASTTV      ,
                       'partners.nettvplus.com': self.pp.parserNETTVPLUSCOM,
                       'picasaweb.google.com':  self.pp.parserPICASAWEB     ,
                       'pipipopo.me':           self.pp.parserTXNEWSNETWORK ,
                       'player.m2list.com':     self.pp.parserM2LIST        ,
                       'playhydrax.com':        self.pp.parserPLAYHYDRAX,
                       'playbb.me':             self.pp.parserEASYVIDEOME   ,
                       'played.to':             self.pp.parserPLAYEDTO      ,
                       'playedto.me':           self.pp.parserPLAYEDTO      ,
                       'playpanda.net':         self.pp.parserPLAYPANDANET   ,
                       'playreplay.net':        self.pp.parserPLAYEREPLAY   ,
                       'playtube.ws':           self.pp.parserONLYSTREAM   ,
                       'playvid.org':           self.pp.parserEASYVIDORG    , 
                       'polbal.net':            self.pp.parserTXNEWSNETWORK ,
                       'polsatsport.pl':        self.pp.parserPOLSATSPORTPL  ,
                       'posiedze.pl':           self.pp.parserPOSIEDZEPL    ,
                       'powvideo.cc':           self.pp.parserPOWVIDEONET    ,
                       'powvideo.net':          self.pp.parserPOWVIDEONET    ,
                       'powv1deo.cc':           self.pp.parserPOWVIDEONET  ,
                       'premiertvlive.com':     self.pp.parserTXNEWSNETWORK ,
                       'primevideos.net':       self.pp.parserPRIMEVIDEOS,  
                       'privatestream.tv':      self.pp.parserPRIVATESTREAM ,
                       'promptfile.com':        self.pp.parserPROMPTFILE    ,
                       'protectlink.stream':    self.pp.parserFEMBED        ,
                       'publicvideohost.org':   self.pp.parserPUBLICVIDEOHOST,
                       'pumpnews.xyz':          self.pp.parserTXNEWSNETWORK ,
                       'putlive.in':            self.pp.parserPUTLIVEIN      ,
                       'putlocker.com':         self.pp.parserFIREDRIVE     , 
                       'putstream.com':         self.pp.parserPUTSTREAM     ,
                       'pxstream.tv':           self.pp.parserPXSTREAMTV    ,
                       'qfer.net':              self.pp.parserQFER          ,
                       'rapidcrypt.net':        self.pp.parserRAPIDCRYPT,
                       'rapidvideo.com':        self.pp.parserRAPIDVIDEO    ,
                       'rapidvideo.ws':         self.pp.parserRAPIDVIDEOWS  ,
                       'raptu.com':             self.pp.parserRAPTUCOM       ,
                       'realvid.net':           self.pp.parserFASTVIDEOIN   ,
                       'rutube.ru':             self.pp.parserRUTUBE        ,
                       'videovard.sx':          self.pp.parserVIDEOVARDSX   ,
                       'sawlive.tv':            self.pp.parserSAWLIVETV     ,
                       'sbfast.com':            self.pp.parserSTREAMSB    ,
                       'sbfull.com':            self.pp.parserSTREAMSB    ,
                       'sbplay.one':            self.pp.parserSTREAMSB    ,
                       'sbplay1.com':           self.pp.parserSTREAMSB    ,
                       'sbplay2.com':           self.pp.parserSTREAMSB    ,
                       'sbplay2.xyz':           self.pp.parserSTREAMSB    ,
                       'scs.pl':                self.pp.parserSCS           ,
                       'sendvid.com':           self.pp.parserSENDVIDCOM    ,
                       'seositer.com':          self.pp.parserYANDEX        ,
                       'serpens.nl':            self.pp.parserMOONWALKCC    ,
                       'sfdmn.eu':              self.pp.parserSTREAMTAPE       ,
                       'sfiles.org':            self.pp.parserUPLOAD         ,
                       'shared.sx':             self.pp.parserSHAREDSX      ,
                       'share-online.biz':      self.pp.parserSHAREONLINEBIZ ,
                       'sharerepo.com':         self.pp.parserSHAREREPOCOM   ,
                       'sharesix.com':          self.pp.parserFILENUKE      ,
                       'sharevideo.pl':         self.pp.parserSHAREVIDEOPL   ,
                       'sharing-box.cloud':     self.pp.parserSHAREVIDEOPL   ,
                       'shidurlive.com':        self.pp.parserSHIDURLIVECOM ,
                       'sockshare.com':         self.pp.parserSOCKSHARE     ,
                       'sonline.pro':           self.pp.parserFEMBED,
                       'sostart.org':           self.pp.parserSOSTARTORG    ,
                       'sostart.pw':            self.pp.parserSOSTARTPW     ,
                       'soundcloud.com':        self.pp.parserSOUNDCLOUDCOM  ,
                       'speedvid.net':          self.pp.parserSPEEDVIDNET    ,
                       'speedwatch.io':         self.pp.parserSPEEDWATCH    ,
                       'speedvideo.net':        self.pp.parserSPEEDVIDEONET  ,
                       'sportstream365.com':    self.pp.parserSPORTSTREAM365 ,
                       'sprocked.com':          self.pp.parserSPROCKED      ,
                       'spruto.tv':             self.pp.parserSPRUTOTV       ,
                       'srkcast.com':           self.pp.parserSRKCASTCOM    ,
                       'ssh101.com':            self.pp.parserSSH101COM     ,
                       'statics.mystream.to':   self.pp.parserMSTREAMICU    ,
                       'swzz.xyz':              self.pp.parserSWZZ,
                       'st.dwn.so':             self.pp.parserDWN           ,
                       'stayonline.pro':        self.pp.parserSTAYONLINE,
                       'stopbot.tk':            self.pp.parserSTOPBOTTK      ,
                       'stream.moe':            self.pp.parserSTREAMMOE      ,
                       'stream4k.to':           self.pp.parserSTREAM4KTO    ,
                       'streamable.com':        self.pp.parserSTREAMABLECOM  ,
                       'streamatus.tk':         self.pp.parserVIUCLIPS,
                       'streamango.com':        self.pp.parserSTREAMANGOCOM  ,
                       'streamcherry.com':      self.pp.parserSTREAMANGOCOM  ,
                       'streamcloud.eu':        self.pp.parserSTREAMCLOUD   ,
                       'streamcrypt.net':       self.pp.parserVCRYPT        ,
                       'streame.net':           self.pp.parserSTREAMENET    ,
                       'streamin.to':           self.pp.parserSTREAMINTO    ,
                       'streamix.cloud':        self.pp.parserSTREAMIXCLOUD  ,
                       'streamlive.to':         self.pp.parserSTREAMLIVETO   ,
                       'streamo.tv':            self.pp.parserIITV          ,
                       'streamhoe.online':      self.pp.parserFEMBED        ,
                       'streamon.to':           self.pp.parserDOOD          ,
                       'streamp1ay.cc':         self.pp.parserSTREAMPLAY    ,
                       'streamplay.cc':         self.pp.parserSTREAMPLAY    ,
                       'streamplay.me':         self.pp.parserSTREAMPLAY    ,
                       'streamplay.to':         self.pp.parserSTREAMPLAY    ,
                       'sbplay.org':            self.pp.parserSTREAMSB      ,
                       'streamsb.net':          self.pp.parserSTREAMSB      ,
                       'streamsss.net':         self.pp.parserSTREAMSB      ,
                       'streamta.pe':           self.pp.parserSTREAMTAPE    ,
                       'streamtape.com':        self.pp.parserSTREAMTAPE    ,
                       'streamtape.net':        self.pp.parserSTREAMTAPE    ,
                       'streamtape.to':         self.pp.parserSTREAMTAPE    ,
                       'streamz.cc':            self.pp.parserSTREAMZ       ,
                       'streamz.vg':            self.pp.parserSTREAMZ       ,
                       'streamz.ws':            self.pp.parserSTREAMZ       ,
                       'streamzz.to':            self.pp.parserSTREAMZ       ,
                       'streamwire.net':        self.pp.parserONLYSTREAM   ,
                       'superfastvideos.xyz':   self.pp.parserTXNEWSNETWORK ,
                       'superfilm.pl':          self.pp.parserSUPERFILMPL   ,
                       'supervideo.tv':         self.pp.parserSUPERVIDEO    ,
                       'supergoodtvlive.com':   self.pp.parserTXNEWSNETWORK ,
                       'suprafiles.org':        self.pp.parserUPLOAD         ,
                       'suspents.info':         self.pp.parserFASTVIDEOIN   ,
                       'swirownia.com.usrfiles.com': self.pp.parserSWIROWNIA,
                       'talbol.net':            self.pp.parserTXNEWSNETWORK ,
                       'tantifilm.fit':         self.pp.parserTANTIFILM     ,
                       'tantifilm.ga':          self.pp.parserTANTIFILM     ,
                       'tantifilm.top':         self.pp.parserTANTIFILM     ,
                       'tapecontent.net':       self.pp.parserSTREAMTAPE   ,
                       'telerium.tv':           self.pp.parserTELERIUMTV     ,
                       'theactionlive.com':     self.pp.parserTHEACTIONLIVE ,
                       'thefile.me':            self.pp.parserTHEFILEME     ,
                       'thevideo.cc':           self.pp.parserTHEVIDEOME    ,
                       'thevideo.me':           self.pp.parserTHEVIDEOME    ,
                       'thevideos.ga':          self.pp.parserTHEVIDEOME    ,
                       'thevideobee.to':        self.pp.parserTHEVIDEOBEETO  ,
                       'thevideome.com':        self.pp.parserTHEVIDEOME    ,
                       'tiny.cc':               self.pp.parserTINYCC        ,
                       'tinymov.net':           self.pp.parserTINYMOV       ,
                       'topupload.tv':          self.pp.parserTOPUPLOAD     ,
                       'toclipit.com':          self.pp.parserVIUCLIPS,
                       'tronpriceprediction2020.com': self.pp.parserTRONPRICE,
                       'tubecloud.net':         self.pp.parserTUBECLOUD     ,
                       'tubeload.co':           self.pp.parserTUBELOADCO,
                       'tune.pk':               self.pp.parserTUNEPK         ,
                       'tunein.com':            self.pp.parserTUNEINCOM      ,
                       'tunestream.net':        self.pp.parserONLYSTREAM    ,
                       'tusfiles.com':          self.pp.parserUSERSCLOUDCOM ,
                       'tusfiles.net':          self.pp.parserUSERSCLOUDCOM ,
                       'tvad.me':               self.pp.parserTHEVIDEOME    ,
                       'tvope.com':             self.pp.parserTVOPECOM      ,
                       'tvp.pl':                self.pp.parserTVP           ,
                       'txnewsnetwork.net':     self.pp.parserTXNEWSNETWORK,
                       'twitch.tv':             self.pp.parserTWITCHTV      ,
                       'ultimatedown.com':      self.pp.parserULTIMATEDOWN   ,
                       'up2stream.com':         self.pp.parserVIDEOMEGA     ,
                       'upclips.online':        self.pp.parserVIUCLIPS,
                       'upfile.mobi':           self.pp.parserUPFILEMOBI     ,
                       'upload.af':             self.pp.parserUPLOAD         ,
                       'upload.mn':             self.pp.parserUPLOAD2        ,
                       'uploadc.com':           self.pp.parserUPLOADCCOM    ,
                       'uploadit.cc':           self.pp.parserUPLOADIT       ,
                       'uploaduj.net':          self.pp.parserUPLOADUJNET    ,
                       'uploadx.link':          self.pp.parserUPLOAD         ,
                       'uploadx.org':           self.pp.parserUPLOAD         ,
                       'uploadz.co':            self.pp.parserUPLOAD         ,
                       'uploadz.org':           self.pp.parserUPLOAD         ,
                       'upmela.com':            self.pp.parserVIUCLIPS       ,
                       'uprotector.xyz':        self.pp.parserWSTREAMVIDEO   ,
                       'upstream.to':           self.pp.parserONLYSTREAM    ,
                       'uptobox.com':           self.pp.parserUPTOSTREAMCOM  ,
                       'uptostream.com':        self.pp.parserUPTOSTREAMCOM  ,
                       'upvid.co':              self.pp.parserWATCHUPVIDCO   ,
                       'upvid.mobi':            self.pp.parserUPFILEMOBI     ,
                       'upvideo.cc':            self.pp.parserONLYSTREAM   ,
                       'upvideo.to':            self.pp.parserONLYSTREAM   ,
                       'userload.co':           self.pp.parserUSERLOADCO     ,
                       'userscloud.com':        self.pp.parserUSERSCLOUDCOM ,
                       'ustream.to':            self.pp.parserUSTREAMTV     ,
                       'ustream.tv':            self.pp.parserUSTREAMTV     ,
                       'ustreamix.com':         self.pp.parserUSTREAMIXCOM  ,
                       'vcrypt.net':            self.pp.parserVCRYPT        ,
                       'vcrypt.pw':             self.pp.parserVCRYPT        ,
                       'vcstream.to':           self.pp.parserVCSTREAMTO     ,
                       'veehd.com':             self.pp.parserVEEHDCOM       ,
                       'veoh.com':              self.pp.parserVEOHCOM        ,
                       'verystream.com':        self.pp.parserVERYSTREAM     ,
                       'verystream.info':       self.pp.parserFEMBED  ,
                       'very.streamango.to':    self.pp.parserONLYSTREAM  , 
                       'veuclips.com':          self.pp.parserVIUCLIPS     ,
                       'vev.io':                self.pp.parserTHEVIDEOME    ,
                       'vevo.com':              self.pp.parserVEVO          ,
                       'vid.ag':                self.pp.parserVIDAG         ,
                       'vid.gg':                self.pp.parserVIDGGTO       ,
                       'vid.me':                self.pp.parserVIDME          ,
                       'vidabc.com':            self.pp.parserVIDABCCOM     ,
                       'vidbom.com':            self.pp.parserVIDBOMCOM     ,
                       'vidbull.com':           self.pp.parserVIDBULL       ,
                       'vidcloud.co':           self.pp.parserVIDCLOUD      ,
                       'vidcloud.icu':          self.pp.parserVIDCLOUD      ,
                       'vidcloud.net':          self.pp.parserVIDCLOUD      ,
                       'vidcloud9.com':         self.pp.parserVIDCLOUD9     ,
                       'videa.hu':              self.pp.parserVIDEAHU       ,
                       'vidembed.cc':           self.pp.parserVIDEMBED     ,
                       'vidembed.io':           self.pp.parserVIDEMBED     ,
                       'vidembed.me':           self.pp.parserVIDEMBED     ,
                       'vidembed.net':          self.pp.parserVIDEMBED     , 
                       'video.filmoviplex.com': self.pp.parserNETUTV        ,
                       'video.meta.ua':         self.pp.parserMETAUA        ,
                       'video.rutube.ru':       self.pp.parserRUTUBE        ,
                       'video.sibnet.ru':       self.pp.parserSIBNET        ,
                       'video.tt':              self.pp.parserVIDEOTT       ,
                       'video.yandex.ru':       self.pp.parserYANDEX        ,
                       'videoapi.my.mail.ru':   self.pp.parserVIDEOMAIL     ,
                       'videobin.co':           self.pp.parserVIDEOBIN      ,
                       'videohouse.me':         self.pp.parserVIDEOHOUSE    ,
                       'videomega.tv':          self.pp.parserVIDEOMEGA     ,
                       'videomore.ru':          self.pp.parserVIDEOMORERU   ,
                       'videoslasher.com':      self.pp.parserVIDEOSLASHER  ,
                       'videos.sapo.pt':        self.pp.parserSAPOPT     ,
                       'videovard.sx':          self.pp.parserVIDEOVARDSX   ,
                       'videoweed.com':         self.pp.parserVIDEOWEED     ,
                       'videoweed.es':          self.pp.parserVIDEOWEED     ,
                       'videowood.tv':          self.pp.parserVIDEOWOODTV   ,
                       'vidfile.net':           self.pp.parserVIDFILENET    ,
                       'vidia.tv':              self.pp.parserSUPERVIDEO    ,
                       'vidgg.to':              self.pp.parserVIDGGTO       ,
                       'vidload.co':            self.pp.parserVIDLOADCO     ,
                       'vidlox.me':             self.pp.parserVIDLOXTV      ,
                       'vidlox.tv':             self.pp.parserVIDLOXTV      ,
                       'vidnext.net':           self.pp.parserVIDCLOUD9     ,
                       'vidnode.net':           self.pp.parserVIDCLOUD      ,
                       'vidoo.tv':              self.pp.parserONLYSTREAM   ,
                       'vidoza.net':            self.pp.parserVIDOZANET     ,
                       'vidoza.co':             self.pp.parserVIDOZANET     ,
                       'viewsb.com':            self.pp.parserSTREAMSB,
                       'vidshare.tv':           self.pp.parserVIDSHARETV    ,
                       'vidsource.me':          self.pp.parserVIDSOURCE     ,
                       'vidspot.net':           self.pp.parserVIDSPOT       ,
                       'vidsrc.me':             self.pp.parserVIDSRC        ,
                       'vidsso.com':            self.pp.parserVIDSSO        ,
                       'vidstodo.me':           self.pp.parserVIDSTODOME     ,
                       'vidstream.in':          self.pp.parserVIDSTREAM     ,
                       'vidstream.to':          self.pp.parserVIDSTREAM     ,
                       'vidstream.top':         self.pp.parserVIDSTREAM     ,
                       'vidstreamup.com':       self.pp.parserVIUCLIPS    ,
                       'vidhdthe.club':         self.pp.parserHDVIDTV       ,
                       'vidhdthe.online':       self.pp.parserHDVIDTV       ,
                       'vidthehd.club':         self.pp.parserHDVIDTV       ,
                       'vidto.me':              self.pp.parserVIDTO         ,
                       'vidtodo.com':           self.pp.parserVIDSTODOME     ,
                       'vidup.me':              self.pp.parserVIDUPME       ,
                       'vidzer.net':            self.pp.parserVIDZER        ,
                       'vidzi.tv':              self.pp.parserVIDZITV       ,
                       'vimeo.com':             self.pp.parserVIMEOCOM       ,
                       'viuclips.net':          self.pp.parserVIUCLIPS     ,
                       'vivo.sx':               self.pp.parserVIVOSX        ,
                       'vkprime.com':           self.pp.parserONLYSTREAM    ,
                       'vk.com':                self.pp.parserVK            ,
                       'vodlocker.com':         self.pp.parserVODLOCKER     ,
                       'vod-share.com':         self.pp.parserVODSHARECOM   ,
                       'voe.sx':                self.pp.parserMATCHATONLINE,
                       'voodaith7e.com':        self.pp.parserYOUWATCH      ,
                       'vshare.eu':             self.pp.parserVSHAREEU      ,
                       'vshare.io':             self.pp.parserVSHAREIO       ,
                       'vsports.pt':            self.pp.parserSAPOPT     ,
                       'vtube.to':              self.pp.parserONLYSTREAM    ,
                       'vudeo.io':              self.pp.parserONLYSTREAM    ,
                       'vudeo.net':             self.pp.parserONLYSTREAM    ,
                       'vup.to':                self.pp.parserONLYSTREAM    ,
                       'vupload.com':           self.pp.parserONLYSTREAM    ,
                       'waaw.tv':               self.pp.parserNETUTV         ,
                       'waaw.to':               self.pp.parserNETUTV         ,
                       'wat.tv':                self.pp.parserWATTV          ,
                       'watchers.to':           self.pp.parserWATCHERSTO    ,
                       'watchsb.com':           self.pp.parserSTREAMSB      ,
                       'watchvideo17.us':       self.pp.parserWATCHVIDEO17US ,
                       'webcamera.mobi':        self.pp.parserWEBCAMERAPL   ,
                       'webcamera.pl':          self.pp.parserWEBCAMERAPL   ,
                       'wgrane.pl':             self.pp.parserWGRANE        ,
                       'wholecloud.net':        self.pp.parserWHOLECLOUD     ,
                       'wholecloud.net':        self.pp.parserWHOLECLOUD    ,
                       'widestream.io':         self.pp.parserWIDESTREAMIO   ,
                       'wiiz.tv':               self.pp.parserWIIZTV         ,
                       'wolfstream.tv':         self.pp.parserCLIPWATCHINGCOM,
                       'woof.tube':             self.pp.parserWOOFTUBE,
                       'wrzuta.pl':             self.pp.parserWRZUTA        ,
                       'wstream.video':         self.pp.parserWSTREAMVIDEO   ,
                       'ww1.opendrive.top':     self.pp.parserOPENDRIVE     ,
                       'xage.pl':               self.pp.parserXAGEPL        ,
                       'xvidstage.com':         self.pp.parserXVIDSTAGECOM   ,
                       'yocast.tv':             self.pp.parserYOCASTTV      ,
                       'yodbox.com':            self.pp.parserONLYSTREAM   ,
                       'yourvideohost.com':     self.pp.parserYOURVIDEOHOST ,
                       'youtu.be':              self.pp.parserYOUTUBE       ,
                       'youtube.com':           self.pp.parserYOUTUBE       ,
                       'youtube-nocookie.com':  self.pp.parserYOUTUBE       ,
                       'youvideos.ru':          self.pp.parserFEMBED       ,
                       'youwatch.org':          self.pp.parserYOUWATCH      ,
                       'yukons.net':            self.pp.parserYUKONS        ,
                       'zalaa.com':             self.pp.parserZALAACOM      ,
                       'zerocast.tv':           self.pp.parserZEROCASTTV    ,
                       'zstream.to':            self.pp.parserZSTREAMTO     ,
                       'nba-streams.online':    self.pp.parserSHOWSPORTXYZ,
                       'showsport.xyz':         self.pp.parserSHOWSPORTXYZ,
                       'assia.org':             self.pp.parserASSIAORG,
                       'assia2.com':            self.pp.parserASSIAORG,
                       'assia22.com':           self.pp.parserASSIAORG,
                       'assia4.com':            self.pp.parserASSIAORG,
                       'castfree.me':           self.pp.parserASSIAORG,
                       'cricplay2.xyz':         self.pp.parserASSIAORG,
                       'freefeds.click':        self.pp.parserASSIAORG,
                       'givemenbastreams.com':  self.pp.parserASSIAORG,
                       'embedstream.me':        self.pp.parserEMBEDSTREAMME,
                       'daddylive.me':          self.pp.parserDADDYLIVE,
                       'daddylive.club':        self.pp.parserDADDYLIVE,
                       'teleriumtv.com':        self.pp.parserTELERIUMTVCOM,
                       'f1livegp.me':           self.pp.parserF1LIVEGPME,
                       'bestnhl.com':           self.pp.parserF1LIVEGPME,
                       'highload.to':           self.pp.parserHIGHLOADTO,
                       'liveonscore.to':        self.pp.parserLIVEONSCORETV,
                       'weakstreams.com':       self.pp.parserLIVEONSCORETV,
                       'sportsonline.to':       self.pp.parserSPORTSONLINETO,
                       'ufckhabib.com':         self.pp.parserSPORTSONLINETO,
                       'castfree.me':           self.pp.parserCASTFREEME,
                       'noob4cast.com':         self.pp.parserCASTFREEME,
                       'hlsplayer.org':         self.pp.parserHLSPLAYER,
                       'starlive.xyz':          self.pp.parserSTARLIVEXYZ,
                       'jokerswidget.org':      self.pp.parserJOKERSWIDGETORG

                       
        } 
        return                 
        
    
    def getHostName(self, url, nameOnly = False):
        hostName = strwithmeta(url).meta.get('host_name', '')
        if not hostName:
            match = re.search('https?://(?:www.)?(.+?)/', url)
            if match:
                hostName = match.group(1)
                if (nameOnly):
                    n = hostName.split('.')
                    try: hostName = n[-2]
                    except Exception: printExc()
            hostName = hostName.lower()
        printDBG("_________________getHostName: [%s] -> [%s]" % (url, hostName))
        return hostName
        
    def getParser(self, url, host=None):
        if None == host:
            host = self.getHostName(url)
        parser = self.hostMap.get(host, None)
        if None == parser:
            host2 = host[host.find('.')+1:]
            printDBG('urlparser.getParser II try host[%s]->host2[%s]' % (host, host2))
            parser = self.hostMap.get(host2, None)
        return parser
    
    def checkHostSupport(self, url):
        # -1 - not supported
        #  0 - unknown
        #  1 - supported
        host  = self.getHostName(url)
        
        # quick fix
        if host == 'facebook.com' and 'likebox.php' in url or 'like.php' in url or '/groups/' in url:
            return 0
        
        ret = 0
        parser = self.getParser(url, host)
        if None != parser:
            return 1
        elif self.isHostsNotSupported(host):
            return -1
        return ret
        
    def isHostsNotSupported(self, host):
        return host in ['rapidgator.net', 'oboom.com']

    def getVideoLinkExt(self, url):
        videoTab = []
        try:
            ret = self.getVideoLink(url, True)
            
            if isinstance(ret, basestring):
                if 0 < len(ret):
                    host = self.getHostName(url)
                    videoTab.append({'name': host, 'url': ret})
            elif isinstance(ret, list) or isinstance(ret, tuple):
                videoTab = ret
                
            for idx in range(len(videoTab)):
                if not self.cm.isValidUrl(url): continue
                url = strwithmeta(videoTab[idx]['url'])
                if 'User-Agent' not in url.meta:
                    #url.meta['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0'
                    url.meta['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
                    
                    videoTab[idx]['url'] = url
        except Exception:
            printExc()
            
        return videoTab
        
    def getVideoLink(self, url, acceptsList = False):
        try:
            url = self.decorateParamsFromUrl(url)
            nUrl=''
            parser = self.getParser(url)
            if None != parser:
                nUrl = parser(url)
            else:
                host = self.getHostName(url)
                if self.isHostsNotSupported(host):
                    SetIPTVPlayerLastHostError(_('Hosting "%s" not supported.') % host)
                else:
                    SetIPTVPlayerLastHostError(_('Hosting "%s" unknown.') % host)
    
            if isinstance(nUrl, list) or isinstance(nUrl, tuple):
                if True == acceptsList:
                    return nUrl
                else:
                    if len(nUrl) > 0:
                        return nUrl[0]['url']
                    else:
                        return False
            return nUrl
        except Exception:
            printExc()
        return False
        
    def getAutoDetectedStreamLink(self, baseUrl, data=None):
        printDBG("urlparser.getAutoDetectedStreamLink baseUrl[%s]" % baseUrl)
        url = baseUrl
        num = 0
        while True:
            num += 1
            if None == data:
                url = strwithmeta(url)
                HTTP_HEADER = dict(pageParser.HTTP_HEADER) 
                HTTP_HEADER['Referer'] = url.meta.get('Referer', url)
                sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
                if not sts: return []
            data = re.sub("<!--[\s\S]*?-->", "", data)
            if 1 == num  and 'http://up4free.com/' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([^'^"]+?)['"];""")[0]
                tmpUrl = url
                url = 'http://embed.up4free.com/stream.php?id=' + id + '&amp;width=700&amp;height=450&amp;stretching='
                url = strwithmeta(url, {'Referer':tmpUrl})
                data = None
                continue
            elif 'hdfree.tv/live' in data and 'hdfree.tv' not in url:
                tmpUrl = url
                url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?hdfree.tv/live[^"^']+?)["']''', 1, True)[0]
                url = strwithmeta(url, {'Referer':tmpUrl})
                data = None
                continue
            elif 'srkcast.com' in data:
                videoUrl = ''
                fid = self.cm.ph.getSearchGroups(data, '''fid=['"]([^'^"]+?)['"]''')[0]
                player = self.cm.ph.getSearchGroups(data, '''fid=['"]([^'^"]+?)['"]''')[0]
                if '' != fid:
                    videoUrl = 'http://www.srkcast.com/embed.php?player=%s&live=%s&vw=640&vh=480' % (player, fid)
                else:
                    videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](https?://[^"^']*?srkcast.com/[^"^']+?)["']''', 1, True)[0].replace('&amp;', '&')
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'dotstream.tv' in data:
                streampage = self.cm.ph.getSearchGroups(data, """streampage=([^&]+?)&""")[0]
                videoUrl = 'http://dotstream.tv/player.php?streampage={0}&height=490&width=730'.format(streampage)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'player.nadaje.com' in data:
                tmpUrl = self.cm.ph.getDataBeetwenNodes(data, ('<script', '>', 'player.nadaje.com'), ('</script', '>'))[1]
                tmpUrl = self.cm.ph.getSearchGroups(tmpUrl, """player\-id=['"]([^'^"]+?)['"]""")[0]
                videoUrl = 'https://nadaje.com/api/1.0/services/video/%s/' % tmpUrl
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'allcast.is' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]?([0-9]+?)[^0-9]""")[0]
                videoUrl = 'http://www.allcast.is/stream.php?id={0}&width=100%&height=100%&stretching=uniform'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'ucaster.js' in data:
                channel = self.cm.ph.getSearchGroups(data, """channel=['"]([^'^"]+?)['"]""")[0]
                g = self.cm.ph.getSearchGroups(data, """g=['"]([^'^"]+?)['"]""")[0]
                width = self.cm.ph.getSearchGroups(data, """width=([0-9]+?)[^0-9]""")[0]
                height = self.cm.ph.getSearchGroups(data, """height=([0-9]+?)[^0-9]""")[0]
                videoUrl = 'http://www.embeducaster.com/membedplayer/{0}/{1}/{2}/{3}'.format(channel, g, width, height)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'leton.tv' in data:
                streampage = self.cm.ph.getSearchGroups(data, """streampage=([^&]+?)&""")[0]
                videoUrl = 'http://leton.tv/player.php?streampage={0}&height=490&width=730'.format(streampage)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'tvope.com' in data:
                channel = self.cm.ph.getSearchGroups(data, """[^a-zA-Z0-9]c=['"]([^'^"]+?)['"]""")[0]
                videoUrl = 'http://tvope.com/emb/player.php?c={0}&w=600&h=400&d={1}'.format(channel, urlparser.getDomain(baseUrl))
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'nowlive.' in data:
                id = self.cm.ph.getSearchGroups(data, """[^a-zA-Z0-9]id=['"]([0-9]+?)['"]""")[0]
                videoUrl = 'http://nowlive.pw/stream.php?id={0}&width=640&height=480&stretching=uniform&p=1'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'caston.tv/player.php' in data:
                id = self.cm.ph.getSearchGroups(data, """var\sid\s?=[^0-9]([0-9]+?)[^0-9]""")[0]
                if id == '': id = self.cm.ph.getSearchGroups(data, """id\s?=[^0-9]([0-9]+?)[^0-9]""")[0]
                videoUrl = 'http://www.caston.tv/player.php?width=1920&height=419&id={0}'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'liveonlinetv247' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http://[^'^"]*?liveonlinetv247[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'ssh101.com/secure/' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]*?ssh101.com/secure/[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'twitch.tv' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]*?twitch.tv[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'goodrtmp.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]*?goodrtmp.com[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'life-rtmp.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]*?life-rtmp.com[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'sostart.org' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([^'"]+?)['"]""")[0]
                videoUrl = 'http://sostart.org/streamk.php?id={0}&width=640&height=390'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'bro.adca.' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?bro\.adca\.[^'^"]+?stream\.php\?id=[^'^"]+?)['"]""")[0] 
                if videoUrl == '':
                    tmpUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?bro\.adca\.[^'^"]+?)['"]""")[0] 
                    if '' == tmpUrl: tmpUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?bro\.adcast\.[^'^"]+?)['"]""")[0]
                    sts, tmpUrl = self.cm.getPage(tmpUrl)
                    if not sts: return []
                    tmpUrl = self.cm.ph.getSearchGroups(tmpUrl, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
                    id = self.cm.ph.getSearchGroups(data, """id=['"]([^'"]+?)['"];""")[0]
                    videoUrl = self.cm.getBaseUrl(tmpUrl) + 'stream.php?id={0}&width=600&height=400'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'sostart.pw' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([0-9]+?)['"]""")[0]
                videoUrl = 'http://www.sostart.pw/jwplayer6.php?channel={0}&vw=710&vh=460'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'theactionlive.com' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([^'"]+?)['"]""")[0]
                videoUrl = 'http://theactionlive.com/livegamecr2.php?id={0}&width=640&height=460&stretching='.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'biggestplayer.me' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([^'"]+?)['"]""")[0]
                videoUrl = 'http://biggestplayer.me/streamcrjeje.php?id={0}&width=640&height=460'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'yocast.tv' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([^'"]+?)['"]""")[0]
                videoUrl = 'http://www.yocast.tv/embed.php?live={0}&vw=620&vh=490'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'miplayer.net' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http://miplayer.net[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':strwithmeta(baseUrl).meta.get('Referer', baseUrl)})
                return self.getVideoLinkExt(videoUrl)
            elif 'p2pcast' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"]""")[0]
                videoUrl = 'http://p2pcast.tv/stream.php?id={0}&live=0&p2p=0&stretching=uniform'.format(id)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'liveall.tv' in data: 
                videoUrl = self.cm.ph.getSearchGroups(data, 'SRC="([^"]+?liveall.tv[^"]+?)"', 1, True)[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'putlive.in' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '="([^"]*?putlive.in/[^"]+?)"')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'streamlive.to' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '="([^"]*?streamlive.to/[^"]+?)"')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'megom.tv' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '="([^"]*?megom.tv/[^"]+?)"')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'byetv.org' in data:
                file = self.cm.ph.getSearchGroups(data, "file=([0-9]+?)[^0-9]")[0]
                if '' == file: file = self.cm.ph.getSearchGroups(data, "a=([0-9]+?)[^0-9]")[0]
                videoUrl = "http://www.byetv.org/embed.php?a={0}&id=&width=710&height=460&autostart=true&strech=".format(file)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'castto.me' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([0-9]+?)['"]""")[0]
                videoUrl = 'http://static.castto.me/embedlivepeer5.php?channel={0}&vw=710&vh=460'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'cast4u.tv' in data:
                channel = self.cm.ph.getSearchGroups(data, """channel=['"]([^'^"]+?)['"]""")[0]
                g = self.cm.ph.getSearchGroups(data, """g=['"]([^'^"]+?)['"]""")[0]
                height = 640
                width = 360
                videoUrl = 'http://www.cast4u.tv/hembedplayer/{0}/{1}/{2}/{3}'.format(channel, g, width, height)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'hdcast.info' in data:
                fid = self.cm.ph.getSearchGroups(data, """fid=['"]([^'^"]+?)['"]""")[0]
                videoUrl = 'http://www.hdcast.info/embed.php?live={0}&vw=700&vh=450'.format(fid)
                videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                return self.getVideoLinkExt(videoUrl)
            elif 'deltatv.pw' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"];""")[0]
                videoUrl = 'http://deltatv.pw/stream.php?id=' + id
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'pxstream.tv' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](https?://[^'^"]+?)['"]''', ignoreCase=True)[0]
                if not self.cm.isValidUrl(videoUrl):
                    id = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                    videoUrl = 'http://pxstream.tv/embed.php?file=' + id
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'widestream.io' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](https?://[^'^"]*?widestream\.io[^'^"]+?)['"]''', ignoreCase=True)[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'kabab.lima-city.de' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](https?://[^'^"]+?)['"]''', ignoreCase=True)[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'ustreamix.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](https?://[^'^"]*?ustreamix[^'^"]+?)['"]''', ignoreCase=True)[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'coolcast.eu' in data:
                id = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                videoUrl = 'http://coolcast.eu/?name=' + id
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'goodcast.co' in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"];""")[0]
                videoUrl = 'http://goodcast.co/stream.php?id=' + id
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif '7cast.net' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?7cast.net[^'^"]+?)['"]""")[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'partners.nettvplus.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](http://partners.nettvplus.com[^'^"]+?)['"]""")[0]
                return self.getVideoLinkExt(videoUrl)
            elif "yukons.net" in data:
                channel = self.cm.ph.getDataBeetwenMarkers(data, 'channel="', '"', False)[1]
                videoUrl = strwithmeta('http://yukons.net/watch/'+channel, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif "castamp.com" in data:
                channel = self.cm.ph.getDataBeetwenMarkers(data, 'channel="', '"', False)[1]
                videoUrl = strwithmeta('http://www.castamp.com/embed.php?c='+channel, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'liveonlinetv247.info/embed/' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """['"](https?://(?:www\.)?liveonlinetv247\.info/embed/[^'^"]+?)['"]""")[0]
                return self.getVideoLinkExt(videoUrl)
            elif "crichd.tv" in data:
                if baseUrl.startswith('http://crichd.tv'):
                    videoUrl = strwithmeta(baseUrl, {'Referer':baseUrl})
                else:
                    videoUrl = self.cm.ph.getSearchGroups(data, 'src="(http://crichd.tv[^"]+?)"')[0]
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif "privatestream.tv" in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '''['"](https?://w*?privatestream.tv/[^"^']+?)['"]''')[0]
                if '' == videoUrl: videoUrl = self.cm.ph.getSearchGroups(data, '''=(https?://w*?privatestream.tv/[^"^'^>^<^\s]+?)['"><\s]''')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif "aliez.me" in data:
                videoUrl = self.cm.ph.getSearchGroups(data, '''['"](https?://[^'^"]*?aliez.me/[^"^']+?)['"]''')[0]
                if '' == videoUrl: videoUrl = self.cm.ph.getSearchGroups(data, '''=(https?://[^'^"]*?aliez.me/[^"^'^>^<^\s]+?)['"><\s]''')[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif "ustream.tv" in data:
                tmp = self.cm.ph.getSearchGroups(data, '<([^>]+?src="[^"]+?ustream.tv[^"]+?"[^>]*?)>')[0]
                videoUrl = self.cm.ph.getSearchGroups(tmp, 'src="([^"]+?ustream.tv[^"]+?)"')[0]
                if '/flash/' in videoUrl or videoUrl.split('?')[0].endswith('.swf'):
                    cid = self.cm.ph.getSearchGroups(tmp, """cid=([0-9]+?)[^0-9]""")[0]
                    videoUrl = 'http://www.ustream.tv/channel/' + cid
                if videoUrl.startswith('//'):
                    videoUrl = 'http:' + videoUrl
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'source=rtmp://' in data:
                tmp = self.cm.ph.getSearchGroups(data, """source=(rtmp://[^'^"]+?)['"]""")[0]
                tmp = tmp.split('&amp;')
                r = tmp[0]
                swfUrl='swf'
                r += ' swfUrl=%s pageUrl=%s live=1' % (swfUrl, url)
                return [{'name':'[rtmp]', 'url':r}]
            elif 'rtmp://' in data:
                tmp = self.cm.ph.getSearchGroups(data, """(rtmp://[^'^"]+?)['"]""")[0]
                tmp = tmp.split('&amp;')
                r = tmp[0]
                if 1 < len(tmp)and tmp[1].startswith('c='):
                    playpath = tmp[1][2:]
                else:
                    playpath = self.cm.ph.getSearchGroups(data, """['"]*url['"]*[ ]*?:[ ]*?['"]([^'^"]+?)['"]""")[0]
                if '' != playpath:
                    r += ' playpath=%s' % playpath.strip()
                swfUrl = self.cm.ph.getSearchGroups(data, """['"](http[^'^"]+?swf)['"]""")[0]
                r += ' swfUrl=%s pageUrl=%s' % (swfUrl, url)
                return [{'name':'team-cast', 'url':r}]
            elif 'abcast.biz' in data or 'abcast.net' in data:
                videoUrl = ''
                file = self.cm.ph.getSearchGroups(data, "file='([^']+?)'")[0]
                if '' != file:
                    if 'abcast.net' in data:
                        videoUrl = 'http://abcast.net/embed.php?file='
                    else:
                        videoUrl = 'http://abcast.biz/embed.php?file='
                    videoUrl += file+'&width=640&height=480'
                else:
                    videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"](https?://[^'^"]*?abcast[^'^"]+?/embed\.php\?file=[^'^"]+?)['"]''', ignoreCase=True)[0]
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'openlive.org' in data:
                file = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                videoUrl = 'http://openlive.org/embed.php?file={0}&width=710&height=460'.format(file)
                videoUrl = strwithmeta(videoUrl, {'Referer':url})
                return self.getVideoLinkExt(videoUrl)
            elif 'shidurlive.com' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """src=['"](http[^'^"]+?shidurlive.com[^'^"]+?)['"]""")[0]
                if '' != videoUrl:
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.getVideoLinkExt(videoUrl)
            elif 'sawlive.tv' in data:
                videoUrl = self.cm.ph.getSearchGroups(data, """src=['"](http[^'^"]+?sawlive.tv[^'^"]+?)['"]""")[0]
                if '' != videoUrl:
                    videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
                    return self.getVideoLinkExt(videoUrl)
            elif "castalba.tv" in data:
                id = self.cm.ph.getSearchGroups(data, """id=['"]([0-9]+?)['"];""")[0]
                if '' != id:
                    videoUrl = 'http://castalba.tv/embed.php?cid='+id+'&wh=640&ht=400&r=team-cast.pl.cp-21.webhostbox.net'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.getVideoLinkExt(videoUrl)
            elif "fxstream.biz" in data:
                file = self.cm.ph.getSearchGroups(data, """file=['"]([^'^"]+?)['"];""")[0]
                if '' != file:
                    videoUrl = 'http://fxstream.biz/embed.php?file='+file+'&width=640&height=400'
                    videoUrl = strwithmeta(videoUrl, {'Referer':url})
                    return self.getVideoLinkExt(videoUrl)
            else:
                file = self.cm.ph.getSearchGroups(data, """['"]*(http[^'^"]+?\.m3u8[^'^"]*?)['"]""")[0]
                if '' != file: 
                    file = file.split('&#038;')[0]
                    file = urllib.unquote(clean_html(file))
                    printDBG("> file[%s]" % file)
                    if file.count('://') > 1: file = self.cm.ph.getSearchGroups(file[1:], """(https?://[^'^"]+?\.m3u8[^'^"]*?)$""")[0]
                    printDBG("> file[%s]" % file)
                    return getDirectM3U8Playlist(file, checkExt=False)
                if 'x-vlc-plugin' in data:
                    vlcUrl = self.cm.ph.getSearchGroups(data, """target=['"](http[^'^"]+?)['"]""")[0]
                    if '' != vlcUrl: return [{'name':'vlc', 'url':vlcUrl}]
                printDBG("=======================================================================")
                printDBG("No link extractor for url[%s]" % url)
                printDBG("=======================================================================")
            return []

class pageParser(CaptchaHelper):
    HTTP_HEADER= {  'User-Agent'  : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36',
                    'Accept'      : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Content-type': 'application/x-www-form-urlencoded' }
    FICHIER_DOWNLOAD_NUM = 0
    def __init__(self):
        self.cm = common()
        self.captcha = captchaParser()
        self.ytParser = None
        self.moonwalkParser = None
        self.vevoIE = None
        self.bbcIE = None
        self.sportStream365ServIP = None
        
        #config
        self.COOKIE_PATH = GetCookieDir('')
        self.jscode = {}
        self.jscode['jwplayer'] = 'window=this; function stub() {}; function jwplayer() {return {setup:function(){print(JSON.stringify(arguments[0]))}, onTime:stub, onPlay:stub, onComplete:stub, onReady:stub, addButton:stub}}; window.jwplayer=jwplayer;'
        
    def getPageCF(self, baseUrl, addParams = {}, post_data = None):
        addParams['cloudflare_params'] = {'cookie_file':addParams['cookiefile'], 'User-Agent':addParams['header']['User-Agent']}
        sts, data = self.cm.getPageCFProtection(baseUrl, addParams, post_data)
        return sts, data
    
    def getYTParser(self):
        if self.ytParser == None:
            try:
                from youtubeparser import YouTubeParser
                self.ytParser = YouTubeParser()
            except Exception:
                printExc()
                self.ytParser = None
        return self.ytParser
        
    def getVevoIE(self):
        if self.vevoIE == None:
            try:
                from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.vevo import VevoIE
                self.vevoIE = VevoIE()
            except Exception:
                self.vevoIE = None
                printExc()
        return self.vevoIE
        
    def getBBCIE(self):
        if self.bbcIE == None:
            try:
                from Plugins.Extensions.IPTVPlayer.libs.youtube_dl.extractor.bbc import BBCCoUkIE
                self.bbcIE = BBCCoUkIE()
            except Exception:
                self.bbcIE = None
                printExc()
        return self.bbcIE
        
    def getMoonwalkParser(self):
        if self.moonwalkParser == None:
            try:
                from moonwalkcc import MoonwalkParser
                self.moonwalkParser = MoonwalkParser()
            except Exception:
                printExc()
                self.moonwalkParser = None
        return self.moonwalkParser
        
    def _getSources(self, data):
        printDBG('>>>>>>>>>> _getSources')
        urlTab = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'sources', ']')[1]
        if tmp != '':
            tmp = tmp.replace('\\', '')
            tmp = tmp.split('}')
            urlAttrName = 'file'
            sp = ':'
        else:
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', withMarkers=True)
            urlAttrName = 'src'
            sp = '='
        printDBG(tmp)
        for item in tmp:
            url  = self.cm.ph.getSearchGroups(item, r'''['"]?{0}['"]?\s*{1}\s*['"](https?://[^"^']+)['"]'''.format(urlAttrName, sp))[0]
            if not self.cm.isValidUrl(url): continue
            name = self.cm.ph.getSearchGroups(item, r'''['"]?label['"]?\s*''' + sp + r'''\s*['"]?([^"^'^\,^\{]+)['"\,\{]''')[0]
            
            printDBG('---------------------------')
            printDBG('url:  ' + url)
            printDBG('name: ' + name)
            printDBG('+++++++++++++++++++++++++++')
            printDBG(item)
            
            if 'flv' in item:
                if name == '': name = '[FLV]'
                urlTab.insert(0, {'name':name, 'url':url})
            elif 'mp4' in item:
                if name == '': name = '[MP4]'
                urlTab.append({'name':name, 'url':url})
            
        return urlTab
        
    def _findLinks(self, data, serverName='', linkMarker=r'''['"]?file['"]?[ ]*:[ ]*['"](http[^"^']+)['"][,}]''', m1='sources', m2=']', contain='', meta={}):
        linksTab = []
        
        def _isSmil(data):
            return data.split('?')[0].endswith('.smil')
        
        def _getSmilUrl(url):
            if _isSmil(url):
                SWF_URL=''
                # get stream link
                sts, data = self.cm.getPage(url)
                if sts:
                    base = self.cm.ph.getSearchGroups(data, 'base="([^"]+?)"')[0]
                    src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                    #if ':' in src:
                    #    src = src.split(':')[1]   
                    if base.startswith('rtmp'):
                        return base + '/' + src + ' swfUrl=%s pageUrl=%s' % (SWF_URL, url)
            return ''
        
        subTracks = []
        subData = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''['"]?tracks['"]?\s*?:'''), re.compile(']'), False)[1].split('}')
        for item in subData:
            kind = self.cm.ph.getSearchGroups(item, r'''['"]?kind['"]?\s*?:\s*?['"]([^"^']+?)['"]''')[0].lower()
            if kind != 'captions': continue
            src = self.cm.ph.getSearchGroups(item, r'''['"]?file['"]?\s*?:\s*?['"](https?://[^"^']+?)['"]''')[0]
            if src == '': continue
            label = self.cm.ph.getSearchGroups(item, r'''label['"]?\s*?:\s*?['"]([^"^']+?)['"]''')[0]
            format = src.split('?', 1)[0].split('.')[-1].lower()
            if format not in ['srt', 'vtt']: continue
            if 'empty' in src.lower(): continue
            subTracks.append({'title':label, 'url':src, 'lang':'unk', 'format':'srt'})
        
        srcData = self.cm.ph.getDataBeetwenMarkers(data, m1, m2, False)[1].split('},')
        for item in srcData:
            item += '},'
            if contain != '' and contain not in item: continue
            link = self.cm.ph.getSearchGroups(item, linkMarker)[0].replace('\/', '/')
            if '%3A%2F%2F' in link and '://' not in link:
                link = urllib.unquote(link)
            link = strwithmeta(link, meta)
            label = self.cm.ph.getSearchGroups(item, r'''['"]?label['"]?[ ]*:[ ]*['"]([^"^']+)['"]''')[0]
            if _isSmil(link):
                link = _getSmilUrl(link)
            if '://' in link:
                proto = 'mp4'
                if link.startswith('rtmp'):
                    proto = 'rtmp'
                if link.split('?')[0].endswith('m3u8'):
                    tmp = getDirectM3U8Playlist(link)
                    linksTab.extend(tmp)
                else:
                    linksTab.append({'name': '%s %s' % (proto + ' ' +serverName, label), 'url':link})
                printDBG('_findLinks A')
        
        if 0 == len(linksTab):
            printDBG('_findLinks B')
            link = self.cm.ph.getSearchGroups(data, linkMarker)[0].replace('\/', '/')
            link = strwithmeta(link, meta)
            if _isSmil(link):
                link = _getSmilUrl(link)
            if '://' in link:
                proto = 'mp4'
                if link.startswith('rtmp'):
                    proto = 'rtmp'
                linksTab.append({'name':proto + ' ' +serverName, 'url':link})
        
        if len(subTracks):
            for idx in range(len(linksTab)):
                linksTab[idx]['url'] = urlparser.decorateUrl(linksTab[idx]['url'], {'external_sub_tracks':subTracks})
        
        return linksTab
        
    def _findLinks2(self, data, baseUrl):
        videoUrl = self.cm.ph.getSearchGroups(data, 'type="video/divx"src="(http[^"]+?)"')[0]
        if '' != videoUrl: return strwithmeta(videoUrl, {'Referer':baseUrl})
        videoUrl = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*[:,][ ]*['"](http[^"^']+)['"][,}\)]''')[0]
        if '' != videoUrl: return strwithmeta(videoUrl, {'Referer':baseUrl})
        return False
        
    def _parserUNIVERSAL_A(self, baseUrl, embedUrl, _findLinks, _preProcessing=None, httpHeader={}, params={}):
        HTTP_HEADER = { 'User-Agent':"Mozilla/5.0"}
        if 'Referer' in strwithmeta(baseUrl).meta:
            HTTP_HEADER['Referer'] = strwithmeta(baseUrl).meta['Referer']
        HTTP_HEADER.update(httpHeader)
        
        if 'embed' not in baseUrl and '{0}' in embedUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{12})[/.-]')[0]
            url = embedUrl.format(video_id)
        else:
            url = baseUrl
        
        params = dict(params)
        params.update({'header':HTTP_HEADER})
        post_data = None
        
        if params.get('cfused', False): sts, data = self.getPageCF(url, params, post_data)
        else: sts, data = self.cm.getPage(url, params, post_data)
        if not sts: return False
        
        #printDBG(data)
        data = re.sub("<!--[\s\S]*?-->", "", data)
        #data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        errMarkers = ['File was deleted', 'File Removed', 'File Deleted.', 'File Not Found']
        for errMarker in errMarkers:
            if errMarker in data:
                SetIPTVPlayerLastHostError(errMarker)
        
        if _preProcessing != None:
            data = _preProcessing(data)
        printDBG("Data: " + data)
        
        # get JS player script code from confirmation page
        vplayerData = ''
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item and 'vplayer' in item:
                vplayerData = item
        
        if vplayerData != '':
            jscode = base64.b64decode('''ZnVuY3Rpb24gc3R1Yigpe31mdW5jdGlvbiBqd3BsYXllcigpe3JldHVybntzZXR1cDpmdW5jdGlvbigpe3ByaW50KEpTT04uc3RyaW5naWZ5KGFyZ3VtZW50c1swXSkpfSxvblRpbWU6c3R1YixvblBsYXk6c3R1YixvbkNvbXBsZXRlOnN0dWIsb25SZWFkeTpzdHViLGFkZEJ1dHRvbjpzdHVifX12YXIgZG9jdW1lbnQ9e30sd2luZG93PXRoaXM7''')
            jscode += vplayerData
            vplayerData = ''
            tmp = []
            ret = js_execute( jscode )
            if ret['sts'] and 0 == ret['code']:
                vplayerData = ret['data'].strip()
        
        if vplayerData != '':
            data += vplayerData
        else:
            mrk1 = ">eval("
            mrk2 = 'eval("'
            if mrk1  in data:
                m1 = mrk1
            elif mrk2 in data :
                m1 = mrk2
            else: m1 = "eval(" 
            tmpDataTab = self.cm.ph.getAllItemsBeetwenMarkers(data, m1, '</script>', False)
            for tmpData in tmpDataTab:
                data2 = tmpData
                tmpData = None
                # unpack and decode params from JS player script code
                tmpData = unpackJSPlayerParams(data2, VIDUPME_decryptPlayerParams)
                if tmpData == '':
                    tmpData = unpackJSPlayerParams(data2, VIDUPME_decryptPlayerParams, 0)
                    
                if None != tmpData:
                    data = data + tmpData
        
        printDBG("-*-*-*-*-*-*-*-*-*-*-*-*-*-\nData: %s\n-*-*-*-*-*-*-*-*-*-*-*-*-*-\n" % data)
        return _findLinks(data)
        
    def _parserUNIVERSAL_B(self, url, userAgent='Mozilla/5.0'):
        printDBG("_parserUNIVERSAL_B url[%s]" % url)
        
        domain = urlparser.getDomain(url) 
        
        if self.cm.getPage(url, {'max_data_size':0})[0]:
            url = self.cm.meta['url']
            
        post_data = None
        
        if '/embed' not in url: 
            sts, data = self.cm.getPage( url, {'header':{'User-Agent': userAgent}} )
            if not sts: return False
            try:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post" action="">', '</form>', False, False)[1]
                if tmp == '': tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<form[^>]+?method="post"[^>]*?>', re.IGNORECASE), re.compile('</form>', re.IGNORECASE), False)[1]
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            except Exception:
                printExc()
            try:
                tmp = dict(re.findall(r'<button[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
                post_data.update(tmp)
            except Exception:
                printExc()
        videoTab = []
        params = {'header':{ 'User-Agent': userAgent, 'Content-Type':'application/x-www-form-urlencoded','Referer':url} }
        try:
            sts, data = self.cm.getPage(url, params, post_data)
            #printDBG(data)
            
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')
            if sts:
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>')
                printDBG(tmp)
                for item in tmp:
                    if 'video/mp4' not in item and 'video/x-flv' not in item: continue
                    tType = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0].replace('video/', '')
                    tUrl  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
                    printDBG(tUrl)
                    if self.cm.isValidUrl(tUrl):
                        videoTab.append({'name':'[%s] %s' % (tType, domain), 'url':strwithmeta(tUrl, {'User-Agent': userAgent})})
                if len(videoTab):
                    return videoTab
            
            tmp = self.cm.ph.getDataBeetwenMarkers(data, 'player.ready', '}')[1]
            url = self.cm.ph.getSearchGroups(tmp, '''src['"\s]*?:\s['"]([^'^"]+?)['"]''')[0]
            if url.startswith('/'):
                url = domain + url[1:]
            if self.cm.isValidUrl(url) and url.split('?')[0].endswith('.mpd'):
                url = strwithmeta(url, {'User-Agent':params['header']['User-Agent']})
                videoTab.extend(getMPDLinksWithMeta(url, False))
            
            filekey = re.search('flashvars.filekey="([^"]+?)";', data)
            if None == filekey: 
                filekey = re.search("flashvars.filekey=([^;]+?);", data)
                filekey = re.search('var {0}="([^"]+?)";'.format(filekey.group(1)), data)
            filekey = filekey.group(1)
            file    = re.search('flashvars.file="([^"]+?)";', data).group(1)
            domain  = re.search('flashvars.domain="(http[^"]+?)"', data).group(1)
            
            url = domain + '/api/player.api.php?cid2=undefined&cid3=undefined&cid=undefined&user=undefined&pass=undefined&numOfErrors=0'
            url = url + '&key=' + urllib.quote_plus(filekey) + '&file=' + urllib.quote_plus(file)
            sts, data = self.cm.getPage(url)
            videoUrl = re.search("url=([^&]+?)&", data).group(1)
            
            errUrl = domain + '/api/player.api.php?errorCode=404&cid=1&file=%s&cid2=undefined&cid3=undefined&key=%s&numOfErrors=1&user=undefined&errorUrl=%s&pass=undefined' % (urllib.quote_plus(file), urllib.quote_plus(filekey), urllib.quote_plus(videoUrl))
            sts, data = self.cm.getPage(errUrl)
            errUrl = re.search("url=([^&]+?)&", data).group(1)
            if '' != errUrl: url = errUrl
            if '' != url:
                videoTab.append({'name':'base', 'url':strwithmeta(url, {'User-Agent': userAgent})})
        except Exception:
            printExc()
        return videoTab
        
    def parserLOOKMOVIE(self, url):
        return url
        
    def __parseJWPLAYER_A(self, baseUrl, serverName='', customLinksFinder=None, folowIframe=False, sleep_time=None):
        printDBG("pageParser.__parseJWPLAYER_A serverName[%s], baseUrl[%r]" % (serverName, baseUrl))
        
        linkList = []
        tries = 3
        while tries > 0:
            tries -= 1
            HTTP_HEADER = dict(self.HTTP_HEADER) 
            HTTP_HEADER['Referer'] = baseUrl
            sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})

            if sts:
                HTTP_HEADER = dict(self.HTTP_HEADER) 
                HTTP_HEADER['Referer'] = baseUrl
                url = self.cm.ph.getSearchGroups(data, 'iframe[ ]+src="(https?://[^"]*?embed[^"]+?)"')[0]
                if '' != url and (serverName in url or folowIframe): 
                    sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}) 
                else:
                    url = baseUrl
            
            if sts and '' != data:
                try:
                    sts, data2 = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
                    if sts:
                        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data2))
                        try:
                            tmp = dict(re.findall(r'<button[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
                            post_data.update(tmp)
                        except Exception:
                            printExc()
                        if tries == 0:
                            try:
                                sleep_time = self.cm.ph.getSearchGroups(data2, '>([0-9]+?)</span> seconds<')[0]
                                if '' != sleep_time: GetIPTVSleep().Sleep(int(sleep_time))
                            except Exception:
                                if sleep_time != None:
                                    GetIPTVSleep().Sleep(sleep_time)
                                printExc()
                        HTTP_HEADER['Referer'] = url
                        sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}, post_data)
                        if sts:
                            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, ">eval(", '</script>')
                            for tmpItem in tmp:
                                try:
                                    tmpItem = unpackJSPlayerParams(tmpItem, VIDUPME_decryptPlayerParams)
                                    data = tmpItem + data
                                except Exception: printExc()
                    if None != customLinksFinder: linkList = customLinksFinder(data)
                    if 0 == len(linkList): linkList = self._findLinks(data, serverName)
                except Exception:
                    printExc()
            if len(linkList) > 0:
                break
        return linkList
            
    def parserFIREDRIVE(self, url):
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
        COOKIEFILE = self.COOKIE_PATH + "firedrive.cookie"
        url = url.replace('putlocker', 'firedrive').replace('file', 'embed')
        HTTP_HEADER['Referer'] = url
        
        sts, data = self.cm.getPage( url, {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': COOKIEFILE} )
        if not sts: return False
        if not 'Continue to ' in data: return False
        data = re.search('name="confirm" value="([^"]+?)"', data)
        if not data: return False
        data = {'confirm' : data.group(1)}
        sts, data = self.cm.getPage( url, {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE}, data)
        if not sts: return False
        sts, link_data = CParsingHelper.getDataBeetwenMarkers(data, "function getVideoUrl(){", 'return', False)
        if sts:       match = re.search("post\('(http[^']+?)'", link_data)
        else:         match = re.search("file: '(http[^']+?)'", data)
        if not match: match = re.search("file: loadURL\('(http[^']+?)'", data)

        if not match: return False
        url = match.group(1)
        printDBG('parserFIREDRIVE url[%s]' % url)
        return url

    def parserMEGUSTAVID(self, url):
        sts, link = self.cm.getPage(url)
    
        match = re.compile('value="config=(.+?)">').findall(link)
        if len(match) > 0:
            p = match[0].split('=')
            url = "http://megustavid.com/media/nuevo/player/playlist.php?id=" + p[1]
            sts, link = self.cm.getPage(url)
            match = re.compile('<file>(.+?)</file>').findall(link)
            if len(match) > 0:
                return match[0]
            else:
                return False
        else:
            return False

    def parserSPROCKED(self, url):
        url = url.replace('embed', 'show')
        sts, link = self.cm.getPage(url)
        match = re.search("""url: ['"](.+?)['"],.*\nprovider""",link)
        if match: return match.group(1)
        else: return False

    def parserWGRANE(self, url):
        # extract video hash from given url
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        paramsUrl = {'with_metadata':True, 'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(url, paramsUrl)
        if not sts: return False
        agree = ''
        if 'controversial_content_agree' in data: agree = 'controversial_content_agree'
        elif 'adult_content_agree' in data: agree = 'adult_content_agree'
        if '' != agree:
            vidHash = re.search("([0-9a-fA-F]{32})$", url)
            if not vidHash: return False
            paramsUrl.update( {'use_cookie': True, 'load_cookie':False, 'save_cookie':False} )
            url = "http://www.wgrane.pl/index.html?%s=%s" % (agree, vidHash.group(1))
            sts, data = self.cm.getPage(url, paramsUrl)
            if not sts: return False
        
        cUrl = data.meta['url']
        videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^'^"]*?embedlocal[^'^"]*?)['"]''', ignoreCase=True)[0]
        if videoUrl != '':
            videoUrl = self.cm.getFullUrl(videoUrl, self.cm.getBaseUrl(cUrl))
            paramsUrl['header']['Referer'] = cUrl
            sts, tmp = self.cm.getPage(videoUrl, paramsUrl)
            if sts: 
                urlTab = []
                tmp = self.cm.ph.getDataBeetwenReMarkers(tmp, re.compile('''['"]?urls['"]?\s*\:\s*\['''), re.compile('\]'))[1].split('}')
                for item in tmp:
                    name = self.cm.ph.getSearchGroups(item, '''['"]?name['"]?\s*\:\s*['"]([^'^"]+?)['"]''')[0]
                    url = self.cm.ph.getSearchGroups(item, '''['"]?url['"]?\s*\:\s*['"]([^'^"]+?)['"]''')[0]
                    if url == '': continue 
                    url = self.cm.getFullUrl(url, self.cm.getBaseUrl(cUrl)) 
                    urlTab.append({'name':name, 'url':url})
                if len(urlTab): return urlTab

        tmp = re.search('''["'](http[^"^']+?/video/[^"^']+?\.mp4[^"^']*?)["']''', data)
        if tmp: return tmp.group(1)
        data = re.search("<meta itemprop='contentURL' content='([^']+?)'", data)
        if not data: return False
        url = clean_html(data.group(1))
        return url
        
    def parserCDA(self, baseUrl):
        printDBG("parserCDA baseUrl [%r]" % baseUrl)

        COOKIE_FILE = GetCookieDir('cdapl.cookie')
        self.cm.clearCookie(COOKIE_FILE, removeNames=['vToken'])
        
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome') 
        defaultParams = {
            'header': HTTP_HEADER, 
            'use_cookie': True, 
            'load_cookie': True, 
            'save_cookie': True, 
            'cookiefile': COOKIE_FILE
        }
        
        def _decorateUrl(baseUrl, host, referer):
            #add cookies
            cookies = []
            cj = self.cm.getCookie(COOKIE_FILE)
            for cookie in cj:
                if (cookie.name == 'vToken' and cookie.path in baseUrl) or cookie.name == 'PHPSESSID':
                    cookies.append('%s=%s;' % (cookie.name, cookie.value))
                    printDBG("Cookie ----> \t%s \t%s \t%s \t%s" % (cookie.domain, cookie.path, cookie.name, cookie.value) )

            # prepare extended link
            retUrl = strwithmeta( baseUrl )
            retUrl.meta['User-Agent']        = HTTP_HEADER['User-Agent']
            retUrl.meta['Referer']           = referer
            retUrl.meta['Cookie']            = ' '.join(cookies)
            retUrl.meta['iptv_proto']        = 'http'
            retUrl.meta['iptv_urlwithlimit'] = False
            retUrl.meta['iptv_livestream']   = False
            return retUrl
            
        videoUrls = []
        uniqUrls  = []
        tmpUrls = []
        
        if '/video/' in baseUrl: 
            video_id = self.cm.ph.getSearchGroups(baseUrl + '/', "/video/([^/]+?)/")[0]
            baseUrl = 'http://ebd.cda.pl/620x368/' + video_id
            printDBG("Url transformed into %s " % baseUrl)

        sts, data = self.cm.getPage(baseUrl, defaultParams)
        
        if sts:
            sts, match = self.cm.ph.getDataBeetwenMarkers(data, "Link do tego video:", '</a>', False)
            if sts: 
                match = self.cm.ph.getSearchGroups(match, 'href="([^"]+?)"')[0] 
            else: 
                match = self.cm.ph.getSearchGroups(data, "link[ ]*?:[ ]*?'([^']+?/video/[^']+?)'")[0]
            
            if match.startswith('http'): 
                baseUrl = match
        
        # extract qualities
        sts, data = self.cm.getPage(baseUrl, defaultParams)
        if sts:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'Jakość:', '</div>', False)
            if sts:
                data = re.findall('<a[^>]+?href="([^"]+?)"[^>]*?>([^<]+?)</a>', data)
                for urlItem in data:
                    tmpUrls.append({'name':'cda.pl ' + urlItem[1], 'url':urlItem[0]})
        
        if not tmpUrls:
            tmpUrls.append({'name':'cda.pl', 'url':baseUrl})
            
        def __appendVideoUrl(params):
            if params['url'] not in uniqUrls:
                videoUrls.append(params)
                uniqUrls.append(params['url'])
        
        def __ca(dat):
            def __rot47(s):
               x = []
               for i in xrange(len(s)):
                   j = ord(s[i])
                   if j >= 33 and j <= 126:
                       x.append(chr(33 + ((j + 14) % 94)))
                   else:
                       x.append(s[i])
               return ''.join(x)

            def __replace(c):
                code = ord(c.group(1))
                if code <= ord('Z'):
                    tmp = 90
                else: 
                    tmp = 122
                c = code + 13
                if tmp < c:
                    c -= 26
                return chr(c)
            
            if not self.cm.isValidUrl(dat):
                try:
                    if 'uggcf' in dat:
                        dat = re.sub('([a-zA-Z])', __replace, dat)
                        # 'uggc' becomes 'http'
                    else:
                        dat = __rot47(urllib.unquote(dat))
                        dat = dat.replace(".cda.mp4", "").replace(".2cda.pl", ".cda.pl").replace(".3cda.pl", ".cda.pl");
                        dat = 'https://' + str(dat) + '.mp4'
                    if not dat.endswith('.mp4'):
                        dat += '.mp4'
                    dat = dat.replace("0)sss", "")
                except Exception:
                    dat = ''
                    printExc()
            return str(dat)

        def __jsplayer(dat):
            sts, jsdata = self.cm.getPage('https://ebd.cda.pl/js/player.js', defaultParams)
            
            if not sts: 
                return ''

            jscode = self.cm.ph.getSearchGroups(jsdata, '''var\s([a-z]+?,[a-z]+?,.*?);''')[0]
            tmp = jscode.split(',')
            jscode = self.cm.ph.getSearchGroups(jsdata, '''(var\s[a-z]+?,[a-z]+?,.*?;)''')[0]
            
            for item in tmp:
                jscode += self.cm.ph.getSearchGroups(jsdata, '(%s=function\(.*?};)' % item)[0]
            
            jscode += "file = '%s';" % dat;
            
            tmp = self.cm.ph.getSearchGroups(jsdata, '''\(this\.options,"video"\)&&\((.*?)=this\.options\.video\);''')[0] + "."
            
            jscode += self.cm.ph.getDataBeetwenMarkers(jsdata, "%sfile" % tmp, ';', True)[1].replace(tmp, '')
            
            jscode += 'print(file);'
            
            printDBG("--------------- jscode -------------")
            printDBG(jscode)
            printDBG("------------------------------------")
            
            ret = js_execute( jscode )
            
            if ret['sts'] and 0 == ret['code']:
                printDBG("-------- return javascript exec ---------")
                printDBG(ret['data'])
                
                return  ret['data'].strip('\n')
            else:
                return ''
        
        for urlItem in tmpUrls:
            if urlItem['url'].startswith('/'): 
                baseUrl = 'http://www.cda.pl/' + urlItem['url']
            else: 
                baseUrl = urlItem['url']
            
            sts, pageData = self.cm.getPage(baseUrl, defaultParams)
            
            if not sts: 
                continue
            
            tmpData = self.cm.ph.getDataBeetwenMarkers(pageData, "eval(", '</script>', False)[1]
            
            if tmpData:
                m1 = '$.get' 
                if m1 in tmpData:
                    tmpData = tmpData[:tmpData.find(m1)].strip() + '</script>'
                try: 
                    tmpData = unpackJSPlayerParams(tmpData, TEAMCASTPL_decryptPlayerParams, 0, True, True)
                except Exception: 
                    pass
            
            tmpData += pageData
            
            tmp = self.cm.ph.getDataBeetwenMarkers(tmpData, "player_data='", "'", False)[1].strip()
            
            if tmp == '': 
                tmp = self.cm.ph.getDataBeetwenMarkers(tmpData, 'player_data="', '"', False)[1].strip()
            
            tmp = clean_html(tmp).replace('&quot;', '"')
            
            printDBG("------------- tmp -------------")
            printDBG(tmp)
            printDBG("-------------------------------")
            try:
                if tmp:
                    tmpJson = json_loads(tmp)
                    tmp = __jsplayer(tmpJson['video']['file'])
                    if 'cda.pl' not in tmp: 
                        tmp = __ca(tmpJson['video']['file'])
            
            except Exception:
                tmp = ''
                printExc()
            
            if not tmp:
                data = self.cm.ph.getDataBeetwenReMarkers(tmpData, re.compile('''modes['"]?[\s]*:'''), re.compile(']'), False)[1]
                data = re.compile("""file:[\s]*['"]([^'^"]+?)['"]""").findall(data)
            else: 
                data = [tmp]
            
            for index in range(len(data)):
                if data[index].startswith('http'): 
                    if (index == 0):
                        typestr = 'flv'
                    elif (index == 1):
                        typestr = 'mp4'
                    
                    new_url = _decorateUrl(data[index], 'cda.pl', urlItem['url'])
                    
                    __appendVideoUrl({'name': "%s [%s]" % (urlItem['name'], typestr), 'url': new_url})
            
            if not data:
                data = self.cm.ph.getDataBeetwenReMarkers(tmpData, re.compile('video:[\s]*{'), re.compile('}'), False)[1]
                new_url = self.cm.ph.getSearchGroups(data, "'(http[^']+?(?:\.mp4|\.flv)[^']*?)'")[0]
                if new_url:
                    typestr = 'flv'
                    if '.mp4' in data:
                        typestr = 'mp4'

                    new_url = _decorateUrl(new_url , 'cda.pl', urlItem['url'])
                        
                    __appendVideoUrl({'name': "%s [%s]" % (urlItem['name'], typestr), 'url': new_url })

        return videoUrls[::-1]

    def parserDWN(self,url):
        if "play4.swf" in url:
            match = re.search("play4.swf([^']+?)',", url+"',")
        else:
            sts, url = self.cm.getPage(url)
            if not sts: return False
            match = re.search('src="([^"]+?)" width=', url)
            if match:
                sts, url = self.cm.getPage( match.group(1) )
                if not sts: return False
            match = re.search("play4.swf([^']+?)',", url)

        if match:
            url = 'http://st.dwn.so/xml/videolink.php' + match.group(1)
            sts, data = self.cm.getPage(url)
            if not sts: return False
            match = re.search('un="([^"]+?),0"', data)
            if match:
                linkvideo = 'http://' + match.group(1)
                printDBG("parserDWN directURL [%s]" % linkvideo)
                return linkvideo
        return False

    def parserWOOTLY(self,url):
        sts, link = self.cm.getPage(url)
        c = re.search("""c.value="(.+?)";""", link)
        if c:
            cval = c.group(1)
        else:
            return False
        match = re.compile("""<input type=['"]hidden['"] value=['"](.+?)['"].+?name=['"](.+?)['"]""").findall(link)
        if len(match) > 0:
            postdata = {};
            for i in range(len(match)):
                if (len(match[i][0])) > len(cval):
                    postdata[cval] = match[i][1]
                else:
                    postdata[match[i][0]] = match[i][1]
            self.COOKIEFILE = self.COOKIE_PATH + "wootly.cookie"
            params = {'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': self.COOKIEFILE}
            sts, link = self.cm.getPage(url, params, postdata)
            match = re.search("""<video.*\n.*src=['"](.+?)['"]""",link)
            if match:
                return match.group(1)
            else:
                return False
        else:
            return False

    def parserVIDEOWEED(self, url):
        return self._parserUNIVERSAL_B(url)
        
    def parserAURORAVIDTO(self, url):
        return self._parserUNIVERSAL_B(url)

    def parserNOVAMOV(self, url):
        return self._parserUNIVERSAL_B(url)

    def parserNOWVIDEO(self, baseUrl):
        urlTab = []

        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0" }
        
        COOKIE_FILE = GetCookieDir('nowvideo.sx')
        params_s  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params_l  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True} 
        
        if 'embed' not in baseUrl:
            vidId = self.cm.ph.getSearchGroups(baseUrl + '/', '/video/([^/]+?)/')[0]
            if '' == vidId: vidId = self.cm.ph.getSearchGroups(baseUrl + '&', '[\?&]v=([^&]+?)&')[0]
            baseUrl = 'http://embed.nowvideo.sx/embed/?v=' + vidId
        
        sts, data = self.cm.getPage(baseUrl, params_s)
        if not sts: return False
            
        tokenUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?/api/toker[^'^"]+?)['"]''')[0]
        if tokenUrl.startswith('/'):
            tokenUrl = 'http://embed.nowvideo.sx' + tokenUrl
        
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True}
        HTTP_HEADER['Referer'] = baseUrl
        sts, token = self.cm.getPage(tokenUrl, params)
        if not sts: return False
        token = self.cm.ph.getDataBeetwenMarkers(token, '=', ';', False)[1].strip()
         
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?video/mp4''')[0]
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        
        tmp = self._parserUNIVERSAL_B(baseUrl)
        if isinstance(tmp, basestring) and 0 < len(tmp):
            tmp += '?client=FLASH'
        return tmp
        
    def parserSOCKSHARE(self, baseUrl):
        url = url.replace('file', 'embed')
        sts, link = self.cm.getPage(url)
        r = re.search('value="(.+?)" name="fuck_you"', link)
        if r:
            params = { 'url': url.replace('file', 'embed'), 'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': GetCookieDir("sockshare.cookie")}
            postdata = {'fuck_you' : r.group(1), 'confirm' : 'Close Ad and Watch as Free User'}
            
            sts, link = self.cm.getPage(url, params, postdata)

            match = re.compile("playlist: '(.+?)'").findall(link)
            if len(match) > 0:
                url = "http://www.sockshare.com" + match[0]
                sts, link = self.cm.getPage(url)
                match = re.compile('</link><media:content url="(.+?)" type="video').findall(link)
                if len(match) > 0:
                    url = match[0].replace('&amp;','&')
                    return url
                else:
                    return False
            else:
                return False
        else:
            return False

    def parserRAPIDVIDEO(self, baseUrl, getQualityLink=False):
        retTab = []
        
        if not getQualityLink:
            if '/e/' not in baseUrl:
                video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '(?:embed|e|view|v)[/-]([A-Za-z0-9]+)[^A-Za-z0-9]')[0]
                url = 'http://www.rapidvideo.com/e/'+video_id
            else:
                url = baseUrl
        else:
            url = baseUrl
            
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', '')
        
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        if referer != '': HTTP_HEADER['Referer'] = referer
        paramsUrl = {'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(url, paramsUrl)
        if not sts: return False
        
        if not getQualityLink:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, 'Quality:', '<script')[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<a', '</a>')
            for item in tmp:
                url = self.cm.ph.getSearchGroups(item, '''href=['"]([^'^"]+?)['"]''')[0]
                title = clean_html(item).strip()
                if self.cm.isValidUrl(url):
                    try:
                        tmpTab = self.parserRAPIDVIDEO(url, True)
                        for vidItem in tmpTab:
                            vidItem['name'] = '%s - %s' % (title, vidItem['name'])
                            retTab.append(vidItem)
                    except Exception:
                        pass
            if len(retTab): return retTab[::-1]
        
        try:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '.setup(', ');', False)[1].strip()
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '"sources":', ']', False)[1].strip()
            if tmp != '': tmp = json_loads(data+']')
        except Exception:
            printExc()
        
        for item in tmp:
            try: retTab.append({'name':'rapidvideo.com ' + item.get('label', item.get('res', '')), 'url':item['file']})
            except Exception: pass
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>', False)
        for item in tmp:
            url = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if url.startswith('/'):
                url = domain + url[1:]
            if self.cm.isValidUrl(url):
                type = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0] 
                label = self.cm.ph.getSearchGroups(item, '''label=['"]([^'^"]+?)['"]''')[0] 

                if 'video' in type:
                    retTab.append({'name': type + ' ' + label, 'url':url})
                elif 'x-mpeg' in type:
                    retTab.extend(getDirectM3U8Playlist(url, checkContent=True))

        return retTab
        
    def parserVIDEOSLASHER(self, baseUrl):
        url = baseUrl.replace('embed', 'video')
        params = {'use_cookie': True, 'save_cookie': True, 'load_cookie': False, 'cookiefile': GetCookieDir("videoslasher.cookie")}
        postdata = {'confirm': 'Close Ad and Watch as Free User', 'foo': 'bar'}
        
        sts, data = self.cm.getPage(url, params, postdata)
        match = re.compile("playlist: '/playlist/(.+?)'").findall(data)
        if len(match)>0:
            params['load_cookie'] = True
            url = 'http://www.videoslasher.com//playlist/' + match[0]
            sts, data = self.cm.getPage(params)
            match = re.compile('<title>Video</title>.*?<media:content url="(.+?)"').findall(data)
            if len(match)>0:
                sid = self.cm.getCookieItem(self.COOKIEFILE,'authsid')
                if sid != '':
                    streamUrl = urlparser.decorateUrl(match[0], {'Cookie':"authsid=%s" % sid, 'iptv_buffering':'required'})
                    return streamUrl
                else:
                    return False
            else:
                return False
        else:
            return False

    def parserDAILYMOTION(self, baseUrl):
        printDBG("parserDAILYMOTION %s" % baseUrl)

        # source from https://github.com/ytdl-org/youtube-dl/blob/master/youtube_dl/extractor/dailymotion.py
        COOKIE_FILE = self.COOKIE_PATH + "dailymotion.cookie"
        HTTP_HEADER = {"User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36"}
        httpParams = {'header': HTTP_HEADER, 'use_cookie': True, 'save_cookie': False, 'load_cookie': False, 'cookiefile': COOKIE_FILE}
        
        _VALID_URL = r'''(?ix)
                    https?://
                        (?:
                            (?:(?:www|touch)\.)?dailymotion\.[a-z]{2,3}/(?:(?:(?:embed|swf|\#)/)?video|swf)|
                            (?:www\.)?lequipe\.fr/video
                        )
                        /(?P<id>[^/?_]+)(?:.+?\bplaylist=(?P<playlist_id>x[0-9a-z]+))?
                    '''
        
        mobj = re.match(_VALID_URL, baseUrl)
        video_id = mobj.group('id')

        if not video_id:
            printDBG("parserDAILYMOTION -- Video id not found")
            return []
        
        printDBG("parserDAILYMOTION video id: %s " % video_id)
        
        urlsTab =[]

        sts, data = self.cm.getPage(baseUrl, httpParams)

        metadataUrl = 'https://www.dailymotion.com/player/metadata/video/' + video_id
        
        sts, data = self.cm.getPage(metadataUrl, httpParams)
        
        if sts:
            try:
                metadata = json_loads(data)
                
                printDBG("----------------------")
                printDBG(json_dumps(data))
                printDBG("----------------------")

                error = metadata.get('error')
                if error:
                    title = error.get('title') or error['raw_message']
                    
                    # See https://developer.dailymotion.com/api#access-error
                    #if error.get('code') == 'DM007':
                    #    allowed_countries = try_get(media, lambda x: x['geoblockedCountries']['allowed'], list)
                    #    self.raise_geo_restricted(msg=title, countries=allowed_countries)
                    #raise ExtractorError(
                    #    '%s said: %s' % (self.IE_NAME, title), expected=True)

                    printDBG("Error accessing metadata: %s " % title)
                    return []
                     
                #subtitles = {}
                #subtitles_data = try_get(metadata, lambda x: x['subtitles']['data'], dict) or {}
                #for subtitle_lang, subtitle in subtitles_data.items():
                #    subtitles[subtitle_lang] = [{
                #        'url': subtitle_url,
                #    } for subtitle_url in subtitle.get('urls', [])]

                
                for quality, media_list in metadata['qualities'].items():
                    for m in media_list:
                        media_url = m.get('url')
                        media_type = m.get('type')
                        if not media_url or media_type == 'application/vnd.lumberjack.manifest':
                            continue
                        
                        media_url = urlparser.decorateUrl(media_url, {'Referer': baseUrl})
                        if media_type == 'application/x-mpegURL':
                            tmpTab = getDirectM3U8Playlist(media_url, False, checkContent=True, sortWithMaxBitrate=99999999, cookieParams={'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True})
                            cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
                            
                            for tmp in tmpTab:
                                hlsUrl = self.cm.ph.getSearchGroups(tmp['url'], """(https?://[^'^"]+?\.m3u8[^'^"]*?)#?""")[0]
                                redirectUrl =  strwithmeta(hlsUrl, {'iptv_proto':'m3u8', 'Cookie':cookieHeader, 'User-Agent': HTTP_HEADER['User-Agent']})
                                urlsTab.append({'name':'dailymotion.com: %sp hls' % (tmp.get('heigth', '0')), 'url':redirectUrl, 'quality':tmp.get('heigth', '0')})

                        else:
                            urlsTab.append({'name': quality, 'url': media_url})
                
            except:
                printExc
                
        return urlsTab

    def parserSIBNET(self, baseUrl):
        printDBG("parserSIBNET url[%s]" % baseUrl)
        videoUrls = []
        
        videoid = self.cm.ph.getSearchGroups(baseUrl+'|', """videoid=([0-9]+?)[^0-9]""")[0]
        #baseUrl.split('?')[0].endswith('.swf') and
        if '' != videoid: configUrl = "http://video.sibnet.ru/shell_config_xml.php?videoid=%s&partner=null&playlist_position=null&playlist_size=0&related_albid=0&related_tagid=0&related_ids=null&repeat=null&nocache" % (videoid)
        else: configUrl = baseUrl
        # get video for android
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        sts, data = self.cm.getPage(configUrl, {'header':HTTP_HEADER})
        if sts:
            url = self.cm.ph.getSearchGroups(data, """<file>(http[^<]+?\.mp4)</file>""")[0]
            if '' == url: url = self.cm.ph.getSearchGroups(data, """(http[^"']+?\.mp4)""")[0]
            if '' != url: videoUrls.append({'name':'video.sibnet.ru: mp4', 'url':url})
        # get video for PC
        sts, data = self.cm.getPage(configUrl)
        if sts:
            url = self.cm.ph.getSearchGroups(data, """<file>(http[^<]+?)</file>""")[0]
            if '' == url: url = self.cm.ph.getSearchGroups(data, """['"]file['"][ ]*?:[ ]*?['"]([^"^']+?)['"]""")[0]
            if url.split('?')[0].endswith('.m3u8'):
                retTab = getDirectM3U8Playlist(url)
                for item in retTab:
                    videoUrls.append({'name':'video.sibnet.ru: ' + item['name'], 'url':item['url']})
            elif '' != url: videoUrls.append({'name':'video.sibnet.ru: ' + url.split('.')[-1], 'url':url})
        return videoUrls

    def parserVK(self, baseUrl):
        printDBG("parserVK url[%s]" % baseUrl)
        
        COOKIE_FILE = GetCookieDir('vkcom.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'}
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        def _doLogin(login, password):
             
            loginSts = False
            rm(COOKIE_FILE)
            loginUrl = 'https://vk.com/login'
            sts, data = self.cm.getPage(loginUrl, params)
            if not sts: return False
            data = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post"', '</form>', False, False)[1]
            action = self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''')[0]
            printDBG(data)
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            post_data.update({'email':login, 'pass':password})
            if not self.cm.isValidUrl(action):
                return False
            params['header']['Referr'] = loginUrl
            sts, data =  self.cm.getPage(action, params, post_data)
            if not sts: return False
            sts, data =  self.cm.getPage('https://vk.com/', params)
            if not sts: return False            
            if 'logout_link' not in data: return False
            return True
            
        if baseUrl.startswith('http://'):
            baseUrl = 'https' + baseUrl[4:]
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        login    = config.plugins.iptvplayer.vkcom_login.value
        password = config.plugins.iptvplayer.vkcom_password.value
        try:
            vkcom_login = self.vkcom_login
            vkcom_pass  = self.vkcom_pass
        except:
            rm(COOKIE_FILE)
            vkcom_login = ''
            vkcom_pass  = ''
            self.vkcom_login = ''
            self.vkcom_pass  = ''
            
            printExc()
        if '<div id="video_ext_msg">' in data or vkcom_login != login or vkcom_pass != password:
            rm(COOKIE_FILE)
            self.vkcom_login = login
            self.vkcom_pass  = password
            
            if login.strip() == '' or password.strip() == '':
                sessionEx = MainSessionWrapper() 
                sessionEx.waitForFinishOpen(MessageBox, _('To watch videos from http://vk.com/ you need to login.\nPlease fill your login and password in the IPTVPlayer configuration.'), type = MessageBox.TYPE_INFO, timeout = 10 )
                return False
            elif not _doLogin(login, password):
                sessionEx = MainSessionWrapper() 
                sessionEx.waitForFinishOpen(MessageBox, _('Login user "%s" to http://vk.com/ failed!\nPlease check your login data in the IPTVPlayer configuration.' % login), type = MessageBox.TYPE_INFO, timeout = 10 )
                return False
            else:
                sts, data = self.cm.getPage(baseUrl, params)
                if not sts: return False
        
        #data = self.cm.ph.getDataBeetwenMarkers(data, 'var playerParams =', '};', False, False)[1]
        
        movieUrls = []
        item = self.cm.ph.getSearchGroups(data, '''['"]?cache([0-9]+?)['"]?[=:]['"]?(http[^"]+?\.mp4[^;^"^']*)[;"']''', 2)
        if '' != item[1]:
            cacheItem = { 'name': 'vk.com: ' + item[0] + 'p (cache)', 'url':item[1].replace('\\/', '/').encode('UTF-8') }
        else: cacheItem = None
        
        tmpTab = re.findall('''['"]?url([0-9]+?)['"]?[=:]['"]?(http[^"]+?\.mp4[^;^"^']*)[;"']''', data)
        ##prepare urls list without duplicates
        for item in tmpTab:
            item = list(item)
            if item[1].endswith('&amp'): item[1] = item[1][:-4]
            item[1] = item[1].replace('\\/', '/')
            found = False
            for urlItem in movieUrls:
                if item[1] == urlItem['url']:
                    found = True
                    break
            if not found:        
                movieUrls.append({ 'name': 'vk.com: ' + item[0] + 'p', 'url':item[1].encode('UTF-8') })
        ##move default format to first position in urls list
        ##default format should be a configurable
        DEFAULT_FORMAT = 'vk.com: 720p'
        defaultItem = None
        for idx in range(len(movieUrls)):
            if DEFAULT_FORMAT == movieUrls[idx]['name']:
                defaultItem = movieUrls[idx]
                del movieUrls[idx]
                break
        movieUrls = movieUrls[::-1]
        if None != defaultItem:
            movieUrls.insert(0, defaultItem)
        if None != cacheItem:
            movieUrls.insert(0, cacheItem)
        return movieUrls

    def parserPETEAVA(self, url):
        mid = re.search("hd_file=(.+?_high.mp4)&", url)
        movie = "http://content.peteava.ro/video/"+mid.group(1)+"?token=PETEAVARO"
        return movie

    def parserVPLAY(self, url):
        vid = re.search("key=(.+?)$", url)
        url = 'http://www.vplay.ro/play/dinosaur.do'
        postdata = {'key':vid.group(1)}
        link = self.cm.getPage(url, {}, postdata)
        movie = re.search("nqURL=(.+?)&", link)
        if movie:
            return movie.group(1)
        else:
            return False

    def parserIITV(self, url):
        if 'streamo' in url:
            match = re.compile("url: '(.+?)',").findall(self.cm.getPage(url)[1])
        
        if 'nonlimit' in url:
            match = re.compile('url: "(.+?)",     provider:').findall(self.cm.getPage(url + '.html?i&e&m=iitv')[1])
        
        if len(match) > 0:
            linkVideo = match[0]
            printDBG ('linkVideo ' + linkVideo)
            return linkVideo
        else:
            SetIPTVPlayerLastHostError('Przepraszamy\nObecnie zbyt dużo osób ogląda film za pomocą\ndarmowego playera premium.\nSproboj ponownie za jakis czas')
        return False

    def parserDIVXSTAGE(self,url):
        return self._parserUNIVERSAL_B(url)
            
    def parserBESTREAMS(self, baseUrl):
        printDBG("parserBESTREAMS baseUrl[%s]" % baseUrl)
        USER_AGENT = 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '[/-]([A-Za-z0-9]{12})[/-]')[0]
        
        url = 'http://bestreams.net/{0}'.format(video_id)
        
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = USER_AGENT
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})
        
        tries = 0
        while tries < 3:
            tries += 1

            try:
                sleep_time = self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0]
                sleep_time = int(sleep_time)
                if sleep_time < 12: GetIPTVSleep().Sleep(sleep_time)
            except Exception:
                printExc()
            
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
            if not sts: continue
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            HTTP_HEADER['Referer'] = url
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}, post_data)
            if not sts: continue
            #printDBG(data)
            
            try:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, 'id="file_title"', '</a>', False)[1]
                videoUrl = self.cm.ph.getSearchGroups(tmp, 'href="(http[^"]+?)"')[0]
                if '' == videoUrl: continue
                return urlparser.decorateUrl(videoUrl, {'User-Agent':USER_AGENT})
            except Exception:
                printExc()
            
        return False

    def parserTUBECLOUD(self, url):
        params = {'save_cookie': True, 'load_cookie': False, 'cookiefile': GetCookieDir("tubecloud.cookie")}
        sts, link = self.cm.getPage(url, params)
        ID = re.search('name="id" value="(.+?)">', link)
        FNAME = re.search('name="fname" value="(.+?)">', link)
        HASH = re.search('name="hash" value="(.+?)">', link)
        if ID and FNAME and HASH > 0:
            GetIPTVSleep().Sleep(105)
            postdata = {'fname' : FNAME.group(1), 'hash' : HASH.group(1), 'id' : ID.group(1), 'imhuman' : 'Proceed to video', 'op' : 'download1', 'referer' : url, 'usr_login' : '' }
            params.update({'save_cookie': False, 'load_cookie': True})
            sts, link = self.cm.getPage(url, params, postdata)
            match = re.compile('file: "(.+?)"').findall(link)
            if len(match) > 0:
                linkvideo = match[0]
                return linkvideo
            else:
                return self.parserPLAYEDTO(url)
        else:
            return self.parserPLAYEDTO(url)
            
    def parserPLAYEDTO(self, url):
        sts, data = self.cm.getPage(url)
        url = re.search('file: "(http[^"]+?)"', data)
        if url:
            return url.group(1)
        return False
        
    def parserFREEDISC(self, baseUrl):
        linksTab = []
        COOKIE_FILE = GetCookieDir('FreeDiscPL.cookie')
        HTTP_HEADER= {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0 ', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        videoId = self.cm.ph.getSearchGroups(baseUrl, '''\,f\-([0-9]+?)[^0-9]''')[0]
        if videoId == '': videoId = self.cm.ph.getSearchGroups(baseUrl, '''/video/([0-9]+?)[^0-9]''')[0]
        rest = baseUrl.split('/')[-1].split(',')[-1]
        idx  = rest.rfind('-')
        if idx != -1:
            rest = rest[:idx] + '.mp4'
            videoUrl = 'https://stream.freedisc.pl/video/%s/%s' % (videoId, rest)
            try:
                params2 = dict(params)
                params2['max_data_size'] = 0
                params2['header'] = dict(HTTP_HEADER)
                params2['header'].update({'Referer':'https://freedisc.pl/static/player/v612/jwplayer.flash.swf'})
                
                sts, data = self.cm.getPage(videoUrl, params2)
                if 200 == self.cm.meta['status_code']:
                    cookieHeader = self.cm.getCookieHeader(COOKIE_FILE, unquote=False)
                    linksTab.append({'name':'[prepared] freedisc.pl', 'url': urlparser.decorateUrl(self.cm.meta['url'], {'Cookie':cookieHeader, 'Referer':params2['header']['Referer'], 'User-Agent':params2['header']['User-Agent']})}) 
            except Exception:
                printExc()
        
        params.update({'load_cookie':False, 'cookiefile':GetCookieDir('FreeDiscPL_2.cookie')})
        
        tmpUrls = []
        if '/embed/' not in baseUrl:
            sts, data = self.cm.getPage(baseUrl, params)
            if not sts: return linksTab
            try:
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<script type="application/ld+json">', '</script>', False)[1]
                tmp = json_loads(tmp)
                tmp = tmp['embedUrl'].split('?file=')
                if tmp[1].startswith('http'):
                    linksTab.append({'name':'freedisc.pl', 'url': urlparser.decorateUrl(tmp[1], {'Referer':tmp[0], 'User-Agent':HTTP_HEADER['User-Agent']})})
                    tmpUrls.append(tmp[1])
            except Exception:
                printExc()
                
            videoUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?/embed/[^"^']+?)["']''', 1, True)[0]
        else:
            videoUrl = baseUrl
        
        if '' != videoUrl:
            params['load_cookie'] = True
            params['header']['Referer'] = baseUrl
            
            sts, data = self.cm.getPage(videoUrl, params)
            if sts:
                videoUrl = self.cm.ph.getSearchGroups(data, '''data-video-url=["'](http[^"^']+?)["']''', 1, True)[0]
                if videoUrl == '': videoUrl = self.cm.ph.getSearchGroups(data, '''player.swf\?file=(http[^"^']+?)["']''', 1, True)[0]
                if videoUrl.startswith('http') and  videoUrl not in tmpUrls:
                    linksTab.append({'name':'freedisc.pl', 'url': urlparser.decorateUrl(videoUrl, {'Referer':'http://freedisc.pl/static/player/v612/jwplayer.flash.swf', 'User-Agent':HTTP_HEADER['User-Agent']})}) 
        return linksTab

    def parserGINBIG(self,url):
        sts, link = self.cm.getPage(url)
        ID = re.search('name="id" value="(.+?)">', link)
        FNAME = re.search('name="fname" value="(.+?)">', link)
        if ID and FNAME > 0:
            postdata = { 'op': 'download1', 'id': ID.group(1), 'fname': FNAME.group(1), 'referer': url, 'method_free': 'Free Download', 'usr_login': '' }
            sts, link = self.cm.getPage(url, {}, postdata)
            data = link.replace('|', '<>')
            PL = re.search('<>player<>(.+?)<>flvplayer<>', data)
            HS = re.search('video<>(.+?)<>(.+?)<>file<>', data)
            if PL and HS > 0:
                linkVideo = 'http://' + PL.group(1) + '.ginbig.com:' + HS.group(2) + '/d/' + HS.group(1) + '/video.mp4?start=0'
                print ('linkVideo ' + linkVideo)
                return linkVideo
            else:
                return False
        else:
            return False

    def parserQFER(self, url):
        match = re.compile('"PSST",url: "(.+?)"').findall(self.cm.getPage(url)[1])
        if len(match) > 0:
            linkVideo = match[0]
            print ('linkVideo ' + linkVideo)
            return linkVideo
        else:
            return False

    def parserSTREAMCLOUD(self, baseUrl):
        printDBG("parserSTREAMCLOUD [%s]" % baseUrl)
        # code from https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/streamcloud.py
    
        _VALID_URL = r'https?://streamcloud\.eu/(?P<id>[a-zA-Z0-9_-]+)(?:/(?P<fname>[^#?]*)\.html)?'
        mobj = re.match(_VALID_URL, baseUrl)
        video_id = mobj.group('id')
        url = 'http://streamcloud.eu/%s' % video_id
        
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(url, urlParams)
        if not sts: return False
        
        fields = re.findall(r'''(?x)<input\s+
            type="(?:hidden|submit)"\s+
            name="([^"]+)"\s+
            (?:id="[^"]+"\s+)?
            value="([^"]*)"
            ''', data)
            
        if 0 == len(fields):
            msg = self.cm.ph.getDataBeetwenMarkers(data, '<div id="file"', '</div>')[1]
            msg = clean_html(self.cm.ph.getDataBeetwenMarkers(data, '<p', '</p>')[1])
            SetIPTVPlayerLastHostError(msg)
        else:
            try: t = int(self.cm.ph.getSearchGroups(data, '''var\s*count\s*=\s*([0-9]+?)\s*;''')[0]) + 1
            except Exception:
                printExc()
                t = 12
            GetIPTVSleep().Sleep(t)
        
        sts, data = self.cm.getPage(url, urlParams, fields)
        if not sts: return False
        cUrl = self.cm.meta['url']
        
        file = self.cm.getFullUrl(self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0], cUrl)
        if file != '':
            return strwithmeta(file, {'Referer':cUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
            
        msg = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'msgboxinfo'), ('</div', '>'), False)[1])
        SetIPTVPlayerLastHostError(msg)
        return False

    def parserLIMEVIDEO(self,url):
        sts, link = self.cm.getPage(url)
        ID = re.search('name="id" value="(.+?)">', link)
        FNAME = re.search('name="fname" value="(.+?)">', link)
        if ID and FNAME > 0:
            GetIPTVSleep().Sleep(205)
            postdata = {'fname' : FNAME.group(1), 'id' : ID.group(1), 'method_free' : 'Continue to Video', 'op' : 'download1', 'referer' : url, 'usr_login' : '' }
            sts, link = self.cm.getPage(url, {}, postdata)
            ID = re.search('name="id" value="(.+?)">', link)
            RAND = re.search('name="rand" value="(.+?)">', link)
            table = self.captcha.textCaptcha(link)
            value = table[0][0] + table [1][0] + table [2][0] + table [3][0]
            code = clean_html(value)
            printDBG('captcha-code :' + code)
            if ID and RAND > 0:
                postdata = {'rand' : RAND.group(1), 'id' : ID.group(1), 'method_free' : 'Continue to Video', 'op' : 'download2', 'referer' : url, 'down_direct' : '1', 'code' : code, 'method_premium' : '' }
                sts, link = self.cm.getPage(url, {}, postdata)
                data = link.replace('|', '<>')
                PL = re.search('<>player<>video<>(.+?)<>(.+?)<>(.+?)<><>(.+?)<>flvplayer<>', data)
                HS = re.search('image<>(.+?)<>(.+?)<>(.+?)<>file<>', data)
                if PL and HS > 0:
                    linkVideo = 'http://' + PL.group(4) + '.' + PL.group(3) + '.' + PL.group(2) + '.' + PL.group(1) + ':' + HS.group(3) + '/d/' + HS.group(2) + '/video.' + HS.group(1)
                    printDBG('linkVideo :' + linkVideo)
                    return linkVideo
        return False

    def parserSCS(self,url):
        sts, link = self.cm.getPage(url)
        ID = re.search('"(.+?)"; ccc', link)
        if ID > 0:
            postdata = {'f' : ID.group(1) }
            sts, link = self.cm.getPage('http://scs.pl/getVideo.html', {}, postdata)
            match = re.compile("url: '(.+?)',").findall(link)
            if len(match) > 0:
                linkVideo = match[0]
                print ('linkVideo ' + linkVideo)
                return linkVideo
            else:
                print ('Przepraszamy','Obecnie zbyt dużo osób ogląda film za pomocą', 'darmowego playera premium.', 'Sproboj ponownie za jakis czas')
                return False
        else:
            return False
        
    def parserYOUWATCH(self, baseUrl):
        if 'embed' in baseUrl:
            url = baseUrl
        else:
            url = baseUrl.replace('org/', 'org/embed-').replace('to/', 'to/embed-') + '.html'
        COOKIE_FILE = GetCookieDir('youwatchorg.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0'}
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        tries = 0
        while tries < 3:
            tries += 1
            sts, data = self.cm.getPage(url, params)
            if not sts: return False
            if 'sources:' in data:
                break
            else:
                params['header']['Referer'] = url
                url = self.cm.ph.getSearchGroups(data, '<iframe[^>]*?src="(http[^"]+?)"', 1, True)[0].replace('\n', '')
        try:       
            linksTab = self._findLinks(data)
            if len(linksTab):
                for idx in range(len(linksTab)):
                    linksTab[idx]['url'] = urlparser.decorateUrl(linksTab[idx]['url'], {'User-Agent':HTTP_HEADER['User-Agent'],'Referer': url})
                return linksTab
        except Exception:
            pass
        
        def rc4(e, code):
            d = base64.b64decode(base64.b64decode(base64.b64decode(code)))
            b = []
            for a in range(256):
                b.append(a)
            c = 0
            for a in range(256):
                c = (c + b[a] + ord(d[a % len(d)])) % 256
                f = b[a]
                b[a] = b[c]
                b[c] = f
            a = 0
            c = 0
            d = 0
            g = ""
            for d in range(len(e)): 
                a = (a + 1) % 256
                c = (c + b[a]) % 256
                f = b[a]
                b[a] = b[c]
                b[c] = f
                g += chr(ord(e[d]) ^ b[(b[a] + b[c]) % 256])
            return g
        
        def link(e, code):
            e = base64.b64decode(base64.b64decode(e))
            return rc4(e, code)
        
        jsUrl = self.cm.ph.getSearchGroups(data, '"(http[^"]+?==\.js)"', 1, True)[0]
        sts, data = self.cm.getPage(jsUrl, params)
        printDBG(data)
        code = self.cm.ph.getSearchGroups(data, 'code[ ]*?\=[ ]*?"([^"]+?)"')[0]
        direct_link = self.cm.ph.getSearchGroups(data, 'direct_link[ ]*?\=[^"]*?"([^"]+?)"')[0]    
        videoUrl = link(direct_link, code)
        if not videoUrl.strtswith("http"): return False
        videoUrl = urlparser.decorateUrl(videoUrl, {'User-Agent':HTTP_HEADER['User-Agent'],'Referer': url})
        return videoUrl
        
    def parserSTREAMENET(self, baseUrl):
        return self.parserWATCHERSTO(baseUrl)
        
    def parserESTREAMTO(self, baseUrl):
        return self.parserWATCHERSTO(baseUrl)
        
    def parserWATCHERSTO(self, baseUrl):
        if 'embed' in baseUrl:
            url = baseUrl
        else:
            url = baseUrl.replace('org/', 'org/embed-').replace('to/', 'to/embed-').replace('me/', 'me/embed-').replace('.net/', '.net/embed-')
            if not url.endswith('.html'):
             url += '-640x360.html'

        sts, allData = self.cm.getPage(url)
        if not sts: return False
        
        errMsg = clean_html(CParsingHelper.getDataBeetwenMarkers(allData, '<div class="delete"', '</div>')[1]).strip()
        if errMsg != '': SetIPTVPlayerLastHostError(errMsg)
        
        # get JS player script code from confirmation page
        sts, tmpData = CParsingHelper.getDataBeetwenMarkers(allData, ">eval(", '</script>', False)
        if sts:
            data = tmpData
            tmpData = None
            # unpack and decode params from JS player script code
            data = unpackJSPlayerParams(data, VIDUPME_decryptPlayerParams, 0, r2=True) #YOUWATCH_decryptPlayerParams == VIDUPME_decryptPlayerParams
            printDBG(data)
        else:
            data = allData
        
        # get direct link to file from params
        linksTab = self._findLinks(data, serverName=urlparser.getDomain(baseUrl), meta={'Referer':baseUrl})
        if len(linksTab): return linksTab
        
        domain = urlparser.getDomain(url, False) 
        tmp = self.cm.ph.getDataBeetwenMarkers(allData, '<video', '</video>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>', False)
        for item in tmp:
            url = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            type = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0]
            if 'video' not in type and 'x-mpeg' not in type: continue
            if url.startswith('/'):
                url = domain + url[1:]
            if self.cm.isValidUrl(url):
                if 'video' in type:
                    linksTab.append({'name':'[%s]' % type, 'url':url})
                elif 'x-mpeg' in type:
                    linksTab.extend(getDirectM3U8Playlist(url, checkContent=True))
        return linksTab[::-1]

    def parserPLAYEDTO(self, baseUrl):
        if 'embed' in baseUrl:
            url = baseUrl
        else:
            url = baseUrl.replace('org/', 'org/embed-').replace('to/', 'to/embed-').replace('me/', 'me/embed-')
            if not url.endswith('.html'):
             url += '-640x360.html'
             
        #HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10'}
        #, {'header':HTTP_HEADER}
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        url = self.cm.ph.getSearchGroups(data, '<iframe[^>]*?src="(http[^"]+?)"', 1, True)[0]
        if url != '':
            sts, data = self.cm.getPage(url, {'header':{'Referer':url, 'User-Agent':'Mozilla/5.0'}})
            if not sts: return False
        
        # get JS player script code from confirmation page
        sts, tmpData = CParsingHelper.getDataBeetwenMarkers(data, ">eval(", '</script>', False)
        if sts:
            data = tmpData
            tmpData = None
            # unpack and decode params from JS player script code
            data = unpackJSPlayerParams(data, VIDUPME_decryptPlayerParams, 0) #YOUWATCH_decryptPlayerParams == VIDUPME_decryptPlayerParams

        printDBG(data)
        return self._findLinks(data, serverName='played.to')

    def parserVIDEOMEGA(self, baseUrl):
        baseUrl = strwithmeta(baseUrl)
        Referer = baseUrl.meta.get('Referer', 'http://nocnyseans.pl/film/chemia-2015/15471') 
        
        video_id  = self.cm.ph.getSearchGroups(baseUrl, 'https?://(?:www\.)?videomega\.tv/(?:iframe\.php|cdn\.php|view\.php)?\?ref=([A-Za-z0-9]+)')[0]
        if video_id == '': video_id = self.cm.ph.getSearchGroups(baseUrl + '&', 'ref=([A-Za-z0-9]+)[^A-Za-z0-9]')[0]
        COOKIE_FILE = GetCookieDir('videomegatv.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36',
                       'Accept-Encoding':  'gzip,deflate,sdch'} # (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10' }
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        #if 'iframe' in baseUrl:
        #    iframe_url = 'http://videomega.tv/iframe.php?ref=%s' % (video_id)
        #    url = 'http://videomega.tv/iframe.php?ref=%s' % (video_id)
        #else:
            
        for i in range(2):
        
            if i == 0:
                iframe_url = 'http://videomega.tv/?ref=%s' % (video_id)
                url = 'http://videomega.tv/cdn.php?ref=%s' % (video_id)
            else:
                url = 'http://videomega.tv/view.php?ref=%s&width=730&height=440&val=1' % (video_id)
                iframe_url = url
            
            HTTP_HEADER['Referer'] = Referer
            sts, data = self.cm.getPage(url, params)
            if not sts: 
                continue
            if 'dmca ' in data:
                DMCA = True
                SetIPTVPlayerLastHostError("'Digital Millennium Copyright Act' detected.")
                return False
            else: DMCA = False
            
            adUrl =self.cm.ph.getSearchGroups(data, '"([^"]+?/ad\.php[^"]+?)"')[0]
            if adUrl.startswith("/"): 
                adUrl = 'http://videomega.tv' + adUrl
            
            params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True} 
            HTTP_HEADER['Referer'] = url
            if adUrl:
                sts, tmp = self.cm.getPage(adUrl, params)
            
            subTracksData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<track ', '>', False, False)
            subTracks = []
            for track in subTracksData:
                if 'kind="captions"' not in track: continue
                subUrl = self.cm.ph.getSearchGroups(track, 'src="(http[^"]+?)"')[0]
                subLang = self.cm.ph.getSearchGroups(track, 'srclang="([^"]+?)"')[0]
                subLabel = self.cm.ph.getSearchGroups(track, 'label="([^"]+?)"')[0]
                subTracks.append({'title':subLabel + '_' + subLang, 'url':subUrl, 'lang':subLang, 'format':'srt'})
            
            linksTab = []
            fakeLinkVideo  = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"[^>]+?type="video')[0]
            
            # get JS player script code from confirmation page
            sts, data = CParsingHelper.getDataBeetwenMarkers(data, "eval(", '</script>')
            if not sts: continue
            
            printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            printDBG(data)
            printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            
            # unpack and decode params from JS player script code
            decrypted = False
            for decryptor in [SAWLIVETV_decryptPlayerParams, VIDUPME_decryptPlayerParams]:
                try:
                    data = unpackJSPlayerParams(data, decryptor, 0)
                    if len(data):
                        decrypted = True
                    break
                except Exception:
                    continue
            if not decrypted: continue
            
            linkVideo  = self.cm.ph.getSearchGroups(data, '"(http[^"]+?\.mp4\?[^"]+?)"')[0]
            
            if fakeLinkVideo == linkVideo:
                SetIPTVPlayerLastHostError(_("Videomega has blocked your IP for some time.\nPlease retry this link after some time."))
                if i == 0: GetIPTVSleep().Sleep(3)
                continue
            
            #printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            #printDBG("DMCA [%r]" % DMCA)

            if linkVideo.startswith('http'):
                linksTab.append({'name': 'videomega_2', 'url':urlparser.decorateUrl(linkVideo, {'external_sub_tracks':subTracks, "iptv_wget_continue":True, "iptv_wget_timeout":10, "Orgin": "http://videomega.tv/", 'Referer': url, 'User-Agent':HTTP_HEADER['User-Agent'], 'iptv_buffering':'required'})})
            #"Cookie": "__cfduid=1", "Range": "bytes=0-",
        return linksTab

    def parserVIDTO(self, baseUrl):
        printDBG('parserVIDTO baseUrl[%s]' % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        if 'embed' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{12})[\./]')[0]
            url = 'http://vidto.me/embed-{0}-640x360.html'.format(video_id)
        else:
            url = baseUrl 
        params = {'header' : HTTP_HEADER}
        sts, data = self.cm.getPage(url, params)
        
        if '<b>File Not Found</b>' in data:
            SetIPTVPlayerLastHostError(_('File Not Found.'))
        
        # get JS player script code from confirmation page
        tmp = CParsingHelper.getDataBeetwenMarkers(data, ">eval(", '</script>')[1]
        if not sts: return False
        # unpack and decode params from JS player script code
        tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
        if tmp != None: data = tmp + data
        printDBG(tmp)
        subData = CParsingHelper.getDataBeetwenMarkers(data, "captions", '}')[1]
        subData = self.cm.ph.getSearchGroups(subData, '''['"](http[^'^"]+?)['"]''')[0]
        sub_tracks = []
        if (subData.startswith('https://') or subData.startswith('http://')) and (subData.endswith('.srt') or subData.endswith('.vtt')):
            sub_tracks.append({'title':'attached', 'url':subData, 'lang':'unk', 'format':'srt'})
        linksTab = []
        links = self._findLinks(data, 'vidto.me')
        for item in links:
            item['url'] = strwithmeta(item['url'], {'external_sub_tracks':sub_tracks})
            linksTab.append(item)
        return linksTab

    def parserVIDSTREAM(self, url):
        printDBG('parserVIDSTREAM baseUrl[%s]' % url)
        HTTP_HEADER= {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36', 
                      'Accept': 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
                      'Accept-Encoding':'gzip, deflate' 
                     }
        COOKIE_FILE = GetCookieDir('vidstream.cookie') 
        http_params={'header': HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True}
        
        sts, data = self.cm.getPage(url, http_params)

        
        if not sts: return
        printDBG("------------")
        printDBG(data)
        printDBG("------------")

        
        ID = re.search('name="id" value="(.+?)">', data)
        FNAME = re.search('name="fname" value="(.+?)">', data)
        HASH = re.search('name="hash" value="(.+?)">', data)

        if ID and FNAME and HASH > 0:
            # previous version
            GetIPTVSleep().Sleep(55)
            postdata = {'fname' : FNAME.group(1), 'id' : ID.group(1), 'hash' : HASH.group(1), 'imhuman' : 'Proceed to video', 'op' : 'download1', 'referer' : url, 'usr_login' : '' }
            sts, link = self.cm.getPage(url, {}, postdata)
            match = re.compile('file: "(.+?)",').findall(link)
            if len(match) > 0:
                linkVideo = match[0]
                printDBG ('linkVideo :' + linkVideo)
                return linkVideo
            else:
                return False
        else:
            # new
            url2 = re.findall("<source src=[\"'](.*?)[\"']", data)
            # controllare
            if url2:
                url2 = self.cm.getFullUrl(url2[0], self.cm.getBaseUrl(url))
                printDBG("---------> %s " % url )
                videoUrls = getDirectM3U8Playlist(url2, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                return videoUrls
            else:
                # look for javascript
                script =''
                tmp_script = re.findall("<script.*?>(.*?)</script>", data, re.S)
                for s in tmp_script:
                    if s.startswith('function'):
                        script = s
                        break

                if script:
                    #printDBG("------------")
                    printDBG(script)
                    printDBG("------------")

                    #  model for step }(a, 0x1b4));
                    # search for big list of words
                    tmpStep = re.findall("}\(a ?,(0x[0-9a-f]{1,3})\)\);", script) 
                    if tmpStep:
                        step = eval(tmpStep[0])
                    else:
                        step = 128
                    
                    printDBG("----> step: %s -> %s" % (tmpStep[0], step))
                    
                    # search post data
                    # ,'data':{'_OvhoOHFYjej7GIe':'ok'}
                    post_key = re.findall("'data':{'(_[0-9a-zA-Z]{10,20})':'ok'", script)
                    if post_key:
                        post_key = post_key[0]
                        printDBG("post_key : '%s'" % post_key)
                    else:
                        printDBG("Not found post_key ... check code")
                        return 
                    
                    tmpVar = re.findall("(var a=\[.*?\];)", script)
                    if tmpVar:
                        wordList=[]
                        var_list = tmpVar[0].replace('var a=','wordList=').replace("];","]").replace(";","|")
                        printDBG("------------")
                        printDBG(var_list)
                        #printDBG("------------")
                        exec(var_list)
                        #for i in range(0, 20):
                        #    printDBG(wordList[i])
                        
                        # search for second list of vars
                        tmpVar2 = re.findall(";e\(\);(var .*?)\$\('\*'\)", script, re.S)
                        if tmpVar2:
                            printDBG("------------")
                            printDBG(tmpVar2[0])
                            threeListNames = re.findall("var (_[a-zA-z0-9]{4,8})=\[\];" , tmpVar2[0])
                            printDBG(str(threeListNames))
                            for n in range(0, len(threeListNames)):
                                tmpVar2[0] = tmpVar2[0].replace(threeListNames[n],"charList%s" % n) 
                            
                            # substitutions of terms from first list
                            for i in range(0,len(wordList)):
                                r = "b('0x{:x}')".format(i)
                                j = i + step
                                while j >= len(wordList): 
                                    j = j - len(wordList)
                                tmpVar2[0] = tmpVar2[0].replace(r, "'%s'" % wordList[j])
                            
                            var2_list=tmpVar2[0].split(';')
                            printDBG("------------")
                            printDBG(str(var2_list))
                            # populate array
                            charList0={}
                            charList1={}
                            charList2={}
                            for v in var2_list:
                                if v.startswith('charList'):
                                    exec(v)        
                            
                            bigString=''
                            for i in range(0,len(charList2)):
                                #printDBG(charList2[i])
                                if charList2[i] in charList1:
                                    bigString = bigString + charList1[charList2[i]]
                                #else:
                                    #printDBG("missing key %s " % charList2[i])
                            printDBG("------------")
                            printDBG(bigString)

                            sts, data = self.cm.getPage(urlparser.getDomain(url, False) + "cv.php", http_params)
                            
                            cv_url = urlparser.getDomain(url, False) + "cv.php?verify=" + bigString
                            postData={ post_key : 'ok'}
                            
                            AJAX_HEADER = {
                                'Accept': '*/*',
                                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                                'Origin': self.cm.getBaseUrl(url),
                                'Referer': url,
                                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
                                'X-Requested-With': 'XMLHttpRequest'
                            }

                            sts, ret = self.cm.getPage(cv_url, {'header': AJAX_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True}, postData)
                            if sts:
                                printDBG("------------")
                                printDBG(ret)
                                if 'ok' in ret:
                                    if '?' in url:
                                        url2 = url + "&r"
                                    else:
                                        url2 = url + "?r"

                                    # retry to load the page
                                    GetIPTVSleep().Sleep(1)
                                    http_params['header']['Referer'] = url
                                    sts, data = self.cm.getPage(url2, http_params)
                                    if sts:
                                        printDBG("------------")
                                        printDBG(data)
                                    url3 = re.findall("<source src=[\"'](.*?)[\"']", data)
                                    if url3:
                                        url3 = self.cm.getFullUrl(url3[0], self.cm.getBaseUrl(url))
                                        printDBG("---------> %s " % url )
                                        videoUrls = getDirectM3U8Playlist(url3, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                                        return videoUrls

    def parserYANDEX(self, url):
        DEFAULT_FORMAT = 'mpeg4_low'
        # authorization
        authData = ''
        urlElems = urlparse(url)
        urlParams = parse_qs(urlElems.query)
        if 0 < len(urlParams.get('file', [])):
            return urlParams['file'][0]
        elif 0 < len(urlParams.get('login', [])) and 0 < len(urlParams.get('storage_directory', [])):
            authData = urlParams['login'][0] + '/' + urlParams['storage_directory'][0]
        elif 'vkid=' in url:
            sts, data = self.cm.getPage(url)
            if not sts: return False
            data = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"')[0]
            return urlparser().getVideoLink(data, True)
        else:
            # last chance
            r = re.compile('iframe/(.+?)\?|$').findall(url)
            if 0 <= len(r): return False
            authData = r[0]
        # consts
        playerUrlPrefix    = "http://flv.video.yandex.ru/"
        tokenUrlPrefix     = "http://static.video.yandex.ru/get-token/"
        serviceHostUrl     = "http://video.yandex.ru/"
        storageHostUrl     = "http://static.video.yandex.ru/"
        clipStorageHostUrl = "http://streaming.video.yandex.ru/"
        nameSpace          = "get"
        FORMATS_MAP = {}
        FORMATS_MAP["flv_low"]          = "0.flv"
        FORMATS_MAP["mpeg4_low"]        = "m450x334.mp4"
        FORMATS_MAP["mpeg4_med"]        = "medium.mp4"
        FORMATS_MAP["mpeg4_hd_720p"]    = "m1280x720.mp4"
        FORMATS_MAP["flv_h264_low"]     = "m450x334.flv"
        FORMATS_MAP["flv_h264_med"]     = "medium.flv"
        FORMATS_MAP["flv_h264_hd_720p"] = "m1FLV_SAME_QUALITY280x720.flv"
        FORMATS_MAP["flv_same_quality"] = "sq-medium.flv"
        
        # get all video formats info
        # http://static.video.yandex.ru/get/eriica/xeacxjweav.5822//0h.xml?nc=0.9776535825803876
        url = storageHostUrl + nameSpace + "/" + authData + "/0h.xml?nc=" + str(random())
        sts, data = self.cm.getPage(url)
        if not sts: return False
        try:
            formatsTab = []
            defaultItem = None
            for videoFormat in cElementTree.fromstring(data).find("formats_available").getiterator():
                fileName = FORMATS_MAP.get(videoFormat.tag, '')
                if '' != fileName:
                    bitrate  = int(videoFormat.get('bitrate', 0))
                    formatItem = { 'bitrate': bitrate, 'file':fileName, 'ext':fileName[-3:] }
                    if DEFAULT_FORMAT == videoFormat.tag:
                        defaultItem = formatItem
                    else:
                        formatsTab.append(formatItem)
            if None != defaultItem: formatsTab.insert(0, defaultItem)
            if 0 == len(formatsTab): return False
            # get token
            token = tokenUrlPrefix + authData + "?nc=" + str(random())
            sts, token = self.cm.getPage(token)
            sts, token = CParsingHelper.getDataBeetwenMarkers(token, "<token>", '</token>', False)
            if not sts:
                printDBG("parserYANDEX - get token problem")
                return False
            movieUrls = []
            for item in formatsTab:
                # get location
                location = clipStorageHostUrl + 'get-location/' + authData + '/' + item['file'] + '?token=' + token + '&ref=video.yandex.ru'
                sts, location = self.cm.getPage(location)
                sts, location = CParsingHelper.getDataBeetwenMarkers(location, "<video-location>", '</video-location>', False)
                if sts: movieUrls.append({ 'name': 'yandex.ru: ' + item['ext'] + ' bitrate: ' + str(item['bitrate']), 'url':location.replace('&amp;', '&') })
                else: printDBG("parserYANDEX - get location problem")
            return movieUrls
        except Exception:
            printDBG("parserYANDEX - formats xml problem")
            printExc()
            return False
        
    def parserANIMESHINDEN(self, url):
        self.cm.getPage(url, {'max_data_size':0})
        return self.cm.meta['url']

    def parserRUTUBE(self, url):
        printDBG("parserRUTUBE baseUrl[%s]" % url)

        videoUrls = []
        videoID = ''
        videoPrivate = ''
        url = url + '/'
        
        #if '//rutube.ru/video/embed' in url or '//rutube.ru/play/embed/' in url:
        #    sts, data = self.cm.getPage(url)
        #    if not sts: 
        #        return False
        #    url = self.cm.ph.getSearchGroups(data, '''<link[^>]+?href=['"]([^'^"]+?)['"]''')[0]

        
        videoID = re.findall("[^0-9^a-z]([0-9a-z]{32})[^0-9^a-z]", url)
        if not videoID:
            videoID = re.findall("/([0-9]+)[/\?]", url)
        
        if '/private/' in url: 
            videoPrivate = self.cm.ph.getSearchGroups(url+'&', '''[&\?]p=([^&^/]+?)[&/]''')[0]
        
        if videoID:
            videoID = videoID[0]
            printDBG('parserRUTUBE: videoID[%s]' % videoID)
            # get videoInfo:
            #vidInfoUrl = 'http://rutube.ru/api/play/trackinfo/%s/?format=json' % videoID
            vidInfoUrl = 'http://rutube.ru/api/play/options/%s/?format=json&referer=&no_404=true&sqr4374_compat=1' % videoID
            if videoPrivate != '': 
                vidInfoUrl += '&p=' + videoPrivate
            
            sts, data = self.cm.getPage(vidInfoUrl)
            data = json_loads(data)
            if 'm3u8' in data['video_balancer'] and self.cm.isValidUrl(data['video_balancer'].get('m3u8', '')):
                videoUrls = getDirectM3U8Playlist(data['video_balancer']['m3u8'], checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
            elif 'json' in data['video_balancer'] and self.cm.isValidUrl(data['video_balancer'].get('json', '')): 
                sts, data = self.cm.getPage(data['video_balancer']['json'])
                printDBG(data)
                data = json_loads(data)
                if self.cm.isValidUrl(data['results'][0]):
                    videoUrls.append({'name':'default', 'url':data['results'][0]})
        
        return videoUrls




    def parserYOUTUBE(self, url):
        sts, datal = self.cm.getPage(url)
        videoUrls = []
        if "channel" and "live" in url or "user" and "live" in url:
            url = url.replace("live", "")
            sts, datal = self.cm.getPage(url)
            data1 = self.cm.ph.getAllItemsBeetwenMarkers(datal, '{"videoRenderer":{"videoId":"', '","thumbnail":{"thumbnails":', False)
            if not data1:
			    data1 = self.cm.ph.getAllItemsBeetwenMarkers(datal, '{"horizontalListRenderer":{"items":[{"gridVideoRenderer":{"videoId":"', '","thumbnail":{"thumbnails":', False)
            data2 = self.cm.ph.getAllItemsBeetwenMarkers(datal, '}]},"title":{"runs":[{"text":"', '"}],"accessibility":', False)
            if not data2:
			    data2 = self.cm.ph.getAllItemsBeetwenMarkers(datal, '"simpleText":"', '"},"navigationEndpoint":', False)
            for item in data1:
                url = "https://youtube.com/watch?v=" + item
                sts, datal = self.cm.getPage(url)
                data = self.cm.ph.getDataBeetwenMarkers(datal, '"hlsManifestUrl":"', '"},"heartbeatParams":', False) [1]	
                sts, data = self.cm.getPage(data)
                if not sts:
                    data = self.cm.ph.getDataBeetwenMarkers(datal, '"hlsManifestUrl":"', '","probeUrl"', False) [1]
                    sts, data = self.cm.getPage(data)
                try:
                   data = data.split()
                   url = data[-1]
                   uri = urlparser.decorateParamsFromUrl(url)
                   name = data2[data1.index(item)]
                   videoUrls.append({'name':name, 'url':uri})
                except:
				   pass
            return videoUrls
           
        if "channel" in url or "user" in url:
            url = "https://youtube.com/watch?v=" + self.cm.ph.getDataBeetwenMarkers(datal, 'gridVideoRenderer":{"videoId":"', '","thumbnail":', False) [1]
        def __getLinkQuality( itemLink ):
            val = itemLink['format'].split('x', 1)[0].split('p', 1)[0]
            try:
                val = int(val) if 'x' in itemLink['format'] else int(val) - 1
                return val
            except Exception:
                return 0

        if None != self.getYTParser():
            try:
                formats = config.plugins.iptvplayer.ytformat.value
                height = config.plugins.iptvplayer.ytDefaultformat.value
                dash    = self.getYTParser().isDashAllowed()
                age     = self.getYTParser().isAgeGateAllowed()
            except Exception:
                printDBG("parserYOUTUBE default ytformat or ytDefaultformat not available here")
                formats = "mp4"
                height = "360"
                dash    = False
                age     = False
        if '"is_viewed_live","value":"True"' in datal:
            data = self.cm.ph.getDataBeetwenMarkers(datal, '"hlsManifestUrl":"', '"},"heartbeatParams":', False) [1]	
            sts, data = self.cm.getPage(data)
            if not sts:
                data = self.cm.ph.getDataBeetwenMarkers(datal, '"hlsManifestUrl":"', '","probeUrl"', False) [1]
                sts, data = self.cm.getPage(data)
            data = data.split()
            url = data[-1]
            videoUrls = []
            uri = urlparser.decorateParamsFromUrl(url)
            videoUrls.append({'name':'direct link', 'url':uri})
            return videoUrls
        else:
           tmpTab, dashTab = self.getYTParser().getDirectLinks(url, formats, dash, dashSepareteList = True, allowAgeGate = age)
           #tmpTab = CSelOneLink(tmpTab, __getLinkQuality, int(height)).getSortedLinks()
           #dashTab = CSelOneLink(dashTab, __getLinkQuality, int(height)).getSortedLinks()

           videoUrls = []
           for item in tmpTab:
               url = strwithmeta(item['url'], {'youtube_id':item.get('id', '')})
               videoUrls.append({ 'name': 'YouTube | {0}: {1}'.format(item['ext'], item['format']), 'url':url, 'format':item.get('format', '')})
           for item in dashTab:
               url = strwithmeta(item['url'], {'youtube_id':item.get('id', '')})
               if item.get('ext', '') == 'mpd':
                   videoUrls.append({'name': 'YouTube | dash: ' + item['name'], 'url':url, 'format':item.get('format', '')})
               else:
                   videoUrls.append({'name': 'YouTube | custom dash: ' + item['format'], 'url':url, 'format':item.get('format', '')})

           videoUrls = CSelOneLink(videoUrls, __getLinkQuality, int(height)).getSortedLinks()
           return videoUrls
    
    
        
    def parserTINYMOV(self, url):
        printDBG('parserTINYMOV url[%s]' % url)
        sts, data = self.cm.getPage(url)
        if sts:
            match = re.search("url: '([^']+?.mp4|[^']+?.flv)',", data)
            if match:
                linkVideo = match.group(1)
                printDBG ('parserTINYMOV linkVideo :' + linkVideo)
                return linkVideo
            
        return False
     
    def parserTOPUPLOAD(self, url):
        url = url.replace('topupload.tv', 'maxupload.tv')
        HTTP_HEADER = {'Referer':url}
        post_data = {'ok':'yes', 'confirm':'Close+Ad+and+Watch+as+Free+User', 'submited':'true'}        
        sts, data = self.cm.getPage(url=url, addParams={'header':HTTP_HEADER}, post_data = post_data)
        if sts:
            posibility = ["'file': '([^']+?)'", "file: '([^']+?)'", "'url': '(http[^']+?)'", "url: '(http[^']+?)'"]
            for posibe in posibility:
                match = re.search(posibe, data)  
                if match:
                    header = {'Referer':'http://www.maxupload.tv/media/swf/player/player.swf'}
                    self.cm.getPage(match.group(1), {'header':header})
                    return self.cm.meta['url']
            else:
                printDBG('parserTOPUPLOAD direct link not found in return data')
        else:
            printDBG('parserTOPUPLOAD error when getting page')
        return False
        
    def parserLIVELEAK(self, baseUrl):
        printDBG('parserLIVELEAK baseUrl[%s]' % baseUrl)
        urlTab = []
        sts, data = self.cm.getPage(baseUrl)
        if sts:
            file_url    = urllib.unquote(self.cm.ph.getSearchGroups(data, 'file_url=(http[^&]+?)&')[0])
            hd_file_url = urllib.unquote(self.cm.ph.getSearchGroups(data, 'hd_file_url=(http[^&]+?)&')[0])
            if '' != file_url:
                urlTab.append({'name':'liveleak.com SD', 'url':file_url})
            if '' != hd_file_url:
                urlTab.append({'name':'liveleak.com HD', 'url':hd_file_url})
            if len(urlTab) == 0:
                tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False, False)
                for item in tmp:
                    if 'video/mp4' in item or '.mp4' in item:
                        label = self.cm.ph.getSearchGroups(item, '''label=['"]([^"^']+?)['"]''')[0]
                        if label == '': label = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
                        url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                        if url.startswith('//'): url = 'http:' + url
                        if not self.cm.isValidUrl(url): continue
                        urlTab.append({'name':label, 'url':strwithmeta(url, {'Referer':baseUrl})})
                
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> [%s]" % urlTab)
            if 0 == len(urlTab):
                data = re.compile('<iframe[^>]+?src="([^"]+?youtube[^"]+?)"').findall(data)
                for item in data:
                    url = item
                    if url.startswith('//'): url = 'http:' + url
                    if not self.cm.isValidUrl(url): continue
                    urlTab.extend(self.parserYOUTUBE(url))
        return urlTab
            
    def parserVIDUPME(self, baseUrl):
        printDBG("parserVIDUPME baseUrl[%r]" % baseUrl)
        
        def _preProcessing(data):
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script', '</script>')
            for item in tmp:
                if 'eval' in item:
                    item = self.cm.ph.getDataBeetwenReMarkers(item, re.compile('<script[^>]*?>'), re.compile('</script>'), False)[1]
                    jscode = base64.b64decode('''dmFyIGRvY3VtZW50ID0ge307DQpkb2N1bWVudC53cml0ZSA9IGZ1bmN0aW9uIChzdHIpDQp7DQogICAgcHJpbnQoc3RyKTsNCn07DQoNCiVz''') % (item)
                    ret = js_execute( jscode )
                    if ret['sts'] and 0 == ret['code']:
                        item = self.cm.ph.getSearchGroups(ret['data'], '''<script[^>]+?src=['"]([^'^"]+?)['"]''')[0]
                        if item != '':
                            item = urljoin(baseUrl, item)
                            sts, item = self.cm.getPage(item)
                            if sts:
                                jscode = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('var\s*jwConfig[^=]*\s*=\s*\{'), re.compile('\};'))[1]
                                varName = jscode[3:jscode.find('=')].strip()
                                jscode = base64.b64decode('''JXMNCnZhciBpcHR2YWxhID0gandDb25maWcoJXMpOw0KcHJpbnQoSlNPTi5zdHJpbmdpZnkoaXB0dmFsYSkpOw==''') % (item + '\n' + jscode, varName)
                                ret = js_execute( jscode )
                                if ret['sts'] and 0 == ret['code']:
                                    printDBG(ret['data'])
                                    return ret['data']
            
            return data
        return self._parserUNIVERSAL_A(baseUrl, 'http://vidup.me/embed-{0}-640x360.html', self._findLinks, _preProcessing)
        
    def parserFILEUPLOADCOM(self, baseUrl):
        printDBG("parserFILEUPLOADCOM baseUrl[%r]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return self.parserUPLOAD(baseUrl)
        
        jscode = ''
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item:
                jscode += item
        linksTab = []
        jscode = base64.b64decode('''dmFyIGlwdHZfc3JjZXM9W10sZG9jdW1lbnQ9e30sd2luZG93PXRoaXM7ZG9jdW1lbnQud3JpdGU9ZnVuY3Rpb24oKXt9O3ZhciBqd3BsYXllcj1mdW5jdGlvbigpe3JldHVybntzZXR1cDpmdW5jdGlvbih0KXt0cnl7aXB0dl9zcmNlcy5wdXNoKHQuZmlsZSl9Y2F0Y2gobil7fX19fTsgJXM7cHJpbnQoSlNPTi5zdHJpbmdpZnkoaXB0dl9zcmNlcykpOw==''') % jscode
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            data = json_loads(ret['data'])
            for url in data:
                if url.split('?', 1)[0][-3:].lower() == 'mp4':
                    linksTab.append({'name':'mp4', 'url':url})
        if len(linksTab):
            return linksTab
        return self.parserUPLOAD(baseUrl)
        
    def parserVIDBOMCOM(self, baseUrl):
        printDBG("parserVIDBOMCOM baseUrl[%r]" % baseUrl)
        
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        
        cUrl = self.cm.getBaseUrl(data.meta['url'])
        domain = urlparser.getDomain(cUrl)
        
        jscode = [self.jscode['jwplayer']]
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item and 'setup' in item:
                jscode.append(item)
        urlTab = []
        try:
            jscode = '\n'.join(jscode)
            ret = js_execute( jscode )
            tmp = json_loads(ret['data'])
            for item in tmp['sources']:
                url = item['file']
                type = item.get('type', '')
                if type == '': type = url.split('.')[-1].split('?', 1)[0]
                type = type.lower()
                label = item['label']
                if 'mp4' not in type: continue
                if url == '': continue
                url = urlparser.decorateUrl(self.cm.getFullUrl(url, cUrl), {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
                urlTab.append({'name':'{0} {1}'.format(domain, label), 'url':url})
        except Exception:
            printExc()
        if len(urlTab) == 0:
            items = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''sources\s*[=:]\s*\['''), re.compile('''\]'''), False)[1].split('},')
            printDBG(items)
            domain = urlparser.getDomain(baseUrl)
            for item in items:
                item = item.replace('\/', '/')
                url  = self.cm.ph.getSearchGroups(item, '''(?:src|file)['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                if not url.lower().split('?', 1)[0].endswith('.mp4') or not self.cm.isValidUrl(url): continue
                type = self.cm.ph.getSearchGroups(item, '''type['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                res  = self.cm.ph.getSearchGroups(item, '''res['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                if res == '': res = self.cm.ph.getSearchGroups(item, '''label['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                lang = self.cm.ph.getSearchGroups(item, '''lang['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                url = urlparser.decorateUrl(self.cm.getFullUrl(url, cUrl), {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
                urlTab.append({'name':domain + ' {0} {1}'.format(lang, res), 'url':url})
        return urlTab
        
    def parserINTERIATV(self, baseUrl):
        printDBG("parserINTERIATV baseUrl[%r]" % baseUrl)
        
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        
        cUrl = self.cm.getBaseUrl(data.meta['url'])
        domain = urlparser.getDomain(cUrl)
        
        urlTab = []
        embededLink = self.cm.ph.getSearchGroups(data, '''['"]data\-url['"]\s*?\,\s*?['"]([^'^"]+?)['"]''')[0]
        if embededLink.startswith('//'): embededLink = 'http:' + embededLink
        if self.cm.isValidUrl(embededLink):
            urlParams['header']['Referer'] = baseUrl
            sts, tmp = self.cm.getPage(embededLink, urlParams)
            printDBG(tmp)
            if sts:
                embededLink = self.cm.ph.getSearchGroups(tmp, '''['"]?src['"]?\s*?:\s*?['"]([^'^"]+?\.mp4(?:\?[^'^"]+?)?)['"]''')[0]
                if embededLink.startswith('//'): embededLink = 'http:' + embededLink
                if self.cm.isValidUrl(embededLink):
                    urlTab.append({'name':'{0} {1}'.format(domain, 'external'), 'url':embededLink})
        
        jscode = ['var window=this,document={};function jQuery(){return document}document.ready=function(n){n()};var element=function(n){this._name=n,this.setAttribute=function(){},this.attachTo=function(){}};document.getElementById=function(n){return new element(n)};var Inpl={Video:{}};Inpl.Video.createInstance=function(n){print(JSON.stringify(n))};']
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'Video.createInstance' in item:
                jscode.append(item)
        
        jscode = '\n'.join(jscode)
        ret = js_execute( jscode )
        try:
            data = json_loads(ret['data'])['tracks']
            for tmp in data:
                printDBG(tmp)
                for key in ['hi', 'lo']:
                    if not isinstance(tmp['src'][key], list):
                        tmp['src'][key] = [tmp['src'][key]]
                    for item in tmp['src'][key]:
                        if 'mp4' not in item['type'].lower(): continue
                        if item['src'] == '': continue
                        url = urlparser.decorateUrl(self.cm.getFullUrl(item['src'], cUrl), {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
                        urlTab.append({'name':'{0} {1}'.format(domain, key), 'url':url})
        except Exception:
            printExc()
        return urlTab
        
    def parserMEGADRIVETV(self, baseUrl):
        printDBG("parserMEGADRIVETV baseUrl[%r]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        jscode = ''
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item:
                jscode += item
        linksTab = []
        jscode = base64.b64decode('''dmFyIGlwdHZfc3JjZXM9W10sZG9jdW1lbnQ9e30sd2luZG93PXRoaXM7ZG9jdW1lbnQud3JpdGU9ZnVuY3Rpb24oKXt9O3ZhciBqd3BsYXllcj1mdW5jdGlvbigpe3JldHVybntzZXR1cDpmdW5jdGlvbihlKXt0cnl7aXB0dl9zcmNlcy5wdXNoKGUuZmlsZSl9Y2F0Y2gobil7fX19fSxlbGVtZW50PWZ1bmN0aW9uKGUpe3RoaXMucGFyZW50Tm9kZT17aW5zZXJ0QmVmb3JlOmZ1bmN0aW9uKCl7fX19LCQ9ZnVuY3Rpb24oZSl7cmV0dXJuIG5ldyBlbGVtZW50KGUpfTtkb2N1bWVudC5nZXRFbGVtZW50QnlJZD1mdW5jdGlvbihlKXtyZXR1cm4gbmV3IGVsZW1lbnQoZSl9LGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQ9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQsZG9jdW1lbnQuZ2V0RWxlbWVudHNCeVRhZ05hbWU9ZnVuY3Rpb24oZSl7cmV0dXJuW25ldyBlbGVtZW50KGUpXX07JXM7cHJpbnQoSlNPTi5zdHJpbmdpZnkoaXB0dl9zcmNlcykpOw==''') % jscode
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            data = json_loads(ret['data'])
            for url in data:
                if url.split('?', 1)[0][-3:].lower() == 'mp4':
                    linksTab.append({'name':'mp4', 'url':url})
        return linksTab
        
    def parserWATCHVIDEO17US(self, baseUrl):
        printDBG("parserWATCHVIDEO17US baseUrl[%r]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        jscode = ''
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if item.startswith('eval('):
                jscode += item
        linksTab = []
        hlsTab = []
        jscode = base64.b64decode('''dmFyIGlwdHZfc3JjZXM9W10sZG9jdW1lbnQ9e30sd2luZG93PXRoaXM7ZG9jdW1lbnQud3JpdGU9ZnVuY3Rpb24oKXt9O3ZhciBqd3BsYXllcj1mdW5jdGlvbigpe3JldHVybntzZXR1cDpmdW5jdGlvbihlKXt0cnl7aXB0dl9zcmNlcy5wdXNoLmFwcGx5KGlwdHZfc3JjZXMsZS5zb3VyY2VzKX1jYXRjaChuKXt9fSxvblRpbWU6ZG9jdW1lbnQud3JpdGUsb25QbGF5OmRvY3VtZW50LndyaXRlLG9uQ29tcGxldGU6ZG9jdW1lbnQud3JpdGUsb25QYXVzZTpkb2N1bWVudC53cml0ZSxkb1BsYXk6ZG9jdW1lbnQud3JpdGV9fSxlbGVtZW50PWZ1bmN0aW9uKGUpe3RoaXMucGFyZW50Tm9kZT17aW5zZXJ0QmVmb3JlOmZ1bmN0aW9uKCl7fX19LCQ9ZnVuY3Rpb24oZSl7cmV0dXJuIG5ldyBlbGVtZW50KGUpfTtkb2N1bWVudC5nZXRFbGVtZW50QnlJZD1mdW5jdGlvbihlKXtyZXR1cm4gbmV3IGVsZW1lbnQoZSl9LGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQ9ZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQsZG9jdW1lbnQuZ2V0RWxlbWVudHNCeVRhZ05hbWU9ZnVuY3Rpb24oZSl7cmV0dXJuW25ldyBlbGVtZW50KGUpXX07JXM7cHJpbnQoSlNPTi5zdHJpbmdpZnkoaXB0dl9zcmNlcykpOw==''') % jscode
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            data = json_loads(ret['data'], '', True)
            for item in data:
                ext = item['file'].split('?', 1)[0][-4:].lower()
                printDBG("|>><<| EXT[%s]" % ext)
                if ext == 'm3u8':
                    hlsTab = getDirectM3U8Playlist(item['file'], checkExt=False, checkContent=True)
                elif ext[1:] == 'mp4':
                    linksTab.append({'name':item['label'], 'url':item['file']})
        linksTab.extend(hlsTab)
        return linksTab
        
    def parserWATCHUPVIDCO(self, baseUrl):
        printDBG("parserWATCHUPVIDCO baseUrl[%r]" % baseUrl)
        urlParams = {'header':{ 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }}
        url = baseUrl
        subFrameNum = 0
        while subFrameNum < 6:
            sts, data = self.cm.getPage(url, urlParams)
            if not sts: return False
            newUrl = ''
            if '<iframe' in data:
                newUrl = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=['"](https?://[^"^']+?)['"]''', 1, True)[0]
                if newUrl == '':
                    newUrl = self.cm.ph.getSearchGroups(data, ''' <input([^>]+?link[^>]+?)>''')[0]
                    newUrl = self.cm.ph.getSearchGroups(data, '''\svalue=['"](https?://[^"^']+?)['"]''', 1, True)[0]
            if self.cm.isValidUrl(newUrl):
                urlParams['header']['Referer'] = url
                url = newUrl
            else:
                break
            subFrameNum += 1
        elemName = 'iptv_id_elems'
        jscode = ['%s={};' % elemName]
        elems = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>')
        for elem in elems:
            id = self.cm.ph.getSearchGroups(elem, '''id=['"]([^'^"]+?)['"]''', 1, True)[0]
            if id == '': continue
            val = self.cm.ph.getSearchGroups(elem, '''value=['"]([^'^"]+?)['"]''', 1, True)[0].replace('\n', '').replace('\r', '')
            jscode.append('%s.%s="%s";' % (elemName, id, val))
        
        jscode.append(base64.b64decode('''aXB0dl9kZWNvZGVkX2NvZGU9W107dmFyIGRvY3VtZW50PXt9O3dpbmRvdz10aGlzLHdpbmRvdy5hdG9iPWZ1bmN0aW9uKGUpe2U9RHVrdGFwZS5kZWMoImJhc2U2NCIsZSksZGVjVGV4dD0iIjtmb3IodmFyIG49MDtuPGUuYnl0ZUxlbmd0aDtuKyspZGVjVGV4dCs9U3RyaW5nLmZyb21DaGFyQ29kZShlW25dKTtyZXR1cm4gZGVjVGV4dH07dmFyIGVsZW1lbnQ9ZnVuY3Rpb24oZSl7dGhpcy5fbmFtZT1lLHRoaXMuX2lubmVySFRNTD1pcHR2X2lkX2VsZW1zW2VdLE9iamVjdC5kZWZpbmVQcm9wZXJ0eSh0aGlzLCJpbm5lckhUTUwiLHtnZXQ6ZnVuY3Rpb24oKXtyZXR1cm4gdGhpcy5faW5uZXJIVE1MfSxzZXQ6ZnVuY3Rpb24oZSl7dGhpcy5faW5uZXJIVE1MPWV9fSksT2JqZWN0LmRlZmluZVByb3BlcnR5KHRoaXMsInZhbHVlIix7Z2V0OmZ1bmN0aW9uKCl7cmV0dXJuIHRoaXMuX2lubmVySFRNTH0sc2V0OmZ1bmN0aW9uKGUpe3RoaXMuX2lubmVySFRNTD1lfX0pfTtkb2N1bWVudC5nZXRFbGVtZW50QnlJZD1mdW5jdGlvbihlKXtyZXR1cm4gbmV3IGVsZW1lbnQoZSl9LGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQ9ZnVuY3Rpb24oZSl7cmV0dXJuIG5ldyBlbGVtZW50KGUpfSxkb2N1bWVudC5ib2R5PXt9LGRvY3VtZW50LmJvZHkuYXBwZW5kQ2hpbGQ9ZnVuY3Rpb24oZSl7aXB0dl9kZWNvZGVkX2NvZGUucHVzaChlLmlubmVySFRNTCksd2luZG93LmV2YWwoZS5pbm5lckhUTUwpfSxkb2N1bWVudC5ib2R5LnJlbW92ZUNoaWxkPWZ1bmN0aW9uKCl7fTs='''))
        marker = 'ﾟωﾟﾉ= /｀ｍ´）'
        elems = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for elem in elems:
            if marker in elem:
                jscode.append(elem)
                break
        
        jscode.append('print(iptv_decoded_code);')
        
        ret = js_execute( '\n'.join(jscode) )
        videoUrl = self.cm.ph.getSearchGroups(ret['data'], '''['"](https?://[^"^']+?\.mp4(?:\?[^'^"]+?)?)['"]''', 1, True)[0]
        printDBG(">>")
        printDBG(videoUrl)
        printDBG("<<")
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        return False
        
    def parserPOWVIDEONET(self, videoUrl):
        printDBG("parserPOWVIDEONET baseUrl[%r]" % videoUrl)
        
        HEADER = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36', 'Accept':'*/*', 'Accept-Encoding':'gzip, deflate'}
        httpParams = {'header': HEADER, 'use_cookie':True, 'load_cookie': True, 'save_cookie':True, 'cookiefile': GetCookieDir('powvideo.cookie')}
        
        #check this format https://powv1deo.cc/embed-elh97qztxk95-920x560.html
        video_id = re.findall("[a-z0-9]{11,}", videoUrl)
        if video_id:
            video_id = video_id[0] 
            baseUrl = urlparser.getDomain(videoUrl, False)
            videoUrl = baseUrl + video_id
        
        else:
            printDBG("Check format of url : %s" % videoUrl)
            video_id = videoUrl.split('/')[-1]
        
        linksTab = []
        
        sts, data = self.cm.getPage(videoUrl, httpParams)
        if not sts: 
            return False
        
        baseUrl = urlparser.getDomain(self.cm.meta['url'], False)
        
        if 'sitekey' in data:
            # need to solve a reCaptcha
            #sitekey: '6LfsXx4TAAAAAG7fRIpL2LpS_NLxj1HBlotEDhT7'
            key = re.findall("sitekey:\s'([^']+?)'", data)
            if key:
                key = key[0]
                printDBG("sitekey = %s" % key)
                (token, errorMsgTab) = CaptchaHelper().processCaptcha(key, baseUrl)
                
                if token:
                    printDBG(token)
                    
                    #<form method="POST" action='' id="d0Form">
                    form_html = self.cm.ph.getDataBeetwenMarkers(data, ('<form','>','POST'), '</form>')[1]
                    inputs = self.cm.ph.getAllItemsBeetwenMarkers(form_html, '<input','>', False, caseSensitive=False)
                    post_data = {}
                    
                    for item in inputs:
                        name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
                        value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
                        if name:
                            post_data[name] = value
                        
                    post_data['g-recaptcha-response'] = token
                    post_data['token'] = token
                    
                    printDBG(json_dumps(post_data))
                    
                    sts, data = self.cm.getPage(videoUrl, httpParams, post_data)
 
                    if not sts:
                        return[]
                    
                    #printDBG("-------------- after recaptcha ---------------")
                    #printDBG(data)
                    #printDBG("----------------------------------------------")
                        
        
        scripts = re.findall("<script type=[\"']text/javascript[\"']>(eval.*?)</script>", data, re.S)
        
        if scripts:
            for script in scripts:
                printDBG("----------- pack -----------------")
                printDBG(script)
                
                script = script + "\n"
                # mods
                script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                script = script.replace("return p}(", "print(p)}\n\npippo(")
                script = script.replace("))\n",");\n")

                # duktape
                ret = js_execute( script )
                decoded = ret['data']
                printDBG('------------------------------')
                printDBG(decoded)
                printDBG('------------------------------')

                sources = re.findall("src:\s?[\"']([^\"^']+.m3u8)[\"']", decoded)  
                sources.extend(re.findall("src:\s?[\"']([^\"^']+.mp4)[\"']", decoded))
                
                for link_url in sources:
                    if  self.cm.isValidUrl(link_url):
                        if 'pvdcdn' in link_url:
                            # modify url
                            link_url = powvideo_swapUrl(data, link_url)
                            
                        link_url = urlparser.decorateUrl(link_url, {'Referer': videoUrl})
                        if 'm3u8' in link_url:
                            params = getDirectM3U8Playlist(link_url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                            printDBG(str(params))    
                            linksTab.extend(params)
                        else:
                            params = {'name': 'link' , 'url': link_url}
                            printDBG(str(params))
                            linksTab.append(params)
                
        if linksTab:
            return linksTab
        
        # check for error messages. Example
        # <div id="over_player_msg">Video is processing now.<br>Conversion stage: <span id='enc_pp'>...</span></div>
        msg =  clean_html(self.cm.ph.getDataBeetwenMarkers(data, ('<div','>','over_player_msg') , ('</div','>'), False)[1])
        if msg: 
            SetIPTVPlayerLastHostError(error)
            return linksTab
        
        vidId = self.cm.ph.getSearchGroups(videoUrl, '''[^-]*?\-([^-^.]+?)[-.]''')[0]
        if not vidId: 
            vidId = videoUrl.rsplit('/')[-1].split('.', 1)[0]
        
        printDBG('parserPOWVIDEONET VID ID: %s' % vidId)
        referer = baseUrl + ('preview-%s-1920x882.html' % vidId)
        videoUrl = baseUrl + ('iframe-%s-1920x882.html' % vidId)
        HEADER['Referer'] = referer
        
        sts, data = self.cm.getPage(videoUrl, {'header': HEADER})
        if not sts: return False
        
        jscode = []
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item:
                jscode.append(item)
            elif 'S?S' in item:
                jscode.append(self.cm.ph.getSearchGroups(item, '(var\s_[^\n]+?)\n')[0])
        
        jwplayer = self.cm.ph.getSearchGroups(data, '''<script[^>]+?src=['"]([^'^"]+?jwplayer\.js[^'^"]*?)['"]''')[0]
        if jwplayer != '' and not self.cm.isValidUrl(jwplayer):
            if jwplayer.startswith('//'): jwplayer = 'https:' + jwplayer
            elif jwplayer.startswith('/'): jwplayer = baseUrl + jwplayer[1:]
            else: jwplayer = baseUrl + jwplayer
        
        sts, data = self.cm.getPage(jwplayer, {'header': HEADER})
        if not sts: return False
        
        hlsTab = []
        jscode.insert(0, 'location={};jQuery.cookie = function(){};function ga(){};document.getElementsByTagName = function(){return [document]}; document.createElement = function(){return document};document.parentNode = {insertBefore: function(){return document}};')
        jscode.insert(0, data[data.find('var S='):])
        jscode.insert(0, base64.b64decode('''aXB0dl9zb3VyY2VzPVtdO3ZhciBkb2N1bWVudD17fTt3aW5kb3c9dGhpcyx3aW5kb3cuYXRvYj1mdW5jdGlvbih0KXt0Lmxlbmd0aCU0PT09MyYmKHQrPSI9IiksdC5sZW5ndGglND09PTImJih0Kz0iPT0iKSx0PUR1a3RhcGUuZGVjKCJiYXNlNjQiLHQpLGRlY1RleHQ9IiI7Zm9yKHZhciBlPTA7ZTx0LmJ5dGVMZW5ndGg7ZSsrKWRlY1RleHQrPVN0cmluZy5mcm9tQ2hhckNvZGUodFtlXSk7cmV0dXJuIGRlY1RleHR9LGpRdWVyeT17fSxqUXVlcnkubWFwPUFycmF5LnByb3RvdHlwZS5tYXAsalF1ZXJ5Lm1hcD1mdW5jdGlvbigpe3JldHVybiBhcmd1bWVudHNbMF0ubWFwKGFyZ3VtZW50c1sxXSksaXB0dl9zb3VyY2VzLnB1c2goYXJndW1lbnRzWzBdKSxhcmd1bWVudHNbMF19LCQ9alF1ZXJ5LGlwdHZvYmo9e30saXB0dm9iai5zZXR1cD1mdW5jdGlvbigpe3JldHVybiBpcHR2b2JqfSxpcHR2b2JqLm9uPWZ1bmN0aW9uKCl7cmV0dXJuIGlwdHZvYmp9LGp3cGxheWVyPWZ1bmN0aW9uKCl7cmV0dXJuIGlwdHZvYmp9Ow=='''))
        jscode.append('print(JSON.stringify(iptv_sources[iptv_sources.length-1]));')
        ret = js_execute( '\n'.join(jscode) )
        if ret['sts'] and 0 == ret['code']:
            data = json_loads(ret['data'])
            for item in data:
                if 'src' in item: url = item['src']
                else: url = item['file']
                url = strwithmeta(url, {'Referer':HEADER['Referer'], 'User-Agent':HEADER['User-Agent']})
                test = url.lower()
                if test.split('?', 1)[0].endswith('.mp4'):
                    linksTab.append({'name':'mp4', 'url':url})
                elif test.split('?', 1)[0].endswith('.m3u8'):
                    hlsTab.extend(getDirectM3U8Playlist(url, checkContent=True))
                #elif test.startswith('rtmp://'):
                #    linksTab.append({'name':'rtmp', 'url':url})
        linksTab.extend(hlsTab)
        return linksTab
        
    def parserSPEEDVIDNET(self, baseUrl):
        printDBG("parserSPEEDVIDNET baseUrl[%r]" % baseUrl)
        retTab = None
        defaultParams = {'header':self.cm.getDefaultHeader(), 'with_metadata':True, 'cfused':True, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('speedvidnet.cookie')}
        def _findLinks2(data):
            return _findLinks(data, 1)
            
        def _findLinks(data, lvl=0):
            if lvl == 0:
                jscode = ['var url,iptvRetObj={cookies:{},href:"",sources:{}},primary=!1,window=this;location={assign:function(t){iptvRetObj.href=t;}};var document={};iptvobj={},iptvobj.setup=function(){iptvRetObj.sources=arguments[0]},jwplayer=function(){return iptvobj},Object.defineProperty(document,"cookie",{get:function(){return""},set:function(t){t=t.split(";",1)[0].split("=",2),iptvRetObj.cookies[t[0]]=t[1];}}),Object.defineProperty(location,"href",{set:function(t){iptvRetObj.href=t}}),window.location=location;']
                tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), withNodes=False, caseSensitive=False)
                for item in tmp:
                    if 'ﾟωﾟﾉ =/｀ｍ´ ）' in item or 'eval(' in item:
                        jscode.append(item)
                jscode.append(';print(JSON.stringify(iptvRetObj));')
                if len(jscode) > 2:
                    ret = js_execute( '\n'.join(jscode) )
                    if ret['sts'] and 0 == ret['code']:
                        data = json_loads(ret['data'].strip())
                        defaultParams['cookie_items'] = data['cookies']
                        defaultParams['header']['Referer'] = baseUrl
                        url = self.cm.getFullUrl(data['href'], self.cm.meta['url'])
                        if self.cm.isValidUrl(url):
                            return self._parserUNIVERSAL_A(url, '', _findLinks2, httpHeader=defaultParams['header'], params=defaultParams)
            
            data = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''jwplayer\([^\)]+?player[^\)]+?\)\.setup'''), re.compile(';'))[1]
            url = self.cm.ph.getSearchGroups(data, '''['"]?file['"]?\s*:\s*['"]([^'^"]+?)['"]''')[0]
            if '.mp4' in url.lower(): 
                return [{'url':url, 'name':'speedvid.net'}]
            return False
        return self._parserUNIVERSAL_A(baseUrl, 'http://www.speedvid.net/embed-{0}-540x360.html', _findLinks, params=defaultParams)
        
    def parserVIDLOXTV(self, baseUrl):
        printDBG("parserVIDLOXTV baseUrl[%r]" % baseUrl)
        # example video: http://vidlox.tv/embed-e9r0y7i65i1v.html
        def _findLinks(data):
            data = re.sub("<!--[\s\S]*?-->", "", data)
            errorMsg = ph.find(data, ('<h1', '>'), '</p>', flags=0)[1]
            if '<script' not in errorMsg: SetIPTVPlayerLastHostError(ph.clean_html(errorMsg))
            linksTab = []
            data = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', ']', False)[1]
            data = re.compile('"(http[^"]+?)"').findall(data)
            for link in data:
                if link.split('?')[0].endswith('m3u8'):
                    linksTab.extend(getDirectM3U8Playlist(link, checkContent=True))
                elif link.split('?')[0].endswith('mp4'):
                    linksTab.append({'name':'mp4', 'url': link})
            return linksTab
        return self._parserUNIVERSAL_A(baseUrl, 'http://vidlox.tv/embed-{0}.html', _findLinks)
        
    def parserMYCLOUDTO(self, baseUrl):
        printDBG("parserMYCLOUDTO baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        header = {
            'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36', 'Referer':baseUrl.meta.get('Referer', baseUrl), 
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 
            'Accept-Encoding':'gzip, deflate',
            'sec-fetch-dest': 'iframe', 'sec-fetch-mode': 'navigate', 'sec-fetch-site': 'cross-site'
        }
        httpParams={'use_cookie': True, 'save_cookie':True, 'load_cookie': True, 'cookiefile': GetCookieDir('mycloud.cookie'), 'header': header}
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        if not sts: 
            return False

        printDBG(data)

        data = data.replace('\\/', '/')

        url = self.cm.ph.getSearchGroups(data, '''['"]((?:https?:)?//[^"^']+\.m3u8[^'^"]*?)['"]''')[0]
        if url.startswith('//'):
            url = 'http:' + url

        url = strwithmeta(url, {'User-Agent':header['User-Agent'], 'Origin':"https://" + urlparser.getDomain(baseUrl), 'Referer':baseUrl})
        tab =  getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999)
        printDBG("parserMYCLOUDTO tab[%s]" % tab)
            
        return tab
        
    def parserVODSHARECOM(self, baseUrl):
        printDBG("parserVODSHARECOM baseUrl[%r]" % baseUrl)
        HTTP_HEADER = { 'User-Agent':'Mozilla/5.0', 'Referer':baseUrl}
        COOKIE_FILE = GetCookieDir('vod-share.com.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True}
        
        rm(COOKIE_FILE)
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        url = self.cm.ph.getSearchGroups(data, '''location\.href=['"]([^'^"]+?)['"]''')[0]
        params['header']['Referer'] = baseUrl
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        
        cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
        
        urlTab = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source ', '>', False, False)
        for item in data:
            url  = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
            if url.startswith('//'):
                url = 'http:' + url
            if not url.startswith('http'):
                continue
            
            if 'video/mp4' in item:
                type = self.cm.ph.getSearchGroups(item, '''type=['"]([^"^']+?)['"]''')[0]
                res  = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
                label = self.cm.ph.getSearchGroups(item, '''label=['"]([^"^']+?)['"]''')[0]
                if label == '': label = res
                url = urlparser.decorateUrl(url, {'Cookie':cookieHeader, 'Referer':baseUrl,  'User-Agent':HTTP_HEADER['User-Agent']})
                urlTab.append({'name':'{0}'.format(label), 'url':url})
            elif 'mpegurl' in item:
                url = urlparser.decorateUrl(url, {'iptv_proto':'m3u8', 'Cookie':cookieHeader, 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
                tmpTab = getDirectM3U8Playlist(url, checkExt=True, checkContent=True)
                urlTab.extend(tmpTab)
        return urlTab
        
    def parserVIDOZANET(self, baseUrl):
        printDBG("parserVIDOZANET baseUrl[%r]" % baseUrl)
        referer = strwithmeta(baseUrl).meta.get('Referer', '')
        baseUrl = strwithmeta(baseUrl, {'Referer':referer})
        domain = urlparser.getDomain(baseUrl)
        
        def _findLinks(data):
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>', False)
            videoTab = []
            for item in tmp:
                if 'video/mp4' not in item and 'video/x-flv' not in item: continue
                tType = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0].replace('video/', '')
                tUrl  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
                printDBG(tUrl)
                if self.cm.isValidUrl(tUrl): videoTab.append({'name':'[%s] %s' % (tType, domain), 'url':strwithmeta(tUrl)})
            return videoTab
        
        return self._parserUNIVERSAL_A(baseUrl, 'https://vidoza.net/embed-{0}.html', _findLinks)
        
    def parserCLIPWATCHINGCOM(self, baseUrl):
        printDBG("parserCLIPWATCHINGCOM baseUrl[%r]" % baseUrl)
        urlTabs= []
        
        sts, data = self.cm.getPage(baseUrl)
        
        if sts:
#            printDBG("----------------------")
#            printDBG(data)
#            printDBG("----------------------")
            
            data = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''jwplayer\([^\)]+?player[^\)]+?\)\.setup'''), re.compile(';'))[1]
#            printDBG(str(data))
            
            if 'sources' in data:
                items = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''[\{\s]sources\s*[=:]\s*\['''), re.compile('''\]'''), False)[1].split('},')
                for item in items:
                    label   = self.cm.ph.getSearchGroups(item, 'label:[ ]*?"([^"]+?)"')[0]
                    src     = self.cm.ph.getSearchGroups(item, 'file:[ ]*?"([^"]+?)"')[0]
                    if  self.cm.isValidUrl(src):
                        src = urlparser.decorateUrl(src, {'Referer': baseUrl})
                        if 'm3u8' in src:
                            params = getDirectM3U8Playlist(src, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                            urlTabs.extend(params)
                        else:
                            params = {'name': 'mp4 ' + label, 'url': src}
                            urlTabs.append(params)
                    
        return urlTabs
        
    def parserVIDABCCOM(self, baseUrl):
        printDBG("parserVIDABCCOM baseUrl[%r]" % baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://vidabc.com/embed-{0}.html', self._findLinks)
        
    def parserFASTPLAYCC(self, baseUrl):
        printDBG("parserFASTPLAYCC baseUrl[%r]" % baseUrl)
        return self._parserUNIVERSAL_A(strwithmeta(baseUrl, {'Referer':''}), 'http://fastplay.cc/embed-{0}.html', self._findLinks)
    
    def parserSPRUTOTV(self, baseUrl):
        printDBG("parserSPRUTOTV baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        return self._findLinks(data, serverName='spruto.tv', linkMarker=r'''['"]?file['"]?[ ]*:[ ]*['"](http[^"^']+)['"][,}]''', m1='Uppod(', m2=')', contain='.mp4')
        
    def parserRAPTUCOM(self, baseUrl):
        printDBG("parserRAPTUCOM baseUrl[%r]" % baseUrl)
        HTTP_HEADER = { 'User-Agent':'Mozilla/5',
                        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language':'pl,en-US;q=0.7,en;q=0.3',
                        'Accept-Encoding':'gzip, deflate',
                        'DNT':1,
                      }
        
        COOKIE_FILE = GetCookieDir('raptucom.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True}
        
        rm(COOKIE_FILE)
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<form[^>]+?method="POST"', re.IGNORECASE),  re.compile('</form>', re.IGNORECASE), True)[1]
        if tmp != '':
            printDBG(tmp)
            action = self.cm.ph.getSearchGroups(tmp, '''action=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<input', '>', False, False)
            post_data = {}
            for item in tmp:
                name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
                value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
                if name != '' and value != '': post_data[name] = value
            
            printDBG(post_data)
            printDBG(action)
            if action == '#':
                post_data['confirm.x'] = 70 - randint(0, 30)
                post_data['confirm.y'] = 70 - randint(0, 30)
                params['header']['Referer'] = baseUrl
                sts, data = self.cm.getPage(baseUrl+'#', params, post_data)
                if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '.setup(', ');', False)[1].strip()
        data = self.cm.ph.getDataBeetwenMarkers(data, '"sources":', ']', False)[1].strip()
        printDBG(data)
        data = json_loads(data+']')
        retTab = []
        for item in data:
            try: retTab.append({'name':'raptu.com ' + item.get('label', item.get('res', '')), 'url':item['file']})
            except Exception: pass
        return retTab[::-1]
        
    def parserOVVATV(self, baseUrl):
        printDBG("parserOVVATV baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'ovva(', ')', False)[1].strip()[1:-1]
        data = json_loads(base64.b64decode(data))
        url = data['url']
        
        sts, data = self.cm.getPage(url)
        if not sts: return False
        data = data.strip()
        if data.startswith('302='):
            url = data[4:]
        
        return getDirectM3U8Playlist(url, checkContent=True)[::-1]
            
    def parserMOSHAHDANET(self, baseUrl):
        printDBG("parserMOSHAHDANET baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False)[1]
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        try:
            sleep_time = int(self.cm.ph.getSearchGroups(data, '<span id="cxc">([0-9])</span>')[0])
            GetIPTVSleep().Sleep(sleep_time)
        except Exception:
            printExc()
            
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER}, post_data)
        if not sts: return False
        
        printDBG(data)
        return self._findLinks(data, 'moshahda.net')
        
        linksTab = []
        srcData = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', '],', False)[1].strip()
        srcData = json_loads(srcData+']')
        for link in srcData:
            if not self.cm.isValidUrl(link): continue
            if link.split('?')[0].endswith('m3u8'):
                tmp = getDirectM3U8Playlist(link)
                linksTab.extend(tmp)
            else:
                linksTab.append({'name': 'mp4', 'url':link})
        return linksTab
                
        #return self._findLinks(data, 'moshahda.net', linkMarker=r'''['"](http[^"^']+)['"]''')
        
    def parserSTREAMMOE(self, baseUrl):
        printDBG("parserSTREAMMOE baseUrl[%r]" % baseUrl)
        
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        url = baseUrl
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub('''atob\(["']([^"^']+?)['"]\)''', lambda m: base64.b64decode(m.group(1)), data)
        printDBG(data)
        tab = self._findLinks(data, 'stream.moe', linkMarker=r'''['"]?url['"]?[ ]*:[ ]*['"](http[^"^']+(?:\.mp4|\.flv)[^"^']*)['"][,}]''', m1='clip:')
        if len(tab) == 0:
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False, False)
            for item in data:
                if 'video/mp4' in item:
                    url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                    tab.append({'name':'stream.moe', 'url':url})
            return tab
        
    def parserCASTFLASHPW(self, baseUrl):
        printDBG("parserCASTFLASHPW baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        Referer = baseUrl.meta.get('Referer', baseUrl) 
        aesKey = baseUrl.meta.get('aes_key', '') 
        
        def getUtf8Str(st):
            idx = 0
            st2 = ''
            while idx < len(st):
                st2 += '\\u0' + st[idx:idx + 3]
                idx += 3
            return st2.decode('unicode-escape').encode('UTF-8')
            
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
        
        #['Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10']
        for agent in ['Mozilla/5.0 (iPhone; CPU iPhone OS 9_0_2 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13A452 Safari/601.1']: 
            HTTP_HEADER= { 'User-Agent':agent, 'Referer':Referer }
            COOKIE_FILE = GetCookieDir('sport365live.cookie') #('castflashpw.cookie')
            baseParams = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':False, 'save_cookie':True} 
            params = dict(baseParams)
            
            url = baseUrl
            sts, data = self.cm.getPage(url, params)
            if not sts: return False
            
            printDBG(data)
            
            post_data = self.cm.ph.getDataBeetwenMarkers(data, '<form ', '</form>', withMarkers=False, caseSensitive=False)[1]
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', post_data))
            params['header']['Referer'] = url
            params['load_cookie'] = True
            url = self.cm.ph.getSearchGroups(data, '''attr\([^<]*?['"]action["'][^<]*?\,[^<]*?["'](http[^'^"]+?)['"]''')[0]
            printDBG(url)
            
            sts, data = self.cm.getPage(url, params, post_data)
            printDBG(data)
            if not sts: return False
            
            linksData = []
            tmp = re.compile('''['"]([^'^"]+?)['"]''').findall(data)
            printDBG(linksData)

            for t in tmp:
                try:
                    linkData = base64.b64decode(t).strip()
                    if linkData[0] == '{' and '"ct"' in linkData: break
                except Exception:
                    printExc()

            linkData   = json_loads(linkData)
            
            ciphertext = base64.b64decode(linkData['ct'])
            iv         = a2b_hex(linkData['iv'])
            salt       = a2b_hex(linkData['s'])
            
            playerUrl = cryptoJS_AES_decrypt(ciphertext, aesKey, salt)
            playerUrl = json_loads(playerUrl)
            if playerUrl.startswith('#') and 3 < len(playerUrl): 
                playerUrl = getUtf8Str(playerUrl[1:])
            printDBG("[%r]" % playerUrl)
            if playerUrl.startswith('http'):
                COOKIE_FILE_M3U8 = GetCookieDir('sport365live.cookie')
                params = {'cookiefile':COOKIE_FILE_M3U8, 'use_cookie': True, 'load_cookie':False, 'save_cookie':True} 
                playerUrl = urlparser.decorateUrl(playerUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Referer':'http://h5.adshell.net/peer5', 'Origin':'http://h5.adshell.net', 'User-Agent':HTTP_HEADER['User-Agent']})
                try:
                    import uuid
                    playerUrl.meta['X-Playback-Session-Id'] = str(uuid.uuid1()).upper()
                except Exception:
                    printExc()
                
                urlsTab = getDirectM3U8Playlist(playerUrl, False, cookieParams=params)
                try:
                    PHPSESSID = self.cm.getCookieItem(COOKIE_FILE_M3U8, 'PHPSESSID')
                    newUrlsTab = []
                    for item in urlsTab:
                        if PHPSESSID != '': item['url'].meta['Cookie'] = 'PHPSESSID=%s' % PHPSESSID
                        newUrlsTab.append(item)
                    return newUrlsTab
                except Exception:
                    printExc()
                    return urlsTab
                    
                params = dict(baseParams)
                params['header']['Referer'] = 'http://www.sport365.live/en/main'
                sts, data = self.cm.getPage("http://www.sport365.live/en/sidebar", params)
                if not sts: return False
                
        return False
        
    def parserTRILULILU(self, baseUrl):
        def getTrack(userid, hash):
            hashLen = len(hash) / 2
            mixedStr = (hash[0:hashLen] + userid) + hash[hashLen:len(hash)]
            md5Obj = MD5()
            hashTab = md5Obj(mixedStr)
            return hexlify(hashTab)
        
        match = re.search("embed\.trilulilu\.ro/video/([^/]+?)/([^.]+?)\.swf", baseUrl)
        data = None
        if not match:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return False
            match = re.search('userid=([^"^<^>^&]+?)&hash=([^"^<^>^&]+?)&', data)
        if match:          
            userid = match.group(1)
            hash = match.group(2)
            refererUrl = "http://static.trilulilu.ro/flash/player/videoplayer2011.swf?userid=%s&hash=%s&referer=" % (userid, hash)
            fileUrl = "http://embed.trilulilu.ro/flv/" + userid + "/" + hash + "?t=" + getTrack(userid, hash) + "&referer=" + urllib.quote_plus( base64.b64encode(refererUrl) ) + "&format=mp4-360p"
            return fileUrl
        # new way to get video
        if sts:
            url = self.cm.ph.getSearchGroups(data, 'id="link" href="(http[^"]+?)"')[0]
            if '' != url:
                HTTP_HEADER = dict(self.HTTP_HEADER) 
                HTTP_HEADER['Referer'] = baseUrl
                sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
                data = self.cm.ph.getSearchGroups(data, """["']*video["']*:[ ]*["']([^"']+?)["']""")[0]
                if '' != data:
                    if data.startswith('//'):
                        data = 'http:' + data
                    return data
        return False
        
    def parserALIEZ(self, url):
        sts, data = self.cm.getPage(url)
        if not sts: return False
        r = re.compile("file:.+?'(.+?)'").findall(data)
        return r[0]
    
    def parserCOUDMAILRU(self, baseUrl):
        printDBG("parserCOUDMAILRU baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        weblink  = self.cm.ph.getSearchGroups(data, '"weblink"\s*:\s*"([^"]+?)"')[0]
        videoUrl = self.cm.ph.getSearchGroups(data, '"weblink_video"\s*:[^\]]*?"url"\s*:\s*"(https?://[^"]+?)"')[0]
        videoUrl += '0p/%s.m3u8?double_encode=1' % (base64.b64encode(weblink))
        videoUrl = strwithmeta(videoUrl, {'User-Agent':HTTP_HEADER['User-Agent']})
        
        return getDirectM3U8Playlist(videoUrl, checkContent=True)
    
    def parserVIDEOMAIL(self, url):
        printDBG("parserVIDEOMAIL baseUrl[%s]" % url)
        #http://api.video.mail.ru/videos/embed/mail/etaszto/_myvideo/852.html
        #http://my.mail.ru/video/mail/etaszto/_myvideo/852.html#video=/mail/etaszto/_myvideo/852
        COOKIEFILE = self.COOKIE_PATH + "video.mail.ru.cookie"
        movieUrls = []
        try:
            sts, data = self.cm.getPage(url, {'cookiefile': COOKIEFILE, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False})
            if 'This video is only available on Mail.Ru' in data:
                tmpUrl = self.cm.ph.getSearchGroups(data, 'href="([^"]+?)"')[0]
                sts, data = self.cm.getPage(tmpUrl)
            metadataUrl =  self.cm.ph.getSearchGroups(data, """["']*metadataUrl["']*[ ]*:[ ]*["']((?:https?\:)?//[^"']+?[^"']*?)["']""")[0]
            if '' == metadataUrl:
                tmp =  self.cm.ph.getSearchGroups(data, """["']*metadataUrl["']*[ ]*:[ ]*["'][^0-9]*?([0-9]{19})[^0-9]*?["']""")[0]
                if '' == tmp:
                    tmp = self.cm.ph.getSearchGroups(data, '<link[^>]*?rel="image_src"[^>]*?href="([^"]+?)"')[0]
                    if '' == tmp: tmp = self.cm.ph.getSearchGroups(data, '<link[^>]*?href="([^"]+?)"[^>]*?rel="image_src"[^>]*?')[0]
                    tmp = self.cm.ph.getSearchGroups(urllib.unquote(tmp), '[^0-9]([0-9]{19})[^0-9]')[0]
                metadataUrl = 'http://videoapi.my.mail.ru/videos/{0}.json?ver=0.2.102'.format(tmp)
            if metadataUrl.startswith('//'): metadataUrl = 'http:' + metadataUrl
            sts, data = self.cm.getPage(metadataUrl, {'cookiefile': COOKIEFILE, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True})
            video_key = self.cm.getCookieItem(COOKIEFILE,'video_key')
            if '' != video_key:
                data = json_loads(data)['videos']
                for item in data:
                    videoUrl = item['url']
                    if videoUrl.startswith('//'): videoUrl = 'https:' + videoUrl
                    videoUrl = strwithmeta(videoUrl, {'Cookie':"video_key=%s" % video_key, 'iptv_buffering':'required'})
                    videoName = 'mail.ru: %s' % item['key'].encode('utf-8')
                    movieUrls.append({ 'name': videoName, 'url': videoUrl}) 
        except Exception:
            printExc()
        # Try old code extractor
        if 0 == len(movieUrls):
            idx = url.find(".html")
            if 1 > idx: return False
            authData = url[:idx].split('/')
            url = 'http://api.video.mail.ru/videos/' + authData[-4] + '/' + authData[-3] + '/' + authData[-2] + '/' + authData[-1] + '.json'
            sts, data = self.cm.getPage(url, {'cookiefile': COOKIEFILE, 'use_cookie': True, 'save_cookie': True, 'load_cookie': False})
            if not sts: return False
            video_key = self.cm.getCookieItem(COOKIEFILE,'video_key')
            if '' == video_key: return False
            data = re.search('"videos":{([^}]+?)}', data)
            if not data: return False
            formats = ['sd', 'hd']
            for item in formats:
                url = re.search('"%s":"([^"]+?)"' % item, data.group(1))
                if url:
                    movieUrls.append({ 'name': 'mail.ru: %s' % item, 'url':url.group(1) + '|Cookie="video_key=' + video_key + '"' })
        return movieUrls
        
        
    def parserWRZUTA(self, url):
        movieUrls = []
        
        # start algo from https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/wrzuta.py
        _VALID_URL = r'https?://(?P<uploader>[0-9a-zA-Z]+)\.wrzuta\.pl/(?P<typ>film|audio)/(?P<id>[0-9a-zA-Z]+)'
        try:
            while True:
                mobj = re.match(_VALID_URL, url)
                video_id = mobj.group('id')
                typ = mobj.group('typ')
                uploader = mobj.group('uploader')
                
                #sts, data = self.cm.getPage(url)
                #if not sts: break
                quality = {'SD':240, 'MQ':360, 'HQ':480, 'HD':720}
                audio_table = {'flv': 'mp3', 'webm': 'ogg', '???': 'mp3'}
                sts, data = self.cm.getPage('http://www.wrzuta.pl/npp/embed/%s/%s' % (uploader, video_id))
                if not sts: break
                
                data = json_loads(data)
                for media in data['url']:
                    fmt = media['type'].split('@')[0]
                    if typ == 'audio':
                        ext = audio_table.get(fmt, fmt)
                    else:
                        ext = fmt
                    if fmt in ['webm']: continue
                    movieUrls.append({'name': 'wrzuta.pl: ' + str(quality.get(media['quality'], 0)) + 'p', 'url':media['url']})                
                break;
        
        except Exception: 
            printExc()
        # end algo
        
        if len(movieUrls): return movieUrls
    
        def getShardUserFromKey(key):
            tab = ["w24", "w101", "w70", "w60", "w2", "w14", "w131", "w121", "w50", "w40", "w44", "w450", "w90", "w80", "w30", "w20", "w25", "w100", "w71", "w61", "w1", "w15", "w130", "w120", "w51", "w41", "w45", "w451", "w91", "w81", "w31", "w21"]
            abc = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            usr_idx = 0
            for i in range(11):
                tmp = key[i]
                usr_idx = (usr_idx * len(abc))
                usr_idx = (usr_idx + abc.find(tmp))
                usr_idx = (usr_idx & 0xFFFF)
            return tab[usr_idx]
            
        def getFileData(login, key, flagaXml, host, site, pltype): 
            url = "http://" + login + "." + host + "/xml/" + flagaXml + "/" + key + "/" + site + "/" + pltype + "/" + str(int(random() * 1000000 + 1))
            sts, data = self.cm.getPage(url)
            return data
        
        urlElems = urlparse(url)
        urlParams = parse_qs(urlElems.query)
        site     = urlParams.get('site', ["wrzuta.pl"])[0]
        host     = urlParams.get('host', ["wrzuta.pl"])[0]
        key      = urlParams.get('key', [None])[0]
        login    = urlParams.get('login', [None])[0]
        language = urlParams.get('login', ["pl"])[0]
        boolTab  = ["yes", "true", "t", "1"]
        embeded  = urlParams.get('embeded', ["false"])[0].lower() in boolTab
        inskin   = urlParams.get('inskin', ["false"])[0].lower() in boolTab
        
        if None == key: return False
        if None == login: login = getShardUserFromKey(key)
        if embeded: pltype = "eb"
        elif inskin: pltype = "is"
        else: pltype = "sa"

        data = getFileData(login, key, "kontent", host, site, pltype)
        formatsTab = [{'bitrate':360, 'file':'fileMQId_h5'},\
                      {'bitrate':480, 'file':'fileHQId_h5'},\
                      {'bitrate':720, 'file':'fileHDId_h5'},\
                      {'bitrate':240, 'file':'fileId_h5'}]
        
        for item in formatsTab:
            sts, url = CParsingHelper.getDataBeetwenMarkers(data, "<%s>" % item['file'], '</%s>' % item['file'], False)
            url = url.replace('<![CDATA[', '').replace(']]>', '')
            if sts: movieUrls.append({'name': 'wrzuta.pl: ' + str(item['bitrate']) + 'p', 'url':url.strip() + '/0'})
        return movieUrls
        
    def parserGOLDVODTV(self, baseUrl):
        printDBG("parserGOLDVODTV baseUrl[%s]" % baseUrl)
        COOKIE_FILE = GetCookieDir('goldvodtv.cookie')
        HTTP_HEADER = { 'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3' }
        SWF_URL = 'http://goldvod.tv/jwplayer_old/jwplayer.flash.swf'
        
        url = strwithmeta(baseUrl)
        baseParams = url.meta.get('params', {})
        
        params = {'header':HTTP_HEADER, 'with_metadata':True, 'cookie_items':{}, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params.update(baseParams)
        
        sts, data = self.cm.getPage('http://185.35.139.177/myip.php', params)
        params['cookie_items'].update({'my-ip':data.strip()})
        
        sts, data = self.cm.getPage(baseUrl, params)
        cUrl = data.meta['url']
        
        msg = 'Dostęp wyłącznie dla użytkowników z kontem premium' 
        if msg in data:
            SetIPTVPlayerLastHostError(msg)
        
        urlTab = []
        qualities = []
        tmp = self.cm.ph.getDataBeetwenMarkers(data, "box_quality", "</div>", False)[1]
        tmp = re.compile('''<a[^>]+?href=['"]([^'^"]+?)['"][^>]*?>([^<]+?)</a>''').findall(tmp)
        for item in tmp:
            qualities.append({'title':item[1], 'url':baseUrl+item[0]})
        
        if len(qualities):
            data2 = None
        else:
            data2 = data
            qualities.append({'title':'', 'url':baseUrl})
        
        titlesMap = {0:'SD', 1:'HD'}
        for item in qualities:
            if data2 == None:
                sts, data2 = self.cm.getPage( item['url'], params)
                if not sts:
                    data2 = None
                    continue
            data2 = self.cm.ph.getDataBeetwenMarkers(data2, '.setup(', '}', False)[1]
            rtmpUrls = re.compile('''=(rtmp[^"^']+?)["'&]''').findall(data2)
            if 0 == len(rtmpUrls): rtmpUrls = re.compile('''['"](rtmp[^"^']+?)["']''').findall(data2)
            for idx in range(len(rtmpUrls)):
                rtmpUrl = urllib.unquote(rtmpUrls[idx])
                if len(rtmpUrl):
                    rtmpUrl = rtmpUrl + ' swfUrl=%s live=1 pageUrl=%s' % (SWF_URL, baseUrl)
                    title = item['title']
                    if title == '': title = titlesMap.get(idx, 'default')
                    urlTab.append({'name':'[rtmp] ' + title, 'url':rtmpUrl})
            data2 = None
        
        if len(urlTab):
            printDBG(urlTab)
            return urlTab[::-1]
        
        # get connector link
        url = self.cm.ph.getSearchGroups(data, "'(http://goldvod.tv/tv-connector/[^']+?\.smil[^']*?)'")[0]
        if '.smil' in data:
            printDBG("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<EEE")
        if url == '': url = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?\.smil\?[^'^"]+?)['"]''')[0]
        if url != '' and not self.cm.isValidUrl(url): url = self.cm.getFullUrl(url, cUrl)
        
        params['load_cookie'] = True
        params['header']['Referer'] = SWF_URL
        
        # get stream link
        sts, data = self.cm.getPage(url, params)
        if sts:
            base = self.cm.ph.getSearchGroups(data, 'base="([^"]+?)"')[0]
            src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
            if ':' in src:
                src = src.split(':')[1]
                
            if base.startswith('rtmp'):
                return base + '/' + src + ' swfUrl=%s live=1 pageUrl=%s' % (SWF_URL, baseUrl)
        return False
        
    def parserVIDZER(self, baseUrl):
        printDBG("parserVIDZER baseUrl[%s]" % baseUrl)
        
        baseUrl = baseUrl.split('?')[0]
        
        HTTP_HEADER = { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        defaultParams = {'header' : HTTP_HEADER, 'cookiefile':GetCookieDir('vidzernet.cookie'), 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        def getPage(url, params={}, post_data=None):
            sts, data = False, None
            sts, data = self.cm.getPage(url, defaultParams, post_data)
            if sts:
                imgUrl = self.cm.ph.getSearchGroups(data, '"([^"]+?captcha-master[^"]+?)"')[0]
                if imgUrl.startswith('/'): imgUrl = 'http://www.vidzer.net' + imgUrl
                if imgUrl.startswith('http://') or imgUrl.startswith('https://'):
                    sessionEx = MainSessionWrapper() 
                    header = dict(HTTP_HEADER)
                    header['Accept'] = 'image/png,image/*;q=0.8,*/*;q=0.5'
                    params = dict(defaultParams)
                    params.update( {'maintype': 'image', 'subtypes':['jpeg', 'png'], 'check_first_bytes':['\xFF\xD8','\xFF\xD9','\x89\x50\x4E\x47'], 'header':header} )
                    filePath = GetTmpDir('.iptvplayer_captcha.jpg')
                    #Accept=image/png,image/*;q=0.8,*/*;q=0.5
                    ret = self.cm.saveWebFile(filePath, imgUrl.replace('&amp;', '&'), params)
                    if not ret.get('sts'):
                        SetIPTVPlayerLastHostError(_('Fail to get "%s".') % imgUrl)
                        return False
                    from Plugins.Extensions.IPTVPlayer.components.iptvmultipleinputbox import IPTVMultipleInputBox
                    from copy import deepcopy
                    params = deepcopy(IPTVMultipleInputBox.DEF_PARAMS)
                    params['accep_label'] = _('Send')
                    params['title'] = _('Answer')
                    params['list'] = []
                    item = deepcopy(IPTVMultipleInputBox.DEF_INPUT_PARAMS)
                    item['label_size'] = (160,75)
                    item['input_size'] = (300,25)
                    item['icon_path'] = filePath
                    item['title'] = clean_html(CParsingHelper.getDataBeetwenMarkers(data, '<h1', '</h1>')[1]).strip()
                    item['input']['text'] = ''
                    params['list'].append(item)
        
                    ret = 0
                    retArg = sessionEx.waitForFinishOpen(IPTVMultipleInputBox, params)
                    printDBG(retArg)
                    if retArg and len(retArg) and retArg[0]:
                        printDBG(retArg[0])
                        sts, data = self.cm.getPage(url, defaultParams, {'captcha':retArg[0][0]})
                        return sts, data
                    else:
                        SetIPTVPlayerLastHostError(_('Wrong answer.'))
                    return False, None
            return sts, data
            
        ########################################################
                    

        sts, data = getPage(baseUrl)
        if not sts: return False
        url = self.cm.ph.getSearchGroups(data, '<iframe src="(http[^"]+?)"')[0]
        if url != '':        
            sts, data = getPage(url)
            if not sts: return False
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div id="playerVidzer">', '</a>', False)[1]
        match = re.search('href="(http[^"]+?)"', data)
        if match:
            url = urllib.unquote( match.group(1) )
            return url
        
        r = re.search('value="(.+?)" name="fuck_you"', data)
        r2 = re.search('name="confirm" type="submit" value="(.+?)"', data)
        r3 = re.search('<a href="/file/([^"]+?)" target', data)
        if r:
            printDBG("r_1[%s]" % r.group(1))
            printDBG("r_2[%s]" % r2.group(1))
            data = 'http://www.vidzer.net/e/'+r3.group(1)+'?w=631&h=425'
            postdata = {'confirm' : r2.group(1), 'fuck_you' : r.group(1)}
            sts, data = getPage(data, {}, postdata)
            match = re.search("url: '([^']+?)'", data)
            if match:
                url = match.group(1) #+ '|Referer=http://www.vidzer.net/media/flowplayer/flowplayer.commercial-3.2.18.swf'
                return url
            else:
                return False
        else:
            return False
            
    def parserNOWVIDEOCH(self, url):
        printDBG("parserNOWVIDEOCH url[%s]" % url)
        return self._parserUNIVERSAL_B(url)
    
    def parserSTREAMINTO(self, baseUrl):
        printDBG("parserSTREAMINTO baseUrl[%s]" % baseUrl)
        # example video: http://streamin.to/okppigvwdk8w
        #                http://streamin.to/embed-rme4hyg6oiou-640x500.html
        #tmp =  self.__parseJWPLAYER_A(baseUrl, 'streamin.to')
        
        def getPageUrl(data):
            #printDBG("=======================================")
            #printDBG(data)
            #printDBG("=======================================")
            
            tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, ">eval(", '</script>')
            for tmp in tmpTab:
                tmp2 = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams, 0, r2=True)
                data += tmp2
            
            vidTab = []
            sub_tracks = []
            subData = self.cm.ph.getDataBeetwenMarkers(data, 'tracks:', ']', False)[1].split('}')
            for item in subData:
                if '"captions"' in item:
                    label   = self.cm.ph.getSearchGroups(item, 'label:\s*?"([^"]+?)"')[0]
                    srclang = self.cm.ph.getSearchGroups(item, 'srclang:\s*?"([^"]+?)"')[0]
                    src     = self.cm.ph.getSearchGroups(item, 'file:\s*?"([^"]+?)"')[0]
                    if not src.startswith('http'): continue
                    sub_tracks.append({'title':label, 'url':src, 'lang':label, 'format':'srt'})
            data = re.sub("tracks:[^\]]+?\]", "", data)
            
            streamer = self.cm.ph.getSearchGroups(data, 'streamer: "(rtmp[^"]+?)"')[0]
            printDBG(streamer)
            data     = re.compile('file:[ ]*?"([^"]+?)"').findall(data)
            
            for item in data:
                if item.startswith('http://'):
                    vidTab.insert(0, {'name': 'http://streamin.to/ ', 'url':strwithmeta(item, {'external_sub_tracks':sub_tracks})})
                elif item.startswith('rtmp://') or '' != streamer:
                    try:
                        if item.startswith('rtmp://'):
                            item     = item.split('flv:')
                            r        = item[0]
                            playpath = item[1]
                        else:
                            r        = streamer
                            playpath = item 
                        swfUrl  = "http://streamin.to/player6/jwplayer.flash.swf"
                        rtmpUrl = r + ' playpath=%s' % playpath + ' swfUrl=%s' % swfUrl + ' pageUrl=%s' % baseUrl
                        vidTab.append({'name': 'rtmp://streamin.to/ ', 'url':urlparser.decorateUrl(rtmpUrl, {'external_sub_tracks':sub_tracks, 'iptv_livestream':False})})
                    except Exception:
                        printExc()
            return vidTab
        vidTab = []
        if 'embed' not in baseUrl:
            baseUrl = 'http://streamin.to/embed-%s-640x500.html' % baseUrl.split('/')[-1]
        
        HTTP_HEADER = {"User-Agent":"Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10"}
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})
        #printDBG(data)
        if sts:
            errMarkers = ['File was deleted', 'File Removed', 'File Deleted.']
            for errMarker in errMarkers:
                if errMarker in data:
                    SetIPTVPlayerLastHostError(errMarker)
            vidTab = getPageUrl(data)
            if 0 == len(vidTab):
                cookies_data = ''
                cookies = re.findall("cookie\('([^']*)', '([^']*)'", data)
                for item in cookies:
                    cookies_data += '%s=%s;' % (item[0], item[1])
                
                sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False)
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
                HTTP_HEADER['Referer'] = baseUrl
                # get cookie for streamin.to
                if len(cookies_data):
                    HTTP_HEADER['Cookie'] = cookies_data[:-1]
                try:
                    sleep_time = int(self.cm.ph.getSearchGroups(data, '<span id="cxc">([0-9]+?)</span>')[0])
                    GetIPTVSleep().Sleep(sleep_time)
                except Exception:
                    printExc()
                    
                sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER}, post_data)
                if sts:
                    vidTab = getPageUrl(data)
        return vidTab
        
    def parserVSHAREIO(self, baseUrl):
        printDBG("parserVSHAREIO baseUrl[%s]" % baseUrl)
        # example video: 
        # http://vshare.io/v/72f9061/width-470/height-305/
        # http://vshare.io/v/72f9061/width-470/height-305/
        # http://vshare.io/d/72f9061/1
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/[dv]/([A-Za-z0-9]{7})/')[0]
        url = 'http://vshare.io/v/{0}/width-470/height-305/'.format(video_id)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36', 'Accept-Encoding':'gzip, deflate', 'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Referer':baseUrl}
        
        vidTab = []
        
        sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
        if not sts: return []
        
        tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<div[^>]+?class="xxx-error"[^>]*>'), re.compile('</div>'), False)[1]
        SetIPTVPlayerLastHostError(clean_html(tmp).strip())
        
        printDBG(data)
        
        enc = self.cm.ph.getDataBeetwenMarkers(data, 'eval(', '{}))')[1]
        if enc != '':
            try:
                jscode = base64.b64decode('''dmFyIGRlY29kZWQgPSAiIjsNCnZhciAkID0gZnVuY3Rpb24oKXsNCiAgcmV0dXJuIHsNCiAgICBhcHBlbmQ6IGZ1bmN0aW9uKGEpew0KICAgICAgaWYoYSkNCiAgICAgICAgZGVjb2RlZCArPSBhOw0KICAgICAgZWxzZQ0KICAgICAgICByZXR1cm4gaWQ7DQogICAgfQ0KICB9DQp9Ow0KDQolczsNCg0KcHJpbnQoZGVjb2RlZCk7DQo=''') % (enc)                     
                printDBG("+++++++++++++++++++++++  CODE  ++++++++++++++++++++++++")
                printDBG(jscode)
                printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                ret = js_execute( jscode )
                if ret['sts'] and 0 == ret['code']:
                    decoded = ret['data'].strip()
                    printDBG('DECODED DATA -> [%s]' % decoded)
                    data = decoded + '\n' + data
            except Exception:
                printExc()
        
        stream   = self.cm.ph.getSearchGroups(data, '''['"](http://[^"^']+?/stream\,[^"^']+?)['"]''')[0]
        if '' == stream: stream   = json_loads('"%s"' % self.cm.ph.getSearchGroups(data, '''['"](http://[^"^']+?\.flv)['"]''')[0])
        if '' != stream:
            vidTab.append({'name': 'http://vshare.io/stream ', 'url':stream})
            
        if 0 == len(vidTab):
            tmp = self.cm.ph.getDataBeetwenMarkers(data, 'clip:', '}', False)[1]
            url = json_loads('"%s"' % self.cm.ph.getSearchGroups(tmp, '''['"](http[^"^']+?)['"]''')[0])
            if url != '': vidTab.append({'name': 'http://vshare.io/ ', 'url':url})
        
        if 0 == len(vidTab):
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False, False)
            for item in tmp:
                if 'video/mp4' in item or '.mp4' in item:
                    label = self.cm.ph.getSearchGroups(item, '''label=['"]([^"^']+?)['"]''')[0]
                    res = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
                    if label == '': label = res
                    url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                    if url.startswith('//'): url = 'http:' + url
                    if not self.cm.isValidUrl(url): continue
                    vidTab.append({'name':'vshare.io ' + label, 'url':strwithmeta(url, {'Referer':baseUrl})})
            
        return vidTab
            
    def parserVIDSSO(self, url):
        printDBG("parserVIDSSO url[%s]" % url)
        # example video: http://www.vidsso.com/video/hhbwr85FMGX
        try:
            sts, data = self.cm.getPage(url)
            try:
                confirm  = re.search('<input name="([^"]+?)" [^>]+?value="([^"]+?)"', data)
                vs       = re.search('<input type="hidden" value="([^"]+?)" name="([^"]+?)">', data)
                post = {confirm.group(1):confirm.group(2), vs.group(2):vs.group(1)}
                sts, data = self.cm.getPage(url, {'Referer':url}, post)
            except Exception:
                printExc()
            
            url = re.search("'file': '(http[^']+?)'", data).group(1)
            return url
        except Exception:
            printExc()
        return False
            
    def parserWATTV(self, url="http://www.wat.tv/images/v70/PlayerLite.swf?videoId=6owmd"):
        printDBG("parserWATTV url[%s]\n" % url)
        # example video: http://www.wat.tv/video/orages-en-dordogne-festival-6xxsn_2exyh_.html
        def getTS():
            #ts = math.floor( float(ts) / 1000 )
            url = "http://www.wat.tv/servertime?%d" % int(random() * 0x3D0900)
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
            ts = int(data.split('|')[0])
            return int2base(int(ts), 36)

        def computeToken(urlSuffixe, ts):
            tHex = int2base(int(ts, 36), 16)
            while len(tHex) < 8:
                tHex = "0" + tHex
            constToken = "9b673b13fa4682ed14c3cfa5af5310274b514c4133e9b3a81e6e3aba009l2564"
            hashAlg = MD5() 
            return hexlify( hashAlg(constToken + urlSuffixe + tHex) ) + "/" + tHex

        movieUrls = []
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
        HTTP_HEADER['Referer'] = url
        match = re.search("videoId=([^']+?)'", url + "'")

        sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
        if sts:
            real_id = re.search(r'xtpage = ".*-(.*?)";', data)
            if real_id:
                real_id = real_id.group(1)
                movieUrls.append({'name': 'wat.tv: Mobile', 'url':'http://wat.tv/get/android5/%s.mp4' % real_id})    
            if not match:
                match = re.search('videoId=([^"]+?)"', data)
        
        for item in ["webhd", "web"]:
            try:
                vidId = int(match.group(1), 36)
                url_0 = "/%s/%d" % (item, vidId)
                url_1 = computeToken(url_0, getTS())
                url_2 =  url_0 + "?token=" + url_1 + "&"
                url   = "http://www.wat.tv/get" + url_2 + "domain=www.wat.tv&refererURL=www.wat.tv&revision=04.00.388%0A&synd=0&helios=1&context=playerWat&pub=5&country=FR&sitepage=WAT%2Ftv%2Fu%2Fvideo&lieu=wat&playerContext=CONTEXT_WAT&getURL=1&version=WIN%2012,0,0,44"
                printDBG("====================================================: [%s]\n" % url)
                
                sts, url = self.cm.getPage(url, {'header' : HTTP_HEADER})
                if sts:
                    if url.split('?')[0].endswith('.f4m'):
                        url = urlparser.decorateUrl(url, HTTP_HEADER)
                        retTab = getF4MLinksWithMeta(url)
                        movieUrls.extend(retTab)
                    elif 'ism' not in url:
                        movieUrls.append({'name': 'wat.tv: ' + item, 'url':url})
            except Exception:
                printExc()
        movieUrls.reverse()
        return movieUrls
        
    def parserFILEONETV(self, baseUrl):
        printDBG("parserFILEONETV baseUrl[%s]" % baseUrl)
        url = baseUrl.replace('show/player', 'v')
        sts, data = self.cm.getPage(url)
        if not sts: return False
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'setup({', '});', True)[1]
        videoUrl  = self.cm.ph.getSearchGroups(tmp, '''file[^"^']+?["'](https?://[^"^']+?)['"]''')[0]
        if videoUrl == '': videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=([^'^"]+?)\s[^>]*?video/mp4''')[0]
        if videoUrl.startswith('//'): videoUrl = 'https:' + videoUrl
        if self.cm.isValidUrl(videoUrl): return videoUrl
        return False
        
    def parserHDGOCC(self, baseUrl):
        printDBG("parserHDGOCC url[%s]\n" % baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', 'Referer' : Referer}
        
        episode = self.cm.ph.getSearchGroups(baseUrl+'|', '''[&\?]e=([0-9]+?)[^0-9]''')[0]
        
        vidTab = []
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        printDBG(data)
        
        url = self.cm.ph.getSearchGroups(data, '<iframe[^>]+?src="([^"]+?)"', 1, True)[0]
        if url.startswith('//'):
            url = 'http:' + url
        HTTP_HEADER['Referer'] = baseUrl
        
        if episode != '':
            if '?' in url: url += '&e=' + episode
            else: url += '?e=' + episode
        
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return
        
        unique = []
        urls = []
        
        printDBG(data)
        
        tmpTab = re.compile('''var\s*url\s*=\s*['"]([,]*?http[^'^"]+?)['"]''').findall(data)
        for tmp in tmpTab:
            urls.extend(tmp.split(' or '))
        tmp = self.cm.ph.getSearchGroups(data, '''file\s*:\s*['"]([,]*?http[^'^"]+?)['"]''', 1, True)[0]
        urls.extend(tmp.split(' or '))
        
        urlsTab = []
        for item in urls:
            urlsTab.extend(item.split(','))
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'media:', ']', False)[1].split('}')
        for item in tmp:
            ok = False
            if 'video/mp4' in item:
                ok = True
            url = self.cm.ph.getSearchGroups(item,'''["']([^"^']+?\.mp4(?:\?[^'^"]*?)?)["']''', 1, True)[0]
            if ok or url.split('?')[0].lower().endswith('.mp4'): 
                urlsTab.append(self.cm.getFullUrl(url, self.cm.meta['url']))
        
        for url in urlsTab:
            url = url.strip()
            if not self.cm.isValidUrl(url): continue
            if url in unique: continue
            label = self.cm.ph.getSearchGroups(url, '''/([0-9]+?)\-''', 1, True)[0]
            if label == '':
                if '/3/' in url: label = '720p'
                elif '/2/' in url: label = '480p'
                else: label = '360p'
            if url.split('?')[0].endswith('.m3u8'):
                url = urlparser.decorateUrl(url, HTTP_HEADER)
                tmpTab = getDirectM3U8Playlist(url, checkContent=True)
                tmpTab.extend(vidTab)
                vidTab = tmpTab
            elif url.split('?')[0].endswith('.f4m'):
                url = urlparser.decorateUrl(url, HTTP_HEADER)
                tmpTab = getF4MLinksWithMeta(url)
                tmpTab.extend(vidTab)
                vidTab = tmpTab
            else:
                url = urlparser.decorateUrl(url, HTTP_HEADER)
                vidTab.append({'name':label, 'url':url})
        reNum = re.compile('([0-9]+)')
        def __quality(x):
            try: return int(x['name'][:-1])
            except Exception:
                printExc()
                return 0
        vidTab.sort(key=__quality, reverse=True)
        return vidTab
        
    def parserUSERSCLOUDCOM(self, baseUrl):
        printDBG("parserUSERSCLOUDCOM baseUrl[%s]\n" % baseUrl)
        HTTP_HEADER = {'User-Agent': "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"}
        COOKIE_FILE = GetCookieDir('userscloudcom.cookie')
        rm(COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        sts, data = self.cm.getPage(baseUrl, params)
        cUrl = self.cm.meta['url']

        errorTab = ['File Not Found', 'File was deleted']
        for errorItem in errorTab:
            if errorItem in data:
                SetIPTVPlayerLastHostError(_(errorItem))
                break
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player_code"', '</div>', True)[1]
        tmp = self.cm.ph.getDataBeetwenMarkers(tmp, ">eval(", '</script>')[1]
        # unpack and decode params from JS player script code
        tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
        if tmp != None: data = tmp + data
        # printDBG(data)
        # get direct link to file from params
        videoUrl = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl
        videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?["']video''')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
        if not sts: return False
        
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        params['header']['Referer'] = cUrl
        params['max_data_size'] = 0
        
        sts, data = self.cm.getPage(cUrl, params, post_data)
        if sts and 'text' not in self.cm.meta['content-type']:
            return self.cm.meta['url']
        
    def parserTUNEPK(self, baseUrl):
        printDBG("parserTUNEPK url[%s]\n" % baseUrl)
        # example video: http://tune.pk/video/4203444/top-10-infamous-mass-shootings-in-the-u
        HTTP_HEADER = {'User-Agent': "Mozilla/5.0"}
        COOKIE_FILE = GetCookieDir('tunepk.cookie')
        rm(COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        for item in ['vid=', '/video/', '/play/']:
            vid = self.cm.ph.getSearchGroups(baseUrl+'&', item+'([0-9]+)[^0-9]')[0]
            if '' != vid: break
        if '' == vid: return []
        
        url = 'http://embed.tune.pk/play/%s?autoplay=no&ssl=no' % vid
        
        sts, data = self.cm.getPage(url, params)
        if not sts: return []
        
        printDBG(data)
        
        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](https?://[^"^']+?)["']''', 1, True)[0]
        if self.cm.isValidUrl(url):
            params['header']['Referer'] = url
            sts, data = self.cm.getPage(url, params)
            if not sts: return []
        
        url = self.cm.ph.getSearchGroups(data, '''var\s+?requestURL\s*?=\s*?["'](https?://[^"^']+?)["']''', 1, True)[0]
        
        sts, data = self.cm.getPage(url, params)
        if not sts: return []
        
        data = json_loads(data)
        vidTab = []
        for item in data['data']['details']['player']['sources']:
            if 'mp4' == item['type']:
                url  = item['file']
                name = str(item['label']) + ' ' + str(item['type'])
                vidTab.append({'name':name, 'url':url})
        
        return vidTab
    
    def parserVIDEOTT(self, url):
        printDBG("parserVIDEOTT url[%r]" % url)
        # based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/videott.py
        # example video: http://www.video.tt/video/HRKwm3EhI
        linkList = []
        try:
            mobj = re.match(r'http://(?:www\.)?video\.tt/(?:video/|watch_video\.php\?v=|embed/)(?P<id>[\da-zA-Z]{9})', url)
            video_id = mobj.group('id')
        except Exception:
            printExc()
            return linkList
        url = 'http://www.video.tt/player_control/settings.php?v=%s' % video_id
        sts, data = self.cm.getPage(url)
        if sts:
            try:
                data = json_loads(data)['settings']
                linkList = [
                    {
                        'url': base64.b64decode(res['u']),
                        'name': res['l'],
                    } for res in data['res'] if res['u']
                ]
            except Exception:
                printExc()
        return linkList
        
    def parserEXASHARECOM(self, url):
        printDBG("parserEXASHARECOM url[%r]" % url)
        # example video: http://www.exashare.com/s4o73bc1kd8a
        HTTP_HEADER = { 'User-Agent':"Mozilla/5.0", 'Referer':url }
        if 'exashare.com' in url:
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})
            if not sts: return
            url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?)["']''', 1, True)[0].replace('\n', '').replace('\r', '')
            printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>> url[%s]\n" % url)
        def _findLinks(data):
            return self._findLinks(data, 'exashare.com', m1='setup(', m2=')')
        return self.__parseJWPLAYER_A(url, 'exashare.com', _findLinks, folowIframe=True)
        
    def parserALLVIDCH(self, baseUrl):
        printDBG("parserALLVIDCH baseUrl[%r]" % baseUrl)
        # example video: http://allvid.ch/embed-fhpd7sk5ac2o-830x500.html
        
        HTTP_HEADER = { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        params = {'header' : HTTP_HEADER, 'cookiefile':GetCookieDir('allvidch.cookie'), 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        def _findLinks(data):
            return self._findLinks(data, 'allvid.ch', m1='setup(', m2='image:')
        
        def _preProcessing(data):
            url2 = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=["'](http[^"^']+?)["']''', 1, True)[0]
            if url2.startswith('http'):
                sts, data2 = self.cm.getPage(url2, params)
                if sts:
                    return data2
            return data
        
        return self._parserUNIVERSAL_A(baseUrl, 'http://allvid.ch/embed-{0}-830x500.html', _findLinks, _preProcessing,  HTTP_HEADER, params)
        #return self.__parseJWPLAYER_A(baseUrl, 'allvid.ch', _findLinks)
        
    def parserALBFILMCOM(self, baseUrl):
        printDBG("parserALBFILMCOM baseUrl[%r]" % baseUrl)
        # www.albfilm.com/video/?m=endless_love_2014
        def _findLinks(data):
            videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=["'](http[^"^']+?)["']''', 1, True)[0]
            if videoUrl == '': return []
            return [{'name':'albfilm.com', 'url':videoUrl}]
        url = baseUrl
        return self._parserUNIVERSAL_A(baseUrl, url, _findLinks)
        
    def parserVIDAG(self, baseUrl):
        printDBG("parserVIDAG baseUrl[%r]" % baseUrl)
        # example video: http://vid.ag/embed-24w6kstkr3zt-540x360.html
        def _findLinks(data):
            tab = []
            tmp = self._findLinks(data, 'vid.ag', m1='setup(', m2='image:')
            for item in tmp:
                if not item['url'].split('?')[0].endswith('.m3u8'):
                    tab.append(item)
            return tab
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':'http://www.streaming-series.xyz/', 'Cookie':'__test' }
        return self._parserUNIVERSAL_A(baseUrl, 'http://vid.ag/embed-{0}-540x360.html', _findLinks, None, HTTP_HEADER)
        
    def parserVODLOCKER(self, url):
        printDBG("parserVODLOCKER url[%r]" % url)
        # example video: http://vodlocker.com/txemekqfbopy
        return self.__parseJWPLAYER_A(url, 'vodlocker.com')
        
    def parserSTREAMABLECOM(self, baseUrl):
        printDBG("parserSTREAMABLECOM baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?video/mp4''')[0]
        if videoUrl == '':
            tmp = re.compile('''sourceTag\.src\s*?=\s*?['"]([^'^"]+?)['"]''').findall(data)
            for item in tmp:
                if 'mobile' not in item:
                    videoUrl = item
                    break
            if videoUrl == '' and len(tmp):
                videoUrl = tmp[-1]
        if videoUrl == '':
            videoUrl = self.cm.ph.getSearchGroups(data, '''<video[^>]+?src=['"]([^'^"]+?)['"]''')[0]
            if videoUrl.split('?', 1)[0].split('.')[-1].lower() != 'mp4':
                videoUrl = ''
            
        if videoUrl.startswith('//'):
            videoUrl = 'https:' + videoUrl
        if self.cm.isValidUrl(videoUrl):
            return videoUrl.replace('&amp;', '&')
        msg = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'content'), ('</div', '>'))[1])
        SetIPTVPlayerLastHostError(msg)
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++ " + msg)
        return False
        
    def parserMATCHATONLINE(self, baseUrl):
        printDBG("parserMATCHATONLINE baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        hlsUrl = self.cm.ph.getSearchGroups(data, '''['"]?hls['"]?\s*?:\s*?['"]([^'^"]+?)['"]''')[0]
        if hlsUrl.startswith('//'): hlsUrl = 'http:' + hlsUrl
        if self.cm.isValidUrl(hlsUrl):
            hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto':'m3u8', 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False)})
            return getDirectM3U8Playlist(hlsUrl, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999)
        return False
        
    def parserPLAYPANDANET(self, baseUrl):
        printDBG("parserPLAYPANDANET baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl.replace('&amp;', '&'))
        if not sts: return False
        videoUrl = self.cm.ph.getSearchGroups(data, '''_url\s*=\s*['"]([^'^"]+?)['"]''')[0]
        if videoUrl.startswith('//'):
            videoUrl = 'http:' + videoUrl
        videoUrl = urllib.unquote(videoUrl)
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        return False
        
    def parserAKVIDEOSTREAM(self, baseUrl):
        printDBG("parserAKVIDEOSTREAM baseUrl[%r]" % baseUrl)
        
        # if url is in this form
        # https://akvideo.stream/video.php?file_code=mo2iqr25yds3
        # try to convert to
        # https://akvideo.stream/video/mo2iqr25yds3
        #https://akvideo.stream/swvideoid/246231.html
        
        i = baseUrl.find("file_code=")
        if i>0 :
            video_id = baseUrl[ i+10 :]
            baseUrl = "https://akvideo.stream/video/" + video_id
            printDBG("try similar url '%s':" % baseUrl)
            
        urlTab = []
        

        USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
        COOKIE_FILE = GetCookieDir('akvideo.stream.cookie')
        HttpHeader = {
            'User-Agent': USER_AGENT, 
            'Accept': 'text/html', 
            'Accept-Encoding': 'gzip', 
            'Referer': baseUrl
        }
        
        HttpParams = {'header': HttpHeader , 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        HttpParams['cloudflare_params'] = {'domain':'akvideo.stream', 'cookie_file': COOKIE_FILE, 'User-Agent': USER_AGENT}
        
        sts, data = self.cm.getPageCFProtection(baseUrl, HttpParams)

        if not sts: 
            return False
        
        printDBG(data)
        
        
        # test if there is a captcha to solve
        if 'sitekey' in data:
            # captcha to solve
            sitekey = re.findall("data-sitekey='([^']+)'", data)
            if sitekey:
                # solve captcha to login
                (token, errorMsgTab) = CaptchaHelper().processCaptcha(sitekey[0], baseUrl)
                
                printDBG(token)
                
                return
                
        names = {}
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<a', '>', 'pure-button'), ('</td', '>'))
        for idx in range(len(tmp)):
            t = clean_html(tmp[idx]).strip()
            names[idx] = t
        
        jscode = [self.jscode['jwplayer']]
        jscode.append('var element=function(n){print(JSON.stringify(n)),this.on=function(){}},Clappr={};Clappr.Player=element,Clappr.Events={PLAYER_READY:1,PLAYER_TIMEUPDATE:1,PLAYER_PLAY:1,PLAYER_ENDED:1};')
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item: jscode.append(item)
        urlTab = []
        ret = js_execute( '\n'.join(jscode) )
        if ret['sts'] and 0 == ret['code']:
            data = json_loads(ret['data'].strip())
            for item in data['sources']:
                name = names.get(len(urlTab), 'direct %d' % (len(urlTab) + 1))
                if isinstance(item, dict):
                    url = item['file']
                    name = item.get('label', name)
                else:
                    url = item
                
                if self.cm.isValidUrl(url) and '.mp4' in url.lower():
                    urlTab.append({'name':name, 'url':url})
        
        return urlTab
        
    def parserVSHAREEU(self, baseUrl):
        printDBG("parserVSHAREEU baseUrl[%r]" % baseUrl)
        # example video: http://vshare.eu/mvqdaea0m4z0.htm
        
        HTTP_HEADER = {'User-Agent': "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"}
        
        if 'embed' not in baseUrl:
            COOKIE_FILE = GetCookieDir('vshareeu.cookie')
            rm(COOKIE_FILE)
            params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
            sts, data = self.cm.getPage(baseUrl, params)
            if not sts: return False
            
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
            if not sts: return False
            
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            params['header']['Referer'] = baseUrl
            
            GetIPTVSleep().Sleep(5)
            
            sts, data = self.cm.getPage(baseUrl, params, post_data)
            if not sts: return False
        else:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return False
            
        sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, ">eval(", '</script>')
        if sts:
            # unpack and decode params from JS player script code
            tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams, 0, r2=True)
            printDBG(tmp)
            data = tmp + data
        
        linksTab = self._findLinks(data, urlparser.getDomain(baseUrl))
        if 0 == len(linksTab):
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source ', '>', False, False)
            for item in data:
                url  = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                if url.startswith('//'):
                    url = 'http:' + url
                if not url.startswith('http'):
                    continue
                
                if 'video/mp4' in item:
                    type = self.cm.ph.getSearchGroups(item, '''type=['"]([^"^']+?)['"]''')[0]
                    res  = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
                    label = self.cm.ph.getSearchGroups(item, '''label=['"]([^"^']+?)['"]''')[0]
                    if label == '': label = res
                    url = urlparser.decorateUrl(url, {'Referer':baseUrl,  'User-Agent':HTTP_HEADER['User-Agent']})
                    linksTab.append({'name':'{0}'.format(label), 'url':url})
                elif 'mpegurl' in item:
                    url = urlparser.decorateUrl(url, {'iptv_proto':'m3u8', 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
                    tmpTab = getDirectM3U8Playlist(url, checkExt=True, checkContent=True)
                    linksTab.extend(tmpTab)
        for idx in range(len(linksTab)):
            linksTab[idx]['url'] = strwithmeta(linksTab[idx]['url'], {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
        return linksTab
        
    def parserVIDSPOT(self, url):
        printDBG("parserVIDSPOT url[%r]" % url)
        # example video: http://vidspot.net/2oeqp21cdsee
        return self.__parseJWPLAYER_A(url, 'vidspot.net')
            
    def parserVIDBULL(self, baseUrl):
        printDBG("parserVIDBULL baseUrl[%s]" % baseUrl)
        # example video: http://vidbull.com/zsi9kwq0eqm4.html
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = baseUrl
        
        # we will try three times if they tell us that we wait to short
        tries = 0
        while tries < 3:
            # get embedded video page and save returned cookie
            sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})
            if not sts: return False
            
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<input type="hidden" name="op" value="download2">', '</Form>', True)
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            
            try:
                sleep_time = int(self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0]) 
                GetIPTVSleep().Sleep(sleep_time)
            except Exception:
                printExc()
            if {} == post_data:
                post_data = None
            sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER}, post_data)
            if not sts: return False
            if 'Skipped countdown' in data:
                tries += tries
                continue # we will try three times if they tell us that we wait to short
            # get JS player script code from confirmation page
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player_code"', '</div>', True)
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(tmp, ">eval(", '</script>')
            if sts:
                # unpack and decode params from JS player script code
                data = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
                printDBG(data)
                # get direct link to file from params
                src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                if src.startswith('http'):
                    return src
            # get direct link to file from params
            file = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0]
            if '' != file:
                if file.startswith('http'): return src
                else:
                    key = 'YTk0OTM3NmUzN2IzNjlmMTdiYzdkM2M3YTA0YzU3MjE='
                    bkey, knownCipherText = a2b_hex(base64.b64decode(key)), a2b_hex(file)
                    kSize = len(bkey)
                    alg = AES(bkey, keySize=kSize, padding=noPadding())
                    file = alg.decrypt(knownCipherText).split('\x00')[0]
                    if file.startswith('http'):
                        return file
            break
        return False
        
    def parserDIVEXPRESS(self, baseUrl):
        printDBG("parserDIVEXPRESS baseUrl[%s]" % baseUrl)
        # example video: http://divxpress.com/h87ygyutusp6/The.Last.Ship.S01E04.HDTV.x264-LOL_Napisy_PL.AVI.html
        return self.parserVIDBULL(baseUrl)
        
    def parserPROMPTFILE(self, baseUrl):
        printDBG("parserPROMPTFILE baseUrl[%s]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if sts:
            HTTP_HEADER = dict(self.HTTP_HEADER) 
            HTTP_HEADER['Referer'] = baseUrl
            if 'Continue to File' in data:
                sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post" action="">', '</form>', False, False)
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
                params = {'header' : HTTP_HEADER, 'cookiefile':GetCookieDir('promptfile.cookie'), 'use_cookie': True, 'save_cookie':True, 'load_cookie':False}
                sts, data = self.cm.getPage(baseUrl, params, post_data)
                if not sts:
                    return False
            data = self.cm.ph.getSearchGroups(data, """url: ["'](http[^"']+?)["'],""")[0]
            if '' != data:
                return data
        return False
        
    def parserPLAYEREPLAY(self, baseUrl):
        printDBG("parserPLAYEREPLAY baseUrl[%s]" % baseUrl)
        videoIDmarker = "((?:[0-9]){5}\.(?:[A-Za-z0-9]){28})"
        HTTP_HEADER = {'User-Agent': "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"}

        COOKIE_FILE = GetCookieDir('playreplaynet.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        sts, data = self.cm.getPage(baseUrl, params)
        if sts:
            data = self.cm.ph.getSearchGroups(data, videoIDmarker)[0]
        if data == '':
            data = self.cm.ph.getSearchGroups(baseUrl, videoIDmarker)[0]
        if '' != data: 
            HTTP_HEADER['Referer'] = baseUrl
            post_data = {'r':'[["file/flv_link2",{"uid":"%s","link":true}],["file/flv_image",{"uid":"%s","link":true}]]' % (data, data)}
            #
            params['header'] = HTTP_HEADER
            params['load_cookie'] = True
            sts, data = self.cm.getPage('http://playreplay.net/data', params, post_data)
            printDBG(data)
            if sts:
                data = json_loads(data)['data'][0]
                if 'flv' in data[0]:
                    return strwithmeta(data[0], {'Range':'0', 'iptv_buffering':'required'})
        return False
        
    def parserVIDEOWOODTV(self, baseUrl):
        printDBG("parserVIDEOWOODTV baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        if 'embed' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{4})/')[0]
            url = 'http://videowood.tv/embed/{0}'.format(video_id)
        else:
            url = baseUrl 
        
        params = {'header' : HTTP_HEADER}
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        while True:
            vidUrl = self.cm.ph.getSearchGroups(data, """["']*file["']*:[ ]*["'](http[^"']+?(?:\.mp4|\.flv)[^"']*?)["']""")[0]
            if '' != vidUrl:
                return vidUrl.replace('\\/', '/')
            
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>')
            if sts:
                # unpack and decode params from JS player script code
                data = unpackJSPlayerParams(data, TEAMCASTPL_decryptPlayerParams)
                #data = self.cm.ph.getDataBeetwenMarkers(data, 'config=', ';',
                printDBG(data)
                continue
            break
        return False
        
    def parserMOVRELLCOM(self, baseUrl):
        printDBG("parserMOVRELLCOM baseUrl[%s]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if sts:
            HTTP_HEADER = dict(self.HTTP_HEADER) 
            HTTP_HEADER['Referer'] = baseUrl
            if 'Watch as Free User' in data:
                sts, data = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>', False, False)
                post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
                params = {'header' : HTTP_HEADER}
                sts, data = self.cm.getPage(baseUrl, params, post_data)
                if not sts:
                    return False
            # get JS player script code from confirmation page
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="player_code"', '</div>', True)
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(tmp, ">eval(", '</script>')
            if sts:
                # unpack and decode params from JS player script code
                data = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
                printDBG(data)
                # get direct link to file from params
                src = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
                if src.startswith('http'):
                    return src
        return False
        
    def parserVIDFILENET(self, baseUrl):
        printDBG("parserVIDFILENET baseUrl[%s]" % baseUrl)
        vidTab = []
        #COOKIE_FILE = GetCookieDir('vidfilenet.cookie')
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        params = {'header':HTTP_HEADER} #, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        rm(HTTP_HEADER)
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        #cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False, False)
        for item in data:
            if 'video/mp4' in item or '.mp4' in item:
                res = self.cm.ph.getSearchGroups(item, '''res=['"]([^"^']+?)['"]''')[0]
                url = self.cm.ph.getSearchGroups(item, '''src=['"]([^"^']+?)['"]''')[0]
                if url.startswith('//'): url = 'http:' + url
                if not self.cm.isValidUrl(url): continue
                vidTab.append({'name':'vidfile.net ' + res, 'url':strwithmeta(url, {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})}) #'Cookie':cookieHeader,
        vidTab.reverse()
        return vidTab
        
    def parserMP4UPLOAD(self, baseUrl):
        printDBG("parserMP4UPLOAD baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        if referer != '': HTTP_HEADER['Referer'] = referer
        paramsUrl = {'header':HTTP_HEADER}
        videoUrls = []
        
        sts, data = self.cm.getPage(baseUrl, paramsUrl)
        
        cUrl = self.cm.getBaseUrl(self.cm.meta['url'])
        domain = urlparser.getDomain(cUrl)
        
        jscode = [self.jscode['jwplayer']]
        printDBG(jscode)
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item and 'setup' in item:
                jscode.append(item)
        urlTab = []
        jscode = '\n'.join(jscode)
        ret = js_execute( jscode )
        #if ret['sts'] and 0 == ret['code']:
        data = json_loads(ret['data'])
        if 'sources' in data: data = data['sources']
        else: data = [data]
        for item in data:
            url = item['file']
            type = item.get('type', url.rsplit('.', 1)[-1].split('?', 1)[0]).lower()
            label = item.get('label', domain)
            if 'mp4' not in type: continue
            if url == '': continue
            url = urlparser.decorateUrl(self.cm.getFullUrl(url, cUrl), {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
            urlTab.append({'name':'{0} {1}'.format(domain, label), 'url':url})
        return urlTab
        
    def parserYUKONS(self, baseUrl):
        printDBG("parserYUKONS url[%s]" % baseUrl)
        #http://yukons.net/watch/willstream002?Referer=wp.pl
        def _resolveChannelID(channel):
            def _decToHex(a):
                b = hex(a)[2:]
                if 1 == len(b):
                    return '0'+b
                else:
                    return b
            
            def _resolve(a):
                b = ''
                for i in range(len(a)):
                    b += _decToHex(ord(a[i]))
                return b
                
            return _resolve( _resolve(channel) )
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        shortChannelId = baseUrl.split('?')[0].split('/')[-1]
        Referer = baseUrl.meta.get('Referer', '')
        
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Referer' : Referer}
        COOKIE_FILE = GetCookieDir('yukonsnet.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}

        longChannelId = _resolveChannelID(shortChannelId)
        url1 = 'http://yukons.net/yaem/' + longChannelId
        sts, data = self.cm.getPage(url1, params)
        if sts:
            kunja = re.search("'([^']+?)';", data).group(1)
            url2 = 'http://yukons.net/embed/' + longChannelId + '/' + kunja + '/680/400'
            params.update({'save_cookie' : False, 'load_cookie' : True}) 
            sts, data = self.cm.getPage(url2, params)
            if sts:
                data = CParsingHelper.getDataBeetwenMarkers(data, "eval(", '</script>', False)[1]
                data = unpackJSPlayerParams(data, VIDUPME_decryptPlayerParams, 0)
                printDBG(data)
                id = CParsingHelper.getDataBeetwenMarkers(data, "id=", '&', False)[1]
                pid = CParsingHelper.getDataBeetwenMarkers(data, "pid=", '&', False)[1]
                data = CParsingHelper.getDataBeetwenMarkers(data, "eval(", '</script>', False)[1]
                sts, data = self.cm.getPage("http://yukons.net/srvload/"+id, params)
                printDBG(">> [%s]" % data)
                if sts:
                    ip = data[4:].strip()
                    url = 'rtmp://%s:443/kuyo playpath=%s?id=%s&pid=%s  swfVfy=http://yukons.net/yplay2.swf pageUrl=%s conn=S:OK live=1' % (ip, shortChannelId, id, pid, url2)
                    return url
        return False
        
    def parserUSTREAMTV(self, linkUrl):
        printDBG("parserUSTREAMTV linkUrl[%s]" % linkUrl)
        WS_URL = "http://r{0}-1-{1}-{2}-{3}.ums.ustream.tv"
        def generate_rsid():
            return "{0:x}:{1:x}".format(randint(0, 1e10), randint(0, 1e10))

        def generate_rpin():
            return "_rpin.{0:x}".format(randint(0, 1e15))
        
        referer = linkUrl
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25', 'Accept':'*/*', 'Accept-Encoding': 'gzip, deflate', 'Referer': referer}
        COOKIE_FILE = GetCookieDir('ustreamtv.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True, 'load_cookie':True}
        
        #http://www.ustream.tv/channel/nasa-educational
        linksTab = []
        live = True
        # get PC streams
        while True:
            channelID = self.cm.ph.getSearchGroups(linkUrl+'|', "cid=([0-9]+?)[^0-9]")[0]
            if '' == channelID:            
                sts, data = self.cm.getPage(linkUrl)
                if not sts: break
                channelID = self.cm.ph.getSearchGroups(data, 'data-content-id="([0-9]+?)"')[0]
                if '' == channelID: channelID = self.cm.ph.getSearchGroups(data, 'ustream.vars.contentId=([0-9]+?)[^0-9]')[0]
                if '' == channelID: channelID = self.cm.ph.getSearchGroups(data, 'ustream.vars.cId=([0-9]+?)[^0-9]')[0]

            if '' == channelID: break
            #in linkUrl and 'ustream.vars.isLive=true' not in data and '/live/' not in linkUrl
            if '/recorded/' in linkUrl:
                videoUrl = 'https://www.ustream.tv/recorded/' + channelID
                live = False
            else:
                videoUrl = 'https://www.ustream.tv/embed/' + channelID
                live = True
            
            # get mobile streams
            if live:
                rsid = generate_rsid()
                rpin = generate_rpin()
                mediaId = channelID
                apiUrl = WS_URL.format(randint(0, 0xffffff), mediaId, 'channel', 'lp-live') + '/1/ustream'
                #('password', '')
                url = apiUrl + '?' + urllib.urlencode([('media', mediaId), ('referrer', referer), ('appVersion', 2), ('application', 'channel'), ('rsid', rsid), ('appId', 11), ('rpin', rpin), ('type', 'viewer') ])
                sts, data = self.cm.getPage(url, params)
                if not sts: return []
                data = json_loads(data)
                printDBG(data)
                host = data[0]['args'][0]['host']
                connectionId = data[0]['args'][0]['connectionId']
                if len(host):
                    apiUrl = "http://" + host + '/1/ustream'
                url = apiUrl + '?connectionId=' + str(connectionId)
                
                for i in range(5):
                    sts, data = self.cm.getPage(url, params)
                    if not sts: continue
                    if 'm3u8' in data:
                        break
                    GetIPTVSleep().Sleep(1)
                data = json_loads(data)
                playlist_url = data[0]['args'][0]['stream'][0]['url']
                try:
                    retTab = getDirectM3U8Playlist(playlist_url)
                    if len(retTab):
                        for item in retTab:
                            pyCmd = GetPyScriptCmd('ustreamtv') + ' "%s" "%s" "%s" "%s" ' % (item['width'], mediaId, referer, HTTP_HEADER['User-Agent'])
                            name = ('ustream.tv %s' % item.get('heigth', 0))
                            url = urlparser.decorateUrl("ext://url/" + item['url'], {'iptv_proto':'em3u8', 'iptv_livestream': True, 'iptv_refresh_cmd':pyCmd})
                            linksTab.append({'name':name, 'url':url})
                        break
                except Exception:
                    printExc()
                return linksTab
            else:
                sts, data = self.cm.getPage(videoUrl)
                if not sts: return
                data = self.cm.ph.getDataBeetwenMarkers(data, '"media_urls":{', '}', False)[1]
                data = json_loads('{%s}' % data)
                printDBG("+++")
                printDBG(data)
                if self.cm.isValidUrl(data['flv']) and '/{0}?'.format(channelID) in data['flv']:
                    return urllib.unquote(data['flv'].replace('&amp;', '&'))
                return False
                
            
            baseWgetCmd = DMHelper.getBaseWgetCmd({})
            cmd = DMHelper.GET_F4M_PATH() + (" '%s'" % baseWgetCmd) + (' "%s"' % videoUrl) + ' 2>&1 > /dev/null'
            
            printDBG("parserUSTREAMTV cmd[%s" % cmd)
            data = iptv_execute()( cmd )
            printDBG(data)
            if not data['sts'] or 0 != data['code']:
                break
            try:
                data = json_loads(data['data'])
                for item in data['stream_info_list']:
                    if not live and item['chunk_name'].startswith('http'):
                        url = urlparser.decorateUrl(item['chunk_name'])
                        linksTab.append({'name':'ustream.tv recorded', 'url': url})
                    else:
                        name     = 'ustream.tv ' + item['stream_name']
                        chankUrl = (item['prov_url'] + item['chunk_name'])
                        url      = urlparser.decorateUrl(videoUrl, {'iptv_livestream': True, 'iptv_proto':'f4m', 'iptv_chank_url':chankUrl})
                        linksTab.append({'name':name, 'url':url})
            except Exception:
                printExc()
            break
        return linksTab
        
    def parserALIEZME(self, baseUrl):
        printDBG("parserALIEZME baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)

        if baseUrl.split('?')[0].endswith('.js'):
            sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
            if not sts: return []
            tr = 0
            while tr < 3:
                tr += 1
                videoUrl = self.cm.ph.getSearchGroups(data, '"(http://[^/]+?/player?[^"]+?)"')[0]
                if "" != videoUrl: break
                GetIPTVSleep().Sleep(1)
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return []
        urlsTab = []
        videoUrl = self.cm.ph.getSearchGroups(data, """['"]*(http[^'^"]+?\.m3u8[^'^"]*?)['"]""")[0]
        if self.cm.isValidUrl(videoUrl):
            videoUrl = strwithmeta(videoUrl, {'Referer':baseUrl})
            urlsTab.extend(getDirectM3U8Playlist(videoUrl))
        #videoUrl = urllib.unquote(self.cm.ph.getSearchGroups(data, """['"]*(rtmp[^'^"]+?\.m3u8[^'^"]*?)['"]""")[0])
        #if videoUrl.startswith('rtmp://'):
            
        return urlsTab
        
    def parserPRIVATESTREAM(self, baseUrl):
        printDBG("parserPRIVATESTREAM baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(baseUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']

        if videoUrl.split('?')[0].endswith('.js'):
            sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
            if not sts: return False
            printDBG(data)
            tr = 0
            while tr < 3:
                tr += 1
                videoUrl = self.cm.ph.getSearchGroups(data, '"(http://privatestream.tv/player?[^"]+?)"')[0]
                if "" != videoUrl: break
                GetIPTVSleep().Sleep(1)
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        printDBG(data)
        if sts:
            try:
                a = int(self.cm.ph.getSearchGroups(data, 'var a = ([0-9]+?);')[0])
                b = int(self.cm.ph.getSearchGroups(data, 'var b = ([0-9]+?);')[0])
                c = int(self.cm.ph.getSearchGroups(data, 'var c = ([0-9]+?);')[0])
                d = int(self.cm.ph.getSearchGroups(data, 'var d = ([0-9]+?);')[0])
                f = int(self.cm.ph.getSearchGroups(data, 'var f = ([0-9]+?);')[0])
                v_part = self.cm.ph.getSearchGroups(data, "var v_part = '([^']+?)'")[0]
                v_part_m = self.cm.ph.getSearchGroups(data, "var v_part_m = '([^']+?)'")[0]
                addr_part  = self.cm.ph.getSearchGroups(data, "var addr_part = '([^']+?)'")[0]
                videoTabs = []
                url = ('://%d.%d.%d.%d' % (a/f, b/f, c/f, d/f) )
                if url == '://0.0.0.0':
                    url = '://' + addr_part
                
                if v_part != '':
                    rtmpUrl = 'rtmp' + url + v_part
                    rtmpUrl += ' swfUrl=%sclappr/RTMP.swf pageUrl=%s live=1' % (self.cm.getBaseUrl(videoUrl), baseUrl) #token=‪%s '#atd%#$ZH'
                    videoTabs.append({'name':'rtmp', 'url':rtmpUrl})
                if v_part_m != '':
                    hlsUrl = 'http' + url + v_part_m
                    hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
                    videoTabs.extend( getDirectM3U8Playlist(hlsUrl, checkContent=True) )
                return videoTabs
            except Exception:
                printExc()
        return False
        
    def parserTVOPECOM(self, baseUrl):
        printDBG("parserTVOPECOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(baseUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        if not sts: return False
        
        printDBG(data)
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'clip:', '}', False)[1]
        live = self.cm.ph.getSearchGroups(tmp, '''live:\s*([^,]+?),''')[0]
        
        playpath = self.cm.ph.getSearchGroups(tmp, '''url:\s?['"]([^'^"]+?)['"]''')[0]
        if playpath == '': playpath = self.cm.ph.getSearchGroups(data, '''\(\s*['"]file['"]\s*\,\s*['"]([^'^"]+?)['"]''')[0]
        
        swfUrl = self.cm.ph.getSearchGroups(data, '''src:\s?['"](http[^'^"]+?\.swf[^'^"]*?)['"]''')[0]
        if swfUrl == '': swfUrl = self.cm.ph.getSearchGroups(data, '''['"](http[^'^"]+?\.swf[^'^"]*?)['"]''')[0]
        
        rtmpUrl = self.cm.ph.getSearchGroups(data, '''['"](rtmp[^'^"]+?)['"]''')[0]
        
        return rtmpUrl + ' playpath=' + playpath + ' swfUrl=' + swfUrl +  ' pageUrl=' + baseUrl + ' live=1'
        
    def parserVIVOSX(self, baseUrl):
        printDBG("parserVIVOSX baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}

        urlTab = []

        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: 
            return urlTab
        
        #printDBG("----------------------")
        #printDBG(data)
        #printDBG("----------------------")
        
        
        tmp = re.findall("InitializeStream\s?\((.*?)\)", data, re.S)
        
        #printDBG("*********")
        #printDBG(str(tmp))
        #printDBG("*********")
        
        if not tmp:
            return []
        
        j = demjson_loads(tmp[0])
        
        src = j.get('source','')
        if src:
            jsCode = '''function Normalize(a, b) { return ++b ? String.fromCharCode((a = a.charCodeAt() + 47, a > 126 ? a - 94 : a)) : decodeURIComponent(a).replace(/[^ ]/g, this.Normalize) } ; s = Normalize('%s'); console.log(s);'''
            jsCode = jsCode % src
            ret = js_execute(jsCode)
            
            if ret['sts'] and 0 == ret['code']:
                url = ret['data'].replace('\n','')
                
                printDBG("Found url %s" % url)
        
                if self.cm.isValidUrl(url):
                    u = urlparser.decorateUrl(url, {'Referer': baseUrl})
                    label = j.get('quality','link')
                    params = {'name': label , 'url': u}
                    printDBG(str(params))
                    urlTab.append(params)
        
        return urlTab
        
    def parserZSTREAMTO(self, baseUrl):
        printDBG("parserZSTREAMTO baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        return self._findLinks(data, 'zstream')
        
    def parserTHEVIDEOBEETO(self, baseUrl):
        printDBG("parserTHEVIDEOBEETO baseUrl[%r]" % baseUrl)
        
        if 'embed-' not in baseUrl: url = 'https://thevideobee.to/embed-%s.html' % baseUrl.split('/')[-1].replace('.html', '')
        else: url = baseUrl
        
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, 'type="video[^>]*?src="([^"]+?)"')[0]
        if not self.cm.isValidUrl(videoUrl): videoUrl = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"[^>]*?type="video')[0]
        if self.cm.isValidUrl(videoUrl): 
            return videoUrl
        return False
        
    def parserKINGFILESNET(self, baseUrl):
        printDBG("parserKINGFILESNET baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        COOKIE_FILE = GetCookieDir('kingfilesnet.cookie')
        rm(COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</form>', caseSensitive=False)
        if not sts: return False
        
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        post_data.pop('method_premium', None)
        params['header']['Referer'] = baseUrl
        
        sts, data = self.cm.getPage(baseUrl, params, post_data)
        if not sts: return False
        
        sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>')
        if sts:
            tmp = unpackJSPlayerParams(tmp, KINGFILESNET_decryptPlayerParams)
            printDBG(tmp)
            videoUrl = self.cm.ph.getSearchGroups(tmp, 'type="video/divx"[^>]*?src="([^"]+?)"')[0]
            if self.cm.isValidUrl(videoUrl): return videoUrl
            try:
                videoLinks = self._findLinks(tmp, 'kingfiles.net', m1='config:', m2=';')
                printDBG(videoLinks)
                if len(videoLinks): return videoLinks
            except Exception:
                printExc()
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</form>', caseSensitive=False)
        if not sts: return False
        
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        post_data.pop('method_premium', None)
        
        try:
            sleep_time = self.cm.ph.getSearchGroups(data, '>([0-9]+?)</span> seconds<')[0]
            if '' != sleep_time: GetIPTVSleep().Sleep(int(sleep_time))
        except Exception:
            printExc()
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '</tr>', '</table>', caseSensitive=False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<span style', '</span>')
        
        def _cmpLinksBest(item1, item2):
            val1 = int(self.cm.ph.getSearchGroups(item1, '''left\:([0-9]+?)px''')[0])
            val2 = int(self.cm.ph.getSearchGroups(item2, '''left\:([0-9]+?)px''')[0])
            printDBG("%s %s" % (val1, val2))
            if val1 < val2:   ret = -1
            elif val1 > val2: ret = 1
            else:             ret = 0
            return ret
        
        data.sort(_cmpLinksBest)
        data = clean_html(''.join(data)).strip()
        if data != '': post_data['code'] = data
        
        sts, data = self.cm.getPage(baseUrl, params, post_data)
        if not sts: return False
        
        # get JS player script code from confirmation page
        sts, tmp = CParsingHelper.getDataBeetwenMarkers(data, ">eval(", '</script>', False)
        if sts:
            try:
                tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
                data += tmp
            except Exception: printExc()
        
        videoUrl = self.cm.ph.getSearchGroups(data, 'type="video[^>]*?src="([^"]+?)"')[0]
        if videoUrl.startswith('http'):
            return videoUrl
        return False
        
    def parser1FICHIERCOM(self, baseUrl):
        printDBG("parser1FICHIERCOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER = { 'User-Agent': 'Mozilla/%s%s' % (pageParser.FICHIER_DOWNLOAD_NUM, pageParser.FICHIER_DOWNLOAD_NUM), ## 'Wget/1.%s.%s (linux-gnu)'
                        'Accept': '*/*',
                        'Accept-Language':'pl,en-US;q=0.7,en;q=0.3',
                        'Accept-Encoding':'gzip, deflate',
                      }
        pageParser.FICHIER_DOWNLOAD_NUM += 1
        COOKIE_FILE = GetCookieDir('1fichiercom.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True}
        
        rm(COOKIE_FILE)
        login    = config.plugins.iptvplayer.fichiercom_login.value
        password = config.plugins.iptvplayer.fichiercom_password.value
        logedin = False
        if login != '' and password != '':
            url = 'https://1fichier.com/login.pl'
            post_data = {'mail':login, 'pass':password, 'lt':'on', 'purge':'on', 'valider':'Send'}
            params['header']['Referer'] = url
            sts, data = self.cm.getPage(url, params, post_data)
            printDBG(data)
            if sts:
                if 'My files' in data:
                    logedin = True
                else:
                    error = clean_html(self.cm.ph.getDataBeetwenMarkers(data, '<div class="bloc2"', '</div>')[1])
                    sessionEx = MainSessionWrapper() 
                    sessionEx.waitForFinishOpen(MessageBox, _('Login on {0} failed.').format('https://1fichier.com/') + '\n' + error, type = MessageBox.TYPE_INFO, timeout = 5)
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        error = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'bloc'), ('</div', '>'), False)[1])
        if error != '': SetIPTVPlayerLastHostError(error)
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'post'), ('</form', '>'), caseSensitive=False)[1]
        printDBG("++++")
        printDBG(data)
        action = self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>', caseSensitive=False)
        all_post_data = {}
        for item in tmp:
            name = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            all_post_data[name] = value
        
        if 'use_credits' in data:
            all_post_data['use_credits'] = 'on'
            logedin = True
        else:
            logedin = False
        
        error = clean_html(self.cm.ph.getDataBeetwenMarkers(data, '<span style="color:red">', '</div>')[1])
        if error != '' and not logedin:
            timeout = self.cm.ph.getSearchGroups(error, '''wait\s+([0-9]+)\s+([a-zA-Z]{3})''', 2, ignoreCase=True)
            printDBG(timeout)
            if timeout[1].lower() == 'min':
                timeout = int(timeout[0]) * 60 
            elif timeout[1].lower() == 'sec':
                timeout = int(timeout[0])
            else:
                timeout = 0
            printDBG(timeout)
            if timeout > 0:
                sessionEx = MainSessionWrapper() 
                sessionEx.waitForFinishOpen(MessageBox, error, type = MessageBox.TYPE_INFO, timeout = timeout )
            else:
                SetIPTVPlayerLastHostError(error)
        else:
            SetIPTVPlayerLastHostError(error)
        
        
        post_data = {'dl_no_ssl':'on', 'adzone' :all_post_data['adzone']}
        action = urljoin(baseUrl, action)
        
        if logedin:
            params['max_data_size'] = 0
            params['header']['Referer'] = baseUrl
            sts = self.cm.getPage(action, params, post_data)[0]
            if not sts: return False
            if 'text' not in self.cm.meta.get('content-type', ''):
                videoUrl = self.cm.meta['url']
            else:
                SetIPTVPlayerLastHostError(error)
                videoUrl = ''
        else:
            params['header']['Referer'] = baseUrl
            sts, data = self.cm.getPage(action, params, post_data)
            if not sts: return False
            
            printDBG(data)
            videoUrl = self.cm.ph.getSearchGroups(data, '''<a[^>]+?href=['"](https?://[^'^"]+?)['"][^>]+?ok btn-general''')[0]
        
        error = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'bloc'), ('</div', '>'), False)[1])
        if error != '': SetIPTVPlayerLastHostError(error)
        
        printDBG('>>> videoUrl[%s]' % videoUrl)
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        
        return False
    
    def parserUPLOAD(self, baseUrl):
        printDBG("parserUPLOAD baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        baseUrl = self.cm.meta['url']
        HTTP_HEADER['Referer'] = baseUrl
        mainUrl = baseUrl
        
        timestamp = time.time()
        
        for marker in ['File Not Found', 'The file you were looking for could not be found, sorry for any inconvenience.']:
            if marker in data: SetIPTVPlayerLastHostError(_(marker))
        
        sts, tmp = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'post'), ('</form', '>'), caseSensitive=False)
        if not sts: return False
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<input', '>', False, caseSensitive=False)
        post_data = {}
        for item in tmp:
            name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            if name != '' and 'premium' not in name:
                if 'adblock' in name and value == '':
                    value = '0'
                post_data[name] = value
        
        # sleep
        try:
            sleep_time = self.cm.ph.getDataBeetwenNodes(data, ('<span', '>', 'countdown'), ('</span', '>'), False, caseSensitive=False)[1]
            sleep_time = int(self.cm.ph.getSearchGroups(sleep_time, '>\s*([0-9]+?)\s*<')[0])
        except Exception:
            sleep_time = 0
         
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER}, post_data)
        if not sts: return False
        baseUrl = self.cm.meta['url']
        HTTP_HEADER['Referer'] = baseUrl
        
        sitekey = ''
        tmp = re.compile('(<[^>]+?data\-sitekey[^>]*?>)').findall(data)
        for item in tmp:
            if 'hidden' not in item:
                sitekey = self.cm.ph.getSearchGroups(item, 'data\-sitekey="([^"]+?)"')[0]
                break

        if sitekey == '': sitekey = self.cm.ph.getSearchGroups(data, 'data\-sitekey="([^"]+?)"')[0]
        if sitekey != '': 
            token, errorMsgTab = self.processCaptcha(sitekey, mainUrl)
            if token == '':
                SetIPTVPlayerLastHostError('\n'.join(errorMsgTab)) 
                return False
        else:
            token = ''
        
        sts, data = self.cm.ph.getDataBeetwenNodes(data, ('<form', '>', 'post'), ('</form', '>'), caseSensitive=False)
        if not sts: return False
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<input', '>', False, caseSensitive=False)
        post_data = {}
        for item in data:
            name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            if name != '' and 'premium' not in name:
                if 'adblock' in name and value == '':
                    value = '0'
                post_data[name] = value
        
        if '' != token:
            post_data['g-recaptcha-response'] = token
        
        sleep_time -= time.time() - timestamp
        if  sleep_time > 0:
            GetIPTVSleep().Sleep(int(math.ceil(sleep_time)))
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER}, post_data)
        if not sts: return False
        baseUrl = self.cm.meta['url']
        HTTP_HEADER['Referer'] = baseUrl
        
        errorMessage = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'alert-danger'), ('</div', '>'), False)[1])
        SetIPTVPlayerLastHostError(errorMessage)
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        #printDBG(data)
        
        videoUrl = self.cm.ph.rgetDataBeetwenMarkers2(data, '>download<', '<a ', caseSensitive=False)[1]
        videoUrl = self.cm.ph.getSearchGroups(videoUrl, '''href=['"]([^"^']+?)['"]''')[0]
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        
        sts, videoUrl = self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', 'download-btn'), ('</a', '>'), caseSensitive=False)
        if not sts:
            sts, videoUrl = self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', 'downloadbtn'), ('</a', '>'), caseSensitive=False)
        if sts:
            return self.cm.ph.getSearchGroups(videoUrl, '''href=['"]([^"^']+?)['"]''')[0]
        else:
            printDBG(data)
            printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
            looksGood = ''
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
            for item in data:
                url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0]
                title = clean_html(item)
                printDBG(url)
                if title == url and url != '':
                    videoUrl = url
                    break
                if '/d/' in url:
                    looksGood = videoUrl
            if videoUrl == '': videoUrl = looksGood
        
        return videoUrl
        
    def parserFILECLOUDIO(self, baseUrl):
        printDBG("parserFILECLOUDIO baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        if referer != '': HTTP_HEADER['Referer'] = referer
        paramsUrl = {'header':HTTP_HEADER, 'with_metadata':True}
        
        sts, data = self.cm.getPage(baseUrl, paramsUrl)
        if not sts: return False
        cUrl = data.meta['url']

        sitekey = self.cm.ph.getSearchGroups(data, '''['"]?sitekey['"]?\s*?:\s*?['"]([^"^']+?)['"]''')[0]
        if sitekey != '': 
            obj = UnCaptchaReCaptcha(lang=GetDefaultLang())
            obj.HTTP_HEADER.update({'Referer':cUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
            token = obj.processCaptcha(sitekey)
            if token == '': return False
        else: token = ''
        
        requestUrl = self.cm.ph.getSearchGroups(data, '''requestUrl\s*?=\s*?['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
        requestUrl = self.cm.getFullUrl(requestUrl, self.cm.getBaseUrl(cUrl))
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '$.ajax(', ')', caseSensitive=False)[1]
        data = self.cm.ph.getSearchGroups(data, '''data['"]?:\s*?(\{[^\}]+?\})''', ignoreCase=True)[0]
        data = data.replace('response', '"%s"' % token).replace("'", '"')
        post_data = json_loads(data)
        
        paramsUrl['header'].update({'Referer':cUrl, 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'})
        sts, data = self.cm.getPage(requestUrl, paramsUrl, post_data)
        if not sts: return False
        
        data = json_loads(data)
        if self.cm.isValidUrl(data['downloadUrl']):
            return strwithmeta(data['downloadUrl'], {'Referer':cUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
        
        return False
        
    def parserMEGADRIVECO(self, baseUrl):
        printDBG("parserMEGADRIVECO baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        if referer != '': HTTP_HEADER['Referer'] = referer
        paramsUrl = {'header':HTTP_HEADER, 'with_metadata':True}
        
        sts, data = self.cm.getPage(baseUrl, paramsUrl)
        if not sts: return False
        cUrl = data.meta['url']
        
        streamUrl = self.cm.ph.getSearchGroups(data, '''mp4['"]?\s*?:\s*?['"](https?://[^'^"]+?)['"]''')[0]
        if self.cm.isValidUrl(streamUrl):
            return strwithmeta(streamUrl, {'Referer':cUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
        
        return False
        
    def parserUPFILEMOBI(self, baseUrl):
        printDBG("parserUPFILEMOBI baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        if referer != '': HTTP_HEADER['Referer'] = referer
        paramsUrl = {'header':HTTP_HEADER, 'with_metadata':True}
        
        sts, data = self.cm.getPage(baseUrl, paramsUrl)
        if not sts: return False
        cUrl = data.meta['url']
        paramsUrl['header']['Referer'] = cUrl
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        playUrl = ''
        downloadUrl = ''
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<a', '>'), ('</a', '>'))
        for item in data:
            if 'download_button' not in item: continue
            url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0]
            if not self.cm.isValidUrl(url): url = self.cm.getFullUrl(url, self.cm.getBaseUrl(cUrl))
            if 'page=file' in url or 'page=download' in url: downloadUrl = url
            else: playUrl = url
        
        urls = []
        if downloadUrl != '':
            sts, data = self.cm.getPage(downloadUrl, paramsUrl)
            if sts:
                url = data.meta['url']
                downloadUrl = self.cm.ph.getSearchGroups(data, '''href=['"]([^"^']*?page=download[^"^']*?)['"]''')[0]
                if downloadUrl == '': downloadUrl = self.cm.ph.getSearchGroups(data, '''href=['"]([^"^']*?page=dl[^"^']*?)['"]''')[0]
                if downloadUrl != '':
                    if not self.cm.isValidUrl(downloadUrl): downloadUrl = self.cm.getFullUrl(downloadUrl, self.cm.getBaseUrl(url))
                    urls.append({'name':'Download URL', 'url':strwithmeta(downloadUrl, {'Referer':url, 'User-Agent':HTTP_HEADER['User-Agent']})})
        
        if playUrl != '':
            sts, data = self.cm.getPage(playUrl, paramsUrl)
            if sts:
                playUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?video/mp4''', ignoreCase=True)[0]
                if playUrl != '':
                    printDBG('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> %s' % playUrl)
                    if not self.cm.isValidUrl(playUrl): playUrl = self.cm.getFullUrl(playUrl, self.cm.getBaseUrl(data.meta['url']))
                    urls.append({'name':'Watch URL', 'url':strwithmeta(playUrl, {'Referer':data.meta['url'], 'User-Agent':HTTP_HEADER['User-Agent']})})
        
        return urls
        
    def parserUCASTERCOM(self, baseUrl):
        printDBG("parserUCASTERCOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(baseUrl)
        if 'Referer' in videoUrl.meta: HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        
        # get IP
        sts, data = self.cm.getPage('http://www.pubucaster.com:1935/loadbalancer', {'header': HTTP_HEADER})
        if not sts: return False
        ip = data.split('=')[-1].strip()
        
        streamsTab = []
        # m3u8 link
        url = videoUrl.replace('/embedplayer/', '/membedplayer/')
        sts, data = self.cm.getPage(url, {'header': HTTP_HEADER})
        if sts:
            streamUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]+?\.m3u8[^'^"]+?)['"]''')[0]
            if streamUrl != '':
                streamUrl = 'http://' + ip + streamUrl
                streamsTab.extend(getDirectM3U8Playlist(streamUrl))
        
        # rtmp does not work at now
        return streamsTab
        url = videoUrl.replace('/membedplayer/', '/embedplayer/')
        sts, data = self.cm.getPage(url, {'header': HTTP_HEADER})
        if not sts: return streamsTab
        try: 
            tmp = self.cm.ph.getSearchGroups(data, '''['"]FlashVars['"]\s*,\s*['"]([^'^"]+?)['"]''')[0]
            tmp = parse_qs(tmp)
            playpath = '{0}?id={1}&pk={2}'.format(tmp['s'][0], tmp['id'][0], tmp['pk'][0])
            rtmpUrl  = 'rtmp://{0}/live'.format(ip)
            swfUrl   = 'http://www.embeducaster.com/static/scripts/fplayer.swf'
            streamUrl = rtmpUrl + ' playpath=' + playpath +  ' tcUrl=' + rtmpUrl + ' swfUrl=' + swfUrl + ' pageUrl=' + baseUrl + ' app=live live=1 conn=S:OK'
            streamsTab.append({'name':'[rtmp] ucaster', 'url':streamUrl})
        except:
            printExc()
        return streamsTab
        
    def parserALLCASTIS(self, baseUrl):
        printDBG("parserALLCASTIS baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(baseUrl)
        if 'Referer' in videoUrl.meta: HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        if not sts: return False
        
        url = self.cm.ph.getSearchGroups(data, 'curl[^"]*?=[^"]*?"([^"]+?)"')[0]
        if '' == url: url = self.cm.ph.getSearchGroups(data, 'murl[^"]*?=[^"]*?"([^"]+?)"')[0]
        streamUrl = base64.b64decode(url)
        if streamUrl.startswith('//'): streamUrl = 'http:' + streamUrl
        streamUrl = strwithmeta(streamUrl, {'Referer':videoUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
        
        streamsTab = []
        # m3u8 link
        if streamUrl.split('?', 1)[0].endswith('.m3u8'):
            streamsTab.extend(getDirectM3U8Playlist(streamUrl, checkContent=False))
        return streamsTab
        
    def parserDOTSTREAMTV(self, baseUrl):
        printDBG("parserDOTSTREAMTV linkUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(baseUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        #printDBG(data)
        if sts:
            try:
                a = int(self.cm.ph.getSearchGroups(data, 'var a = ([0-9]+?);')[0])
                b = int(self.cm.ph.getSearchGroups(data, 'var b = ([0-9]+?);')[0])
                c = int(self.cm.ph.getSearchGroups(data, 'var c = ([0-9]+?);')[0])
                d = int(self.cm.ph.getSearchGroups(data, 'var d = ([0-9]+?);')[0])
                f = int(self.cm.ph.getSearchGroups(data, 'var f = ([0-9]+?);')[0])
                v_part = self.cm.ph.getSearchGroups(data, "var v_part = '([^']+?)'")[0]
                v_part_m = self.cm.ph.getSearchGroups(data, "var v_part_m = '([^']+?)'")[0]
                addr_part  = self.cm.ph.getSearchGroups(data, "var addr_part = '([^']+?)'")[0]
                videoTabs = []
                url = ('://%d.%d.%d.%d' % (a/f, b/f, c/f, d/f) )
                if url == '://0.0.0.0':
                    url = '://' + addr_part
                
                if v_part != '':
                    rtmpUrl = 'rtmp' + url + v_part
                    rtmpUrl += ' swfUrl=%sclappr/RTMP.swf pageUrl=%s live=1' % (self.cm.getBaseUrl(videoUrl), videoUrl) #token=‪%s '#atd%#$ZH'
                    videoTabs.append({'name':'rtmp', 'url':rtmpUrl})
                if v_part_m != '':
                    hlsUrl = 'http' + url + v_part_m
                    hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
                    videoTabs.extend( getDirectM3U8Playlist(hlsUrl, checkContent=True) )
                return videoTabs
            except Exception:
                printExc()
        return False
        
    def parserSRKCASTCOM(self, baseUrl):
        printDBG("parserSRKCASTCOM linkUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(baseUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return False
        
        streamUrl = self.cm.ph.getSearchGroups(data, '''['"](https?://[^'^"]+?\.m3u8[^'^"]*?)['"]''')[0]
        streamUrl = strwithmeta(streamUrl, {'Referer':videoUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
        
        streamsTab = []
        streamsTab.extend(getDirectM3U8Playlist(streamUrl, checkContent=False))
        return streamsTab
    
    def parserABCASTBIZ(self, linkUrl):
        printDBG("parserABCASTBIZ linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        if 'Referer' in videoUrl.meta: HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        
        sts, data = self.cm.getPage(linkUrl, {'header': HTTP_HEADER})
        if not sts: return False
        
        streamUrl = self.cm.ph.getSearchGroups(data, '''['"](https?://[^'^"]+?\.m3u8[^'^"]*?)['"]''')[0]
        streamUrl = strwithmeta(streamUrl, {'Referer':videoUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
        
        streamsTab = []
        streamsTab.extend(getDirectM3U8Playlist(streamUrl, checkContent=False))
        
        swfUrl = "http://abcast.net/player.swf"
        file = self.cm.ph.getSearchGroups(data, 'file=([^&]+?)&')[0]
        if file.endswith(".flv"): file = file[0:-4]
        streamer = self.cm.ph.getSearchGroups(data, 'streamer=([^&]+?)&')[0]
        if '' != file:
            url    = "rtmpe://live.abcast.biz/redirect"
            url = streamer
            url += ' playpath=%s swfUrl=%s pageUrl=%s' % (file, swfUrl, linkUrl)
            streamsTab.append({'name':'rtmp', 'url':url})
            return streamsTab
        data = self.cm.ph.getDataBeetwenMarkers(data, 'setup({', '});', True)[1]
        url    = self.cm.ph.getSearchGroups(data, 'streamer[^"]+?"(rtmp[^"]+?)"')[0]
        file   = self.cm.ph.getSearchGroups(data, 'file[^"]+?"([^"]+?)"')[0]
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s ' % (file, swfUrl, linkUrl)
            streamsTab.append({'name':'rtmp', 'url':url})
        return streamsTab
        
    def parserOPENLIVEORG(self, linkUrl):
        printDBG("parserOPENLIVEORG linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        if 'Referer' in videoUrl.meta:
            HTTP_HEADER['Referer'] = videoUrl.meta['Referer']
        sts, data = self.cm.getPage(linkUrl, {'header': HTTP_HEADER})
        if not sts: return False
            
        file     = self.cm.ph.getSearchGroups(data, 'file=([^&]+?)&')[0]
        if file.endswith(".flv"): file = file[0:-4]
        streamer = self.cm.ph.getSearchGroups(data, 'streamer=([^&]+?)&')[0]
        swfUrl = "http://openlive.org/player.swf"
        if '' != file:
            url = streamer
            url += ' playpath=%s swfUrl=%s pageUrl=%s' % (file, swfUrl, linkUrl)
            printDBG(url)
            return url
        data = self.cm.ph.getDataBeetwenMarkers(data, 'setup({', '});', True)[1]
        url    = self.cm.ph.getSearchGroups(data, 'streamer[^"]+?"(rtmp[^"]+?)"')[0]
        file   = self.cm.ph.getSearchGroups(data, 'file[^"]+?"([^"]+?)"')[0]
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s ' % (file, swfUrl, linkUrl)
            return url
        return False
        
    def parserGOODCASTCO(self, linkUrl):
        printDBG("parserGOODCASTCO linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        HTTP_HEADER['Referer'] = videoUrl.meta.get('Referer', videoUrl)
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        if not sts: return False
        url  = self.cm.ph.getSearchGroups(data, 'streamer=([^&]+?)&')[0]
        file = self.cm.ph.getSearchGroups(data, 'file=([0-9]+?)&')[0]
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=http://abcast.biz/ab.swf pageUrl=%s token=Fo5_n0w?U.rA6l3-70w47ch' % (file, linkUrl)
            return url
        return False
        
    def parserLIVEALLTV(self, linkUrl):
        printDBG("parserLIVEALLTV linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        videoUrl = strwithmeta(linkUrl)
        HTTP_HEADER['Referer'] = videoUrl.meta.get('Referer', videoUrl)
        sts, data = self.cm.getPage(videoUrl, {'header': HTTP_HEADER})
        if not sts: return False
        
        a = int(self.cm.ph.getSearchGroups(data, 'var a = ([0-9]+?);')[0])
        b = int(self.cm.ph.getSearchGroups(data, 'var b = ([0-9]+?);')[0])
        c = int(self.cm.ph.getSearchGroups(data, 'var c = ([0-9]+?);')[0])
        d = int(self.cm.ph.getSearchGroups(data, 'var d = ([0-9]+?);')[0])
        f = int(self.cm.ph.getSearchGroups(data, 'var f = ([0-9]+?);')[0])
        v_part = self.cm.ph.getSearchGroups(data, "var v_part = '([^']+?)'")[0]
        
        url = ('rtmp://%d.%d.%d.%d' % (a/f, b/f, c/f, d/f) ) + v_part
        url += ' swfUrl=http://wds.liveall.tv/jwplayer.flash.swf pageUrl=%s' % (linkUrl)
        return url
        
    def parserP2PCASTTV(self, linkUrl):
        printDBG("parserP2PCASTTV linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {}
        videoUrl = strwithmeta(linkUrl)
        HTTP_HEADER['Referer'] = videoUrl.meta.get('Referer', videoUrl)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0"
        COOKIE_FILE = GetCookieDir('p2pcasttv.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(videoUrl, params)
        if not sts: return False
        url = self.cm.ph.getSearchGroups(data, 'curl[^"]*?=[^"]*?"([^"]+?)"')[0]
        if '' == url: url = self.cm.ph.getSearchGroups(data, 'murl[^"]*?=[^"]*?"([^"]+?)"')[0]
        url = base64.b64decode(url)
        
        if url.endswith('token='):
            params['header']['Referer'] = linkUrl
            params['header']['X-Requested-With'] = 'XMLHttpRequest'
            params['load_cookie'] = True
            sts, data = self.cm.getPage('http://p2pcast.tech/getTok.php', params)
            if not sts: return False
            data = json_loads(data)
            url += data['token']
        return urlparser.decorateUrl(url, {'Referer':'http://cdn.webplayer.pw/jwplayer.flash.swf', "User-Agent": HTTP_HEADER['User-Agent']})
        
    def parserNOWLIVEPW(self, linkUrl):
        printDBG("parserNOWLIVEPW linkUrl[%s]" % linkUrl)
        HTTP_HEADER = {}
        videoUrl = strwithmeta(linkUrl)
        HTTP_HEADER['Referer'] = videoUrl.meta.get('Referer', videoUrl)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0"
        COOKIE_FILE = GetCookieDir('novelivepw.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(videoUrl, params)
        if not sts: return False
        url = self.cm.ph.getSearchGroups(data, 'curl[^"]*?=[^"]*?"([^"]+?)"')[0]
        if '' == url: url = self.cm.ph.getSearchGroups(data, 'murl[^"]*?=[^"]*?"([^"]+?)"')[0]
        url = base64.b64decode(url)
        
        if url.endswith('token='):
            params['header']['Referer'] = linkUrl
            params['header']['X-Requested-With'] = 'XMLHttpRequest'
            params['load_cookie'] = True
            sts, data = self.cm.getPage(urlparser.getDomain(linkUrl, False) + 'getToken.php', params)
            if not sts: return False
            data = json_loads(data)
            url += data['token']
        return urlparser.decorateUrl(url, {'Referer':linkUrl, "User-Agent": HTTP_HEADER['User-Agent']})
    
    def parserGOOGLE(self, baseUrl):
        printDBG("parserGOOGLE baseUrl[%s]" % baseUrl)
        
        videoTab = []
        _VALID_URL = r'https?://(?:(?:docs|drive)\.google\.com/(?:uc\?.*?id=|file/d/)|video\.google\.com/get_player\?.*?docid=)(?P<id>[a-zA-Z0-9_-]{28,})'
        mobj = re.match(_VALID_URL, baseUrl)
        try:
            video_id = mobj.group('id')
            linkUrl = 'http://docs.google.com/file/d/' + video_id 
        except Exception:
            linkUrl = baseUrl
            
        _FORMATS_EXT = {
            '5': 'flv', '6': 'flv',
            '13': '3gp', '17': '3gp',
            '18': 'mp4', '22': 'mp4',
            '34': 'flv', '35': 'flv',
            '36': '3gp', '37': 'mp4',
            '38': 'mp4', '43': 'webm',
            '44': 'webm', '45': 'webm',
            '46': 'webm', '59': 'mp4',
        }
        
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = linkUrl
        
        COOKIE_FILE = GetCookieDir('google.cookie')
        defaultParams = {'header': HTTP_HEADER, 'use_cookie': True, 'load_cookie': False, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        
        sts, data = self.cm.getPage(linkUrl, defaultParams)
        if not sts: return False 
        
        cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
        fmtDict = {} 
        fmtList = self.cm.ph.getSearchGroups(data, '"fmt_list"[:,]"([^"]+?)"')[0]
        fmtList = fmtList.split(',')
        for item in fmtList:
            item = self.cm.ph.getSearchGroups(item, '([0-9]+?)/([0-9]+?x[0-9]+?)/', 2)
            if item[0] != '' and item[1] != '':
                fmtDict[item[0]] = item[1]
        data = self.cm.ph.getSearchGroups(data, '"fmt_stream_map"[:,]"([^"]+?)"')[0]
        data = data.split(',')
        for item in data:
            item = item.split('|')
            printDBG(">> type[%s]" % item[0])
            if 'mp4' in _FORMATS_EXT.get(item[0], ''):
                try: quality = int(fmtDict.get(item[0], '').split('x', 1)[-1])
                except Exception: quality = 0
                videoTab.append({'name':'drive.google.com: %s' % fmtDict.get(item[0], '').split('x', 1)[-1] + 'p', 'quality':quality, 'url':strwithmeta(unicode_escape(item[1]), {'Cookie':cookieHeader, 'Referer':'https://youtube.googleapis.com/', 'User-Agent':HTTP_HEADER['User-Agent']})})
        videoTab.sort(key=lambda item: item['quality'], reverse=True)
        return videoTab
        
    def parserPICASAWEB(self, baseUrl):
        printDBG("parserPICASAWEB baseUrl[%s]" % baseUrl)
        videoTab = []
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return videoTab
        data = re.compile('(\{"url"[^}]+?\})').findall(data)
        printDBG(data)
        for item in data:
            try:
                item = json_loads(item)
                if 'video' in item.get('type', ''):
                    videoTab.append({'name':'%sx%s' % (item.get('width', ''), item.get('height', '')), 'url':item['url']})
            except Exception:
                printExc()
        return videoTab
        
    def parserMYVIRU(self, linkUrl):
        printDBG("parserMYVIRU linkUrl[%s]" % linkUrl)
        COOKIE_FILE = GetCookieDir('myviru.cookie')
        params  = {'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        rm(COOKIE_FILE)
        
        if linkUrl.startswith('https://'):
            linkUrl = 'http' + linkUrl[5:]
        videoTab = []
        if '/player/flash/' in linkUrl:
            videoId = linkUrl.split('/')[-1]
            
            sts = self.cm.getPage(linkUrl, {'max_data_size':0})[0]
            if not sts: return videoTab
            preloaderUrl = self.cm.meta['url']
            flashApiUrl = "http://myvi.ru/player/api/video/getFlash/%s?ap=1&referer&sig&url=%s" % (videoId, urllib.quote(preloaderUrl))
            sts, data = self.cm.getPage(flashApiUrl)
            if not sts: return videoTab
            data = data.replace('\\', '')
            data = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
            if not data.startswith("//"): return videoTab
            linkUrl = "http:" + data
        if '/embed/html/' in linkUrl: 
            sts, data = self.cm.getPage(linkUrl, params)
            if not sts: return videoTab
            tmp = self.cm.ph.getSearchGroups(data, """dataUrl[^'^"]*?:[^'^"]*?['"]([^'^"]+?)['"]""")[0]
            if tmp.startswith("//"): linkUrl = "http:" + tmp
            elif tmp.startswith("/"): linkUrl = "http://myvi.ru" + tmp
            elif tmp.startswith("http"): linkUrl = tmp

            if linkUrl.startswith('https://'):
                linkUrl = 'http' + linkUrl[5:]
            if self.cm.isValidUrl(linkUrl):
                sts, data = self.cm.getPage(linkUrl, params)
                if not sts: return videoTab
                try:
                    # get cookie data
                    universalUserID = self.cm.getCookieItem(COOKIE_FILE,'UniversalUserID')
                    tmp = json_loads(data)
                    for item in tmp['sprutoData']['playlist']:
                        url = item['video'][0]['url']
                        if url.startswith('http'):
                            videoTab.append({'name': 'myvi.ru: %s' % item['duration'], 'url':strwithmeta(url, {'Cookie':'UniversalUserID=%s; vp=0.33' % universalUserID})})
                except Exception: 
                    printExc()

            data = self.cm.ph.getSearchGroups(data, '''createPlayer\(\s*['"]([^'^"]+?)['"]''')[0].decode('unicode-escape').encode("utf-8")
            printDBG("+++++++++++++++++++++++++++++++++++++++")
            printDBG(data)
            printDBG("+++++++++++++++++++++++++++++++++++++++")
            data = parse_qs(data)
            videoUrl = data.get('v', [''])[0]
            if self.cm.isValidUrl(videoUrl):
                universalUserID = self.cm.getCookieItem(COOKIE_FILE,'UniversalUserID')
                videoTab.append({'name': 'myvi.ru', 'url':strwithmeta(videoUrl, {'Cookie':'UniversalUserID=%s; vp=0.33' % universalUserID})})
        return videoTab
        
    def parserARCHIVEORG(self, linkUrl):
        printDBG("parserARCHIVEORG linkUrl[%s]" % linkUrl)
        videoTab = []
        sts, data = self.cm.getPage(linkUrl)
        if sts: 
            data = self.cm.ph.getSearchGroups(data, '"sources":\[([^]]+?)]')[0]
            data = '[%s]' % data
            try:
                data = json_loads(data)
                for item in data:
                    if 'mp4' == item['type']:
                        videoTab.append({'name':'archive.org: ' + item['label'], 'url':'https://archive.org' + item['file']})
            except Exception:
                printExc()
        return videoTab

    def parserSAWLIVETV(self, baseUrl):
        printDBG("parserSAWLIVETV linkUrl[%s]" % baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)

        if '/embed/stream/' not in baseUrl:
            sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
            if not sts: return False
            js_params = [{'path':GetJSScriptFile('sawlive1.byte')}]
            js_params.append({'name':'sawlive1', 'code':data})
            ret = js_execute_ext( js_params )
            printDBG(ret['data'])
            embedUrl = self.cm.getFullUrl(ph.search(ret['data'], ph.IFRAME)[1], self.cm.meta['url'])
        else:
            embedUrl = baseUrl

        sts, data = self.cm.getPage(embedUrl, {'header': HTTP_HEADER})
        if not sts: return False
        #printDBG(data)

        remote_js_scripts = re.findall("<script type=\"text/javascript\" src=\"(http://sawlive\.tv/[a-z]{2}\.js)\">", data)
        
        code_remote = ''
        for j in remote_js_scripts:
            printDBG(j)
            sts , data2 = self.cm.getPage(j, {'header': HTTP_HEADER})
            if sts:
                code_remote = code_remote + "\n" + data2
                
        js_params = [{'path':GetJSScriptFile('sawlive2.byte')}]
        interHtmlElements = {}
        tmp = ph.findall(data, ('<span', '>', ph.check(ph.all, ('display', 'none'))), '</span>', flags=ph.START_S)
        for idx in range(1, len(tmp), 2):
            if '<' in tmp[idx] or '>' in tmp[idx]: continue
            elemId = ph.getattr(tmp[idx-1], 'id')
            interHtmlElements[elemId] = tmp[idx].strip()
        
        code_var = 'var interHtmlElements=%s;' % json_dumps(interHtmlElements)
        codes = ph.findall(data, ('<script', '>', ph.check(ph.none, ('src=',))), '</script>', flags=0)
        code = code_remote + '\n' + code_var + '\n' + '\n'.join(codes)

        js_params.append({'code': code})
        ret = js_execute_ext( js_params )
        
        printDBG(ret['data'])
        
        data = json_loads(ret['data'])
        swfUrl = data['0']
        decoded = data['6']
        url    = decoded['streamer']
        file   = decoded['file']
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False

    def parserSHIDURLIVECOM(self, baseUrl):
        printDBG("parserSHIDURLIVECOM linkUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', baseUrl)
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return False
        linkUrl = self.cm.ph.getSearchGroups(data, 'src="(http[^"]+?)"')[0].strip()
        sts, data = self.cm.getPage(linkUrl, {'header': HTTP_HEADER})
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, 'new SWFObject', '</script>', True)[1]
        printDBG(data)
        dataTab = data.split(';')
        data = ''
        for line in dataTab: 
            if not line.strip().startswith('//'): 
                data += line+';'
        swfUrl = self.cm.ph.getSearchGroups(data, "'(http[^']+?swf)'")[0]
        url    = self.cm.ph.getSearchGroups(data, "streamer'[^']+?'(rtmp[^']+?)'")[0]#.replace('rtmp://', 'rtmpe://')
        file   = urllib.unquote( self.cm.ph.getSearchGroups(data, "file'[^']+?'([^']+?)'")[0] )
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, linkUrl)
            printDBG(url)
            return url
        return False
        
    def parserCASTALBATV(self, baseUrl):
        printDBG("parserCASTALBATV baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', baseUrl)
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return False
        def _getParam(name):
            return self.cm.ph.getDataBeetwenMarkers(data, "'%s':" % name, ',', False)[1].strip() + ", '{0}'".format(name)
            #self.cm.ph.getSearchGroups(data, """['"]%s['"][^'^"]+?['"]([^'^"]+?)['"]""" % name)[0] 
        def _getParamVal(value, name):
            return value
        data = self.cm.ph.getDataBeetwenMarkers(data, '<script type="text/javascript">', '</script>', False)[1]
        vars = dict( re.compile('''var ([^=]+?)=[^']*?'([^']+?)['];''').findall(data) )
        printDBG("===================================")
        printDBG(vars)
        printDBG("===================================")
        addCode = ''
        for item in vars:
            addCode += '%s="%s"\n' % (item, vars[item])
            
        funData = re.compile('function ([^\(]*?\([^\)]*?\))[^\{]*?\{([^\{]*?)\}').findall(data)
        pyCode = addCode
        for item in funData:
            funHeader = item[0]
            
            funBody = item[1]
            funIns = funBody.split(';')
            funBody = ''
            for ins in funIns:
                ins = ins.replace('var', ' ').strip()
                funBody += '\t%s\n' % ins
            if '' == funBody.replace('\t', '').replace('\n', '').strip():
                continue
            pyCode += 'def %s:' % funHeader.strip() + '\n' + funBody
            
        addCode = pyCode
        printDBG("===================================")
        printDBG(pyCode)
        printDBG("===================================")
            
        swfUrl = unpackJS(_getParam('flashplayer'), _getParamVal, addCode)
        url    = unpackJS(_getParam('streamer'), _getParamVal, addCode)
        file   = unpackJS(_getParam('file'), _getParamVal, addCode)
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserFXSTREAMBIZ(self, baseUrl):
        printDBG("parserFXSTREAMBIZ baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3 Gecko/2008092417 Firefox/3.0.3', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER['Referer'] = Referer
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: return False
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]*%s['"]*[^'^"]+?['"]([^'^"]+?)['"]""" % name)[0]
        file   = _getParam('file')
        printDBG(data)
        return False
        
    def parserWEBCAMERAPL(self, baseUrl):
        printDBG("parserWEBCAMERAPL baseUrl[%s]" % baseUrl)
        
        def _getFullUrl(url):
            if url.startswith('//'):
                url = 'http:' + url
            return url
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        playerUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]+?webcamera\.[^'^"]+?/player/[^'^"]+?)['"]""")[0]
        if playerUrl == '': playerUrl = self.cm.ph.getSearchGroups(data, """['"]([^'^"]+?player\.webcamera\.[^'^"]+?)['"]""")[0]
        playerUrl = _getFullUrl(playerUrl)
        if self.cm.isValidUrl(playerUrl):
            sts, tmp = self.cm.getPage(playerUrl)
            tmp = self.cm.ph.getSearchGroups(tmp, """var\sVIDEO_SRC\s=\s['"]([^'^"]+?)['"]""")[0]
            if tmp != '':
                tmp = codecs.decode(tmp, 'rot13').replace('\/', '/')
                return getDirectM3U8Playlist(_getFullUrl(tmp), checkContent=True)
        
        return False
        
    def parserFLASHXTV(self, baseUrl):
        printDBG("parserFLASHXTV baseUrl[%s]" % baseUrl)
        
        HTTP_HEADER = self.cm.getDefaultHeader()
        
        COOKIE_FILE = GetCookieDir('flashxtv.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        def __parseErrorMSG(data):
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<center>', '</center>', False, False)
            for item in data:
                if 'color="red"' in item or ('ile' in item and '<script' not in item):
                    SetIPTVPlayerLastHostError(clean_html(item))
                    break
        
        def __getJS(data, params):
            tmpUrls = re.compile("""<script[^>]+?src=['"]([^'^"]+?)['"]""", re.IGNORECASE).findall(data)
            printDBG(tmpUrls)
            codeUrl = 'https://www.flashx.tv/js/code.js'
            for tmpUrl in tmpUrls:
                if tmpUrl.startswith('.'):
                    tmpUrl = tmpUrl[1:]
                if tmpUrl.startswith('//'):
                    tmpUrl = 'https:' + tmpUrl
                if tmpUrl.startswith('/'):
                    tmpUrl = 'https://www.flashx.tv' + tmpUrl
                if self.cm.isValidUrl(tmpUrl): 
                    if ('flashx' in tmpUrl and 'jquery' not in tmpUrl and '/code.js' not in tmpUrl and '/coder.js' not in tmpUrl): 
                        printDBG('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
                        sts, tmp = self.cm.getPage(tmpUrl.replace('\n', ''), params)
                    elif '/code.js' in tmpUrl or '/coder.js' in tmpUrl:
                        codeUrl = tmpUrl
            
            sts, tmp = self.cm.getPage(codeUrl, params)
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, 'function', ';');
            for tmpItem in tmp:
                tmpItem = tmpItem.replace(' ', '')
                if '!=null' in tmpItem:
                    tmpItem   = self.cm.ph.getDataBeetwenMarkers(tmpItem, 'get(', ')')[1]
                    tmpUrl    = self.cm.ph.getSearchGroups(tmpItem, """['"](https?://[^'^"]+?)['"]""")[0]
                    if not self.cm.isValidUrl(tmpUrl): continue
                    getParams = self.cm.ph.getDataBeetwenMarkers(tmpItem, '{', '}', False)[1]
                    getParams = getParams.replace(':', '=').replace(',', '&').replace('"', '').replace("'", '')
                    tmpUrl += '?' + getParams
                    sts, tmp = self.cm.getPage(tmpUrl, params)
                    break
        
        if baseUrl.split('?')[0].endswith('.jsp'):
            rm(COOKIE_FILE)
            sts, data = self.cm.getPage(baseUrl, params)
            if not sts: return False
            
            __parseErrorMSG(data)
            
            cookies = dict(re.compile(r'''cookie\(\s*['"]([^'^"]+?)['"]\s*\,\s*['"]([^'^"]+?)['"]''', re.IGNORECASE).findall(data))
            tmpParams = dict(params)
            tmpParams['cookie_items'] = cookies
            tmpParams['header']['Referer'] = baseUrl
            
            __getJS(data, tmpParams)
            
            data = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<form[^>]+?method="POST"', re.IGNORECASE),  re.compile('</form>', re.IGNORECASE), True)[1]
            printDBG(data)
            printDBG("================================================================================")
            
            action = self.cm.ph.getSearchGroups(data, '''action=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            post_data = dict(re.compile(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', re.IGNORECASE).findall(data))
            try:
                tmp = dict(re.findall(r'<button[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
                post_data.update(tmp)
            except Exception:
                printExc()
            
            try: GetIPTVSleep().Sleep(int(self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0])+1)
            except Exception:
                printExc()
            
            if {} == post_data:  post_data = None
            if not self.cm.isValidUrl(action) and url != '':
                action = urljoin(baseUrl, action)
            
            sts, data = self.cm.getPage(action, tmpParams, post_data)
            if not sts: return False
            
            printDBG(data)
            __parseErrorMSG(data)
            
            # get JS player script code from confirmation page
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, ">eval(", '</script>', False)
            for item in tmp:
                printDBG("================================================================================")
                printDBG(item)
                printDBG("================================================================================")
                item = item.strip()
                if item.endswith(')))'): idx = 1
                else: idx = 0
                printDBG("IDX[%s]" % idx)
                for decFun in [SAWLIVETV_decryptPlayerParams, KINGFILESNET_decryptPlayerParams]:
                    decItem = urllib.unquote(unpackJSPlayerParams(item, decFun, idx))
                    printDBG('[%s]' % decItem)
                    data += decItem + ' '
                    if decItem != '': break
            
            urls = []
            tmp = re.compile('''\{[^}]*?src[^}]+?video/mp4[^}]+?\}''').findall(data )
            for item in tmp:
                label = self.cm.ph.getSearchGroups(item, '''['"]?label['"]?\s*:\s*['"]([^"^']+?)['"]''')[0]
                res = self.cm.ph.getSearchGroups(item, '''['"]?res['"]?\s*:\s*[^0-9]?([0-9]+?)[^0-9]''')[0]
                name = '%s - %s' % (res, label)
                url = self.cm.ph.getSearchGroups(item, '''['"]?src['"]?\s*:\s*['"]([^"^']+?)['"]''')[0]
                params = {'name':name, 'url':url}
                if params not in urls: urls.append(params)
            
            return urls[::-1]
        
        if '.tv/embed-' not in baseUrl:
            baseUrl = baseUrl.replace('.tv/', '.tv/embed-')
        if not baseUrl.endswith('.html'):
            baseUrl += '.html'
            
        
        params['header']['Referer'] = baseUrl
        SWF_URL = 'http://static.flashx.tv/player6/jwplayer.flash.swf'
        id = self.cm.ph.getSearchGroups(baseUrl+'/', 'c=([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        if id == '': id = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        if id == '': id = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{32})[^A-Za-z0-9]')[0]
        baseUrl = 'http://www.flashx.tv/embed.php?c=' + id
        
        rm(COOKIE_FILE)
        params['max_data_size'] = 0
        self.cm.getPage(baseUrl, params)
        redirectUrl = self.cm.meta['url']
        
        id = self.cm.ph.getSearchGroups(redirectUrl+'/', 'c=([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        if id == '': id = self.cm.ph.getSearchGroups(redirectUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0] 
        if id == '': id = self.cm.ph.getSearchGroups(redirectUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{32})[^A-Za-z0-9]')[0] 
        baseUrl = 'http://www.flashx.tv/embed.php?c=' + id
        
        params.pop('max_data_size', None)
        sts, data = self.cm.getPage(baseUrl, params)
        params['header']['Referer'] = redirectUrl
        params['load_cookie'] = True
        
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        printDBG(data)
        printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        
        play = ''
        vid = self.cm.ph.getSearchGroups(redirectUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        vid = self.cm.ph.getSearchGroups(redirectUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{32})[^A-Za-z0-9]')[0]
        for item in ['playvid', 'playthis', 'playit', 'playme', 'playvideo']:
            if item+'-' in data:
                play = item
                break
        
        printDBG("vid[%s] play[%s]" % (vid, play))
        
        __getJS(data, params)
        
        url = self.cm.ph.getSearchGroups(redirectUrl, """(https?://[^/]+?/)""")[0] + play + '-{0}.html?{1}'.format(vid, play)
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        printDBG(data)
            
        if 'fxplay' not in url and 'fxplay' in data:
            url = self.cm.ph.getSearchGroups(data, '"(http[^"]+?fxplay[^"]+?)"')[0]
            sts, data = self.cm.getPage(url)
            if not sts: return False
        
        try:
            printDBG(data)
            __parseErrorMSG(data)
            
            tmpTab = self.cm.ph.getAllItemsBeetwenMarkers(data, ">eval(", '</script>', False, False)
            for tmp in tmpTab:
                tmp2 = ''
                for type in [0, 1]:
                    for fun in [SAWLIVETV_decryptPlayerParams, VIDUPME_decryptPlayerParams]:
                        tmp2 = unpackJSPlayerParams(tmp, fun, type=type)
                        printDBG(tmp2)
                        data = tmp2 + data
                        if tmp2 != '': 
                            printDBG("+++")
                            printDBG(tmp2)
                            printDBG("+++")
                            break
                    if tmp2 != '': break
                        
        except Exception:
            printExc()
        
        retTab = []
        linksTab = re.compile("""["']*file["']*[ ]*?:[ ]*?["']([^"^']+?)['"]""").findall(data)
        linksTab.extend(re.compile("""["']*src["']*[ ]*?:[ ]*?["']([^"^']+?)['"]""").findall(data))
        linksTab = set(linksTab)
        for item in linksTab:
            if item.endswith('/trailer.mp4'): continue
            if self.cm.isValidUrl(item):
                if item.split('?')[0].endswith('.smil'):
                    # get stream link
                    sts, tmp = self.cm.getPage(item)
                    if sts:
                        base = self.cm.ph.getSearchGroups(tmp, 'base="([^"]+?)"')[0]
                        src = self.cm.ph.getSearchGroups(tmp, 'src="([^"]+?)"')[0]
                        #if ':' in src:
                        #    src = src.split(':')[1]   
                        if base.startswith('rtmp'):
                            retTab.append({'name':'rtmp', 'url': base + '/' + src + ' swfUrl=%s live=1 pageUrl=%s' % (SWF_URL, redirectUrl)})
                elif '.mp4' in item:
                    retTab.append({'name':'mp4', 'url': item})
        return retTab[::-1]
        
    def parserMYVIDEODE(self, baseUrl):
        printDBG("parserMYVIDEODE baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0",
                       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Language': 'de-DE,de;q=0.8,en-US;q=0.6,en;q=0.4',
                       'Referer': baseUrl}
        baseUrl = strwithmeta(baseUrl)
        ################################################################################
        # Implementation based on:
        # https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/myvideo.py
        ################################################################################
        swfUrl = 'http://is5.myvideo.de/de/player/mingR14b/ming.swf'
        GK = b'WXpnME1EZGhNRGhpTTJNM01XVmhOREU0WldNNVpHTTJOakptTW1FMU5tVTBNR05pWkRaa05XRXhNVFJoWVRVd1ptSXhaVEV3TnpsbA0KTVRkbU1tSTRNdz09'
        requestParams = {'http_proxy':baseUrl.meta.get('http_proxy', '')}
        requestParams['header'] = HTTP_HEADER
        baseUrl = strwithmeta(baseUrl+'/')
        
        videoTab = []
        
        # Original Code from: https://github.com/dersphere/plugin.video.myvideo_de.git
        # Released into the Public Domain by Tristan Fischer on 2013-05-19
        # https://github.com/rg3/youtube-dl/pull/842
        def __rc4crypt(data, key):
            x = 0
            box = list(range(256))
            for i in list(range(256)):
                x = (x + box[i] + ord(key[i % len(key)])) % 256
                box[i], box[x] = box[x], box[i]
            x = 0
            y = 0
            out = ''
            for char in data:
                x = (x + 1) % 256
                y = (y + box[x]) % 256
                box[x], box[y] = box[y], box[x]
                out += chr(ord(char) ^ box[(box[x] + box[y]) % 256])
            return out
        def __md5(s):
            return md5(s).hexdigest().encode()
            
        def _getRtmpLink(r, tcUrl, playpath, swfUrl, page):
            if '?token=' in r:
                tmp = r.split('?token=')
                r = tmp[0]
                token = tmp[1]
            else:
                token = ''
            if '' != tcUrl:    r += ' tcUrl='    + tcUrl
            if '' != playpath: r += ' playpath=' + playpath
            if '' != swfUrl:   r += ' swfUrl='   + swfUrl
            if '' != page:     r += ' pageUrl='  + page
            if '' != token:     r += ' token='    + token
            return urlparser.decorateUrl(r, {'iptv_livestream':False})
        # Get video ID
        video_id = baseUrl
        if '-m-' in video_id:
            video_id = self.cm.ph.getSearchGroups(video_id, """-m-([0-9]+?)[^0-9]""")[0]
        else:
            video_id = self.cm.ph.getSearchGroups(video_id, """/(?:[^/]+/)?watch/([0-9]+)/""")[0]
        if '' != video_id:
            try:
                xmldata_url = "http://www.myvideo.de/dynamic/get_player_video_xml.php?ID=%s&flash_playertype=D&autorun=yes" % video_id
                sts, enc_data = self.cm.getPage(xmldata_url, requestParams)
                enc_data = enc_data.split('=')[1]
                enc_data_b = unhexlify(enc_data)
                sk = __md5(base64.b64decode(base64.b64decode(GK)) + __md5(str(video_id).encode('utf-8')))
                dec_data = __rc4crypt(enc_data_b, sk)
                #printDBG("============================================================================")
                #printDBG(dec_data)
                #printDBG("============================================================================")

                # extracting infos
                connectionurl = urllib.unquote( self.cm.ph.getSearchGroups(dec_data, "connectionurl='([^']*?)'")[0] )
                source        = urllib.unquote( self.cm.ph.getSearchGroups(dec_data, "source='([^']*?)'")[0] )
                path          = urllib.unquote( self.cm.ph.getSearchGroups(dec_data, "path='([^']*?)'")[0] )
                
                if connectionurl.startswith('rtmp'):
                    connectionurl = connectionurl.replace('rtmpe://', 'rtmp://')
                
                    rtmpUrl = urlparser.decorateUrl(connectionurl)
                    if rtmpUrl.meta.get('iptv_proto', '') == 'rtmp':
                        if not source.endswith('f4m') :
                            playpath = source.split('.')
                            playpath = '%s:%s' % (playpath[1], playpath[0]) 
                        videoUrl = _getRtmpLink(rtmpUrl, rtmpUrl, playpath, swfUrl, baseUrl)
                        videoTab.append({'name':'myvideo.de: RTMP', 'url':videoUrl})
                else:
                    videoTab.append({'name':'myvideo.de: HTTP', 'url':path+source})
            except Exception:
                printExc()
                
        return videoTab
        
    def parserVIDZITV(self, baseUrl):
        printDBG("parserVIDZITV baseUrl[%s]" % baseUrl)
        videoTab = []
        if 'embed' not in baseUrl:
            vid = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
            baseUrl = 'http://vidzi.tv/embed-%s.html' % vid
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        msg = clean_html(self.cm.ph.getDataBeetwenMarkers(data, 'The file was deleted', '<')[1]).strip()
        if msg != '': SetIPTVPlayerLastHostError(msg)
        
        #######################################################
        tmpData = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        tmp = []
        for item in tmpData:
            if 'eval(' in item:
                tmp.append(item)
        
        jscode = base64.b64decode('''ZnVuY3Rpb24gc3R1Yigpe31mdW5jdGlvbiBqd3BsYXllcigpe3JldHVybntzZXR1cDpmdW5jdGlvbigpe3ByaW50KEpTT04uc3RyaW5naWZ5KGFyZ3VtZW50c1swXSkpfSxvblRpbWU6c3R1YixvblBsYXk6c3R1YixvbkNvbXBsZXRlOnN0dWIsb25SZWFkeTpzdHViLGFkZEJ1dHRvbjpzdHVifX12YXIgZG9jdW1lbnQ9e30sd2luZG93PXRoaXM7''')
        jscode += '\n'.join(tmp)
        ret = js_execute( jscode )
        try: data = ret['data'].strip() + data
        except Exception: printExc()
        #######################################################
        
        data = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''sources['"]?\s*:'''), re.compile('\]'), False)[1]
        data = re.findall('''['"]?file['"]?\s*:\s*['"]([^"^']+?)['"]''', data)
        for item in data:
            if item.split('?')[0].endswith('m3u8'):
                tmp = getDirectM3U8Playlist(item, checkContent=True, sortWithMaxBitrate=999999999)
                videoTab.extend(tmp)
            else:
                videoTab.append({'name':'vidzi.tv mp4', 'url':item})
        return videoTab
        
    def parserTVP(self, baseUrl):
        printDBG("parserTVP baseUrl[%s]" % baseUrl)
        vidTab = []
        try:
            from Plugins.Extensions.IPTVPlayer.hosts.hosttvpvod import TvpVod
            vidTab = TvpVod().getLinksForVideo({'url':baseUrl})
        except Exception:
            printExc()
        return vidTab
        
    def parserJUNKYVIDEO(self, baseUrl):
        printDBG("parserJUNKYVIDEO baseUrl[%s]" % baseUrl)
        sts,data = self.cm.getPage(baseUrl)
        if not sts: return []
        url = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?[ ]*:[ ]*['"]([^"^']+)['"],''')[0]
        if url.startswith('http'):
            return [{'name':'junkyvideo.com', 'url':url}]
        return []
        
    def parserLIVEBVBTOTALDE(self, baseUrl):
        printDBG("parserJUNKYVIDEO baseUrl[%s]" % baseUrl)
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return []
        data = self.cm.ph.getSearchGroups(data, r'<iframe[^>]+?src="([^"]+)"')[0]
        sts, data = self.cm.getPage(data, {'header':HTTP_HEADER})
        if not sts: return []
        data = self.cm.ph.getSearchGroups(data, r'<iframe[^>]+?src="([^"]+)"')[0]
        sts, data = self.cm.getPage(data, {'header':HTTP_HEADER})
        if not sts: return []
        data = self.cm.ph.getSearchGroups(data, r'url: "([^"]+)"')[0]
        sts, data = self.cm.getPage(data, {'header':HTTP_HEADER})
        if not sts: return []
        printDBG(data)
        if 'statustext="success"' not in data: return []
        url   = self.cm.ph.getSearchGroups(data, r'url="([^"]+)"')[0]
        autch = self.cm.ph.getSearchGroups(data, r'auth="([^"]+)"')[0]
        url += '?' + autch
        linksTab = []
        retTab = getDirectM3U8Playlist(url)
        return retTab
        for item in retTab:
            name = ('live.bvbtotal.de %s' % item.get('heigth', 0))
            url = urlparser.decorateUrl(item['url'], {'iptv_livestream': True})
            linksTab.append({'name':name, 'url':url})
        return linksTab
        
    def parserNETTVPLUSCOM(self, baseUrl):
        printDBG("parserNETTVPLUSCOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        HTTP_HEADER['Referer'] = baseUrl
        if baseUrl.endswith('/source.js'): url = baseUrl
        else: url = baseUrl[:baseUrl.rfind('/')] + '/source.js'
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return []
        url = self.cm.ph.getSearchGroups(data, '''["'](http[^'^"]+?m3u8[^'^"]*?)["']''')[0]
        if '' != url: return getDirectM3U8Playlist(url, False)
        return []
        
    def parser7CASTNET(self, baseUrl):
        printDBG("parser7CASTNET baseUrl[%s]" % baseUrl)
        baseUrl = urlparser.decorateUrl(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        HTTP_HEADER = dict(self.HTTP_HEADER)
        HTTP_HEADER['User-Agent'] = "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30"
        HTTP_HEADER['Referer'] = referer

        url = baseUrl
        if '/embed/' in url:
            sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
            if not sts: return []
            url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^'^"]+?)["']''')[0]
        sts, data = self.cm.getPage(url, {'header': HTTP_HEADER})
        if not sts: return False
        data = data[data.rfind('}(')+2:].split('{}))')[0] + '{}'
        data = unpackJS(data, SAWLIVETV_decryptPlayerParams)
        names  = []
        values = {}
        data = re.compile(";([^;]+?)\.push\('(.)'\)").findall(data)
        for item in data:
            if item[0] not in names:
                names.append(item[0])
                values[item[0]] = item[1]
            else: values[item[0]] += item[1]
        if urllib.unquote(values[names[1]]).startswith('rtmp'): names = names[::-1]
        r = urllib.unquote(values[names[0]]) + '/' + urllib.unquote(values[names[1]])
        printDBG("...............................[%s]" % r)
        if r.startswith('rtmp'):
            swfUrl  = "http://7cast.net/jplayer.swf"
            rtmpUrl = r + ' swfUrl=%s pageUrl=%s live=1 ' % (swfUrl, baseUrl)
            return [{'name': 'rtmp://7cast.com/ ', 'url':urlparser.decorateUrl(rtmpUrl, {'iptv_livestream':True})}]
        return []
        
    def parserFACEBOOK(self, baseUrl):
        printDBG("parserFACEBOOK baseUrl[%s]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return []
        
        #printDBG(data)
        
        urlsTab = []
        for item in ['hd_src_no_ratelimit', 'hd_src', 'sd_src_no_ratelimit', 'sd_src']:
            url = self.cm.ph.getSearchGroups(data, '''"?%s"?\s*?:\s*?"(http[^"]+?\.mp4[^"]*?)"''' % item)[0]
            url = url.replace('\\/', '/')
            if self.cm.isValidUrl(url):
                urlsTab.append({'name':'facebook %s' % item, 'url':url})
                
        return urlsTab
        
    def parserCLOUDYVIDEOS(self, baseUrl):
        printDBG("parserCLOUDYVIDEOS baseUrl[%s]" % baseUrl)
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '[/-]([A-Za-z0-9]{12})[/-]')[0]
        url = 'http://cloudyvideos.com/{0}'.format(video_id)
        
        linkList = []
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})

        try:
            sleep_time = self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0]
            if '' != sleep_time: GetIPTVSleep().Sleep(int(sleep_time))
        except Exception:
            printExc()
        try:
            sts, data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)
            if not sts: return False
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            HTTP_HEADER['Referer'] = url
            sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER}, post_data)
            if not sts: return False
            #printDBG(data)
            linkList = self._findLinks(data, serverName='cloudyvideos.com', m1='setup({', m2='</script>')
            for item in linkList:
                item['url'] = urlparser.decorateUrl(item['url']+'?start=0', {'User-Agent':'Mozilla/5.0', 'Referer':'http://cloudyvideos.com/player510/player.swf'})
        except Exception:
            printExc()
        return linkList
        
    def parserFASTVIDEOIN(self, baseUrl):
        printDBG("parserFASTVIDEOIN baseUrl[%s]" % baseUrl)

        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = referer if referer != '' else 'https://www1.swatchseries.to/'

        COOKIE_FILE = GetCookieDir('FASTVIDEOIN.cookie')
        defaultParams = {'header':HTTP_HEADER, 'with_metadata':True, 'use_new_session':True, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}

        rm(COOKIE_FILE)

        sts, data = self.cm.getPage(baseUrl, defaultParams)
        if not sts: return
        url = self.cm.meta['url']

        defaultParams.pop('use_new_session')

        printDBG("111\n%s\n111" % data)
        defaultParams['cookie_items'] = self.cm.getCookieItems(COOKIE_FILE)

        #http://fastvideo.in/nr4kzevlbuws
        host = ph.find(url, "://", '/', flags=0)[1]

        defaultParams['header']['Referer'] = url
        sts, data = self.cm.getPage(url, defaultParams)
        if not sts: return False

        printDBG("222\n%s\n222" % data)
        try:
            sleep_time =  self.cm.ph.getDataBeetwenMarkers(data, '<div class="btn-box"', '</div>')[1]
            sleep_time = self.cm.ph.getSearchGroups(sleep_time, '>([0-9]+?)<')[0]
            GetIPTVSleep().Sleep(int(sleep_time))
        except Exception:
            printExc()
            
        sts, tmp = ph.find(data, 'method="POST" action', '</Form>', flags=ph.I)
        if sts:
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            post_data.pop('method_premium', None)
            defaultParams['header']['Referer'] = url
            sts, data = self.cm.getPage(url, defaultParams, post_data)
            if sts: SetIPTVPlayerLastHostError(ph.clean_html(ph.find(data, ('<font', '>', 'err'), ('</font', '>'), flags=0)[1]))
            printDBG("333\n%s\n333" % data)
        linksTab = self._findLinks(data, host, linkMarker=r'''['"](https?://[^"^']+(?:\.mp4|\.flv)[^'^"]*?)['"]''')
        for idx in range(len(linksTab)):
            linksTab[idx]['url'] = strwithmeta(linksTab[idx]['url'], {'Referer':url, 'User-Agent':['User-Agent']})
        return linksTab
        
    def parserTHEVIDEOME(self, baseUrl):
        printDBG("parserTHEVIDEOME baseUrl[%s]" % baseUrl)
        #http://thevideo.me/embed-l03p7if0va9a-682x500.html
        HTTP_HEADER = {'User-Agent':'Mozilla/5.0'}
        COOKIE_FILE = GetCookieDir('thvideome.cookie')
        rm(COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'with_metadata':True, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: 
            return False
        
        baseUrl = data.meta['url']
        urlsTab = []
        
        if '/embed/' in baseUrl or 'embed-' in baseUrl: 
            url = baseUrl
        else:
            parsedUri = urlparse( baseUrl )
            path = '/embed/' + parsedUri.path[1:]
            parsedUri = parsedUri._replace(path=path)
            url = urlunparse(parsedUri)
            sts, data = self.cm.getPage(url, params)
            if not sts: 
                return False
        
        videoCode = self.cm.ph.getSearchGroups(data, r'''['"]video_code['"]\s*:\s*['"]([^'^"]+?)['"]''')[0]
        
        if videoCode:
        
            params['header']['Referer'] = url
            params['raw_post_data'] = True
            sts, data = self.cm.getPage(self.cm.getBaseUrl(baseUrl) + 'api/serve/video/' + videoCode, params, post_data='{}') 
            if sts: 
                printDBG("----------------")
                printDBG(data)
                printDBG("----------------")
        
                dataJson = json_loads(data)
                for key in dataJson['qualities']:
                    urlsTab.append({'name':'[%s] %s' % (key, self.cm.getBaseUrl(baseUrl)), 'url':strwithmeta(dataJson['qualities'][key], {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':self.cm.getBaseUrl(baseUrl)})})
        
        else:
            #search for packed code
            scripts = re.findall("<script>.*?(eval\(function.*?)</script>", data, re.S)
            
            if scripts:
                for script in scripts:
                    printDBG("----------- pack -----------------")
                    printDBG(script)

                    script = script + "\n"
                    # mods
                    script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                    script = script.replace("return p}(", "print(p)}\n\npippo(")
                    script = script.replace("))\n",");\n")

                    # duktape
                    ret = js_execute( script )
                    decoded = ret['data']
                    printDBG('------------------------------')
                    printDBG(decoded)
                    printDBG('------------------------------')

                    #video.src({type:'video/mp4',src:'stream9253bce1c89c262dc27e84e36a137f23.mp4'})
                    sources = re.findall("src\((\{.*?\})\)", decoded)

                    for s in sources:
                        src = demjson_loads(s)
                        url = src.get('src','')
                        if url:
                            if not url.startswith('http'):
                                url = self.cm.getFullUrl(url, self.cm.getBaseUrl(baseUrl))
                            
                            srcType = src.get('type','')
                            
                        url = urlparser.decorateUrl(url, {'Referer': baseUrl})
                        if 'm3u' in srcType or 'hls' in srcType:
                            params = getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                            printDBG(str(params))    
                            urlsTab.extend(params)
                        else:
                            params = {'name': 'link' , 'url': url}
                            printDBG(str(params))
                            urlsTab.append(params)

        return urlsTab
    
    def parserMODIVXCOM(self, baseUrl):
        printDBG("parserMODIVXCOM baseUrl[%s]" % baseUrl)
        serverName='movdivx.com'
        def __customLinksFinder(pageData):
            #printDBG(pageData)
            sts, data = CParsingHelper.getDataBeetwenMarkers(pageData, ">eval(", '</script>', False)
            if sts:
                mark1 = "}("
                idx1 = data.find(mark1)
                if -1 == idx1: return False
                idx1 += len(mark1)
                pageData = unpackJS(data[idx1:-3], VIDUPME_decryptPlayerParams)
                return self._findLinks(pageData, serverName)
            else: return []
        return self.__parseJWPLAYER_A(baseUrl, serverName, customLinksFinder=__customLinksFinder)
            
    def parserXAGEPL(self, baseUrl):
        printDBG("parserXAGEPL baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        url = self.cm.ph.getSearchGroups(data, 'src="([^"]+?)"')[0]
        
        
        
    def parserCASTONTV(self, baseUrl):
        printDBG("parserCASTONTV baseUrl[%s]" % baseUrl)

        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict({'User-Agent':'Mozilla/5.0'}) 
        HTTP_HEADER['Referer'] = Referer
        
        COOKIE_FILE = GetCookieDir('castontv.cookie')
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        id = self.cm.ph.getSearchGroups(baseUrl + '|', 'id=([0-9]+?)[^0-9]')[0]
        linkUrl = 'http://www.caston.tv/player.php?width=1920&height=419&id={0}'.format(id)
        
        sts, data = self.cm.getPage(linkUrl, params)
        if not sts: return False
        
        data = re.sub('''unescape\(["']([^"^']+?)['"]\)''', lambda m: urllib.unquote(m.group(1)), data)
        #printDBG(data)
        
        tmpData = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>', True)[1]
        printDBG(tmpData)
        while 'eval' in tmpData:
            tmp = tmpData.split('eval(')
            if len(tmp): del tmp[0]
            tmpData = ''
            for item in tmp:
                for decFun in [VIDEOWEED_decryptPlayerParams, SAWLIVETV_decryptPlayerParams]:
                    tmpData = unpackJSPlayerParams('eval('+item, decFun, 0)
                    if '' != tmpData:   
                        break
                printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                printDBG(tmpData)
                printDBG("ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ")
                if 'token' in tmpData and 'm3u8' in tmpData:
                    break
        token = self.cm.ph.getSearchGroups(tmpData, r"""['"]?token['"]?[\s]*?\:[\s]*?['"]([^"^']+?)['"]""")[0]
        url   = self.cm.ph.getSearchGroups(tmpData, r"""['"]?url['"]?[\s]*?\:[\s]*?['"]([^"^']+?)['"]""")[0]
        file  = self.cm.ph.getSearchGroups(tmpData, r"""['"]?file['"]?[\s]*?\:[\s]*?['"]([^}]+?)\}""")[0] 
        
        printDBG("token[%s]" % token)
        printDBG("url[%s]" % url)
        printDBG("file[%s]" % file)
        
        if url != '' and '://' not in url:
            if url.startswith('//'): url = 'http:' + url
            else: url = 'http://www.caston.tv/' + url

        params['load_cookie'] = True
        params['header'].update({'Referer':linkUrl, 'Accept':'application/json, text/javascript, */*', 'Content-Type':'application/x-www-form-urlencoded', 'X-Requested-With':'XMLHttpRequest' })
        sts, data = self.cm.getPage(url, params, {'token':token, 'is_ajax':1})
        if not sts: return False
        
        data = json_loads(data)
        printDBG(data)
        def _replace(item):
            idx = int(item.group(1))
            return str(data[idx])
            
        file = re.sub('"\+[^"]+?\[([0-9]+?)\]\+"', _replace, file+'+"')
        hlsUrl = urlparser.decorateUrl(file, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Referer':'http://p.jwpcdn.com/6/12/jwplayer.flash.swf', 'User-Agent':'Mozilla/5.0'})
        return getDirectM3U8Playlist(hlsUrl)

    def parserCASTAMPCOM(self, baseUrl):
        printDBG("parserCASTAMPCOM baseUrl[%s]" % baseUrl)
        channel = ph.search(baseUrl + '&', 'c=([^&]+?)&')[0]

        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer

        def _getDomainsa():
            chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXTZabcdefghiklmnopqrstuvwxyz"
            string_length = 8
            randomstring = ''
            for i in range(string_length):
                rnum = randint(0, len(chars)-1)
                randomstring += chars[rnum]
            return randomstring 
        
        linkUrl = 'http://www.castamp.com/embed.php?c={0}&tk={1}&vwidth=710&vheight=460'.format(channel, _getDomainsa())

        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False

        jscode = ['var player={};function setup(e){this.obj=e}function jwplayer(){return player}player.setup=setup,document={},document.getElementById=function(e){return{innerHTML:interHtmlElements[e]}};']
        interHtmlElements = {}
        tmp = ph.findall(data, ('<div', '>', 'display:none;'), '</div>', flags=ph.START_S)
        for idx in range(1, len(tmp), 2):
            if '<' in tmp[idx] or '>' in tmp[idx]: continue
            elemId = ph.getattr(tmp[idx-1], 'id')
            interHtmlElements[elemId] = tmp[idx].strip()
        jscode.append('var interHtmlElements=%s;' % json_dumps(interHtmlElements))

        cUrl = self.cm.meta['url']
        tmp = ph.findall(data, ('<script', '>', 'src'))
        for item in tmp:
            url = self.cm.getFullUrl(ph.getattr(item, 'src'), cUrl)
            sts, item = self.cm.getPage(url, {'header':HTTP_HEADER})
            if sts and 'eval(' in item: jscode.append(item)

        sts, data = ph.find(data, ('<div', '>', 'player'), '</script>')
        if not sts: return False

        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        data = ph.find(data, ('<script', '>'), '</script>', flags=0)[1]
        jscode.append(data)
        jscode.append('print(JSON.stringify(player.obj));')

        printDBG("+++++++++++++++++++++++  CODE  ++++++++++++++++++++++++")
        printDBG(jscode)
        printDBG("+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        ret = js_execute( '\n'.join(jscode) )
        if ret['sts'] and 0 == ret['code']:
            decoded = ret['data'].strip()
            decoded = json_loads(decoded)
            swfUrl = decoded['flashplayer']
            url    = decoded['streamer']
            file   = decoded['file']
            if '' != file and '' != url:
                url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
                printDBG(url)
                return url
        return False

    def parserCRICHDTV(self, baseUrl):
        printDBG("parserCRICHDTV baseUrl[%s]" % baseUrl)
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        baseUrl.meta['Referer'] = baseUrl
        links = urlparser().getAutoDetectedStreamLink(baseUrl, data)
        return links
        
        
        channelId = self.cm.ph.getSearchGroups(data, "id='([0-9]+?)'")[0]
        linkUrl = 'http://popeoftheplayers.eu/crichd.php?id={0}&width=710&height=460'.format(channelId)
        HTTP_HEADER['Referer'] = baseUrl
        
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]%s['"][^'^"]+?['"]([^'^"]+?)['"]""" % name)[0] 
        swfUrl = "http://popeoftheplayers.eu/atdedead.swf"#_getParam('flashplayer')
        url    = _getParam('streamer') #rtmp://89.248.172.159:443/liverepeater
        file   = _getParam('file')
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s token=%s pageUrl=%s live=1 ' % (file, swfUrl, '#atd%#$ZH', linkUrl)
            printDBG(url)
            return url
        return False
        
        
    def parserCASTTOME(self, baseUrl):
        printDBG("parserCASTTOME baseUrl[%s]" % baseUrl)
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        #printDBG(data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]?%s['"]?[^'^"]+?['"]([^'^"]+?)['"]""" % name)[0] 
        swfUrl = "http://www.castto.me/_.swf"
        url    = _getParam('streamer')
        file   = _getParam('file')
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s token=%s pageUrl=%s live=1 ' % (file, swfUrl, '#ed%h0#w@1', baseUrl)
            printDBG(url)
            return url
        else:
            data = re.compile('''["'](http[^'^"]+?\.m3u8[^'^"]*?)["']''').findall(data)
            data.reverse()
            printDBG(data)
            data.insert(0, file)
            data.reverse()
            for file in data:
                if file.startswith('http') and file.split('?')[0].endswith('.m3u8'):
                    tab = getDirectM3U8Playlist(file, checkContent=True)
                    if len(tab): return tab
        return False
        
    def saveGet(self, b, a):
        try: return b[a]
        except Exception: return 'pic'
        
    def justRet(self, data):
        return data
        
    def _unpackJS(self, data, name):
        data = data.replace('Math.min', 'min').replace(' + (', ' + str(').replace('String.fromCharCode', 'chr').replace('return b[a]', 'return saveGet(b, a)')
        try:
            paramsAlgoObj = compile(data, '', 'exec')
        except Exception:
            printExc('unpackJS compile algo code EXCEPTION')
            return ''
        vGlobals = {"__builtins__": None, 'string': string, 'str':str, 'chr':chr, 'decodeURIComponent':urllib.unquote, 'unescape':urllib.unquote, 'min':min, 'saveGet':self.saveGet, 'justRet':self.justRet}
        vLocals = { name: None }

        try:
            exec( data, vGlobals, vLocals )
        except Exception:
            printExc('unpackJS exec code EXCEPTION')
            return ''
        try:
            return vLocals[name]
        except Exception:
            printExc('decryptPlayerParams EXCEPTION')
        return ''
        
    def parserHDCASTINFO(self, baseUrl):
        printDBG("parserHDCASTINFO baseUrl[%s]" % baseUrl)
        return self.parserCAST4UTV(baseUrl, 'hdcast.info')
        
    def parserCAST4UTV(self, baseUrl, domain='cast4u.tv'):
        printDBG("parserCAST4UTV baseUrl[%s]" % baseUrl)
        urlTab = []
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', '')
        M_HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25', 'Accept':'*/*', 'Accept-Encoding': 'gzip, deflate', 'Referer': referer}
        H_HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36', 'Accept':'*/*', 'Accept-Encoding': 'gzip, deflate', 'Referer': referer}
        
        for header in [H_HTTP_HEADER, M_HTTP_HEADER]:
            sts, data = self.cm.getPage(baseUrl, {'header':header})
            if not sts: continue
            printDBG(data)
            loadbalancerUrl = self.cm.ph.getSearchGroups(data, '''['"](https?[^'^"]+?/loadbalancer[^'^"]*?)['"]''')[0]
            if loadbalancerUrl.endswith('?'): loadbalancerUrl += '36'
            streamUrl = self.cm.ph.getSearchGroups(data, '''["']([^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
            pk = self.cm.ph.getSearchGroups(data, '''enableVideo\(\s*['"]([^'^"]+?)['"]\s*\)''')[0]
            
            if not self.cm.isValidUrl(streamUrl):
                sts, data = self.cm.getPage(loadbalancerUrl, {'header':header})
                if not sts: continue
                url = data.split('=')[-1]
                url = 'http://' + url + streamUrl + pk
                urlTab.extend(getDirectM3U8Playlist(url, checkContent=True))
        
        return urlTab
        
        def _getVariables(data):
            printDBG('_getVariables')
            varTabs = []
            tmp = re.compile('var([^;]+?)=[^;]*?(\[[^\]]+?\]);').findall(data)
            for item in tmp:
                var = item[0].strip()
                val = item[1].strip()
                if var == '': continue
                if val == '': continue
                varTabs.append('%s = %s' % (var, val))
            varTabs = '\n'.join( varTabs )
            return varTabs
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<span style', '</script>')[1]
        globalVars = _getVariables(data)
        file = self.cm.ph.getDataBeetwenMarkers(data, 'file:', '}', False)[1].strip()
        token = self.cm.ph.getSearchGroups(data, """securetoken\s*:\s*([^\s]+?)\s""")[0] 
        
        def _evalSimple(dat):
            return '"%s"' % self.cm.ph.getSearchGroups(data, """<[^>]+?id=['"]?%s['"]?[^>]*?>([^<]+?)<""" % dat.group(1))[0] 
        data = re.sub('document\.getElementById\("([^"]+?)"\)\.innerHTML', _evalSimple, data)
        
        def _evalJoin(dat):
            return " ''.join(%s) " % dat.group(1)
        
        funData = re.compile('function ([^\(]*?\([^\)]*?\))[^\{]*?\{([^\{]*?)\}').findall(data)
        pyCode = ''
        for item in funData:
            funHeader = item[0]
            
            funBody = re.sub('(\[[^\]]+?\])\.join\(""\)', _evalJoin, item[1])
            funBody = re.sub(' ([^ ]+?)\.join\(""\)', _evalJoin, funBody)
            funIns = funBody.split(';')
            funBody = ''
            for ins in funIns:
                ins = ins.replace('var', ' ').strip()
                if len(ins) and ins[-1] not in [')', ']', '"']:
                    ins += '()'
                funBody += '\t%s\n' % ins
            if '' == funBody.replace('\t', '').replace('\n', '').strip():
                continue
            pyCode += 'def %s:' % funHeader.strip() + '\n' + funBody
        
        pyCode = 'def retA():\n\t' + globalVars.replace('\n', '\n\t') + '\n\t' + pyCode.replace('\n', '\n\t') + '\n\treturn {0}\n'.format(file) + 'param = retA()'
        printDBG(pyCode)
        file = self._unpackJS(pyCode, 'param').replace('\\/', '/')
        
        swfUrl = 'http://%s/jwplayer/jwplayer.flash.swf' % domain
        token = '%XB00(nKH@#.' #http://stream-recorder.com/forum/rtmp-token-vlc-help-t20959.html?s=7c3a16e350bdc8bdf73c525163884654&amp;
        return file + ' swfUrl=%s token=%s pageUrl=%s live=1 ' % (swfUrl, token, baseUrl)
        
    def parserDELTATVPW(self, baseUrl):
        printDBG("parserDELTATVPW baseUrl[%s]" % baseUrl)
        
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, "%s=([^&]+?)&" % name)[0] 
        swfUrl = "http://cdn.deltatv.pw/players.swf"
        url    = _getParam('streamer')
        file   = _getParam('file')
        if '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s token=%s pageUrl=%s live=1 ' % (file, swfUrl, 'Fo5_n0w?U.rA6l3-70w47ch', baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserKABABLIMA(self, baseUrl):
        printDBG("parserKABABLIMA baseUrl[%s]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        printDBG(data)
        hlsUrl = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
        if hlsUrl != '':
            return getDirectM3U8Playlist(hlsUrl, checkContent=True)
        return False
        
    def parserUSTREAMIXCOM(self, baseUrl):
        printDBG("parserUSTREAMIXCOM baseUrl[%s]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        val = int(self.cm.ph.getSearchGroups(data, ' \- (\d+)')[0])
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '= [', ']')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '"', '"')
        text = ''
        numObj = re.compile('(\d+)')
        for value in data:
            value = base64.b64decode(value)
            text += chr(int(numObj.search(value).group(1)) - val)
        
        statsUrl = self.cm.ph.getSearchGroups(text, '''src=["'](https?://[^'^"]*?stats\.php[^'^"]*?)["']''', ignoreCase=True)[0] 
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(statsUrl, {'header':HTTP_HEADER})
        if not sts: return False
        token = self.cm.ph.getAllItemsBeetwenMarkers(data, '"', '"', False)[-1]
        
        printDBG("token||||||||||||||||| " + token)
        
        hlsUrl = self.cm.ph.getSearchGroups(text, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
        printDBG("hlsUrl||||||||||||||||| " + hlsUrl)
        if hlsUrl != '':
            if hlsUrl.endswith('='): hlsUrl += token
            hlsUrl = strwithmeta(hlsUrl, {'Referer':baseUrl})
            return getDirectM3U8Playlist(hlsUrl, checkContent=True)
        return False
        
    def parserPXSTREAMTV(self, baseUrl):
        printDBG("parserPXSTREAMTV baseUrl[%s]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        printDBG(data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """%s:[^'^"]*?['"]([^'^"]+?)['"]""" % name)[0] 
        swfUrl = "http://pxstream.tv/player510.swf"
        url    = _getParam('streamer')
        file   = _getParam('file')
        if file == '':
            hlsUrl = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
            if self.cm.isValidUrl(hlsUrl):
                tmp = getDirectM3U8Playlist(hlsUrl, checkContent=True)
                if len(tmp): return tmp
        if file.split('?')[0].endswith('.m3u8'):
            return getDirectM3U8Playlist(file)
        elif '' != file and '' != url:
            url += ' playpath=%s swfUrl=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
    
    def parserCOOLCASTEU(self, baseUrl):
        printDBG("parserCOOLCASTEU baseUrl[%s]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        printDBG(data)
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]%s['"]:[^'^"]*?['"]([^'^"]+?)['"]""" % name)[0] 
        swfUrl = "http://coolcast.eu/file/1444766476/player.swf"
        url    = _getParam('streamer')
        file   = _getParam('file')
        if '' != file and '' != url:
            url += ' playpath=%s swfVfy=%s pageUrl=%s live=1 ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
    
    def parserFILENUKE(self, baseUrl):
        printDBG("parserFILENUKE baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0' }
        
        COOKIE_FILE = GetCookieDir('filenuke.com')
        params_s  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params_l  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True} 
        
        sts, data = self.cm.getPage(baseUrl, params_s)
        if not sts: return False
        redirectUrl = self.cm.meta['url']
        
        if 'method_free' in data:
            sts, data = self.cm.getPage(baseUrl, params_l, {'method_free':'Free'})
            if not sts: return False
            
        if 'id="go-next"' in data:
            url = self.cm.ph.getSearchGroups(data, '<a[^>]+?id="go-next"[^>]+?href="([^"]+?)"')[0]
            baseUrl = self.cm.ph.getSearchGroups(redirectUrl, '(https?://[^/]+?)/')[0]
            if url.startswith('/'): url = baseUrl + url
            sts, data = self.cm.getPage(url, params_l)
            if not sts: return False
            
        data = self.cm.ph.getDataBeetwenMarkers(data, 'jwplayer', 'play(')[1]
        printDBG(data)
            
        videoMarker = self.cm.ph.getSearchGroups(data, r"""['"]?file['"]?[ ]*?:[ ]*?([^ ^,]+?),""")[0]
        videoUrl    = self.cm.ph.getSearchGroups(data, r"""['"]?%s['"]?[ ]*?\=[ ]*?['"](http[^'^"]+?)["']""" % videoMarker)[0]
        
        printDBG("parserFILENUKE videoMarker[%s] videoUrl[%s]" % (videoMarker, videoUrl))
        if '' == videoUrl: return False
        videoUrl = urlparser.decorateUrl(videoUrl, {'User-Agent':'Mozilla/5.0', 'Referer':'http://filenuke.com/a/jwplayer/jwplayer.flash.swf'})
        return videoUrl
        
    def parserTHEFILEME(self, baseUrl):
        printDBG("parserTHEFILEME baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; androVM for VirtualBox ('Tablet' version with phone caps) Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Safari/534.30" }
        
        COOKIE_FILE = GetCookieDir('thefile.me')
        params_s  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params_l  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True} 
        
        sts, data = self.cm.getPage(baseUrl, params_s)
        if not sts: return False
        
        data = CParsingHelper.getDataBeetwenMarkers(data, '<div class="main-wrap">', '</script>', False)[1]
        videoUrl = self.cm.ph.getSearchGroups(data, r"""['"]?%s['"]?[ ]*?\=[ ]*?['"](http[^'^"]+?)["']""" % 'href')[0]
        seconds = self.cm.ph.getSearchGroups(data, r"""seconds[ ]*?\=[ ]*?([^;^ ]+?);""")[0]
        printDBG("parserFILENUKE seconds[%s] videoUrl[%s]" % (seconds, videoUrl))
        seconds = int(seconds)
        
        GetIPTVSleep().Sleep(seconds+1) 
        
        params_l['header']['Referer'] = videoUrl
        sts, data = self.cm.getPage(videoUrl, params_l)
        if not sts: return False
        
        data = CParsingHelper.getDataBeetwenMarkers(data, 'setup({', '}', False)[1]
        videoUrl = self.cm.ph.getSearchGroups(data, r"""['"]?file['"]?[ ]*?\:[ ]*?['"]([^"^']+?)['"]""")[0]
        if videoUrl.startswith('http'): return urlparser.decorateUrl(videoUrl)
        return False
        
    def parserCLOUDTIME(self, baseUrl):
        printDBG("parserCLOUDTIME baseUrl[%s]" % baseUrl)
        try:
            url = self._parserUNIVERSAL_B(baseUrl)
            if len(url): return url
        except Exception:
            printExc()
        
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0" }
        
        COOKIE_FILE = GetCookieDir('cloudtime.to')
        params_s  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        params_l  = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True} 
        
        if 'embed' not in baseUrl:
            vidId = self.cm.ph.getSearchGroups(baseUrl + '/', '/video/([^/]+?)/')[0]
            if '' == vidId: vidId = self.cm.ph.getSearchGroups(baseUrl + '&', '[\?&]v=([^&]+?)&')[0]
            baseUrl = 'http://www.cloudtime.to/embed.php?v=' + vidId
        
        sts, data = self.cm.getPage(baseUrl, params_s)
        if not sts: return False
            
        tokenUrl = self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?/api/toker[^'^"]+?)['"]''')[0]
        if tokenUrl.startswith('/'):
            tokenUrl = 'http://www.cloudtime.to' + tokenUrl
        
        HTTP_HEADER['Referer'] = baseUrl
        sts, token = self.cm.getPage(tokenUrl, {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True} )
        if not sts: return False
        token = self.cm.ph.getDataBeetwenMarkers(token, '=', ';', False)[1].strip()
         
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'load_cookie':True, 'save_cookie':True})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=['"]([^'^"]+?)['"][^>]+?video/mp4''')[0]
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        return False
        
    def parserNOSVIDEO(self, baseUrl):
        printDBG("parserNOSVIDEO baseUrl[%s]" % baseUrl)
        # code from https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/nosvideo.py
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10", 'Referer':baseUrl }

        if 'embed' not in baseUrl:
            videoID = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
            videoUrl = 'http://nosvideo.com/embed/' + videoID
        else:
            videoUrl = baseUrl
        sts, data = self.cm.getPage(videoUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, ">eval(", '</script>', False)[1]
        mark1 = "}("
        idx1 = data.find(mark1)
        if -1 == idx1: return False
        idx1 += len(mark1)
        data = unpackJS(data[idx1:-3], VIDUPME_decryptPlayerParams)
        
        videoUrl = self.cm.ph.getSearchGroups(data, r"""['"]?playlist['"]?[ ]*?\:[ ]*?['"]([^"^']+?)['"]""")[0]
        sts, data = self.cm.getPage(videoUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        printDBG(data)
        
        videoUrl = self.cm.ph.getDataBeetwenMarkers(data, '<file>', '</file>', False)[1]
        if not self.cm.isValidUrl(videoUrl):
            videoUrl = self.cm.ph.getSearchGroups(data, 'file="(http[^"]+?)"')[0]

        return videoUrl
        
    def parserPUTSTREAM(self, baseUrl):
        printDBG("parserPUTSTREAM baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'putstream.com')
        return self._parserUNIVERSAL_A(baseUrl, 'http://putstream.com/embed-{0}-640x400.html', _findLinks)
        
    def parserLETWATCHUS(self, baseUrl):
        printDBG("parserLETWATCHUS baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'letwatch.us')
        return self._parserUNIVERSAL_A(baseUrl, 'http://letwatch.us/embed-{0}-640x360.html', _findLinks)
        
    def parserUPLOADCCOM(self, baseUrl):
        printDBG("parserUPLOADCCOM baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://www.uploadc.com/embed-{0}.html', _findLinks)
        
    def parserMIGHTYUPLOAD(self, baseUrl):
        printDBG("parserMIGHTYUPLOAD baseUrl[%s]" % baseUrl)
        def _preProcessing(data):
            return CParsingHelper.getDataBeetwenMarkers(data, '<div id="player_code">', '</div>', False)[1]
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://www.mightyupload.com/embed-{0}-645x353.html', _findLinks, _preProcessing)
        
    def parserZALAACOM(self, baseUrl):
        printDBG("parserZALAACOM baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://www.zalaa.com/embed-{0}.html', _findLinks)
    
    def parserALLMYVIDEOS(self, baseUrl):
        printDBG("parserALLMYVIDEOS baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'allmyvideos.net')
        return self._parserUNIVERSAL_A(baseUrl, 'http://allmyvideos.net/embed-{0}.html', _findLinks)
        
    def parserRAPIDVIDEOWS(self, baseUrl):
        printDBG("parserRAPIDVIDEOWS baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://rapidvideo.ws/embed-{0}-720x420.html', _findLinks)
        
    def parserHDVIDTV(self, baseUrl):
        printDBG("parserHDVIDTV baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://hdvid.tv/{0}-950x480.html', _findLinks)
    
    def parserHDVIDTV(self, baseUrl):
        printDBG("parserHDVIDTV baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'https://vidhdthe.club/utoa28cgx5fs.html', _findLinks)
    
    def parserHDVIDTV(self, baseUrl):
        printDBG("parserHDVIDTV baseUrl[%s]" % baseUrl)
        def _findLinks(data):
            return self._findLinks2(data, baseUrl)
        return self._parserUNIVERSAL_A(baseUrl, 'http://gosafedomain.eu/{0}-950x480.html', _findLinks)

    def parserVIDME(self, baseUrl):
        printDBG("parserVIDME baseUrl[%s]" % baseUrl)
        # from: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/vidme.py
        _VALID_URL = r'https?://vid\.me/(?:e/)?(?P<id>[\da-zA-Z]{,5})(?:[^\da-zA-Z]|$)'
        mobj = re.match(_VALID_URL, baseUrl)
        id = mobj.group('id')
        sts, data = self.cm.getPage('https://api.vid.me/videoByUrl/' + id)
        if not sts: return False
        data = json_loads(data)['video']
        if 'formats' in data:
            urlTab = []
            for item in data['formats']:
                if '-clip' in item['type']: continue
                try: 
                    if item['type'] == 'dash': continue
                    elif item['type'] == 'hls':
                        continue
                        hlsTab = getDirectM3U8Playlist(item['uri'], False)
                        urlTab.extend(hlsTab)
                    else:
                        urlTab.append({'name':item['type'], 'url':item['uri']})
                except Exception: pass
            return urlTab
        else:
            return urlparser().getVideoLinkExt(data['source'])
        return False
        
    def parserVEEHDCOM(self, baseUrl):
        printDBG("parserVEEHDCOM baseUrl[%s]" % baseUrl)
        COOKIE_FILE = GetCookieDir('veehdcom.cookie')
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/37.0.2062.120 Chrome/37.0.2062.120 Safari/537.36',
                       'Referer':baseUrl}
        params = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, 'playeriframe', ';', False)[1]
        url = self.cm.ph.getSearchGroups(data, '''src[ ]*?:[ ]*?['"]([^"^']+?)['"]''')[0]
        if not url.startswith('http'):
            if not url.startswith('/'):
                url = '/' + url 
            url = 'http://veehd.com' + url 
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        vidUrl = self.cm.ph.getSearchGroups(data, '''type=['"]video[^"^']*?["'][^>]+?src=["']([^'^"]+?)['"]''')[0]
        if vidUrl.startswith('http'):
            return vidUrl
        return False
        
    def parserSHAREREPOCOM(self, baseUrl):
        printDBG("parserSHAREREPOCOM baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        tab = []
        tmp = self._findLinks(data, m1='setup', m2='</script>')
        for item in tmp:
            item['url'] = urlparser.decorateUrl(item['url'], {'Referer':baseUrl, 'User-Agent':'Mozilla/5.0'})
            tab.append(item)
        return tab
        
    def parserEASYVIDEOME(self, baseUrl):
        printDBG("parserEASYVIDEOME baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0'}
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        subTracks = []
        videoUrls = []
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<div id="flowplayer">', '</script>', False)[1]
        videoUrls = self._findLinks(tmp, serverName='playlist', linkMarker=r'''['"]?url['"]?[ ]*:[ ]*['"](http[^"^']+)['"][,}]''', m1='playlist', m2=']')
        try:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '"storage":', ']', False)[1]
            printDBG("|||" + tmp)
            tmp = json_loads(tmp + ']')
            for item in tmp:
                videoUrls.append({'name':str(item['quality']), 'url':item['link']})
                if self.cm.isValidUrl(item.get('sub', '')):
                    url  = item['sub']
                    type = url.split('.')[-1]
                    subTracks.append({'title':_('default'), 'url':url, 'lang':'unk', 'format':type})
        except Exception:
            printExc()
        
        video_url = self.cm.ph.getSearchGroups(data, '_url = "(http[^"]+?)"')[0]
        if '' != video_url: 
            video_url = urllib.unquote(video_url)
            videoUrls.insert(0, {'name':'main', 'url':video_url})
            
        if len(subTracks):
            for idx in range(len(videoUrls)):
                videoUrls[idx]['url'] = strwithmeta(videoUrls[idx]['url'], {'external_sub_tracks':subTracks})
        
        return videoUrls
        
    def parserUPTOSTREAMCOM(self, baseUrl):
        printDBG("parserUPTOSTREAMCOM baseUrl[%s]" % baseUrl)
        #example https://uptostream.com/iframe/kfaru03fqthy
        #        https://uptostream.com/xjo9gegjzf8c
        #        https://uptostream.com/api/streaming/source/get?token=null&file_code=zxfcxyy8in9e
        
        
        urlTab = []
        m = re.search("(iframe/|file_code=)(?P<id>.*)$", baseUrl)
        
        if m:
            video_id = m.groupdict().get('id','')
        else:
            video_id = baseUrl.split("/")[-1] 
            
        if video_id:
            url2 = "https://uptostream.com/api/streaming/source/get?token=null&file_code=%s" % video_id
            
            sts, data = self.cm.getPage(url2)
            
            if sts:
                #printDBG(data)
                response=json_loads(data)
                if response.get("message",'') == "Success":
                    code = response["data"]["sources"]
                    
                    code = code.replace(";let",";var")
                    code = code + "\n console.log(sources);"
                    printDBG("---------- javascript code -----------")
                    printDBG(code)
                    
                    ret = js_execute( code )
                    if ret['sts'] and 0 == ret['code']:
                        response = demjson_loads(ret['data'])

                        #printDBG(str(response))
                        
                        for u in response:
                            printDBG(u)

                            url = u.get('src','')
                    
                            if url:
                                if 'label' in u:
                                    title = u.get('label', '')
                                else:
                                    title=''
                        
                                if url[-4:] == 'm3u8':
                                    urlTab.extend(getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
                                else:
                                    urlTab.append({'name': title, 'url':url})
  
        return urlTab
        
    def parserVIMEOCOM(self, baseUrl):
        printDBG("parserVIMEOCOM baseUrl[%s]" % baseUrl)
        
        if 'player' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([0-9]+?)[/.]')[0]
            if video_id != '': 
                url = 'https://player.vimeo.com/video/' + video_id
            else:
                sts, data = self.cm.getPage(baseUrl)
                if not sts: return False
                url = self.cm.ph.getSearchGroups(data, '''['"]embedUrl['"]\s*?:\s*?['"]([^'^"]+?)['"]''')[0]
        else:
            url = baseUrl
        
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        if 'Referer' in baseUrl.meta: HTTP_HEADER['Referer'] = baseUrl.meta['Referer']
        
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return False

        urlTab = []
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'progressive', ']', False)[1]
        tmp = tmp.split('}')
        printDBG(tmp)
        for item in tmp:
            if 'video/mp4' not in item: continue
            quality = self.cm.ph.getSearchGroups(item, '''quality['"]?:['"]([^"^']+?)['"]''')[0]
            url  = self.cm.ph.getSearchGroups(item, '''url['"]?:['"]([^"^']+?)['"]''')[0]
            if url.startswith('http'):
                urlTab.append({'name':'vimeo.com {0}'.format(quality), 'url':url})
                
        hlsUrl = self.cm.ph.getSearchGroups(data, '"hls"[^}]+?"url"\:"([^"]+?)"')[0]
        tab = getDirectM3U8Playlist(hlsUrl)
        urlTab.extend(tab)
        
        return urlTab
        
    def parserDARKOMPLAYER(self, baseUrl):
        printDBG("parserDARKOMPLAYER baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        COOKIE_FILE = GetCookieDir('darkomplayer.cookie')
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        
        rm(COOKIE_FILE)
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        
        cUrl = self.cm.getBaseUrl(data.meta['url'])
        
        jscode = [self.jscode['jwplayer']]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script', '</script>')
        for item in tmp:
            if 'src=' in item:
                scriptUrl = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
                if scriptUrl != '' and 'jwplayer.js' not in scriptUrl:
                    scriptUrl = self.cm.getFullUrl(scriptUrl, self.cm.getBaseUrl(data.meta['url']))
                    sts, scriptData = self.cm.getPage(scriptUrl, urlParams)
                    if not sts: continue
                    jscode.append(scriptData)
            else:
                jscode.append(self.cm.ph.getDataBeetwenNodes(item, ('<script', '>'), ('</script', '>'), False)[1])
        
        urlTab = []
        ret = js_execute( '\n'.join(jscode) )
        if ret['sts'] and 0 == ret['code']:
            data = ret['data']
            data = json_loads(data)
            PHPSESSID = self.cm.getCookieItem(COOKIE_FILE, 'PHPSESSID')
            for item in data['sources']:
                url = item['file']
                type  = item['type'].lower()
                label = item['label']
                if 'mp4' not in type: continue
                if url == '': continue
                url = urlparser.decorateUrl(self.cm.getFullUrl(url, cUrl), {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent'], 'Range':'bytes=0-', 'Cookie':'PHPSESSID=%s' % PHPSESSID})
                urlTab.append({'name':'darkomplayer {0}'.format(label), 'url':url})
        return urlTab
        
    def parserJACVIDEOCOM(self, baseUrl):
        printDBG("parserJACVIDEOCOM baseUrl[%s]" % baseUrl)
        
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('jacvideocom.cookie')}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'jacvideosys(', ');', False)[1]
        tmp = data.split(',')[-1]
        link = self.cm.ph.getSearchGroups(tmp, '''link['"]?:['"]([^"^']+?)['"]''')[0]
        if link != '':
            post_data = {'link':link}
            sts, data = self.cm.getPage('http://www.jacvideo.com/embed/plugins/jacvideosys.php', params, post_data)
            if not sts: return False
            try:
                data = json_loads(data)
                if 'error' in data:
                    SetIPTVPlayerLastHostError(data['error'])
                linksTab = []
                for item in data['link']:
                    if item['type'] != 'mp4': continue
                    url  = item['link']
                    name = item['label']
                    url = urlparser.decorateUrl(url, {'iptv_livestream':False, 'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':baseUrl})
                    linksTab.append({'name':name, 'url':url})
                return linksTab
            except Exception:
                printExc()
        
        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=["'](http[^"^']+?)["']''', 1, True)[0]
        try:
            linksTab = urlparser().getVideoLinkExt(url)
            if len(linksTab): return linksTab
        except Exception:
            printExc()
            
        urlTab = self._getSources(data)
        if len(urlTab): return urlTab
        return self._findLinks(data, contain='mp4')
        
    def parserSPEEDVIDEONET(self, baseUrl):
        printDBG("parserSPEEDVIDEONET baseUrl[%s]" % baseUrl)
        
        if 'embed' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{12})[/.]')[0]
            url = 'http://speedvideo.net/embed-{0}.html'.format(video_id)
        else:
            url = baseUrl
        
        HTTP_HEADER= {'User-Agent':"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36"}
        #defaultParams = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('speedvideo.cookie')}
        defaultParams = {'header': HTTP_HEADER}
        
        sts, data = self.cm.getPage(url, defaultParams)
        if not sts: return False
        
        printDBG(data)
        
        urlTab = []
        tmp = []
        for item in [('linkfile', 'normal'), ('linkfileBackupLq', 'low'), ('linkfileBackupH', 'high'), ('linkfileBackup', 'backup'), ('linkfileBackupN', 'backup N')]:
            try:
                vidUrl = self.cm.ph.getSearchGroups(data, 'var\s+?' + item[0] + '''\s*?=\s*?['"]([^"^']+?)['"]''')[0]
                if vidUrl not in tmp and self.cm.isValidUrl(vidUrl):
                    tmp.append(vidUrl)
                    if vidUrl.split('?')[0].endswith('.m3u8'):
                        tab = getDirectM3U8Playlist(vidUrl)
                        urlTab.extend(tab)
                    else:
                        urlTab.append({'name':item[1], 'url':vidUrl})
            except Exception:
                continue
        return urlTab
        
    def parserXVIDSTAGECOM(self, baseUrl):
        printDBG("parserXVIDSTAGECOM baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        def _first_of_each(*sequences):
            return (next((x for x in sequence if x), '') for sequence in sequences)
        
        def _url_path_join(*parts):
            """Normalize url parts and join them with a slash."""
            schemes, netlocs, paths, queries, fragments = zip(*(urlsplit(part) for part in parts))
            scheme, netloc, query, fragment = _first_of_each(schemes, netlocs, queries, fragments)
            path = '/'.join(x.strip('/') for x in paths if x)
            return urlunsplit((scheme, netloc, path, query, fragment))
        
        sts, data = self.cm.ph.getDataBeetwenMarkers(data.split('site_logo')[-1], '<Form method="POST"', '</Form>', True)
        action = self.cm.ph.getSearchGroups(data, "action='([^']+?)'")[0]
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        
        try:
            sleep_time = int(self.cm.ph.getSearchGroups(data, '>([0-9])</span> seconds<')[0]) 
            GetIPTVSleep().Sleep(sleep_time)
        except Exception:
            printExc()
        if {} == post_data:
            post_data = None
        if action.startswith('/'):
            url = _url_path_join(url[:url.rfind('/')+1], action[1:])
        else: url = action
        if url == '':
            url = baseUrl
        sts, data = self.cm.getPage(url, {}, post_data)
        if not sts: return False
        
        try:
            tmp = CParsingHelper.getDataBeetwenMarkers(data.split('player_code')[-1], ">eval(", '</script>')[1]
            tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams)
            data = tmp + data
        except Exception:
            pass
        
        videoUrl = self.cm.ph.getSearchGroups(data, '<[^>]+?type="video[^>]+?src="([^"]+?)"')[0]
        if videoUrl.startswith('http'):
            return videoUrl
        return False
        
    def parserSTREAMPLAY(self, videoUrl):
        printDBG("parserSTREAMPLAY baseUrl[%s]" % videoUrl)

        HEADER = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36', 'Accept':'*/*', 'Accept-Encoding':'gzip, deflate'}
        httpParams = {'header': HEADER, 'use_cookie':True, 'load_cookie': True, 'save_cookie':True, 'cookiefile': GetCookieDir('streamplay.cookie')}
        
        #check this format https://streamplay.to/embed-ihml2wglkypo-640x360.html
        video_id = re.findall("[a-z0-9]{11,}", videoUrl)
        if video_id:
            video_id = video_id[0] 
            baseUrl = urlparser.getDomain(videoUrl, False)
            videoUrl = baseUrl + video_id
        else:
            printDBG("Check format of url : %s" % videoUrl)
            video_id = videoUrl.split('/')[-1]

        video_id = videoUrl.split('/')[-1]
        linksTab = []
        
        sts, data = self.cm.getPage(videoUrl, httpParams)
        if not sts: 
            return False
        
        baseUrl = urlparser.getDomain(self.cm.meta['url'], False)
        
        if 'sitekey' in data:
            # need to solve a reCaptcha
            #sitekey: '6LfsXx4TAAAAAG7fRIpL2LpS_NLxj1HBlotEDhT7'
            key = re.findall("sitekey:\s'([^']+?)'", data)
            if key:
                key = key[0]
                printDBG("sitekey = %s" % key)
                (token, errorMsgTab) = CaptchaHelper().processCaptcha(key, baseUrl)
                
                if token:
                    printDBG(token)
                    
                    #<form method="POST" action='' id="d0Form">
                    form_html = self.cm.ph.getDataBeetwenMarkers(data, ('<form','>','POST'), '</form>')[1]
                    inputs = self.cm.ph.getAllItemsBeetwenMarkers(form_html, '<input','>', False, caseSensitive=False)
                    post_data = {}
                    
                    for item in inputs:
                        name  = self.cm.ph.getSearchGroups(item, '''name=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
                        value = self.cm.ph.getSearchGroups(item, '''value=['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
                        if name:
                            post_data[name] = value
                        
                    post_data['g-recaptcha-response'] = token
                    post_data['token'] = token
                    
                    printDBG(json_dumps(post_data))
                    
                    sts, data = self.cm.getPage(videoUrl, httpParams, post_data)
 
                    if not sts:
                        return[]
                    
                    #printDBG("-------------- after recaptcha ---------------")
                    #printDBG(data)
                    #printDBG("----------------------------------------------")
                        
        
        scripts = re.findall("<script type=[\"']text/javascript[\"']>(eval.*?)</script>", data, re.S)
        
        if scripts:
            for script in scripts:
                printDBG("----------- pack -----------------")
                printDBG(script)
                
                script = script + "\n"
                # mods
                script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                script = script.replace("return p}(", "print(p)}\n\npippo(")
                script = script.replace("))\n",");\n")

                # duktape
                ret = js_execute( script )
                decoded = ret['data']
                printDBG('------------------------------')
                printDBG(decoded)
                printDBG('------------------------------')

                sources = re.findall("src:\s?[\"']([^\"^']+.m3u8)[\"']", decoded)  
                sources.extend(re.findall("file:\s?[\"']([^\"^']+.m3u8)[\"']", decoded))  
                sources.extend(re.findall("src:\s?[\"']([^\"^']+.mp4)[\"']", decoded))
                sources.extend(re.findall("file:\s?[\"']([^\"^']+.mp4)[\"']", decoded))
                
                for link_url in sources:
                    if  self.cm.isValidUrl(link_url):
                        if 'spcdn' in link_url:
                            # modify url
                            link_url = powvideo_swapUrl(data, link_url)
                        
                        link_url = urlparser.decorateUrl(link_url, {'Referer': videoUrl})
                        if 'm3u8' in link_url:
                            params = getDirectM3U8Playlist(link_url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                            printDBG(str(params))    
                            linksTab.extend(params)
                        else:
                            params = {'name': 'link' , 'url': link_url}
                            printDBG(str(params))
                            linksTab.append(params)
                
        if linksTab:
            return linksTab

        # check for error messages. Example
        # <div id="over_player_msg">Video is processing now.<br>Conversion stage: <span id='enc_pp'>...</span></div>
        msg =  clean_html(self.cm.ph.getDataBeetwenMarkers(data, ('<div','>','over_player_msg') , ('</div','>'), False)[1])
        if msg: 
            SetIPTVPlayerLastHostError(error)
            return linksTab
        
        if '/embed/' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(videoUrl+'/', '/([A-Za-z0-9]{16})/')[0]
            url = 'http://www.streamplay.cc/embed/{0}'.format(video_id)
        else:
            url = baseUrl
        post_data = None

        sts, data = self.cm.getPage(url, httpParams, post_data)
        if not sts: 
            return False
        
        data = CParsingHelper.getDataBeetwenMarkers(data, 'id="playerStream"', '</a>', False)[1]
        videoUrl = self.cm.ph.getSearchGroups(data, 'href="(http[^"]+?)"')[0]
        if '' != videoUrl: 
            return videoUrl
        
        return False
        
    def parserYOURVIDEOHOST(self, baseUrl):
        printDBG("parserYOURVIDEOHOST baseUrl[%s]" % baseUrl)
        video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '[^A-Za-z0-9]([A-Za-z0-9]{12})[^A-Za-z0-9]')[0]
        url = 'http://yourvideohost.com/{0}'.format(video_id)
        return self.__parseJWPLAYER_A(url, 'yourvideohost.com')
        
    def parserVIDGGTO(self, baseUrl):
        printDBG("parserVIDGGTO baseUrl[%s]" % baseUrl)
        return self._parserUNIVERSAL_B(baseUrl)
        
    def parserTINYCC(self, baseUrl):
        printDBG("parserTINYCC baseUrl[%s]" % baseUrl)
        self.cm.getPage(baseUrl, {'max_data_size':0})
        redirectUrl = self.cm.meta['url']
        if baseUrl != redirectUrl:
            return urlparser().getVideoLinkExt(redirectUrl)
        return False
    
    def parserWHOLECLOUD(self, baseUrl):
        printDBG("parserWHOLECLOUD baseUrl[%s]" % baseUrl)
        
        tab = self._parserUNIVERSAL_B(baseUrl)
        if len(tab): return tab
        
        params = {'header': {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:17.0) Gecko/20100101 Firefox/17.0'}, 'max_data_size':0}
        self.cm.getPage(baseUrl, params)
        url = self.cm.meta['url']
        
        #url = baseUrl.replace('movshare.net', 'wholecloud.net')
        mobj = re.search(r'/(?:file|video)/(?P<id>[a-z\d]{13})', baseUrl)
        video_id = mobj.group('id')
        onlyDomain = urlparser.getDomain(url, True) 
        domain = urlparser.getDomain(url, False) 
        url = domain + 'video/' + video_id

        params.pop('max_data_size', None)
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        try:
            tmp = self.cm.ph.getDataBeetwenMarkers(data, '<form method="post" action="">', '</form>', False, False)[1]
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            tmp = dict(re.findall(r'<button[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            post_data.update(tmp)
        except Exception:
            printExc()
        
        if post_data != {}:
            params['header'].update({'Content-Type':'application/x-www-form-urlencoded','Referer':url})
            sts, data = self.cm.getPage(url, params, post_data)
            if not sts: return False
        
        videoTab = []
        url = self.cm.ph.getSearchGroups(data, '"([^"]*?/download[^"]+?)"')[0]
        if url.startswith('/'):
            url = domain + url[1:]
        if self.cm.isValidUrl(url):
            url = strwithmeta(url, {'User-Agent':params['header']})
            videoTab.append({'name':'[Download] %s' % onlyDomain, 'url':url})
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'player.ready', '}')[1]
        url = self.cm.ph.getSearchGroups(tmp, '''src['"\s]*?:\s['"]([^'^"]+?)['"]''')[0]
        if url.startswith('/'):
            url = domain + url[1:]
        if self.cm.isValidUrl(url) and url.split('?')[0].endswith('.mpd'):
            url = strwithmeta(url, {'User-Agent':params['header']})
            videoTab.extend(getMPDLinksWithMeta(url, False))
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>', False)
        links = []
        for item in tmp:
            if 'video/' not in item: continue
            url = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            type = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0] 
            if url.startswith('/'):
                url = domain + url[1:]
            if self.cm.isValidUrl(url):
                if url in links: continue
                links.append(url)
                url = strwithmeta(url, {'User-Agent':params['header']})
                videoTab.append({'name':'[%s] %s' % (type, onlyDomain), 'url':url})
                
        printDBG(data)
        return videoTab
        
    def parserSTREAM4KTO(self, baseUrl):
        printDBG("parserSTREAM4KTO baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        mainData = data
        
        data = self.cm.ph.getSearchGroups(data, "drdX_fx\('([^']+?)'\)")[0]
        data = drdX_fx( data )
        data = self.cm.ph.getSearchGroups(data, 'proxy.link=linkcdn%2A([^"]+?)"')[0]
        printDBG(data)
        if data != '':
            x = gledajfilmDecrypter(198,128)
            Key = "VERTR05uak80NEpDajY1ejJjSjY="
            data = x.decrypt(data, Key.decode('base64', 'strict'), "ECB")
            if '' != data:
                return urlparser().getVideoLinkExt(data)
            
        data = unpackJSPlayerParams(mainData, SAWLIVETV_decryptPlayerParams, 0)
        printDBG(">>>>>>>>>>>>>>>>>>>" + data)
        return self._findLinks(data)
        
    def parserONETTV(self, baseUrl):
        printDBG("parserONETTV baseUrl[%r]" % baseUrl )
        
        videoUrls = []
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return videoUrls
        ckmId = self.cm.ph.getSearchGroups(data, 'data-params-mvp="([^"]+?)"')[0]
        if '' == ckmId: ckmId = self.cm.ph.getSearchGroups(data, 'id="mvp:([^"]+?)"')[0]
        if '' == ckmId: return videoUrls
        
        tm = str(int(time.time() * 1000))
        jQ = str(randrange(562674473039806,962674473039806))
        authKey = 'FDF9406DE81BE0B573142F380CFA6043'
        hostName = urlparser().getHostName(baseUrl)
        contentUrl = 'http://qi.ckm.onetapi.pl/?callback=jQuery183040'+ jQ + '_' + tm + '&body%5Bid%5D=' + authKey + '&body%5Bjsonrpc%5D=2.0&body%5Bmethod%5D=get_asset_detail&body%5Bparams%5D%5BID_Publikacji%5D=' + ckmId + '&body%5Bparams%5D%5BService%5D={0}&content-type=application%2Fjsonp&x-onet-app=player.front.onetapi.pl&_='.format(hostName) + tm
        sts, data = self.cm.getPage(contentUrl)
        if sts:
            try:
                printDBG(data)
                data = json_loads(data[data.find("(")+1:-2])
                data = data['result']['0']['formats']['wideo']
                for type in data:
                    for vidItem in data[type]:
                        if None != vidItem.get('drm_key', None): continue
                        vidUrl = vidItem.get('url', '')
                        if '' == vidUrl: continue
                        if 'hls' == type:
                            tmpTab = getDirectM3U8Playlist(vidUrl)
                            for tmp in tmpTab:
                                videoUrls.append({'name':'ONET type:%s :%s' % (type, tmp.get('bitrate', '0')), 'url':tmp['url']})
                        elif None != vidItem.get('video_bitrate', None):
                            videoUrls.append({'name':'ONET type:%s :%s' % (type, vidItem.get('video_bitrate', '0')), 'url':vidUrl})
                        elif None != vidItem.get('audio_bitrate', None):
                            videoUrls.append({'name':'ONET type:%s :%s' % (type, vidItem.get('audio_bitrate', '0')), 'url':vidUrl})
            except Exception:
                printExc()
        return videoUrls
        
    def parserBYETVORG(self, baseUrl):
        printDBG("parserBYETVORG baseUrl[%r]" % baseUrl )
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl.meta.get('Referer', baseUrl) }
        file = self.cm.ph.getSearchGroups(baseUrl, "file=([0-9]+?)[^0-9]")[0]
        if '' == file: file = self.cm.ph.getSearchGroups(baseUrl, "a=([0-9]+?)[^0-9]")[0]
        linkUrl = "http://www.byetv.org/embed.php?a={0}&id=&width=710&height=460&autostart=true&strech=".format(file)
        
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False 
        
        jscode = []
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if '.m3u8' in item:
                jscode.append(item)
        
        streamsTab = []
        streamUrl = ''
        jscode = base64.b64decode('''dmFyIGRvY3VtZW50PXt9LHdpbmRvdz10aGlzLGVsZW1lbnQ9ZnVuY3Rpb24obil7dGhpcy5fbmFtZT1uLHRoaXMuc2V0QXR0cmlidXRlPWZ1bmN0aW9uKCl7fSx0aGlzLmF0dGFjaFRvPWZ1bmN0aW9uKCl7fX0sJD1mdW5jdGlvbihuKXtyZXR1cm4gbmV3IGVsZW1lbnQobil9O0NsYXBwcj17fSxDbGFwcHIuUGxheWVyPWZ1bmN0aW9uKG4pe3JldHVybiBwcmludChKU09OLnN0cmluZ2lmeShuKSksbmV3IGVsZW1lbnQoInBsYXllciIpfSxkb2N1bWVudC5nZXRFbGVtZW50QnlJZD1mdW5jdGlvbihuKXtyZXR1cm4gbmV3IGVsZW1lbnQobil9Ow==''') + '\n'.join(jscode)
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            streamUrl = json_loads(ret['data'])['source']
        return getDirectM3U8Playlist(streamUrl, checkContent=False)
        
    def parserPUTLIVEIN(self, baseUrl):
        printDBG("paserPUTLIVEIN baseUrl[%r]" % baseUrl )
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl.meta.get('Referer', baseUrl) }
        file = self.cm.ph.getSearchGroups(baseUrl, "file=([0-9]+?)[^0-9]")[0]
        if '' == file: file = self.cm.ph.getSearchGroups(baseUrl+'/', "/e/([^/]+?)/")[0]
        
        linkUrl = "http://www.putlive.in/e/{0}".format(file)
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False 
        #printDBG("=======================================================")
        #printDBG(data)
        #printDBG("=======================================================")
        token =  self.cm.ph.getSearchGroups(data, "'key' : '([^']+?)'")[0]
        if token != "": token = ' token=%s ' % token
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, 'unescape("', '")', False)
        if not sts: return False 
        data = urllib.unquote(data)
        #printDBG(data)
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, "%s=([^&]+?)&" % name)[0] 
        
        swfUrl  = "http://putlive.in/player59.swf"
        streamer = _getParam('streamer')
        file     = _getParam('file')
        provider = _getParam('provider')
        rtmpUrl  = provider + streamer[streamer.find(':'):]
        if '' != file and '' != rtmpUrl:
            rtmpUrl += ' playpath=%s swfUrl=%s %s pageUrl=%s live=1 ' % (file, swfUrl, token, linkUrl)
            printDBG(rtmpUrl)
            return rtmpUrl
        return False
        
    def parserSTREAMLIVETO(self, baseUrl):
        printDBG("parserSTREAMLIVETO baseUrl[%r]" % baseUrl )
        #COOKIE_FILE = GetCookieDir('rocketmediaworld.com.cookie')
        #rm(COOKIE_FILE)
        COOKIE_FILE = GetCookieDir('streamliveto.cookie')
        
        HTTP_HEADER= {'User-Agent':"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0"}
        defaultParams = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        
        if True:
            tmp = InternalCipher(unhexlify('31f2d1daa8ffc1d0a02a7da8c325c9e66ba24e5684091e5a643798031da9d4217eabe17d11aa69b5d6b415e11536ae203e986c79566b7606153582e098283c9df81527340cbe1f2f1c99a9e1fc4db2950c3dde0d26dcd9d5c8a3d39829e7bc75'), False).split('|', 1)
            HTTP_HEADER['User-Agent'] = tmp[1]
            baseDomain = tmp[0]
            try:
                url = baseDomain + 'login'
                login  = config.plugins.iptvplayer.streamliveto_login.value.strip()
                passwd = config.plugins.iptvplayer.streamliveto_password.value.strip()
                if '' not in [login, passwd]:
                    sts, data = self.cm.getPage(url, defaultParams)
                    if sts:
                        HTTP_HEADER['Referer'] = url
                        sts, data = self.cm.getPage(baseDomain + 'login.php', defaultParams, {'username':login, 'password':passwd, 'accessed_by':'web', 'submit':'Login'})
            except Exception:
                printExc()
            #----------------------------------------
            params = dict(defaultParams)
            obj = urlparse(baseUrl)
            videoUrl = baseDomain[:-1] + obj.path #.replace('/info/', '/view/')
            if obj.query != '': videoUrl += '?' + obj.query
        else:
            params = dict(defaultParams)
            videoUrl = baseUrl
        
        HTTP_HEADER = dict(HTTP_HEADER)
        HTTP_HEADER['Referer'] = videoUrl
        params.update({'header':{'header':HTTP_HEADER}})
        sts, data = self.cm.getPage(videoUrl.replace('/info/', '/view/'), params)
        if not sts: return False 
        
        associativeArray = ['var associativeArray = {};']
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<span', '</span>')
        for item in tmp:
            if 'display:none' not in item: continue
            id = self.cm.ph.getSearchGroups(item, '''id\s*=['"]?([^'^"^>]+?)['">]''')[0].strip()
            if id == '': continue
            value = clean_html(item).strip()
            associativeArray.append('associativeArray["%s"] = "%s";' % (id, value))
        
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'sources' in item:
                tmp = item
                break
        tmp = str(tmp)
        printDBG(">>>>\n%s\n<<<<" % tmp)
        
        jscode = base64.b64decode('''dmFyIGRvY3VtZW50ID0ge307DQp2YXIgd2luZG93ID0gdGhpczsNCg0KJXMNCg0KdmFyIGVsZW1lbnQgPSBmdW5jdGlvbiAoaW5uZXJIVE1MKQ0Kew0KICAgIHRoaXMuX2lubmVySFRNTCA9IGlubmVySFRNTDsNCiAgICANCiAgICBPYmplY3QuZGVmaW5lUHJvcGVydHkodGhpcywgImlubmVySFRNTCIsIHsNCiAgICAgICAgZ2V0IDogZnVuY3Rpb24gKCkgew0KICAgICAgICAgICAgcmV0dXJuIHRoaXMuX2lubmVySFRNTDsNCiAgICAgICAgfSwNCiAgICAgICAgc2V0IDogZnVuY3Rpb24gKHZhbCkgew0KICAgICAgICAgICAgdGhpcy5faW5uZXJIVE1MID0gdmFsOw0KICAgICAgICB9DQogICAgfSk7DQp9Ow0KDQpkb2N1bWVudC5nZXRFbGVtZW50QnlJZCA9IGZ1bmN0aW9uKGlkKXsNCiAgICByZXR1cm4gbmV3IGVsZW1lbnQoYXNzb2NpYXRpdmVBcnJheVtpZF0pOw0KfQ0KDQpmdW5jdGlvbiBqd3BsYXllcigpIHsNCiAgICByZXR1cm4gandwbGF5ZXI7DQp9DQoNCmp3cGxheWVyLnNldHVwID0gZnVuY3Rpb24oc3JjZXMpew0KICAgIHByaW50KEpTT04uc3RyaW5naWZ5KHNyY2VzKSk7DQp9''')
        jscode = jscode % ('\n'.join(associativeArray))
        jscode += tmp
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            tmp = ret['data'].strip()
            data += tmp

        streamHlsUrls = re.compile('"((?:https?:)?//[^"]+?\.m3u8[^"]*?)"').findall(data)
        printDBG(streamHlsUrls)
        for streamHlsUrl in streamHlsUrls:
            if streamHlsUrl.startswith('//'):
                streamHlsUrl = 'http:' + streamHlsUrl
            if self.cm.isValidUrl(streamHlsUrl):
                url = streamHlsUrl
                url = urlparser.decorateUrl(url, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Referer':videoUrl, 'Origin':urlparser.getDomain(videoUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
                urlsTab = getDirectM3U8Playlist(url, checkExt=True, checkContent=True)
                if len(urlsTab):
                    return urlsTab
        return False
        #----------------------------------------
        
        
        _url_re = re.compile("http(s)?://(\w+\.)?(ilive.to|streamlive.to)/.*/(?P<channel>\d+)")
        channel = _url_re.match(baseUrl).group("channel")
        
        linksTab = []
        linkUrl ='http://www.streamlive.to/view/%s' % channel
        
        for idx in [0]:
            params = dict(defaultParams)
            params.update({'header':{'header':HTTP_HEADER}})
            sts, data = self.cm.getPage(linkUrl, params)
            if not sts: return False 
            
            if '<div id="loginbox">' in data:
                SetIPTVPlayerLastHostError(_("Only logged in user have access.\nPlease set login data in the host configuration under blue button."))
            
            if 'get_free_credits' in data:
                msg = clean_html(self.cm.ph.getDataBeetwenMarkers(data, '<div id="player_container">', '</a>')[1])
                if msg != '':
                    SetIPTVPlayerLastHostError(msg)
                
            if 0 == idx:
                linkUrl = self.cm.ph.getSearchGroups(data, 'popup\s*=\s*window\.open\(\s*"([^"]+?)"')[0]
        
        # get token
        token = CParsingHelper.getDataBeetwenMarkers(data, 'var token', '});', False)[1]
        token = self.cm.ph.getSearchGroups(token, '"([^"]+?/server.php[^"]+?)"')[0]
        if token.startswith('//'): token = 'http:' + token
        
        params = dict(defaultParams)
        HTTP_HEADER = dict(HTTP_HEADER)
        HTTP_HEADER['Referer'] = linkUrl
        params.update({'header':{'header':HTTP_HEADER}})
        sts, token = self.cm.getPage(token, params)
        if not sts: return False 
        TOKEN = json_loads(token)['token']
        if token != "": token = ' token=%s ' % TOKEN
        sts, token = self.cm.getPage('http://textuploader.com/ddf5v')
        if not sts: return False 
        token = self.cm.ph.getSearchGroups(token, 'description"\s*content="([^"]+?)"')[0]
        token = base64.b64decode(token)

        # get others params
        data = CParsingHelper.getDataBeetwenMarkers(data, '.setup(', '</script>', False)[1]
        
        def _getParam(name):
            return self.cm.ph.getSearchGroups(data, """['"]?%s['"]?[^'^"]+?['"]([^'^"]+?)['"]""" % name)[0].replace('\\/', '/')
        
        swfUrl  = "http://www.streamlive.to/player/Player.swf"
        streamer = _getParam('streamer')
        file     = _getParam('file').replace('.flv', '')
        provider = _getParam('provider')
        rtmpUrl  = provider + streamer[streamer.find(':'):]
        if rtmpUrl.startswith('video://'):
            linksTab.append({'name':'http', 'url': rtmpUrl.replace('video://', 'http://')})
        elif '' != file and '' != rtmpUrl:
            printDBG("streamer[%s]" % streamer)
            parsed_uri = urlparse( streamer )
            printDBG("parsed_uri[%r]" % [parsed_uri])
            rtmpUrl    = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
            app        = '{uri.path}'.format(uri=parsed_uri)[1:]
            if '' != parsed_uri.query: app += '?' + '{uri.query}'.format(uri=parsed_uri)
            rtmpUrl += ' playpath=%s swfUrl=%s token=%s live=1 pageUrl=%s app=%s tcUrl=%s conn=S:OK' % (file, swfUrl, token, linkUrl, app, streamer)
            printDBG(rtmpUrl)
            linksTab.append({'name':'rtmp', 'url': rtmpUrl})
        return linksTab
        
    def parserMEGOMTV(self, baseUrl):
        printDBG("parserMEGOMTV baseUrl[%r]" % baseUrl )
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl.meta.get('Referer', baseUrl) }
        
        id = self.cm.ph.getSearchGroups(baseUrl, "id=([^&]+?)&")[0]
        linkUrl = "http://distro.megom.tv/player-inside.php?id={0}&width=100%&height=450".format(id)
        
        sts, data = self.cm.getPage(linkUrl, {'header':HTTP_HEADER})
        if not sts: return False 
        
        sts, data = CParsingHelper.getDataBeetwenMarkers(data, '<head>', 'var ad_data;', False)
        if not sts: return False 
        swfUrl = 'http://lds.megom.tv/jwplayer.flash.swf'
        a = int(self.cm.ph.getSearchGroups(data, 'var a = ([0-9]+?);')[0])
        b = int(self.cm.ph.getSearchGroups(data, 'var b = ([0-9]+?);')[0])
        c = int(self.cm.ph.getSearchGroups(data, 'var c = ([0-9]+?);')[0])
        d = int(self.cm.ph.getSearchGroups(data, 'var d = ([0-9]+?);')[0])
        f = int(self.cm.ph.getSearchGroups(data, 'var f = ([0-9]+?);')[0])
        v_part = self.cm.ph.getSearchGroups(data, "var v_part = '([^']+?)'")[0]
        
        rtmpUrl = ('rtmp://%d.%d.%d.%d' % (a/f, b/f, c/f, d/f) ) + v_part
        rtmpUrl += ' swfUrl=%s pageUrl=%s live=1 ' % (swfUrl, linkUrl)
        printDBG(rtmpUrl)
        return rtmpUrl

    def parserVIDEOHOUSE(self, baseUrl):
        printDBG("parserVIDEOHOUSE baseUrl[%r]" % baseUrl )
        HTTP_HEADER = MergeDicts(self.cm.getDefaultHeader('firefox'), {'Referer':baseUrl})
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        cUrl = self.cm.meta['url']
        up = urlparser()
        tmp = ph.IFRAME.findall(data)
        tmp.extend(ph.A.findall(data))
        for item in tmp:
            url = self.cm.getFullUrl(item[1], cUrl)
            if 1 == up.checkHostSupport(url):
                urls = up.getVideoLink(url)
                if urls: return urls        
        return False

    def parserVERYSTREAM(self, baseUrl):
        printDBG("parserVERYSTREAM baseUrl[%r]" % baseUrl )
        HTTP_HEADER = MergeDicts(self.cm.getDefaultHeader('firefox'), {'Referer':baseUrl})
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: 
            return False
        
        #printDBG("parserVERYSTREAM data: [%s]" % data )
        id = ph.search(data, '''id\s*?=\s*?['"]videolink['"]>([^>]+?)<''')[0]
        
        if id:
            videoUrl = 'https://verystream.com/gettoken/{0}?mime=true'.format(id)
            sts, data = self.cm.getPage(videoUrl, {'max_data_size':0})
            if not sts: 
                return False
            return self.cm.meta['url']
        else:
            return False
        
    def parserJUSTUPLOAD(self, baseUrl):
        printDBG("parserJUSTUPLOAD baseUrl[%r]" % baseUrl )
        HTTP_HEADER = MergeDicts(self.cm.getDefaultHeader('firefox'), {'Referer':baseUrl})
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        #printDBG("parserJUSTUPLOAD data: [%s]" % data )
        videoUrl = ph.search(data, '''<source\s*?src=['"]([^'^"]+?)['"]''')[0]
        if videoUrl.startswith('//'): videoUrl = 'http:' + videoUrl
        return videoUrl

    def parserOPENLOADIO(self, baseUrl):
        printDBG('parserOPENLOADIO baseUrl[%r]' % baseUrl)
        HTTP_HEADER = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
            'Accept': 'text/html', 
            #'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3', 
            'Accept-Encoding': 'gzip', 
            'Accept-Language': 'en-US,en;q=0.8'
        }
        #referer = strwithmeta(baseUrl).meta.get('Referer', '')
        #if referer:
        #    HTTP_HEADER['Referer'] = referer
        if "openloads.co" in baseUrl:
            video_id = re.findall("openloads.co/f2/([a-zA-Z0-9_-]+?)/", baseUrl)
            if not video_id:
                return []
            printDBG("video_id: %s" % video_id[0])
            baseUrl = "http://openload.co/embed/%s/" % video_id[0]
            printDBG("new url: %s" % baseUrl)

        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts:
            return False
        
        printDBG(data)
        orgData = data
        msg = clean_html(ph.find(data, ('<div', '>', 'blocked'), '</div>', flags=0)[1])
        if msg or 'content-blocked' in data:
            if msg == '':
                msg = clean_html(ph.find(data, ('<p', '>', 'lead'), '</p>', flags=0)[1])
            if msg == '':
                msg = _("We can't find the file you are looking for. It maybe got deleted by the owner or was removed due a copyright violation.")
        if msg:
            SetIPTVPlayerLastHostError(msg)
        
        subTracksData = self.cm.ph.getAllItemsBeetwenMarkers(data, '<track ', '>', False, False)
        subTracks = []
        for track in subTracksData:
            if 'kind="captions"' not in track:
                continue
            subUrl = self.cm.ph.getSearchGroups(track, 'src="([^"]+?)"')[0]
            if subUrl.startswith('/'):
                subUrl = 'http://openload.co' + subUrl
            if subUrl.startswith('http'):
                subLang = self.cm.ph.getSearchGroups(track, 'srclang="([^"]+?)"')[0]
                subLabel = self.cm.ph.getSearchGroups(track, 'label="([^"]+?)"')[0]
                subTracks.append({'title': subLabel + '_' + subLang, 'url': subUrl, 'lang': subLang, 'format': 'srt'})

        videoUrl = ''
        
        encTab = re.findall('<p style="" id="[^"]+">(.*?)</p>', data)
        if not encTab:
            encTab = re.findall('<p id="[^"]+" style="">(.*?)</p>', data)
        if not encTab:
            return

        def _decode_code(code, t3, t1, t2):
            import math
            t4 = ''
            ke = []
            for i in range(0, len(code[0:9*8]),8):
                ke.append(int(code[i:i+8],16))
            t5 = 0
            t6 = 0
            while t5 < len(code[9*8:]):
                t7 = 64
                t8 = 0
                t9 = 0
                ta = 0
                while True:
                    if t5 + 1 >= len(code[9*8:]):
                        t7 = 143;
                    ta = int(code[9*8+t5:9*8+t5+2], 16)
                    t5 +=2
                    if t9 < 6*5:
                        tb = ta & 63
                        t8 += tb << t9
                    else:
                        tb = ta & 63
                        t8 += int(tb * math.pow(2, t9))
                    t9 += 6
                    if not ta >= t7: break
                # tc = t8 ^ ke[t6 % 9] ^ t1 ^ t3 ^ t2
                tc = t8 ^ ke[t6 % 9] ^ t3 ^ t2
                td = t7 * 2 + 127
                for i in range(4):
                    te = chr(((tc & td) >> (9*8/ 9)* i) - 1)
                    if te != '$':
                        t4 += te
                    td = (td << (9*8/ 9))
                t6 += 1
            return t4

        t1 = re.findall('_0x59ce16=([^;]+)', data)
        if t1:
                t1 = eval(t1[0].replace('parseInt', 'int'))

        t2 = re.findall('_1x4bfb36=([^;]+)', data)
        if t2:
                t2 = eval(t2[0].replace('parseInt', 'int'))

        t3 = re.findall('_0x30725e,(\(parseInt.*?)\),', data)
        if t3:
                t3 = eval(t3[0].replace('parseInt', 'int'))

        dec = _decode_code(encTab[0], t3, t1, t2)
        if not dec:
            if len(encTab[0]) > 5:
                SetIPTVPlayerLastHostError(_('%s link extractor error.') % 'https://openload.co/')
            return False
        videoUrl = ('https://openload.co/stream/{0}?mime=true').format(dec)
        printDBG("video url -----> " + videoUrl)
        params = dict(HTTP_HEADER)
        params['external_sub_tracks'] = subTracks
        return urlparser.decorateUrl(videoUrl, params)
        
    def parserGAMETRAILERS(self, baseUrl):
        printDBG("parserGAMETRAILERS baseUrl[%r]" % baseUrl )
        list = GametrailersIE()._real_extract(baseUrl)[0]['formats']
        
        for idx in range(len(list)):
            width   = int(list[idx].get('width', 0))
            height  = int(list[idx].get('height', 0))
            bitrate = int(list[idx].get('bitrate', 0))
            if 0 != width or 0 != height:
                name = '%sx%s' % (width, height)
            elif 0 != bitrate:
                name = 'bitrate %s' % (bitrate)
            else:
                name = '%s.' % (idx + 1)
            list[idx]['name'] = name
        return list
        
    def parserVEVO(self, baseUrl):
        printDBG("parserVEVO baseUrl[%r]" % baseUrl )
        videoUrls = self.getVevoIE()._real_extract(baseUrl)['formats']
        
        for idx in range(len(videoUrls)):
            width   = int(videoUrls[idx].get('width', 0))
            height  = int(videoUrls[idx].get('height', 0))
            bitrate = int(videoUrls[idx].get('bitrate', 0)) / 8
            name = ''
            if 0 != bitrate:
                name = 'bitrate %s' % (formatBytes(bitrate, 0).replace('.0', '')+'/s')
            if 0 != width or 0 != height:
                name += ' %sx%s' % (width, height)
            if '' == name:
                name = '%s.' % (idx + 1)
            videoUrls[idx]['name'] = name
        if 0 < len(videoUrls):
            max_bitrate = int(config.plugins.iptvplayer.vevo_default_quality.value)
            def __getLinkQuality( itemLink ):
                return int(itemLink['bitrate'])
            videoUrls = CSelOneLink(videoUrls, __getLinkQuality, max_bitrate).getSortedLinks()
            if config.plugins.iptvplayer.vevo_use_default_quality.value:
                videoUrls = [videoUrls[0]]
        return videoUrls
        
    def parserBBC(self, baseUrl):
        printDBG("parserBBC baseUrl[%r]" % baseUrl )
        
        vpid = self.cm.ph.getSearchGroups(baseUrl, '/vpid/([^/]+?)/')[0]
        
        if vpid == '':
            data = self.getBBCIE()._real_extract(baseUrl)
        else:
            formats, subtitles = self.getBBCIE()._download_media_selector(vpid)
            data = {'formats':formats, 'subtitles':subtitles}
        
        subtitlesTab = []
        for sub in data.get('subtitles', []):
            if self.cm.isValidUrl(sub.get('url', '')):
                subtitlesTab.append({'title':_(sub['lang']), 'url':sub['url'], 'lang':sub['lang'], 'format':sub['ext']})
        
        videoUrls = []
        hlsLinks = []
        mpdLinks = []
        
        printDBG(">>>>>>>>>>>%s<<<<<<<<<<<<<<" % data['formats'])
        for vidItem in data['formats']:
            if 'url' in vidItem:
                url = self.getBBCIE().getFullUrl(vidItem['url'].replace('&amp;', '&'))
                if vidItem.get('ext', '') == 'hls' and 0 == len(hlsLinks):
                    hlsLinks.extend(getDirectM3U8Playlist(url, False, checkContent=True))
                elif vidItem.get('ext', '') == 'mpd' and 0 == len(mpdLinks):
                    mpdLinks.extend(getMPDLinksWithMeta(url, False))
        
        tmpTab = [hlsLinks, mpdLinks]
        
        if config.plugins.iptvplayer.bbc_prefered_format.value == 'dash':
            tmpTab.reverse()
        
        max_bitrate = int(config.plugins.iptvplayer.bbc_default_quality.value)
        for item in tmpTab:
            def __getLinkQuality( itemLink ):
                try: return int(itemLink['height'])
                except Exception: return 0
            item = CSelOneLink(item, __getLinkQuality, max_bitrate).getSortedLinks()
            if config.plugins.iptvplayer.bbc_use_default_quality.value:
                videoUrls.append(item[0])
                break
            videoUrls.extend(item)
        
        if len(subtitlesTab):
            for idx in range(len(videoUrls)):
                videoUrls[idx]['url'] = strwithmeta(videoUrls[idx]['url'], {'external_sub_tracks':subtitlesTab})
        
        return videoUrls
        
    def parserSHAREDSX(self, baseUrl):
        printDBG("parserSHAREDSX baseUrl[%r]" % baseUrl )
        # based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/shared.py
        sts, data = self.cm.getPage(baseUrl)

        if '>File does not exist<' in data:
            SetIPTVPlayerLastHostError('Video %s does not exist' % baseUrl)
            return False

        data = self.cm.ph.getDataBeetwenMarkers(data, '<form', '</form>', False)[1]
        data = re.compile('name="([^"]+?)"[^>]*?value="([^"]+?)"').findall(data)
        post_data = dict(data)
        sts, data = self.cm.getPage(baseUrl, {'header':self.HTTP_HEADER}, post_data)
        if not sts: return False        
            
        videoUrl = self.cm.ph.getSearchGroups(data, 'data-url="([^"]+)"')[0]
        if videoUrl.startswith('http'): return videoUrl
        return False
        
    def parserPOSIEDZEPL(self, baseUrl):
        printDBG("parserPOSIEDZEPL baseUrl[%r]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        if '/e.' not in baseUrl:
            video_id = self.cm.ph.getSearchGroups(baseUrl+'/', '/([A-Za-z0-9]{10})[/.?]')[0]
            url = 'http://e.posiedze.pl/' + video_id
        else:
            url = baseUrl
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, """["']*file["']*[ ]*?:[ ]*?["']([^"^']+?)['"]""")[0]
        if videoUrl.startswith('http'): return urlparser.decorateUrl(videoUrl)
        return False
        
    def parserNEODRIVECO(self, baseUrl):
        printDBG("parserNEODRIVECO baseUrl[%r]" % baseUrl)
        #http://neodrive.co/embed/EG0F2UYFNR2CN1CUDNT2I5OPN/
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':baseUrl }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, """["']*vurl["']*[ ]*?=[ ]*?["']([^"^']+?)['"]""")[0]
        if videoUrl.startswith('http'): return urlparser.decorateUrl(videoUrl)
        return False
        
    def parserMIPLAYERNET(self, baseUrl):
        printDBG("parserMIPLAYERNET baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        url2 = self.cm.ph.getSearchGroups(data, '''<iframe[^>]*?src=["'](http://miplayer.net[^"^']+?)["']''', 1, True)[0]
        if url2 != '':
            sts, data = self.cm.getPage(url2, {'header':HTTP_HEADER})
            if not sts: return False
        
        curl = self.cm.ph.getSearchGroups(data, '''curl[ ]*?=[ ]*?["']([^"^']+?)["']''', 1, True)[0]
        curl = base64.b64decode(curl)
        if curl.split('?')[0].endswith('.m3u8'):
            return getDirectM3U8Playlist(curl, checkExt=False)
        elif curl.startswith('rtmp'):
            swfUrl = 'http://p.jwpcdn.com/6/12/jwplayer.flash.swf'
            curl += ' swfUrl=%s pageUrl=%s token=OOG17t.x#K9Vh#| ' % (swfUrl, url2)
            #curl += ' token=OOG17t.x#K9Vh#| '
            return curl
        return False
        
    def parserYOCASTTV(self, baseUrl):
        printDBG("parserYOCASTTV baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        swfUrl = self.cm.ph.getSearchGroups(data, '''["'](http[^'^"]+?swf)['"]''')[0]
        url    = self.cm.ph.getSearchGroups(data, '''streamer[^'^"]*?['"](rtmp[^'^"]+?)['"]''')[0]
        file   = self.cm.ph.getSearchGroups(data, '''file[^'^"]*?['"]([^'^"]+?)['"]''')[0].replace('.flv', '')
        if '' != file and '' != url:
            url += ' playpath=%s swfVfy=%s pageUrl=%s ' % (file, swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserSOSTARTORG(self, baseUrl):
        printDBG("parserSOSTARTORG baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        swfUrl = 'http://sostart.org/jw/jwplayer.flash.swf'
        url    = ''
        file   = self.cm.ph.getSearchGroups(data, '''file[^'^"]*?['"]([^'^"]+?)['"]''')[0]
        url += file
        if '' != file and '' != url:
            url += ' swfVfy=%s pageUrl=%s ' % (swfUrl, baseUrl)
            printDBG(url)
            return url
        return False
        
    def parserSOSTARTPW(self, baseUrl):
        printDBG("parserSOSTARTPW baseUrl[%r]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        jsonUrl = self.cm.ph.getSearchGroups(data, '''getJSON\([^"^']*?['"]([^"^']+?)['"]''')[0]
        if not jsonUrl.startswith('http'): return False
        
        if 'chunklist.m3u8' in data:
            hlsStream = True
        sts, data = self.cm.getPage(jsonUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        printDBG(data)
        data = json_loads(data)
        if hlsStream:
            Referer = 'http://api.peer5.com/jwplayer6/assets/jwplayer.flash.swf'
            hlsUrl = data['rtmp']+"/"+data['streamname']+"/chunklist.m3u8"
            hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':Referer})
            return getDirectM3U8Playlist(hlsUrl)
        return False
        
    def parserLIVEONLINETV247(self, baseUrl):
        printDBG("parserLIVEONLINETV247 baseUrl[%r]" % baseUrl)
        urlTab = []
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER = dict(self.HTTP_HEADER) 
        HTTP_HEADER['Referer'] = Referer
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>')
        printDBG(tmp)
        for item in tmp:
            if 'application/x-mpegurl' not in item.lower(): continue
            hlsUrl = self.cm.ph.getSearchGroups(item, '''src=["'](https?://[^'^"]+?)["']''')[0]
            if not self.cm.isValidUrl(hlsUrl): continue
            urlTab.extend(getDirectM3U8Playlist(hlsUrl))
        return urlTab
        
    def parserBROADCAST(self, baseUrl):
        printDBG("parserBROADCAST baseUrl[%r]" % baseUrl)
        baseUrl = urlparser.decorateParamsFromUrl(baseUrl)
        Referer = baseUrl.meta.get('Referer', '')
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('broadcast.cookie')}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        printDBG(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        printDBG(data)
        printDBG("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        hlsUrls = []
        tokenUrl = ''
        base64Obj = re.compile('''=\s*['"]([A-Za-z0-9+/=]+?)['"]''', re.IGNORECASE)
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in data:
            if tokenUrl == '': tokenUrl = self.cm.ph.getSearchGroups(item, '''=\s*['"]([^"^']*?token[^"^']*?\.php)['"]''', 1, True)[0]
            item = base64Obj.findall(item)
            for curl in item:
                try: 
                    curl = base64.b64decode(curl)
                    if '.m3u8' in curl: hlsUrls.append(curl)
                except Exception:
                    printExc()
        
        params['header']['Referer'] = baseUrl
        params['header']['X-Requested-With'] = 'XMLHttpRequest'
        
        vidTab = []
        for hlsUrl in hlsUrls:
            sts, data = self.cm.getPage(self.cm.getBaseUrl(baseUrl) + tokenUrl, params)
            if not sts: continue
            
            printDBG(data)
            
            data = json_loads(data)
            key, token = data.items()[0]
            
            hlsUrl = hlsUrl + token
            hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Origin':self.cm.getBaseUrl(baseUrl), 'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':baseUrl})
            vidTab.extend( getDirectM3U8Playlist(hlsUrl, checkContent=True) )
        return vidTab
    
    def parserGOODRTMP(self, baseUrl):
        printDBG("parserGOODRTMP baseUrl[%r]" % baseUrl)
        SetIPTVPlayerLastHostError('Links from "goodrtmp.com" not supported.')
        return False
        
    def parserLIFERTMP(self, baseUrl):
        printDBG("parserGOODRTMP baseUrl[%r]" % baseUrl)
        SetIPTVPlayerLastHostError('Links from "life-rtmp.com" not supported.')
        return False
    
    def parserTHEACTIONLIVE(self, baseUrl):
        printDBG("parserTHEACTIONLIVE baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        baseUrl = strwithmeta(baseUrl, {'Referer':baseUrl})
        return urlparser().getAutoDetectedStreamLink(baseUrl, data)
        
    def parserBIGGESTPLAYER(self, baseUrl):
        printDBG("parserBIGGESTPLAYER baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', '}', False)[1]
        url  = self.cm.ph.getSearchGroups(data, '''file[^'^"]*?['"]([^'^"]+?)['"]''')[0]
        return getDirectM3U8Playlist(url)
        
    def parserLIVEONLINE247(self, baseUrl):
        printDBG("parserLIVEONLINE247 baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        swfUrl = self.cm.ph.getSearchGroups(data, '''["'](http[^'^"]+?swf)['"]''')[0]
        if swfUrl == '':
            swfUrl = 'http://p.jwpcdn.com/6/12/jwplayer.flash.swf'
        url   = self.cm.ph.getSearchGroups(data, '''file[^'^"]*?['"]([^'^"]+?)['"]''')[0]
        if url.startswith('rtmp'):
            url += ' swfVfy=%s pageUrl=%s ' % (swfUrl, baseUrl)
            printDBG(url)
            return url
        else:
            data = self.cm.ph.getDataBeetwenMarkers(data, 'source:', '}', False)[1]
            url = self.cm.ph.getSearchGroups(data, '''hls[^'^"]*?['"]([^'^"]+?)['"]''')[0]
            return getDirectM3U8Playlist(url)
        return False
        
    def parserFILEPUPNET(self, baseUrl):
        printDBG("parserFILEPUPNET baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        onloadData = self.cm.ph.getDataBeetwenMarkers(data, 'window.onload', '</script>', False)[1]
        qualities = self.cm.ph.getSearchGroups(onloadData, 'qualities:[ ]*?\[([^\]]+?)\]')[0]
        qualities = self.cm.ph.getAllItemsBeetwenMarkers(qualities, '"', '"', False)
        
        defaultQuality = self.cm.ph.getSearchGroups(onloadData, 'defaultQuality:[ ]*?"([^"]+?)"')[0]
        if defaultQuality in qualities: qualities.remove(defaultQuality)
        
        sub_tracks = []
        subData = self.cm.ph.getDataBeetwenMarkers(onloadData, 'subtitles:', ']', False)[1].split('}')
        for item in subData:
            if '"subtitles"' in item:
                label   = self.cm.ph.getSearchGroups(item, 'label:[ ]*?"([^"]+?)"')[0]
                srclang = self.cm.ph.getSearchGroups(item, 'srclang:[ ]*?"([^"]+?)"')[0]
                src     = self.cm.ph.getSearchGroups(item, 'src:[ ]*?"([^"]+?)"')[0]
                if not src.startswith('http'): continue
                sub_tracks.append({'title':label, 'url':src, 'lang':srclang, 'format':'srt'})
        
        printDBG(">> sub_tracks[%s]\n[%s]" % (sub_tracks, subData))
        
        linksTab = []
        onloadData = self.cm.ph.getDataBeetwenMarkers(onloadData, 'sources:', ']', False)[1]
        defaultUrl = self.cm.ph.getSearchGroups(onloadData, '"(https?://[^"]+?)"')[0]
        if defaultUrl != '':
            linksTab.append({'name':defaultQuality, 'url': strwithmeta(defaultUrl, {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':baseUrl, 'external_sub_tracks':sub_tracks})})
            for item in qualities:
                if '.mp4' in defaultUrl:
                    url = defaultUrl.replace('.mp4', '-%s.mp4' % item)
                    linksTab.append({'name':item, 'url': strwithmeta(url, {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':baseUrl, 'external_sub_tracks':sub_tracks})})
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False)
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if self.cm.isValidUrl(url):
                url = strwithmeta(url, {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':baseUrl, 'external_sub_tracks':sub_tracks})
                linksTab.append({'name':self.cm.getBaseUrl(baseUrl, True) + ' %s' % (len(linksTab) + 1), 'url':url})
        
        if len(linksTab) == 1:
            linksTab[0]['name'] = linksTab[0]['name'][:-1] + 'default'
        
        printDBG('++++++++')
        printDBG(linksTab)
        printDBG('--------')
        return linksTab
        
    def parserHDFILMSTREAMING(self, baseUrl):
        printDBG("parserHDFILMSTREAMING baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        sub_tracks = []
        subData = self.cm.ph.getDataBeetwenMarkers(data, 'tracks:', ']', False)[1].split('}')
        for item in subData:
            if '"captions"' in item:
                label   = self.cm.ph.getSearchGroups(item, 'label:[ ]*?"([^"]+?)"')[0]
                src     = self.cm.ph.getSearchGroups(item, 'file:[ ]*?"([^"]+?)"')[0]
                if not src.startswith('http'): continue
                sub_tracks.append({'title':label, 'url':src, 'lang':'unk', 'format':'srt'})
        
        linksTab = self._findLinks(data, serverName='hdfilmstreaming.com')
        for idx in range(len(linksTab)):
            linksTab[idx]['url'] = urlparser.decorateUrl(linksTab[idx]['url'], {'external_sub_tracks':sub_tracks})
        
        return linksTab
        
    def parserPUBLICVIDEOHOST(self, baseUrl):
        printDBG("parserPUBLICVIDEOHOST baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        linksTab = self._findLinks(data, serverName='publicvideohost.org', m1='setup(', m2=')', contain='.mp4')
        return linksTab
                    
    def parserSUPERFILMPL(self, baseUrl):
        printDBG("parserSUPERFILMPL baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video ', '</video>', False)[1]
        linkUrl = self.cm.ph.getSearchGroups(data, '<source[^>]+?src="(http[^"]+?)"')[0]
        return linkUrl
        
    def parserSENDVIDCOM(self, baseUrl):
        printDBG("parserSENDVIDCOM baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video ', '</video>', False)[1]
        linkUrl = self.cm.ph.getSearchGroups(data, '<source[^>]+?src="([^"]+?)"')[0]
        if linkUrl.startswith('//'): linkUrl = 'http:' + linkUrl
        return linkUrl
        
    def parserFILEHOOT(self, baseUrl):
        printDBG("parserFILEHOOT baseUrl[%r]" % baseUrl)
        
        if 'embed-' not in baseUrl:
            baseUrl = 'http://filehoot.com/embed-%s-1046x562.html' % baseUrl.split('/')[-1].replace('.html', '')
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        data = re.search('file:[ ]*?"([^"]+?)"', data)
        if data:
            linkVideo = data.group(1)
            printDBG('parserFILEHOOT direct link: ' + linkVideo)
            return linkVideo
        return False
        
    def parserSSH101COM(self, baseUrl):
        printDBG("parserFILEHOOT baseUrl[%r]" % baseUrl)
        Referer = strwithmeta(baseUrl).meta.get('Referer', baseUrl)
        HTTP_HEADER= { 'User-Agent':"Mozilla/5.0", 'Referer':Referer }
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        videoUrl = self.cm.ph.getSearchGroups(data, 'file:[ ]*?"([^"]+?)"', 1, ignoreCase=True)[0]
        if not videoUrl.split('?')[0].endswith('.m3u8'): videoUrl = self.cm.ph.getSearchGroups(data, '<source[^>]*?src="([^"]+?)"', 1, ignoreCase=True)[0]
        
        if videoUrl.split('?')[0].endswith('.m3u8'):
            return getDirectM3U8Playlist(videoUrl)
        return False
        
    def parserTWITCHTV(self, baseUrl):
        printDBG("parserFILEHOOT baseUrl[%r]" % baseUrl)
        if 'channel'  in baseUrl: data = baseUrl + '&'
        else: sts, data = self.cm.getPage(baseUrl)
        channel = self.cm.ph.getSearchGroups(data, '''channel=([^&^'^"]+?)[&'"]''')[0]
        MAIN_URLS = 'https://api.twitch.tv/'
        CHANNEL_TOKEN_URL = MAIN_URLS + 'api/channels/%s/access_token?need_https=false&oauth_token&platform=web&player_backend=mediaplayer&player_type=site'
        LIVE_URL = 'http://usher.justin.tv/api/channel/hls/%s.m3u8?token=%s&sig=%s&allow_source=true'
        if '' != channel:
            url = CHANNEL_TOKEN_URL % channel
            sts, data = self.cm.getPage(url, {'header':MergeDicts(self.cm.getDefaultHeader(browser='chrome'), {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID':'jzkbprff40iqj646a697cyrvl0zt2m6'})})
            urlTab = []
            if sts:
                try:
                    data = json_loads(data)
                    url = LIVE_URL % (channel, urllib.quote(data['token']), data['sig'])
                    data = getDirectM3U8Playlist(url, checkExt=False)
                    for item in data:
                        item['url'] = urlparser.decorateUrl(item['url'], {'iptv_proto':'m3u8', 'iptv_livestream':True}) 
                        urlTab.append(item)
                except Exception: printExc()
            return urlTab
        return False
        
    def parserMOONWALKCC(self, baseUrl):
        printDBG("parserMOONWALKCC baseUrl[%r]" % baseUrl)
        return self.getMoonwalkParser().getDirectLinks(baseUrl)
        
    def parserEASYVIDORG(self, baseUrl):
        printDBG("parserEASYVIDORG baseUrl[%r]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'easyvid.org')
        return self._parserUNIVERSAL_A(baseUrl, 'http://easyvid.org/embed-{0}-640x360.html', _findLinks)
    
    def parserMYSTREAMLA(self, baseUrl):
        printDBG("parserMYSTREAMLA baseUrl[%r]" % baseUrl)
        def _findLinks(data):
            return self._findLinks(data, 'mystream.la')
        return self._parserUNIVERSAL_A(baseUrl, 'http://mystream.la/external/{0}', _findLinks)
        
    def parserOKRU(self, baseUrl):
        printDBG("parserOKRU baseUrl[%r]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Referer':baseUrl,
                       'Sec-Fetch-Mode':'cors'
                     }
        COOKIE_FILE = GetCookieDir('ok.cookie')
        http_params = {'header':HTTP_HEADER, 'use_cookie':True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        metadataUrl = ''
        if 'videoPlayerMetadata' not in baseUrl:
            sts, data = self.cm.getPage(baseUrl, http_params)
            if not sts: return False
            error = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'vp_video_stub_txt'), ('</div', '>'), False)[1])
            if error == '': error = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<', '>', 'page-not-found'), ('</', '>'), False)[1])
            if error != '': SetIPTVPlayerLastHostError(error)
        
            tmpTab = re.compile('''data-options=['"]([^'^"]+?)['"]''').findall(data)
            for tmp in tmpTab:
                tmp = clean_html(tmp)
                tmp = json_loads(tmp)
                printDBG("====")
                printDBG(tmp)
                printDBG("====")
                
                tmp = tmp['flashvars']
                if 'metadata' in tmp:
                    data = json_loads(tmp['metadata'])
                    metadataUrl = ''
                    break
                else:
                    metadataUrl = urllib.unquote(tmp['metadataUrl'])
        else:
            metadataUrl = baseUrl
        
        if metadataUrl != '':
            url = metadataUrl
            sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
            if not sts: return False
            data = json_loads(data)
        
        urlsTab = []
        for item in data['videos']:
            url = item['url'] #.replace('&ct=4&', '&ct=0&') #+ '&bytes'#=0-7078'
            url = urlparser.decorateUrl(url, {'iptv_proto':'m3u8', 'Referer': baseUrl,'User-Agent': HTTP_HEADER['User-Agent']})
            urlsTab.append({'name':item['name'], 'url':url})
        urlsTab = urlsTab[::-1]
        
        if 1: #0 == len(urlsTab):
            url = urlparser.decorateUrl(data['hlsManifestUrl'], {'iptv_proto':'m3u8', 'Referer': baseUrl,'User-Agent': HTTP_HEADER['User-Agent']})

            urlsTab.append({'name': 'hls', 'url': url})
            linksTab = getDirectM3U8Playlist(url, checkExt=False, checkContent=True, cookieParams = http_params)
            
            for idx in range(len(linksTab)):
                meta = dict(linksTab[idx]['url'].meta)
                meta['iptv_proto'] = 'm3u8'
                url = linksTab[idx]['url']
                if url.endswith('/'):
                    linksTab[idx]['url'] = strwithmeta(url + 'playlist.m3u8', meta)
                    
            try:
                tmpUrlTab = sorted(linksTab, key=lambda item: -1 * int(item.get('bitrate', 0)))
                tmpUrlTab.extend(urlsTab)
                urlsTab = tmpUrlTab
            except Exception:  printExc()
        return urlsTab
        
    def parserALLOCINEFR(self, baseUrl):
        printDBG("parserALLOCINEFR baseUrl[%r]" % baseUrl)
        # based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/allocine.py
        _VALID_URL = r'https?://(?:www\.)?allocine\.fr/_?(?P<typ>article|video|film|video|film)/(iblogvision.aspx\?cmedia=|fichearticle_gen_carticle=|player_gen_cmedia=|fichefilm_gen_cfilm=|video-)(?P<id>[0-9]+)(?:\.html)?'
        mobj = re.match(_VALID_URL, baseUrl)
        typ = mobj.group('typ')
        display_id = mobj.group('id')

        sts, webpage = self.cm.getPage(baseUrl)
        if not sts: return False

        if 'film' == type:
            video_id = self.cm.ph.getSearchGroups(webpage, r'href="/video/player_gen_cmedia=([0-9]+).+"')[0]
        else:
            player = self.cm.ph.getSearchGroups(webpage, r'data-player=\'([^\']+)\'>')[0]
            if player != '':
                player_data = json_loads(player)
                video_id = player_data['refMedia']
            else:
                model = self.cm.ph.getSearchGroups(webpage, r'data-model="([^"]+)"')[0] 
                model_data = json_loads(unescapeHTML(model.decode()))
                if 'videos' in model_data:
                    try:
                        urlsTab = []
                        for item in model_data['videos']:
                            for key in item['sources']:
                                url = item['sources'][key]
                                if url.startswith('//'):
                                    url = 'http:' + url
                                if self.cm.isValidUrl(url):
                                    urlsTab.append({'name':key, 'url':url})
                        if len(urlsTab):
                            return urlsTab
                    except Exception:
                        printExc()
                
                video_id = model_data['id']

        sts, data = self.cm.getPage('http://www.allocine.fr/ws/AcVisiondataV5.ashx?media=%s' % video_id)
        if not sts: return False
        
        data = json_loads(data)
        quality = ['hd', 'md', 'ld']
        urlsTab = []
        for item in quality:
            url = data['video'].get(item + 'Path', '')
            if not url.startswith('http'):
                continue
            urlsTab.append({'name':item, 'url':url})
        return urlsTab
        
    def parserLIVESTRAMTV(self, baseUrl):
        printDBG("parserLIVESTRAMTV baseUrl[%r]" % baseUrl)
        url = 'http://www.live-stream.tv/'
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Referer':baseUrl}
                       
        COOKIEFILE = self.COOKIE_PATH + "live-stream.tv.cookie"
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIEFILE}
        
        def reloadEpgNow(upBaseUrl):
            tm = str(int(time.time() * 1000))
            upUrl = upBaseUrl + "&_="+tm+"&callback=?"
            std, data = self.cm.getPage(upUrl, params)
            return
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return
        
        mediaId = self.cm.ph.getSearchGroups(data, '''reloadEpgNow\(\s*['"]([^'^"]+?)['"]''', 1, True)[0]
        
        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?)["']''', 1, True)[0]
        sts, data = self.cm.getPage(url, params)
        if not sts: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script', '</script>')
        tmp = ''
        for item in data:
            if 'eval(' in item:
                tmp += '\n %s' % self.cm.ph.getDataBeetwenReMarkers(item, re.compile('<script[^>]*?>'), re.compile('</script>'), False)[1].strip()
        
        jscode = base64.b64decode('''dmFyIGlwdHZfc3JjZXM9W10sZG9jdW1lbnQ9e30sd2luZG93PXRoaXMsTGV2ZWxTZWxlY3Rvcj0iIixDbGFwcHI9e307Q2xhcHByLlBsYXllcj1mdW5jdGlvbihyKXt0cnl7aXB0dl9zcmNlcy5wdXNoKHIuc291cmNlKX1jYXRjaChlKXt9fTt2YXIgJD1mdW5jdGlvbigpe3JldHVybntyZWFkeTpmdW5jdGlvbihyKXtyKCl9fX07''')
        jscode += tmp + '\nprint(JSON.stringify(iptv_srces));'
        tmp = []
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            tmp = ret['data'].strip()
            tmp = json_loads(tmp)
            
        refreshUrl = 'http://www.live-stream.tv/php/ajax.php?f=epgNow&cid=' +  mediaId
        reloadEpgNow(refreshUrl)
        
        tmp = set(tmp)
        printDBG(tmp)
        for vidUrl in tmp:
            vidUrl = strwithmeta(vidUrl, {'iptv_proto':'em3u8', 'Referer':url, 'iptv_livestream': True, 'User-Agent':HTTP_HEADER['User-Agent']}) #'iptv_m3u8_skip_seg':2, 'Referer':'http://static.live-stream.tv/player/player.swf'
            tab = getDirectM3U8Playlist(vidUrl, checkContent=True)
            for it in tab:
                it['url'].meta['iptv_refresh_cmd'] = GetPyScriptCmd('livestreamtv') + ' "%s" "%s" "%s" "%s" ' % (it['url'], refreshUrl, baseUrl, HTTP_HEADER['User-Agent'])
            tab.reverse()
            return tab
        return False
        
    def parserZEROCASTTV(self, baseUrl):
        printDBG("parserZEROCASTTV baseUrl[%r]" % baseUrl)
        if 'embed.php' in baseUrl:
            url = baseUrl
        elif 'chan.php?' in baseUrl:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return False
            data = self.cm.ph.getDataBeetwenMarkers(data, '<body ', '</body>', False)[1]
            url = self.cm.ph.getSearchGroups(data, r'''src=['"](http[^"^']+)['"]''')[0]
            
        if 'embed.php' not in url:
            sts, data = self.cm.getPage(url)
            if not sts: return False
            url = self.cm.ph.getSearchGroups(data, r'''var [^=]+?=[^'^"]*?['"](http[^'^"]+?)['"];''')[0]
            
        if url == '': return False
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        channelData = self.cm.ph.getSearchGroups(data, r'''unescape\(['"]([^'^"]+?)['"]\)''')[0]
        channelData = urllib.unquote(channelData)
        
        if channelData == '':
            data = self.cm.ph.getSearchGroups(data, '<h1[^>]*?>([^<]+?)<')[0]
            SetIPTVPlayerLastHostError(data)
        
        if channelData.startswith('rtmp'):
            channelData += ' live=1 '
            return channelData
        return False
        
    def parserCLOUDYEC(self, baseUrl):
        printDBG("parserCLOUDYEC baseUrl[%r]" % baseUrl)
        #based on https://github.com/rg3/youtube-dl/blob/master/youtube_dl/extractor/cloudy.py
        
        _VALID_URL = r'''(?x)
            https?://(?:www\.)?(?P<host>cloudy\.ec|videoraj\.ch)/
            (?:v/|embed\.php\?id=)
            (?P<id>[A-Za-z0-9]+)
            '''
        _EMBED_URL = 'http://www.%s/embed.php?id=%s&playerPage=1&autoplay=1'
        _API_URL = 'http://www.%s/api/player.api.php?%s'
        _MAX_TRIES = 2
        
        mobj = re.match(_VALID_URL, baseUrl)
        video_host = mobj.group('host')
        video_id = mobj.group('id')

        url = _EMBED_URL % (video_host, video_id)
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        urlTab = self._getSources(data)
        if len(urlTab): return urlTab

        file_key = self.cm.ph.getSearchGroups(data, r'key\s*:\s*"([^"]+)"')[0]
        if '' == file_key:
            file_key = self.cm.ph.getSearchGroups(data, r'filekey\s*=\s*"([^"]+)"')[0]

        def _extract_video(video_host, video_id, file_key, error_url=None, try_num=0):

            if try_num > _MAX_TRIES - 1:
                return False

            form = {'file': video_id, 'key': file_key}
            if error_url:
                form.update({'numOfErrors': try_num, 'errorCode': '404', 'errorUrl': error_url})

            data_url = _API_URL % (video_host, urllib.urlencode(form))
            sts, player_data = self.cm.getPage(data_url)
            if not sts: return sts

            data = parse_qs(player_data)
            try_num += 1
            if 'error' in data:
                return False
            title = data.get('title', [None])[0]
            if title:
                title = title.replace('&asdasdas', '').strip()
            video_url = data.get('url', [None])[0]
            if video_url:
                if not self.cm.getPage(video_url, {'max_data_size':0})[0]:
                    return self._extract_video(video_host, video_id, file_key, video_url, try_num)
            return [{'id': video_id, 'url': video_url, 'name': title}]
        return _extract_video(video_host, video_id, file_key)
    
    def parserSWIROWNIA(self, baseUrl):
        printDBG("Ekstraklasa.parserSWIROWNIA baseUrl[%r]" % baseUrl)
        def fun1(x):
            o = ""
            l = len(x)
            i = l - 1;
            while i >= 0:
                try:
                    o += x[i]
                except Exception:
                    pass
                i -= 1
            return o
        def fun2(x):
            o = ""
            ol = len(x)
            l = ol
            while ord(x[l/13]) != 48:
                try:
                    x += x
                    l += l
                except Exception:
                    pass
            i = l - 1
            while i >= 0:
                try:
                    o += x[i]
                except Exception:
                    pass
                i -= 1
            return o[:ol]
        def fun3(x, y, a=1):
            o = ""
            i = 0
            l = len(x)
            while i<l:
                if i<y:
                    y += a
                y %= 127
                o += JS_FromCharCode(ord(x[i]) ^ y)
                y += 1
                i += 1
            return o
              
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return []
        data = data[data.find('x="')+2 : data.rfind('"')+1]
        dataTab = data.split('+\n')
        data = ""
        for line in dataTab:
            line = line.strip()
            if '"' != line[0] or '"' != line[-1]:
                raise Exception("parserSWIROWNIA parsing ERROR")
            data += line[1:-1]


        def backslashUnEscaped(data):
            tmp = ''
            idx = 0
            while idx < len(data):
                if data[idx] == '\\':
                    tmp += data[idx+1]
                    idx += 2
                else:
                    tmp += data[idx]
                    idx += 1
            return tmp
            
        def printDBG2(data):
            printDBG("================================================================")
            printDBG( data )
            printDBG("================================================================")
        data = backslashUnEscaped(data)
        
        data = data[data.find('f("')+3:data.rfind('"')]
        data = fun1( data )
        printDBG2(data)
        data = backslashUnEscaped(data)
        
        printDBG2(data)
        
        data = data[data.find('f("')+3:data.rfind('"')]
        printDBG2(data)
        data = data.decode('string_escape')
        data = fun3( data, 50, 0)
        data = backslashUnEscaped(data)
        
        printDBG2(data)
        
        return
        
        data = data[data.find('f("')+3:data.rfind('"')]
        data = fun2( data )
        data = data.decode('string-escape')

        data = data[data.find('f("')+3:data.rfind('"')]
        data = fun3( data, 23, 1)
        data = backslashUnEscaped(data)
        
        printDBG(data)

    def parserMETAUA(self, baseUrl):
        printDBG("parserMETAUA baseUrl[%s]" % baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', #'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
        sts, data = self.cm.getPage(baseUrl, {'header' : HTTP_HEADER})
        if not sts: return False
        file_url = self.cm.ph.getSearchGroups(data, '''st_html5=['"]([^'^"]+?)['"]''')[0]
        
        def getUtf8Str(st):
            idx = 0
            st2 = ''
            while idx < len(st):
                st2 += '\\u0' + st[idx:idx + 3]
                idx += 3
            return st2.decode('unicode-escape').encode('UTF-8')
        
        if file_url.startswith('#') and 3 < len(file_url):
            file_url = getUtf8Str(file_url[1:])
            file_url = json_loads(file_url)['file']
        
        if file_url.startswith('http'): 
            return urlparser.decorateUrl(file_url, {'iptv_livestream':False, 'User-Agent':HTTP_HEADER['User-Agent']})
            
        
        jscode = self.cm.ph.getDataBeetwenMarkers(data, 'JSON.parse(', '),', False)[1]
        jscode = 'print(%s);' % jscode
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            decoded = ret['data'].strip()
            printDBG('DECODED DATA -> [%s]' % decoded)
            decoded = json_loads(decoded)
            vidTab = []
            for item in decoded['sources']:
                if 'mp4' in item['type']:
                    vidTab.append({'url':item['src'], 'name':item['label']})
            return vidTab
        return False 
        
    def parserNETUTV(self, url):
        printDBG("parseNETUTV url[%s]" % url)
        if 'hqq.none' in urlparser.getDomain(url):
            url = strwithmeta(url.replace('hqq.none', 'hqq.watch'), strwithmeta(url).meta)

        url += '&'
        vid = self.cm.ph.getSearchGroups(url, '''vi?d?=([0-9a-zA-Z]+?)[^0-9^a-z^A-Z]''')[0]
        hashFrom = self.cm.ph.getSearchGroups(url, '''hash_from=([0-9a-zA-Z]+?)[^0-9^a-z^A-Z]''')[0]

        # User-Agent - is important!!!
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10', #'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Referer': 'http://hqq.watch/'
                      }

        COOKIE_FILE = self.COOKIE_PATH + "netu.tv.cookie"
        # remove old cookie file
#        rm(COOKIE_FILE)
        params = {'with_metadata': True, 'header': HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIE_FILE}
        sts, ipData = self.cm.getPage('http://hqq.watch/player/ip.php?type=json', params)
        ipData = json_loads(ipData)

        printDBG("===")
        printDBG(ipData)
        printDBG("===")

        if 'hash.php?hash' in url:
            sts, data = self.cm.getPage(url, params)
            if not sts:
                return False
            data = re.sub('document\.write\(unescape\("([^"]+?)"\)', lambda m: urllib_unquote(m.group(1)), data)
            vid = self.cm.ph.getSearchGroups(data, '''var\s+?vid\s*?=\s*?['"]([^'^"]+?)['"]''')[0]
            hashFrom = self.cm.ph.getSearchGroups(data, '''var\s+?hash_from\s*?=\s*?['"]([^'^"]+?)['"]''')[0]

        if vid == '':
            printDBG('Lack of video id.')
            return False

        playerUrl = "https://hqq.watch/player/embed_player.php?vid=%s&autoplay=no" % vid
        if hashFrom != '':
            playerUrl += '&hash_from=' + hashFrom
        referer = strwithmeta(url).meta.get('Referer', playerUrl)

        #HTTP_HEADER['Referer'] = url
        sts, data = self.cm.getPage(playerUrl, params)
        if not sts:
            return False
        cUrl = data.meta['url']

#        def _getEvalData(data):
#            jscode = ['eval=function(t){return function(){print(arguments[0]);try{return t.apply(this,arguments)}catch(t){}}}(eval);']
#            tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
#            for item in tmp:
#                if 'eval(' in item and 'check(' not in item:
#                    jscode.append(item)
#            ret = js_execute( '\n'.join(jscode) )
#            return ret['data']

#        tmp = _getEvalData(data)

        sub_tracks = []
        subData = self.cm.ph.getDataBeetwenMarkers(data, 'addRemoteTextTrack({', ');', False)[1]
        subData = self.cm.getFullUrl(self.cm.ph.getSearchGroups(subData, '''src:\s?['"]([^'^"]+?)['"]''')[0], cUrl)
        if (subData.endswith('.srt') or subData.endswith('.vtt')):
            sub_tracks.append({'title': 'attached', 'url': subData, 'lang': 'unk', 'format': 'srt'})

        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script>', '</script>', False)
        wise = ''
        tmp = ''
        for item in data:
            if 'orig_vid = "' in item:
                tmp = item
            if "w,i,s,e" in item:
                wise = item

        orig_vid = self.cm.ph.getDataBeetwenMarkers(tmp, 'orig_vid = "', '"', False)[1]
        jscode = self.cm.ph.getDataBeetwenMarkers(tmp, 'location.replace(', ');', False)[1]
        jscode = 'var need_captcha="0"; var server_referer="http://hqq.watch/"; var orig_vid="' + orig_vid + '"; print(' + jscode + ');'

        gt = self.cm.getCookieItem(COOKIE_FILE, 'gt')
        ret = js_execute(jscode)
        if ret['sts'] and 0 == ret['code']:
            secPlayerUrl = self.cm.getFullUrl(ret['data'].strip(), self.cm.getBaseUrl(cUrl)).replace('$secured', '0') #'https://hqq.tv/'
            if 'need_captcha=1' in secPlayerUrl and ipData['need_captcha'] == 0 and gt != '':
                secPlayerUrl = secPlayerUrl.replace('need_captcha=1', 'need_captcha=0')

        HTTP_HEADER['Referer'] = referer
        sts, data = self.cm.getPage(secPlayerUrl, params)
        cUrl = self.cm.meta['url']

        sitekey = ph.search(data, '''['"]?sitekey['"]?\s*?:\s*?['"]([^"^']+?)['"]''')[0]
        if sitekey != '':
            query = {}
            token, errorMsgTab = self.processCaptcha(sitekey, cUrl)
            if token == '':
                SetIPTVPlayerLastHostError('\n'.join(errorMsgTab))
                return False
            else:
                query['g-recaptcha-response'] = token
                tmp = ph.find(data, ('<form', '>', ), '</form>', flags=ph.I | ph.START_E)[1]
                if tmp:
                    printDBG(tmp)
                    action = ph.getattr(tmp, 'action')
                    if not action:
                        action = cUrl.split('?', 1)[0]
                    else:
                        self.cm.getFullUrl(action, cUrl)
                    tmp = ph.findall(tmp, '<input', '>', flags=ph.I)

                    for item in tmp:
                        name = ph.getattr(item, 'name')
                        value = ph.getattr(item, 'value')
                        if name != '':
                            query[name] = value
                    action += '?' + urllib_urlencode(query)
                    sts, data = self.cm.getPage(action, params)
                    if sts:
                        cUrl = self.cm.meta['url']

#        data = re.sub('document\.write\(unescape\("([^"]+?)"\)', lambda m: urllib_unquote(m.group(1)), data)
#        data += _getEvalData(data)
#        printDBG("+++")
#        printDBG(data)
#        printDBG("+++")

        def getUtf8Str(st):
            try:
                idx = 0
                st2 = ''
                while idx < len(st):
                    st2 += '\\u0' + st[idx:idx + 3]
                    idx += 3
                return st2.decode('unicode-escape').encode('UTF-8')
            except Exception:
                return ''

        linksCandidates = re.compile('''['"](#[^'^"]+?)['"]''').findall(data)
        try:
#            jscode = [data.rsplit('//document.domain="hqq.watch";')[-1]]
#            tmp = ph.findall(data, '//document.domain="hqq.watch";', '</script>', flags=0)
#            for item in tmp:
#                if 'var at' in item:
#                    jscode.append(item)
#                    break
#            jscode.append('var adb = "0/"; ext = "";')
            jscode = ['var token = ""; var adb = "0/"; var wasmcheck="1"; var videokeyorig="%s";' % vid]
            jscode.append(wise)
            tmp = ph.search(data, '''(['"][^'^"]*?get_md5\.php[^;]+?);''')[0]
            jscode.append('print(%s)' % tmp)
            ret = js_execute('\n'.join(jscode))

            playerUrl = self.cm.getFullUrl(ret['data'].strip(), cUrl)
            params['header']['Accept'] = '*/*'
            params['header']['Referer'] = cUrl
            sts, data = self.cm.getPage(playerUrl, params)
            obf = json_loads(data)
            linksCandidates.insert(0, obf['obf_link'])
        except Exception:
            printExc()
            rm(COOKIE_FILE)
            SetIPTVPlayerLastHostError(_('Link protected with google recaptcha v2.') + '\n' + _('Download again'))
            return False

        printDBG("linksCandidates >> %s" % linksCandidates)
        retUrls = []
        for file_url in linksCandidates:
            if file_url.startswith('#') and 3 < len(file_url):
                file_url = getUtf8Str(file_url[1:])
            if file_url.startswith('//'):
                file_url = 'https:' + file_url
            if self.cm.isValidUrl(file_url):
                file_url = urlparser.decorateUrl(file_url, {'iptv_livestream': False, 'User-Agent': HTTP_HEADER['User-Agent'], 'Referer': cUrl, 'external_sub_tracks': sub_tracks})
                if file_url.split('?')[0].endswith('.m3u8') or '/hls-' in file_url:
                    file_url = strwithmeta(file_url, {'iptv_proto': 'm3u8'})
                    retUrls.extend(getDirectM3U8Playlist(file_url, False, checkContent=True))
        return retUrls

    def parserVEOHCOM(self, baseUrl):
        printDBG("parserVEOHCOM url[%s]\n" % baseUrl)
        
        mediaId = self.cm.ph.getSearchGroups(baseUrl, '''permalinkId=([^&]+?)[&$]''')[0]
        if mediaId == '': mediaId = self.cm.ph.getSearchGroups(baseUrl, '''/watch/([^/]+?)[/$]''')[0]
        
        #url = 'http://www.veoh.com/api/findByPermalink?permalink=%s' % id
        
        url = 'http://www.veoh.com/iphone/views/watch.php?id=%s&__async=true&__source=waBrowse' % mediaId
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        printDBG(data)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False)
        for item in data:
            url = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            if self.cm.isValidUrl(url): return url
        
        url = 'http://www.veoh.com/rest/video/%s/details' % mediaId
        sts, data = self.cm.getPage(url)
        if not sts: return False
        
        printDBG(data)
        
        url = self.cm.ph.getSearchGroups(data, '''fullPreviewHashPath=['"]([^'^"]+?)['"]''')[0]
        if self.cm.isValidUrl(url): return url
        return False
        
    def parserSTREAMIXCLOUD(self, baseUrl):
        printDBG("parserSTREAMIXCLOUD url[%s]\n" % baseUrl)
        
        url = baseUrl.replace('/embed-', '/').replace('.html', '')
        
        HTTP_HEADER = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36', 
                       'Accept':'*/*', 'Accept-Encoding':'gzip, deflate', 'Referer': url}
        
        COOKIE_FILE = self.COOKIE_PATH + "streamix.cloud.cookie"
        # remove old cookie file
        rm(COOKIE_FILE)
        
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIE_FILE}
        
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)[1]
        post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
        try:
            sleep_time = int(self.cm.ph.getSearchGroups(data, '<span id="cxc">([0-9])</span>')[0])
            GetIPTVSleep().Sleep(sleep_time)
        except Exception:
            printExc()
        
        sts, data = self.cm.getPage(url, params, post_data)
        if not sts: return False
        
        sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, ">eval(", '</script>')
        # unpack and decode params from JS player script code
        tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams, 0, r2=True)
        printDBG(tmp)
        urlTab = []
        items = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source ', '>', False, False)
        if 0 == len(items): items = self.cm.ph.getDataBeetwenReMarkers(tmp, re.compile('''[\{\s]sources\s*[=:]\s*\['''), re.compile('''\]'''), False)[1].split('},')
        printDBG(items)
        domain = urlparser.getDomain(baseUrl)
        for item in items:
            item = item.replace('\/', '/')
            url  = self.cm.ph.getSearchGroups(item, '''(?:src|file)['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            if not url.lower().split('?', 1)[0].endswith('.mp4') or not self.cm.isValidUrl(url): continue
            type = self.cm.ph.getSearchGroups(item, '''type['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            res  = self.cm.ph.getSearchGroups(item, '''res['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            if res == '': res = self.cm.ph.getSearchGroups(item, '''label['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            lang = self.cm.ph.getSearchGroups(item, '''lang['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            url = strwithmeta(url, {'Referer':baseUrl})
            urlTab.append({'name':domain + ' {0} {1}'.format(lang, res), 'url':url})
        return urlTab
        
    def parserSTREAMANGOCOM(self, baseUrl):
        printDBG("parserSTREAMANGOCOM url[%s]\n" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER = dict(pageParser.HTTP_HEADER) 

        videoTab = []
        if '/embed/' not in baseUrl:
            sts, data = self.cm.getPage(baseUrl)
            if not sts: return videoTab
            url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?/embed/[^"^']+?)["']''', 1, True)[0]
            if url == '':
                data = self.cm.ph.getDataBeetwenMarkers(data, 'embedbox', '</textarea>')[1]
                data = clean_html(self.cm.ph.getDataBeetwenMarkers(data, '<textarea', '</textarea>')[1])
                url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=["'](http[^"^']+?/embed/[^"^']+?)["']''', 1, True)[0]
        else:
            url = baseUrl

        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)        
        sts, data = self.cm.getPage(url, {'header' : HTTP_HEADER})

        if not sts: 
            return videoTab
        
        cUrl = self.cm.meta['url']

        timestamp = time.time()

        errMsg = self.cm.ph.getDataBeetwenNodes(data, ('<', '>', 'important'), ('<', '>', 'div'))[1]
        SetIPTVPlayerLastHostError(clean_html(errMsg))

        mp4Tab=[]
        hlsTab=[]
        dashTab=[]
        
        # select valid section
        for video_data in re.findall(r'({[^}]*\bsrc\s*:\s*[^}]*})', data):
            mobj = re.search(r'(src\s*:\s*[^(]+\(([^)]*)\)[\s,]*)', video_data)
            if mobj is None:
                continue

            video_data = video_data.replace(mobj.group(0), '')
            
            printDBG("video format : %s" % video_data)
            m2obj = re.search(r'([\'"])(?P<src>(?:(?!\1).)+)\1\s*,\s*(?P<val>\d+)', mobj.group(1))
            if m2obj is None:
                continue

            src = m2obj.group('src')
            val = m2obj.group('val')
            
            if not (src and val):
                continue
            
            printDBG('src: %s - val: %s' % (src,val))
            ALPHABET = '=/+9876543210zyxwvutsrqponmlkjihgfedcbaZYXWVUTSRQPONMLKJIHGFEDCBA'
            encoded = re.sub(r'[^A-Za-z0-9+/=]', '', src)
            decoded = ''
            sm = [None] * 4
            i = 0
            str_len = len(encoded)
            while i < str_len:
                for j in range(4):
                    sm[j % 4] = ALPHABET.index(encoded[i])
                    i += 1
                char_code = ((sm[0] << 0x2) | (sm[1] >> 0x4)) ^ int(val)
                decoded += chr(char_code)
                if sm[2] != 0x40:
                    char_code = ((sm[1] & 0xf) << 0x4) | (sm[2] >> 0x2)
                    decoded += chr(char_code)
                if sm[3] != 0x40:
                    char_code = ((sm[2] & 0x3) << 0x6) | sm[3]
                    decoded += chr(char_code)
            
            if decoded.startswith('//'):
                decoded =  "http:" + decoded
            
            printDBG("decoded url: %s" % decoded )
            
            url = strwithmeta(decoded, {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':self.cm.meta['url'], 'Range':'bytes=0-'})
            
            if 'dash' in video_data:
                dashTab.extend(getMPDLinksWithMeta(url, False))
            elif 'hls' in video_data:
                hlsTab.extend(getDirectM3U8Playlist(url, checkExt=False, checkContent=True))
            elif 'mp4' in video_data or 'mpegurl' in video_data:
                mp4Tab.append({'name': video_data , 'url':url})

        videoTab.extend(mp4Tab)
        videoTab.extend(hlsTab)
        videoTab.extend(dashTab)
        if len(videoTab):
            wait = time.time() - timestamp
            if wait < 4:
                printDBG(" time [%s]" % wait)
                GetIPTVSleep().Sleep(3 - int(wait))
        
        return videoTab
        
    def parserCASACINEMACC(self, baseUrl):
        printDBG("parserCASACINEMACC url[%s]\n" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, "eval(", '</script>')[1]
        tmp = unpackJSPlayerParams(tmp, TEAMCASTPL_decryptPlayerParams, type=0)
        data += tmp
        
        printDBG(data)
        
        urlTab = self._findLinks(data, 'casacinema.cc')
        return urlTab
        
    def parserULTIMATEDOWN(self, baseUrl):
        printDBG("parserCASACINEMACC url[%s]\n" % baseUrl)
        if 'embed.php' not in baseUrl:
            videoId = self.cm.ph.getSearchGroups(baseUrl, 'ultimatedown\.com/([a-zA-z0-9]+?)/')[0]
            baseUrl = 'https://ultimatedown.com/plugins/mediaplayer/site/_embed.php?u=%s&w=640h=320' % videoId
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        urlTab = self._getSources(data)
        if len(urlTab): return urlTab
        return self._findLinks(data, contain='mp4')
        
    def parserFILEZTV(self, baseUrl):
        printDBG("parserFILEZTV url[%s]\n" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '.setup(', ')', False)[1].strip()
        printDBG(data)
        videoUrl = self.cm.ph.getSearchGroups(data, '''['"]?file['"]?\s*:\s*['"](http[^'^"]+?)['"]''')[0]
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        return False
        
    def parserWIIZTV(self, baseUrl):
        printDBG("parserWIIZTV url[%s]\n" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = { 'User-Agent':'Mozilla/5.0', 'Referer':referer}
        params = {'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, params) 
        if not sts: return False
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        playerUrl = self.cm.ph.getSearchGroups(data, '''<source[^>]+?src=["']([^'^"]+?)['"]''')[0]
        if self.cm.isValidUrl(playerUrl):
            playerUrl = urlparser.decorateUrl(playerUrl, {'iptv_proto':'m3u8', 'iptv_livestream':True, 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
            urlsTab = getDirectM3U8Playlist(playerUrl, checkExt=True, checkContent=True)
            if len(urlsTab):
                return urlsTab
        return False
        
    def parserTUNEINCOM(self, baseUrl):
        printDBG("parserTUNEINCOM url[%s]\n" % baseUrl)
        streamsTab = []
        
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0', 'Referer':baseUrl}
        
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'TuneIn.payload =', '});', False)[1].strip()
        tmp = json_loads(tmp)
        
        
        partnerId = self.cm.ph.getSearchGroups(data, '''partnerServiceId\s*=\s*['"]([^'^"]+?)['"]''')[0]
        if partnerId == '': partnerId = self.cm.ph.getSearchGroups(data, '''embedPartnerKey\s*=\s*['"]([^'^"]+?)['"]''')[0]
        
        stationId = tmp['EmbedPlayer']['guideItem']['Id']
        itemToken = tmp['EmbedPlayer']['guideItem']['Token']
        tuneType  = tmp['EmbedPlayer']['guideItem']['Type']
        
        url = 'http://tunein.com/tuner/tune/?tuneType=%s&preventNextTune=true&waitForAds=false&audioPrerollEnabled=false&partnerId=%s&stationId=%s&itemToken=%s' % (tuneType, partnerId, stationId, itemToken)
        
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return False
        data = json_loads(data)
        printDBG(data)
        printDBG("---")
        url  = data['StreamUrl']
        if url.startswith('//'): url = 'http:' + url
        
        sts, data = self.cm.getPage(url, {'header':HTTP_HEADER})
        if not sts: return False
        data = json_loads(data)
        printDBG(data)
        printDBG("---")
        
        for item in data['Streams']:
            url = item['Url']
            if item.get('Type') == 'Live':
                url = urlparser.decorateUrl(url, {'User-Agent':'VLC', 'iptv_livestream':True})
            if self.cm.isValidUrl(url):
                streamsTab.append({'name':'Type: %s, MediaType: %s, Bandwidth: %s' % (item['Type'], item['MediaType'], item['Bandwidth']), 'url':url})
        
        return streamsTab 
        
    def parserINDAVIDEOHU(self, baseUrl):
        printDBG("parserINDAVIDEOHU url[%s]\n" % baseUrl)
        urlTab = []
        
        templateUrl = 'http://amfphp.indavideo.hu/SYm0json.php/player.playerHandler.getVideoData/'
        videoId = self.cm.ph.getSearchGroups(baseUrl, 'indavideo\.hu/(?:player/video|video)/([0-9A-Za-z-_]+)')[0]
        
        url = templateUrl + videoId
        sts, data = self.cm.getPage(url)
        if not sts: return []
        data = json_loads(data)
        
        if data['success'] == '0': 
            sts, data = self.cm.getPage('http://indavideo.hu/video/%s' % videoId)
            if not sts: return []
        
            hash = self.cm.ph.getSearchGroups('emb_hash.+?value\s*=\s*"([^"]+)', data)[0]
            if '' == hash:
                SetIPTVPlayerLastHostError("File not found.")
                return []

            url = templateUrl + hash
            sts, data = self.cm.getPage(url)
            if not sts: return []
            data = json_loads(data)
        
        if data['success'] == '1':
            if not data['data'].get('video_files', []):
                SetIPTVPlayerLastHostError("File not found.")
                return []
            
            tmpTab = []
            for file in data['data']['video_files']:
                try:
                    name = self.cm.ph.getSearchGroups(file, '\.([0-9]+)\.mp4')[0]
                    url  = file + '&token=' + data['data']['filesh'][name]
                    if url not in tmpTab:
                        tmpTab.append(url)
                        urlTab.append({'name':name, 'url':url})
                except Exception:
                    printExc()

        return urlTab
        
    def parserSAPOPT(self, baseUrl):
        printDBG("parserSAPOPT baseUrl[%s]\n" % baseUrl)
        urlsTab = []
        
        #example http://rd3.videos.sapo.pt/playhtml?file=http://rd3.videos.sapo.pt/iMw78N7Nhv4rEz00MIN5/mov/1&
        #example "//vsports.videos.sapo.pt/qS105THDPkJB9nzFNA5h/mov/"

        videoUrl =  re.findall("(//[a-zA-Z0-9]+\.videos\.sapo\.pt/[\w]+/mov/)", baseUrl)
        
        if not videoUrl:
            # look for link in page
            sts, data = self.cm.getPage(baseUrl)
            if not sts: 
                return []
        
            videoUrl = re.findall("(//[a-zA-Z0-9]+\.videos\.sapo\.pt/[\w]+/mov/)", data)

        if videoUrl:
            videoUrl = "http:" + videoUrl[0] + "?videosrc=true"
            
            sts, link = self.cm.getPage(videoUrl)
            if sts:
                printDBG(" '%s' ---> '%s' " % (videoUrl, link))
                urlsTab.append({'name':'link', 'url': link })
                return urlsTab

        tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''['"]?sources['"]?\s*:\s*\['''), re.compile('\]'), False)[1]
        tmp = tmp.split('}')
        for item in tmp:
            videoUrl = self.cm.ph.getSearchGroups(item, '''['"]?src['"]?\s*:.*?['"]([^'^"]*?//[^'^"]+?)['"]''')[0]
            type = self.cm.ph.getSearchGroups(item, '''['"]?type['"]?\s*:\s*['"]([^'^"]+?)['"]''')[0]
            if videoUrl.startswith('//'): videoUrl = 'http:' + videoUrl
            if self.cm.isValidUrl(videoUrl):
                urlsTab.append({'name':type, 'url':videoUrl})
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '.setup(', ');', False)[1].strip()
        printDBG(data)
        videoUrl = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?\s*:\s*['"]((?:https?:)?//[^"^']+\.mp4)['"]''')[0]
        if videoUrl.startswith('//'): videoUrl = 'http:' + videoUrl
        if self.cm.isValidUrl(videoUrl):
            urlsTab.append({'name':'direct', 'url':videoUrl})
        
        return urlsTab
        
    def parserPUBLICVIDEOHOST(self, baseUrl):
        printDBG("parserPUBLICVIDEOHOST baseUrl[%s]\n" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts: return []
        
        data = self.cm.ph.getDataBeetwenMarkers(data, 'playlist:', ']', False)[1].strip()
        printDBG(data)
        videoUrl = self.cm.ph.getSearchGroups(data, r'''['"]?file['"]?\s*:\s*['"]((?:https?:)?//[^"^']+(?:\.mp4|\.flv))['"]''')[0]
        if videoUrl.startswith('//'): videoUrl = 'http:' + videoUrl
        if self.cm.isValidUrl(videoUrl):
            return videoUrl
        return False
        
    def parserVIDEAHU(self, baseUrl):
        printDBG("parserVIDEAHU baseUrl[%s]\n" % baseUrl)
        
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = { 'User-Agent':'Mozilla/5.0', 'Referer':referer}
        params = {'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return []
        
        f = self.cm.ph.getSearchGroups(data, '''"/player\?f=([0-9\.]+?)&''')[0]
        if f == '': return []
        
        sts, data = self.cm.getPage('http://videa.hu/videaplayer_get_xml.php?f={0}&start=0&enablesnapshot=0&platform=desktop&referrer={1}'.format(f, urllib.quote(baseUrl)))
        if not sts: return []
        
        urlTab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video_sources', '</video_sources>', False)[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<video_source', '</video_source>')
        for item in data:
            printDBG(item)
            url  = self.cm.ph.getDataBeetwenMarkers(item, '>', '<', False)[1].strip()
            if url.startswith('//'):
                url = 'http:' + url
            if not url.startswith('http'):
                continue
                
            printDBG('>>>>>>>>>>>>> ' + url)
            
            if 'video/mp4' in item:
                width  = self.cm.ph.getSearchGroups(item, '''width=['"]([^"^']+?)['"]''')[0]
                height = self.cm.ph.getSearchGroups(item, '''height=['"]([^"^']+?)['"]''')[0]
                name   = self.cm.ph.getSearchGroups(item, '''name=['"]([^"^']+?)['"]''')[0]
                url    = urlparser.decorateUrl(url, {'Referer':baseUrl,  'User-Agent':HTTP_HEADER['User-Agent']})
                urlTab.append({'name':'{0} - {1}x{2}'.format(name, width, height), 'url':url})
            elif 'mpegurl' in item:
                url = urlparser.decorateUrl(url, {'iptv_proto':'m3u8', 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
                tmpTab = getDirectM3U8Playlist(url, checkExt=False, checkContent=True)
                urlTab.extend(tmpTab)
        urlTab.reverse()
        return urlTab
    
    def parserAFLAMYZCOM(self, baseUrl):
        printDBG("parserAFLAMYZCOM baseUrl[%s]\n" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = { 'User-Agent':'Mozilla/5.0', 'Referer':referer}
        params = {'header':HTTP_HEADER}
        
        tries = 0
        while tries < 5 and baseUrl != '':
            tries += 1
            sts, data = self.cm.getPage(baseUrl, params)
            if not sts: return []
            
            printDBG(data)
            
            urlTab = []
            tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '.setup(', ')')
            for item in tmp:
                printDBG(item)
                url  = self.cm.ph.getSearchGroups(item, '''['"]?file['"]?\s*:\s*['"]([^"^']+?)['"]''')[0]
                if url.startswith('//'): url = 'http:' + url
                if not url.startswith('http'): continue
                type = self.cm.ph.getSearchGroups(item, '''['"]?type['"]?\s*:\s*['"]([^"^']+?)['"]''')[0].lower()
                printDBG('>>>>>>>>>>>>> ' + url)
                
                if 'mp4' in type:
                    url    = urlparser.decorateUrl(url, {'Referer':baseUrl,  'User-Agent':HTTP_HEADER['User-Agent']})
                    urlTab.insert(0, {'name':type, 'url':url})
                elif 'mpegurl' in type or 'hls' in type:
                    url = urlparser.decorateUrl(url, {'iptv_proto':'m3u8', 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
                    tmpTab = getDirectM3U8Playlist(url, checkExt=False, variantCheck=False, checkContent=True)
                    try: tmpTab = sorted(tmpTab, key=lambda item: int(item.get('bitrate', '0')))
                    except Exception: pass
                    urlTab.extend(tmpTab)
                elif 'dash' in type:
                    url = urlparser.decorateUrl(url, {'iptv_proto':'dash', 'Referer':baseUrl, 'Origin':urlparser.getDomain(baseUrl, False), 'User-Agent':HTTP_HEADER['User-Agent']})
                    urlTab.extend(getMPDLinksWithMeta(url, False))
            urlTab.reverse()
            if len(urlTab) == 0:
                url = self.cm.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0], self.cm.meta['url'])
                if url != '': 
                    printDBG(url)
                    urlTab = urlparser().getVideoLinkExt(strwithmeta(url, MergeDicts(baseUrl.meta, {'Referer':self.cm.meta['url']})))
                    break
            if len(urlTab) == 0:
                url = self.cm.ph.getSearchGroups(data, '''<meta[^>]+?([^>]+?refresh[^>]+?)>''', 1, True)[0]
                url = self.cm.getFullUrl(self.cm.ph.getSearchGroups(url, '''url=([^'^"]+?)['"]''', 1, True)[0], self.cm.meta['url'])
                baseUrl = strwithmeta(url, MergeDicts(baseUrl.meta, {'Referer':self.cm.meta['url']}))
            else:
                break
        return urlTab
    
    def parserKINGVIDTV(self, baseUrl):
        printDBG("parserKINGVIDTV url[%s]\n" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = { 'User-Agent':'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10',
                        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Referer': referer
                      }
        
        COOKIE_FILE = self.COOKIE_PATH + "kingvidtv.to.cookie"
        # remove old cookie file
        rm(COOKIE_FILE)
        
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIE_FILE}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</Form>', False, False)[1]
        if tmp != '':
            data = tmp
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', data))
            try:
                sleep_time = int(self.cm.ph.getSearchGroups(data, '<span id="cxc">([0-9])</span>')[0])
                GetIPTVSleep().Sleep(sleep_time)
            except Exception:
                printExc()
            
            sts, data = self.cm.getPage(baseUrl, params, post_data)
            if not sts: return False
        
        sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, ">eval(", '</script>')
        if sts:
            # unpack and decode params from JS player script code
            tmp = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams, 0, r2=True)
            printDBG(tmp)
            tab = self._findLinks(tmp, urlparser.getDomain(baseUrl), contain='.mp4')
            return tab
        return False
        
    def _parserEKSTRAKLASATV(self, ckmId):
        printDBG("_parserEKSTRAKLASATV ckmId[%r]" % ckmId )
        tm = str(int(time.time() * 1000))
        jQ = str(randrange(562674473039806,962674473039806))
        authKey = 'FDF9406DE81BE0B573142F380CFA6043'
        contentUrl = 'http://qi.ckm.onetapi.pl/?callback=jQuery183040'+ jQ + '_' + tm + '&body%5Bid%5D=' + authKey + '&body%5Bjsonrpc%5D=2.0&body%5Bmethod%5D=get_asset_detail&body%5Bparams%5D%5BID_Publikacji%5D=' + ckmId + '&body%5Bparams%5D%5BService%5D=ekstraklasa.onet.pl&content-type=application%2Fjsonp&x-onet-app=player.front.onetapi.pl&_=' + tm
        sts, data = self.cm.getPage(contentUrl)
        valTab = []
        if sts:
            try:
                result = json_loads(data[data.find("(")+1:-2])
                strTab = []
                valTab = []
                for items in result['result']['0']['formats']['wideo']:
                    for i in range(len(result['result']['0']['formats']['wideo'][items])):
                        strTab.append(items)
                        strTab.append(result['result']['0']['formats']['wideo'][items][i]['url'])
                        if result['result']['0']['formats']['wideo'][items][i]['video_bitrate']:
                            strTab.append(int(float(result['result']['0']['formats']['wideo'][items][i]['video_bitrate'])))
                        else:
                            strTab.append(0)
                        valTab.append(strTab)
                        strTab = []
            except Exception:
                printExc()
        return valTab
        
    def parserEKSTRAKLASATV(self, baseUrl):
        printDBG("parserEKSTRAKLASATV url[%s]\n" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        url = baseUrl

        videoUrls = []
        tries = 0
        while tries < 2:
            tries += 1
            sts, data = self.cm.getPage(url)
            if not sts: return videoUrls
            ckmId = self.cm.ph.getSearchGroups(data, 'data-params-mvp="([^"]+?)"')[0]
            if '' == ckmId: ckmId = self.cm.ph.getSearchGroups(data, 'id="mvp:([^"]+?)"')[0]
            if '' == ckmId: ckmId = self.cm.ph.getSearchGroups(data, 'data\-mvp="([^"]+?)"')[0]
            if '' != ckmId: 
                tab = self._parserEKSTRAKLASATV(ckmId)
                break
            tmp = ph.find(data, 'pulsembed_embed', '</div>')[1]
            url = ph.getattr(tmp, 'href')
            if url == '':
                tmp = ph.find(data, ('<div', '>', 'embeddedApp'), ('</div', '>'), flags=0)[1]
                tmp = ph.clean_html(self.cm.ph.getSearchGroups(tmp, '''data\-params=['"]([^'^"]+?)['"]''')[0])
                try:
                    tmp = json_loads(tmp)['parameters']['embedCode']
                    url = self.cm.getFullUrl(self.cm.ph.getSearchGroups(tmp, 'data\-src="([^"]+?)"')[0], self.cm.meta['url'])
                except Exception:
                    printExc()

        for item in tab:
            if item[0] != 'mp4': continue
            
            name = "[%s] %s" % (item[0], item[2])
            url  = item[1]
            videoUrls.append({'name':name, 'url':url, 'bitrate':item[2]})

        return videoUrls
        
    def parserUPLOAD2(self, baseUrl):
        printDBG("parserUPLOAD2 baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
            
        self.cm.getPage(baseUrl, {'max_data_size':0})
        baseUrl = self.cm.meta['url']

        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        
        for marker in ['File Not Found', 'The file you were looking for could not be found, sorry for any inconvenience.']:
            if marker in data: SetIPTVPlayerLastHostError(_(marker))
            
        tries = 5
        while tries > 0:
            tries -= 1
            sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, 'method="POST"', '</form>', caseSensitive=False)
            if not sts: break
        
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            for key in post_data:
                post_data[key] = clean_html(post_data[key])
            HTTP_HEADER['Referer'] = baseUrl
        
            try:
                sleep_time = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<span[^>]+?id="countdown'), re.compile('</span>'))[1]
                sleep_time = self.cm.ph.getSearchGroups(sleep_time, '>\s*([0-9]+?)\s*<')[0]
                if '' != sleep_time: GetIPTVSleep().Sleep(int(sleep_time))
            except Exception: pass
                            
            sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER}, post_data )
            if not sts: return False
        
        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)
        
        videoData = self.cm.ph.rgetDataBeetwenMarkers2(data, '>download<', '<a ', caseSensitive=False)[1]
        printDBG('videoData[%s]' % videoData)
        videoUrl = self.cm.ph.getSearchGroups(videoData, 'href="([^"]+?)"')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl
        
        videoUrl = self.cm.ph.getSearchGroups(data, '''<[^>]+?class="downloadbtn"[^>]+?['"](https?://[^'^"]+?)['"]''')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl  

        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'class="downloadbtn"', '</a>', caseSensitive=False)[1]
        videoUrl = self.cm.ph.getSearchGroups(tmp, '''['"](https?://[^'^"]+?)['"]''')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl  
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'direct link', '</a>', caseSensitive=False)[1]
        videoUrl = self.cm.ph.getSearchGroups(tmp, '''['"](https?://[^'^"]+?)['"]''')[0]
        if self.cm.isValidUrl(videoUrl): return videoUrl  
        
        return False
        
    def parserSTOPBOTTK(self, baseUrl):
        printDBG("parserSTOPBOTTK baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        
        HTTP_HEADER = { 'User-Agent':     'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10',
                        'Accept':         'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 
                        'Accept-Encoding':'gzip, deflate',
                      }
        if referer != '': HTTP_HEADER['Referer'] = referer
        
        COOKIE_FILE = self.COOKIE_PATH + "stopbot.tk.cookie"
        rm(COOKIE_FILE)
        
        urlParams = {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIE_FILE}
        
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, 'function bot()', '});')[1]
        botUrl = urljoin(baseUrl, self.cm.ph.getSearchGroups(tmp, '''['"]?url["']?\s*:\s*['"]([^'^"]+?)['"]''')[0])
        raw_post_data = self.cm.ph.getSearchGroups(tmp, '''['"]?data["']?\s*:\s*['"]([^'^"]+?)['"]''')[0]
        
        url = urljoin(baseUrl, '/scripts/jquery.min.js')
        
        sts, data = self.cm.getPage(url, urlParams)
        if not sts: return False
        
        session_ms = ''
        session_id = ''
        cookieItems = {}
        
        jscode = self.cm.ph.getDataBeetwenMarkers(data, 'function csb()', 'csb();')[1]
        part1 = base64.b64decode('''dmFyIGRvY3VtZW50ID0ge307DQpmdW5jdGlvbiBhdG9iKHIpe3ZhciBuPS9bXHRcblxmXHIgXS9nLHQ9KHI9U3RyaW5nKHIpLnJlcGxhY2UobiwiIikpLmxlbmd0aDt0JTQ9PTAmJih0PShyPXIucmVwbGFjZSgvPT0/JC8sIiIpKS5sZW5ndGgpO2Zvcih2YXIgZSxhLGk9MCxvPSIiLGY9LTE7KytmPHQ7KWE9IkFCQ0RFRkdISUpLTE1OT1BRUlNUVVZXWFlaYWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXowMTIzNDU2Nzg5Ky8iLmluZGV4T2Yoci5jaGFyQXQoZikpLGU9aSU0PzY0KmUrYTphLGkrKyU0JiYobys9U3RyaW5nLmZyb21DaGFyQ29kZSgyNTUmZT4+KC0yKmkmNikpKTtyZXR1cm4gb30NCnZhciB3aW5kb3cgPSB0aGlzOw0KDQpTdHJpbmcucHJvdG90eXBlLml0YWxpY3M9ZnVuY3Rpb24oKXtyZXR1cm4gIjxpPjwvaT4iO307DQpTdHJpbmcucHJvdG90eXBlLmxpbms9ZnVuY3Rpb24oKXtyZXR1cm4gIjxhIGhyZWY9XCJ1bmRlZmluZWRcIj48L2E+Ijt9Ow0KU3RyaW5nLnByb3RvdHlwZS5mb250Y29sb3I9ZnVuY3Rpb24oKXtyZXR1cm4gIjxmb250IGNvbG9yPVwidW5kZWZpbmVkXCI+PC9mb250PiI7fTsNCkFycmF5LnByb3RvdHlwZS5maW5kPSJmdW5jdGlvbiBmaW5kKCkgeyBbbmF0aXZlIGNvZGVdIH0iOw0KQXJyYXkucHJvdG90eXBlLmZpbGw9ImZ1bmN0aW9uIGZpbGwoKSB7IFtuYXRpdmUgY29kZV0gfSI7DQpmdW5jdGlvbiBmaWx0ZXIoKQ0Kew0KICAgIGZ1biA9IGFyZ3VtZW50c1swXTsNCiAgICB2YXIgbGVuID0gdGhpcy5sZW5ndGg7DQogICAgaWYgKHR5cGVvZiBmdW4gIT0gImZ1bmN0aW9uIikNCiAgICAgICAgdGhyb3cgbmV3IFR5cGVFcnJvcigpOw0KICAgIHZhciByZXMgPSBuZXcgQXJyYXkoKTsNCiAgICB2YXIgdGhpc3AgPSBhcmd1bWVudHNbMV07DQogICAgZm9yICh2YXIgaSA9IDA7IGkgPCBsZW47IGkrKykNCiAgICB7DQogICAgICAgIGlmIChpIGluIHRoaXMpDQogICAgICAgIHsNCiAgICAgICAgICAgIHZhciB2YWwgPSB0aGlzW2ldOw0KICAgICAgICAgICAgaWYgKGZ1bi5jYWxsKHRoaXNwLCB2YWwsIGksIHRoaXMpKQ0KICAgICAgICAgICAgICAgIHJlcy5wdXNoKHZhbCk7DQogICAgICAgIH0NCiAgICB9DQogICAgcmV0dXJuIHJlczsNCn07DQpPYmplY3QuZGVmaW5lUHJvcGVydHkoZG9jdW1lbnQsICJjb29raWUiLCB7DQogICAgZ2V0IDogZnVuY3Rpb24gKCkgew0KICAgICAgICByZXR1cm4gdGhpcy5fY29va2llOw0KICAgIH0sDQogICAgc2V0IDogZnVuY3Rpb24gKHZhbCkgew0KICAgICAgICBwcmludCh2YWwpOw0KICAgICAgICB0aGlzLl9jb29raWUgPSB2YWw7DQogICAgfQ0KfSk7DQpBcnJheS5wcm90b3R5cGUuZmlsdGVyID0gZmlsdGVyOw0KDQp2YXIgc2Vzc2lvbl9tczsNCnZhciBzZXNzaW9uX2lkOw==''') 
        part2 =  base64.b64decode('''DQpwcmludCgiXG5zZXNzaW9uX21zPSIgKyBzZXNzaW9uX21zICsgIjtcbiIpOw0KcHJpbnQoIlxzZXNzaW9uX2lkPSIgKyBzZXNzaW9uX2lkICsgIjtcbiIpOw0KDQo=''')
        jscode = part1 + '\n' + jscode + '\n' + part2
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            decoded = ret['data'].strip()
            decoded = decoded.split('\n')
            for line in decoded:
                line = line.strip()
                line = line.split(';')[0]
                line = line.replace(' ', '').split('=')
                if 2 != len(line): continue
                name  = line[0].strip()
                value = line[1].split(';')[0].strip()
                if name == 'session_ms':
                    session_ms = int(value)
                elif name == 'session_id':
                    session_id = int(value)
                else:
                    cookieItems[name] = value
        urlParams['cookie_items']  = cookieItems
        urlParams['raw_post_data'] = True
        
        GetIPTVSleep().Sleep(1)
        sts, data = self.cm.getPage(botUrl, urlParams, raw_post_data + str(session_id)) # 
        if not sts: return False
        printDBG(data)
        data = json_loads(data)
        if str(data['error']) == '0' and self.cm.isValidUrl(data['message']):
            return urlparser().getVideoLinkExt(data['message'])
        else:
            SetIPTVPlayerLastHostError(data['message']+' Error: ' + str(data['error']))
        return []
        
    def parserPOLSATSPORTPL(self, baseUrl):
        printDBG("parserPOLSATSPORTPL baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)

        domain = urlparser.getDomain(baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        
        sts, tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')
        if not sts: return False
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>')
        
        videoTab = []
        for item in tmp:
            if 'video/mp4' not in item and 'video/x-flv' not in item: continue
            tType = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0].replace('video/', '')
            tUrl  = self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0]
            printDBG(tUrl)
            if self.cm.isValidUrl(tUrl):
                videoTab.append({'name':'[%s] %s' % (tType, domain), 'url':strwithmeta(tUrl)})#, {'User-Agent': userAgent})})
        return videoTab
        
    def parserSHAREVIDEOPL(self, baseUrl):
        printDBG("parserSHAREVIDEOPL url[%s]\n" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' }
        COOKIE_FILE = GetCookieDir("sharevideo.pl.cookie")
        rm (COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIE_FILE}
        
        videoTab = []
        baseUrl = baseUrl.replace('/f/', '/e/')
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return videoTab
        
        post_data = {}
        try:
            tmp = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('<form[^>]+?method="post"[^>]*?>', re.IGNORECASE), re.compile('</form>', re.IGNORECASE), False)[1]
            post_data = dict(re.findall(r'<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp))
            post_data.update(dict(re.findall(r'<button[^>]*name="([^"]*)"[^>]*value="([^"]*)"[^>]*>', tmp)))
        except Exception:
            printExc()
        sleep_time = self.cm.ph.getSearchGroups(tmp, '''\s([0-9]+?)s''')[0]
        printDBG("Wait for: %s" % sleep_time)
        if sleep_time == '': sleep_time = 5
        else: sleep_time = int(sleep_time)
        
        GetIPTVSleep().Sleep(sleep_time)
        videoTab = []
        HTTP_HEADER['Referer'] = baseUrl
        sts, data = self.cm.getPage(baseUrl, params, post_data)
        if not sts: return False
        
        videoTags = self.cm.ph.getAllItemsBeetwenMarkers(data, '<video', '>')
        if len(videoTags) == 0: return
        
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script', '</script>')
        tmp = ''
        for item in data:
            if 'eval(' in item:
                tmp += '\n %s' % self.cm.ph.getDataBeetwenReMarkers(item, re.compile('<script[^>]*?>'), re.compile('</script>'), False)[1].strip()
        
        jscode = base64.b64decode('''ZnVuY3Rpb24gaXRhbGljcygpe3JldHVybiI8aT4iK3RoaXMrIjwvaT4ifWZ1bmN0aW9uIGxpbmsoKXtyZXR1cm4nPGEgaHJlZj0iJythcmd1bWVudHNbMF0ucmVwbGFjZSgnIicsIiZxdW90ZTsiKSsnIj4nK3RoaXMrIjwvYT4ifWZ1bmN0aW9uIGZvbnRjb2xvcigpe3JldHVybic8Zm9udCBjb2xvcj0iJythcmd1bWVudHNbMF0rJyI+Jyt0aGlzKyI8L2ZvbnQ+In1mdW5jdGlvbiBmaW5kKCl7dmFyIHQsbj1hcmd1bWVudHNbMF0sZT1hcmd1bWVudHNbMV0scj1PYmplY3QodGhpcyksaT0wO2lmKCJudW1iZXIiPT10eXBlb2Ygci5sZW5ndGgmJnIubGVuZ3RoPj0wKWZvcih0PU1hdGguZmxvb3Ioci5sZW5ndGgpO3Q+aTsrK2kpaWYobi5jYWxsKGUscltpXSxpLHIpKXJldHVybiByW2ldfWZ1bmN0aW9uIGVudHJpZXMoKXt2YXIgdD1PYmplY3QodGhpcyk7cmV0dXJuIG5ldyBBcnJheUl0ZXJhdG9yKHQsMSl9ZnVuY3Rpb24gZmlsbCgpe2Zvcih2YXIgdD1hcmd1bWVudHNbMF0sbj1PYmplY3QodGhpcyksZT1wYXJzZUludChuLmxlbmd0aCwxMCkscj1hcmd1bWVudHNbMV0saT1wYXJzZUludChyLDEwKXx8MCxvPTA+aT9NYXRoLm1heChlK2ksMCk6TWF0aC5taW4oaSxlKSxzPWFyZ3VtZW50c1syXSx1PXZvaWQgMD09PXM/ZTpwYXJzZUludChzKXx8MCxhPTA+dT9NYXRoLm1heChlK3UsMCk6TWF0aC5taW4odSxlKTthPm87bysrKW5bb109dDtyZXR1cm4gbn1mdW5jdGlvbiBmaWx0ZXIoKXtmdW49YXJndW1lbnRzWzBdO3ZhciB0PXRoaXMubGVuZ3RoO2lmKCJmdW5jdGlvbiIhPXR5cGVvZiBmdW4pdGhyb3cgbmV3IFR5cGVFcnJvcjtmb3IodmFyIG49bmV3IEFycmF5LGU9YXJndW1lbnRzWzFdLHI9MDt0PnI7cisrKWlmKHIgaW4gdGhpcyl7dmFyIGk9dGhpc1tyXTtmdW4uY2FsbChlLGkscix0aGlzKSYmbi5wdXNoKGkpfXJldHVybiBufWZ1bmN0aW9uIHNldFRpbWVvdXQoKXt9ZnVuY3Rpb24gRGF0ZSgpe3JldHVybiJTdW4gU2VwIDE3IDIwMTcgMjM6NTQ6NDMgR01UKzAyMDAgKENlbnRyYWwgRXVyb3BlYW4gRGF5bGlnaHQgVGltZSkifXZhciBpcHR2X3NyY2VzPVtdLGRvY3VtZW50PXt9LHdpbmRvdz10aGlzO1N0cmluZy5wcm90b3R5cGUuaXRhbGljcz1pdGFsaWNzLFN0cmluZy5wcm90b3R5cGUubGluaz1saW5rLFN0cmluZy5wcm90b3R5cGUuZm9udGNvbG9yPWZvbnRjb2xvcjt2YXIgQXJyYXlJdGVyYXRvcj1mdW5jdGlvbih0LG4pe3RoaXMuX2FycmF5PXQsdGhpcy5fZmxhZz1uLHRoaXMuX25leHRJbmRleD0wfTtBcnJheS5wcm90b3R5cGUuZmlsdGVyPWZpbHRlcixBcnJheS5wcm90b3R5cGUuZmlsbD1maWxsLEFycmF5LnByb3RvdHlwZS5lbnRyaWVzPWVudHJpZXMsQXJyYXkucHJvdG90eXBlLmZpbmQ9ZmluZDt2YXIgZWxlbWVudD1mdW5jdGlvbih0KXt0aGlzLl9uYW1lPXQsdGhpcy5fc3JjPSIiLHRoaXMuX2lubmVySFRNTD0iIix0aGlzLl9wYXJlbnRFbGVtZW50PSIiLHRoaXMuc2hvdz1mdW5jdGlvbigpe30sdGhpcy5hdHRyPWZ1bmN0aW9uKHQsbil7cmV0dXJuInNyYyI9PXQmJiIjdmlkZW8iPT10aGlzLl9uYW1lJiZpcHR2X3NyY2VzLnB1c2gobiksdGhpc30sdGhpcy5tZWRpYWVsZW1lbnRwbGF5ZXI9ZnVuY3Rpb24oKXt9LE9iamVjdC5kZWZpbmVQcm9wZXJ0eSh0aGlzLCJzcmMiLHtnZXQ6ZnVuY3Rpb24oKXtyZXR1cm4gdGhpcy5fc3JjfSxzZXQ6ZnVuY3Rpb24odCl7dGhpcy5fc3JjPXQscHJpbnREQkcodCl9fSksT2JqZWN0LmRlZmluZVByb3BlcnR5KHRoaXMsImlubmVySFRNTCIse2dldDpmdW5jdGlvbigpe3JldHVybiB0aGlzLl9pbm5lckhUTUx9LHNldDpmdW5jdGlvbih0KXt0aGlzLl9pbm5lckhUTUw9dH19KSxPYmplY3QuZGVmaW5lUHJvcGVydHkodGhpcywicGFyZW50RWxlbWVudCIse2dldDpmdW5jdGlvbigpe3JldHVybiBuZXcgZWxlbWVudH0sc2V0OmZ1bmN0aW9uKHQpe319KX0sJD1mdW5jdGlvbih0KXtyZXR1cm4gbmV3IGVsZW1lbnQodCl9O2RvY3VtZW50LmdldEVsZW1lbnRCeUlkPWZ1bmN0aW9uKHQpe3JldHVybiBuZXcgZWxlbWVudCh0KX0sZG9jdW1lbnQuY3VycmVudFNjcmlwdD1uZXcgZWxlbWVudCxkb2N1bWVudC5ib2R5PW5ldyBlbGVtZW50LGRvY3VtZW50LmRvY3VtZW50RWxlbWVudD1uZXcgZWxlbWVudCx0aGlzLnRvU3RyaW5nPWZ1bmN0aW9uKCl7cmV0dXJuIltvYmplY3QgV2luZG93XSJ9Ow==''')
        jscode += tmp + '\nprint(JSON.stringify(iptv_srces));'
        tmp = []
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            tmp = ret['data'].strip()
            tmp = json_loads(tmp)
        
        cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
        dashTab = []
        hlsTab = []
        mp4Tab = []
        for idx in range(len(videoTags)):
            item = videoTags[idx]
            print(item)
            url = tmp[idx]
            printDBG("url -> " + url)
            if url.startswith('//'): url = 'http:' + url
            type = self.cm.ph.getSearchGroups(item, r'''['"]?type['"]?\s*[:=]\s*['"]([^"^']+)['"]''')[0]
            if not self.cm.isValidUrl(url): continue
        
            url = strwithmeta(url, {'Cookie':cookieHeader, 'Referer':HTTP_HEADER['Referer'], 'User-Agent':HTTP_HEADER['User-Agent']})
            if 'dash' in type:
                dashTab.extend(getMPDLinksWithMeta(url, False))
            elif 'hls' in type:
                hlsTab.extend(getDirectM3U8Playlist(url, checkExt=False, checkContent=True))
            elif 'mp4' in type or 'mpegurl' in type:
                name = self.cm.ph.getSearchGroups(item, '''['"]?height['"]?\s*[:=]\s*['"]?([0-9]+?)[^0-9]''')[0]
                mp4Tab.append({'name':'[%s] %sp' % (type, name), 'url':url})
        
        videoTab.extend(mp4Tab)
        videoTab.extend(hlsTab)
        videoTab.extend(dashTab)
        return videoTab
        
    def parserGAMOVIDEOCOM(self, baseUrl):
        printDBG("parserGAMOVIDEOCOM baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', '')

        domain = urlparser.getDomain(baseUrl) 
        HEADER = self.cm.getDefaultHeader(browser='chrome')
        HEADER['Referer'] = referer

        sts, data = self.cm.getPage(baseUrl, {'header': HEADER})
        if not sts: return False

        if 'embed' not in self.cm.meta['url'].lower():
            HEADER['Referer'] = self.cm.meta['url']
            url = self.cm.getFullUrl(self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?embed[^"^']+?)['"]''', 1, True)[0], self.cm.meta['url'])
            sts, data = self.cm.getPage(url, {'header': HEADER})
            if not sts: return False

        jscode = [self.jscode['jwplayer']]
        jscode.append('var element=function(n){print(JSON.stringify(n)),this.on=function(){}},Clappr={};Clappr.Player=element,Clappr.Events={PLAYER_READY:1,PLAYER_TIMEUPDATE:1,PLAYER_PLAY:1,PLAYER_ENDED:1};')
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item and 'jwplayer' in item:
                jscode.append(item)

        ret = js_execute( '\n'.join(jscode) )
        if ret['sts']:
            data += ret['data']

        urlTab = []
        items = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source ', '>', False, False)
        if 0 == len(items): items = self.cm.ph.getDataBeetwenReMarkers(data, re.compile('''[\s'"]sources[\s'"]*[=:]\s*\['''), re.compile('''\]'''), False)[1].split('},')
        printDBG(items)
        for item in items:
            item = item.replace('\/', '/')
            url  = self.cm.ph.getSearchGroups(item, '''(?:src|file)['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            if not url.lower().split('?', 1)[0].endswith('.mp4') or not self.cm.isValidUrl(url): continue
            type = self.cm.ph.getSearchGroups(item, '''type['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            res  = self.cm.ph.getSearchGroups(item, '''res['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            lang = self.cm.ph.getSearchGroups(item, '''lang['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
            url = strwithmeta(url, {'Referer':baseUrl})
            urlTab.append({'name':domain + ' {0} {1}'.format(lang, res), 'url':url})
        return urlTab
        
    def parserWIDESTREAMIO(self, baseUrl):
        printDBG("parserWIDESTREAMIO baseUrl[%s]" % baseUrl)
        domain = urlparser.getDomain(baseUrl) 
        
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', '')
        
        HTTP_HEADER = {} #self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['User-Agent'] = 'Mozilla/5.0'
        if referer != '': HTTP_HEADER['Referer'] = referer
        params = {'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False

        libsPath = GetPluginDir('libs/')
        HTTP_HEADER['Referer'] = baseUrl
        urlTab = []
        data = set(re.compile('''['"](https?://[^'^"]+?\.m3u8(?:\?[^'^"]+?)?)['"]''').findall(data))
        for streamUrl in data:
            streamUrl = urlparser.decorateUrl(streamUrl, HTTP_HEADER)
            tmp = getDirectM3U8Playlist(streamUrl, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999)
            if len(tmp):
                try: port = config.plugins.iptvplayer.livesports_port.value
                except Exception: port = 8193
                pyCmd = GetPyScriptCmd('keepalive_proxy') + ' "%s" "%s" "%s" "%s" "%s" ' % (port, libsPath, HTTP_HEADER['User-Agent'], HTTP_HEADER['Referer'], str(streamUrl))
                meta = {'iptv_proto':'em3u8'}
                meta['iptv_refresh_cmd'] = pyCmd
                streamUrl = urlparser.decorateUrl("ext://url/" + streamUrl, meta)
                urlTab.append({'name':'em3u8', 'url':streamUrl})
        return urlTab
        
    def parserMEDIAFIRECOM(self, baseUrl):
        printDBG("parserMEDIAFIRECOM baseUrl[%s]" % baseUrl)
        HEADER = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0', 'Accept':'*/*', 'Accept-Encoding':'gzip, deflate'}
        sts, data = self.cm.getPage(baseUrl, {'header': HEADER})
        if not sts: return False
        
        data = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', '"download_link"'), ('</div', '>'))[1]
        data = self.cm.ph.getDataBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)[1]
        
        jscode = '''window=this;document={};document.write=function(){print(arguments[0]);}'''
        ret = js_execute( jscode + '\n' + data )
        if ret['sts'] and 0 == ret['code']:
            videoUrl = self.cm.ph.getSearchGroups(ret['data'], '''href=['"]([^"^']+?)['"]''')[0]
            if self.cm.isValidUrl(videoUrl):
                return videoUrl
        return False
    
    def parserGOUNLIMITEDTO(self, baseUrl):
        printDBG("parserGOUNLIMITEDTO baseUrl[%s]" % baseUrl)
        domain = urlparser.getDomain(baseUrl) 
        
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', '')
        
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        if referer != '': HTTP_HEADER['Referer'] = referer
        
        sts, data = self.cm.getPage(baseUrl, {'header': HTTP_HEADER})
        if not sts: 
            return False
        
        printDBG(data)

        urlTab = []
        
        
        tmpTab = re.findall("(eval\(.*?</script>)", data, re.S)
        
        printDBG(str(tmpTab))
        for tmp in tmpTab:
            if not '(p,a,c,k,e,d)' in tmp:
                continue
            tmp2 = unpackJSPlayerParams(">" + tmp, VIDUPME_decryptPlayerParams, 0, r2=True)

            printDBG("=======================================")
            printDBG(tmp2)
            printDBG("=======================================")

            if 'src' in tmp2:
                # example src:"https://fs334.gounlimited.to/tea5vqyj4x2qzxfffp4ytplhutz7fs3un33ig4tezbrdlp6icc4ttdu7l4jq/v.mp4"
                urls = re.findall("src:[\"']([^\"^']+)[\"']", tmp2)
            
            for u in urls:
                if self.cm.isValidUrl(u):
                    u = strwithmeta(u, {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':baseUrl})
                    urlTab.append({'name': 'link', 'url':u})
            
            printDBG(urlTab)
        
        return urlTab
        
    def parserNADAJECOM(self, baseUrl):
        printDBG("parserNADAJECOM baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        referer = baseUrl.meta.get('Referer', baseUrl)
        origin = self.cm.getBaseUrl(referer)[:-1]
        USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.0'
        HEADER = {'User-Agent':USER_AGENT, 'Accept':'*/*', 'Content-Type':'application/json', 'Accept-Encoding':'gzip, deflate', 'Referer':referer, 'Origin':origin}
        
        videoId = self.cm.ph.getSearchGroups(baseUrl + '/', '''/video/([0-9]+?)/''')[0]
        
        sts, data = self.cm.getPage('https://nadaje.com/api/1.0/services/video/%s/' % videoId, {'header': HEADER})
        if not sts: return False
        
        linksTab = []
        data = json_loads(data)['transmission-info']['data']['streams'][0]['urls']
        for key in ['hls', 'rtmp', 'hds']:
            if key not in data: continue
            url = data[key]
            url = urlparser.decorateUrl(url, {'iptv_livestream':True, 'Referer':referer, 'User-Agent':USER_AGENT, 'Origin':origin})
            if key == 'hls': linksTab.extend( getDirectM3U8Playlist(url, checkExt=False, checkContent=True) )
            #elif key == 'hds': linksTab.extend( getF4MLinksWithMeta(url) )
            #elif key == 'rtmp': linksTab.append( {'name':key, 'url':url} )
        return linksTab
        
        sts, data = self.cm.getPage(url, params)
        if not sts: return []
        
    def parserVIDSHARETV(self, baseUrl):
        printDBG("parserVIDSHARETV baseUrl[%s]" % baseUrl)
        
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= { 'User-Agent':'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:21.0) Gecko/20100101 Firefox/21.0',
                       'Referer':baseUrl.meta.get('Referer', ''),
                     }
        COOKIE_FILE = GetCookieDir("vidshare.tv.cookie")
        rm (COOKIE_FILE)
        params = {'header':HTTP_HEADER, 'use_cookie': True, 'save_cookie': True, 'load_cookie': True, 'cookiefile': COOKIE_FILE}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return
        
        printDBG(data)
        
        data = self.cm.ph.getDataBeetwenMarkers(data, '.setup(', ');', False)[1]
        jscode = 'var iptv_srces = %s; \nprint(JSON.stringify(iptv_srces));' % data
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            data = ret['data'].strip()
            data = json_loads(data)
        
        cookieHeader = self.cm.getCookieHeader(COOKIE_FILE)
        dashTab = []
        hlsTab = []
        mp4Tab = []
        for item in data['sources']:
            url = item['file']
            type = item.get('type', url.split('?', 1)[0].split('.')[-1]).lower()
            label = item.get('label', type)
            
            if url.startswith('//'): url = 'http:' + url
            if not self.cm.isValidUrl(url): continue
        
            url = strwithmeta(url, {'Cookie':cookieHeader, 'Referer':HTTP_HEADER['Referer'], 'User-Agent':HTTP_HEADER['User-Agent']})
            if 'dash' in type:
                dashTab.extend(getMPDLinksWithMeta(url, False, sortWithMaxBandwidth=999999999))
            elif 'hls' in type or 'm3u8' in type:
                hlsTab.extend(getDirectM3U8Playlist(url, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999))
            elif 'mp4' in type or 'mpegurl' in type:
                try: sortKey = int(self.cm.ph.getSearchGroups(label, '''([0-9]+)''')[0])
                except Exception: sortKey = -1
                mp4Tab.append({'name':'[%s] %s' % (type, label), 'url':url, 'sort_key':sortKey})
        
        videoTab = []
        mp4Tab.sort(key=lambda item: item['sort_key'], reverse=True)
        videoTab.extend(mp4Tab)
        videoTab.extend(hlsTab)
        videoTab.extend(dashTab)
        return videoTab
        
    def parserVCSTREAMTO(self, baseUrl):
        printDBG("parserVCSTREAMTO baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        cUrl = baseUrl
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = data.meta['url']
        
        playerUrl = self.cm.getFullUrl(self.cm.ph.getSearchGroups(data, '''['"]([^'^"]*?/player[^'^"]*?)['"]''')[0], self.cm.getBaseUrl(cUrl))
        urlParams['header']['Referer'] = cUrl
        
        sts, data = self.cm.getPage(playerUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']
        
        domain = self.cm.getBaseUrl(cUrl, True)
        
        videoTab = []
        data = json_loads(data)['html']
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'sources', ']', False)
        printDBG(data)
        for sourceData in data:
            sourceData = self.cm.ph.getAllItemsBeetwenMarkers(sourceData, '{', '}')
            for item in sourceData:
                marker = item.lower()
                if ' type=' in marker and ('video/mp4' not in marker and 'video/x-flv' not in marker and 'x-mpeg' not in marker): continue
                item = item.replace('\\/', '/')
                url  = self.cm.getFullUrl(self.cm.ph.getSearchGroups(item, '''(?:src|file)['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0], self.cm.getBaseUrl(cUrl))
                type = self.cm.ph.getSearchGroups(item, '''type['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                label = self.cm.ph.getSearchGroups(item, '''label['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                printDBG(url)
                if type == '': type = url.split('?', 1)[0].rsplit('.', 1)[-1].lower()
                if url == '': continue
                url = strwithmeta(url, {'User-Agent': HTTP_HEADER['User-Agent'], 'Referer':cUrl})
                if 'x-mpeg' in marker or type == 'm3u8':
                    videoTab.extend(getDirectM3U8Playlist(url, checkContent=True))
                else:
                    videoTab.append({'name':'[%s] %s %s' % (type, domain, label), 'url':url})
        return videoTab
    
    def parserVIDCLOUD9(self, baseUrl):
        printDBG("parserVIDCLOUD baseUrl[%r]" % baseUrl)

        urlTabs = []
        subTracks=[]

        sts, data = self.cm.getPage(baseUrl)
        
        if sts:
            if '/videos' in baseUrl:
                #search iframe in html
                tmp = self.cm.ph.getDataBeetwenMarkers(data, '<iframe', '</iframe>')[1]
                iframe_url = self.cm.ph.getSearchGroups(tmp, "src=['\"]([^\"^']+?)['\"]")[0]
                
                if  iframe_url:
                    if iframe_url.startswith('//'):
                        iframe_url= "https:" + iframe_url
                        
                    if 1 == urlparser().checkHostSupport(iframe_url):
                        printDBG("----- > Found url '%s' supported in urlparser... try to get direct link" % iframe_url)
                        return urlparser().getVideoLinkExt(iframe_url)
                        if url2:
                            for u in url2:
                                u['name'] = 'Vidcloud9 - ' + u.get('name','')
                                printDBG(str(u))
                                urlTabs.append(u)
                    
            # search main link
            php_file = self.cm.ph.getSearchGroups(baseUrl, "https?://.+?/(.+?)\.php.+?", ignoreCase=True)[0]
            if php_file:
                ajax_url = baseUrl.replace(php_file, 'ajax')
                ajax_params = {'header' :{
                                'Accept-Encoding': 'gzip', 
                               'Accept': '*/*', 
                                'X-Requested-With': 'XMLHttpRequest', 
                                'Referer': baseUrl
                                }
                                }
                sts, ajax_data = self.cm.getPage(ajax_url, ajax_params)
                
                if sts:
                    printDBG("---------- vidcloud9 ajax data -------------")
                    printDBG(ajax_data)
                    
                    response = json_loads(ajax_data)
                    sources = response.get('source',[])
                    sources.extend(response.get('source_bk',[]))
                    decor_url = {'Referer':baseUrl}
                    
                    #look for subtitles
                    track = response.get('track',[])
                    if len(track) == 0:
                        track = {'tracks': []}
                        
                    for t in track.get('tracks',[]):
                        sub_type = t.get('kind', '')
                        sub_url = t.get('file', '')
                        sub_lang = t.get('label','')
                        if sub_type == "captions" and (sub_url.endswith('vtt') or sub_url.endswith('srt')):
                            params = {'title': sub_lang, 'url': sub_url, 'lang':sub_lang.lower()[:3], 'format':'srt'}
                            printDBG(str(params))
                            subTracks.append(params)

                    decor_url.update({'external_sub_tracks':subTracks})
                    
                    #look for links
                    for s in sources:
                        url = s.get('file', '')
                        url = urlparser().decorateUrl(url, decor_url)
                        label = s.get('label', '')
                        url_type = s.get('type','')
                        if url_type == 'hls':
                            urlTabs.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))
                        else :
                            params = {'name': 'movcloud9 - ' + label, 'url': url}
                            printDBG(str(params))
                            urlTabs.append(params)
        
            # search for others servers in html
            #<ul class="list-server-items">
            tmp = self.cm.ph.getDataBeetwenMarkers(data, ('<ul', '>', 'list-server') , '</ul>')[1]
            #example <li class="linkserver" data-status="1" data-video="//vidembed.cc/loadserver.php?id=MzQ3Mjcz&title=Jungle+Cruise&typesub=SUB&sub=L2p1bmdsZS1jcnVpc2UvanVuZ2xlLWNydWlzZS52dHQ=&cover=Y292ZXIvanVuZ2xlLWNydWlzZS5wbmc=">Beta Server</li>

            servers = self.cm.ph.getAllItemsBeetwenMarkers(tmp, ('<li','>'), '</li>')
            for s in servers:
                mirror_url=self.cm.ph.getSearchGroups(s, '''data-video=['"]([^'^"]+?)['"]''')[0]
                mirror_name = clean_html(s)
                
                if mirror_url.startswith('//'):
                    mirror_url= "https:" + mirror_url
                    
                if self.cm.isValidUrl(mirror_url):
                    if 1 == urlparser().checkHostSupport(mirror_url):
                        printDBG("----- > Found url '%s' supported in urlparser... try to get direct link" % mirror_url)
                        url2 = urlparser().getVideoLinkExt(mirror_url)
                        if url2:
                            for u in url2:
                                u['name'] = mirror_name + " - " + u.get('name','')
                                printDBG(str(u))
                                urlTabs.append(u)
                    else:
                        printDBG("------> Found url '%s' not supported in urlparser" % mirror_url)
            
            return urlTabs
        else:
            return []
        
    def parserVIDCLOUD(self, baseUrl):
        printDBG("parserVIDCLOUD baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        cUrl = baseUrl
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = data.meta['url']
        
        urlsTab = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'sources', ']', False)
        if not data:
            videoId = re.findall("embed/([0-9a-z]*?)(/.*|)$", baseUrl)
            if videoId:
                videoId=videoId[0][0]
                url = "https://vidcloud.co/player?fid={0}&page=embed".format(videoId)
                sts, data = self.cm.getPage(url, urlParams)
                if sts: 
                    data = json_loads(data)
                    ret= data["html"]
                    printDBG(ret)
                    data = self.cm.ph.getAllItemsBeetwenMarkers(ret, 'sources', ']', False)
                else:
                    data = ''
        if data:
            printDBG(str(data))
            for sourceData in data:
                sourceData = self.cm.ph.getAllItemsBeetwenMarkers(sourceData, '{', '}')
                for item in sourceData:
                    #printDBG(item)
                    item_data = json_loads(item)
                    printDBG(str(item_data))
                    if 'file' in item_data:
                        video_url = item_data['file']
                    elif 'src' in item_data: 
                        video_url = item_data['src']
                    else:
                        video_url = ''
                    if video_url:
                        if 'type' in item_data:
                            video_type = item_data['type']
                        else:
                            video_type = ''

                        if 'name' in item_data:
                            video_name = item_data['name']
                        else:
                            video_name = urlparser.getDomain(url)
                        
                        video_name = video_name + ' ' + video_type

                        video_url = strwithmeta(video_url, {'Referer':cUrl})
                        urlsTab.append({'name':video_name, 'url': video_url})
        
        return urlsTab
    
    def parserVIDEMBED(self, baseUrl):
        printDBG("parserVIDEMBED baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        cUrl = baseUrl
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: 
            return False
        
        urlsTab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, 'location = "', '"', False)
        data = str(data)
        data = data.replace("(True, '", "")
        data = data.replace("')", "")
        printDBG(data)
        data = strwithmeta(data)
        urlsTab = self.parserDOOD(data)        
        return urlsTab
            
    def parserUPLOADUJNET(self, baseUrl):
        printDBG("parserUPLOADUJNET baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        cUrl = baseUrl
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = data.meta['url']
        
        url = self.cm.getFullUrl('/api/preview/request/', self.cm.getBaseUrl(cUrl))
        HTTP_HEADER['Referer'] = cUrl
        
        hash = ''.join([random_choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for i in range(20)])
        sts, data = self.cm.getPage(url, urlParams, {'hash':hash, 'url':cUrl})
        if not sts: return False
        
        printDBG(data)
        data = json_loads(data)
        if self.cm.isValidUrl( data['clientUrl'] ):
            return strwithmeta(data['clientUrl'], {'Referer':cUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
        return False
        
    def parserMYSTREAMTO(self, baseUrl):
        printDBG("parserMYSTREAMTO baseUrl[%r]" % baseUrl)
        
        # https://mystream.to/watch/b1rhj6vg62lh
        
        baseUrl = strwithmeta(baseUrl)
        cUrl = baseUrl
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        COOKIE_FILE = GetCookieDir('mystream.cookie')
        
        urlParams = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE }
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: 
            return False
        
        #printDBG("-------------------")
        #printDBG(data)
        #printDBG("-------------------")
        
        
        cUrl = self.cm.meta['url']
        domain = self.cm.getBaseUrl(cUrl, True)

        videoTab = []
        
        error = self.cm.ph.getDataBeetwenMarkers(data, '<span id="my-span">', '</span>',False)[1]
        
        if 'unable to find' in error:
            SetIPTVPlayerLastHostError(error)
            
            return []
        
        tmp = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(tmp, '<source', '>')
        printDBG(tmp)
        for item in tmp:
            marker = item.lower()
            if 'video/mp4' not in marker and 'video/x-flv' not in marker: continue
            type = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0].split('/', 1)[-1]
            url  = self.cm.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0], self.cm.getBaseUrl(cUrl))
            label  = self.cm.ph.getSearchGroups(item, '''label=['"]([^'^"]+?)['"]''')[0]
            printDBG(url)
            if url != '':
                videoTab.append({'name':'[%s] %s %s' % (type, domain, label), 'url':strwithmeta(url, {'User-Agent': HTTP_HEADER['User-Agent'], 'Referer':cUrl})})

        if not videoTab:
            
            # search for string similar to "(new Image()).src = '/view/i7AuNg/dWdgAx/g28eeoODv7?msql7c=' + msql7c;"
            view_url = re.findall("\(new Image\(\)\)\.src = '([^']+)' \+", data)
            if view_url:
                view_url = 'https://' + domain + view_url[0] + "0"
                HTTP_HEADER['accept'] = 'image/webp,image/apng,image/*,*/*;q=0.8'
                HTTP_HEADER['accept-encoding'] = 'gzip, deflate, br'
                urlParams = {'header':HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE }
                
                sts, view_data = self.cm.getPage(view_url, urlParams)
                if sts:
                    printDBG(view_data)
        
            # search for javascript to decode with link to video
            data = ph.findall(data, ('<script', '>'), '</script>', flags=0)
            for item in data:
                if 'ﾟωﾟﾉ=' in item:
                    
                    decoded = aadecode(item)
                    printDBG('---------------------')
                    printDBG(decoded)
                    printDBG('---------------------')

                    urls = re.findall("'src', '([^']+)'", decoded)
                    for url in urls:
                        url = strwithmeta( url, urlParams )
                        if 'mp4' in decoded:
                            videoTab.append({'name': 'mp4', 'url': url})
                        elif 'mpeg' in decoded:
                            videoTab.extend(getDirectM3U8Playlist(url))
                    
                    break
                    
        if not videoTab and '/watch/' in baseUrl:
            # try alternative url in format embed.mystream.to/video_id
            m = re.search("watch/(?P<id>.*?)$", baseUrl)
            if m:
                video_id = m.groupdict().get('id','')
                new_url = "https://embed.mystream.to/%s" % video_id
                
                return urlparser().getVideoLinkExt(new_url)
                
        return videoTab
    
    def parserVIDLOADCO(self, baseUrl):
        printDBG("parserVIDLOADCO baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        cUrl = baseUrl
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        
        urlParams = {'header':HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']
        
        domain = self.cm.getBaseUrl(cUrl, True)
        
        videoTab = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'sources', ']', False)
        printDBG(data)
        for sourceData in data:
            sourceData = self.cm.ph.getAllItemsBeetwenMarkers(sourceData, '{', '}')
            for item in sourceData:
                marker = item.lower()
                if 'video/mp4' not in marker and 'video/x-flv' not in marker and 'x-mpeg' not in marker: continue
                item = item.replace('\\/', '/')
                url  = self.cm.getFullUrl(self.cm.ph.getSearchGroups(item, '''(?:src|file)['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0], self.cm.getBaseUrl(cUrl))
                type = self.cm.ph.getSearchGroups(item, '''type['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                label = self.cm.ph.getSearchGroups(item, '''type['"]?\s*[=:]\s*['"]([^"^']+?)['"]''')[0]
                printDBG(url)
                if url == '': continue
                url = strwithmeta(url, {'User-Agent': HTTP_HEADER['User-Agent'], 'Referer':cUrl})
                if 'x-mpeg' in marker:
                    videoTab.extend(getDirectM3U8Playlist(url, checkContent=True))
                else:
                    videoTab.append({'name':'[%s] %s %s' % (type, domain, label), 'url':url})
            
        return videoTab
    
    def parserSOUNDCLOUDCOM(self, baseUrl):
        printDBG("parserCLOUDSTREAMUS baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        cUrl = baseUrl
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = data.meta['url']
        
        tarckId = self.cm.ph.getSearchGroups(data, '''tracks\:([0-9]+)''')[0]
        
        url = self.cm.ph.getSearchGroups(data, '''['"](https?://[^'^"]+?/widget\-[^'^"]+?\.js)''')[0]
        sts, data = self.cm.getPage(url, urlParams)
        if not sts: return False
        
        clinetIds = self.cm.ph.getSearchGroups(data, '''client_id\:[A-Za-z]+?\?"([^"]+?)"\:"([^"]+?)"''', 2)
        baseUrl = 'https://api.soundcloud.com/i1/tracks/%s/streams?client_id=' % tarckId
        jsData = None
        for clientId in clinetIds:
            url = baseUrl + clientId
            sts, data = self.cm.getPage(url, urlParams)
            if not sts: continue
            try:
                jsData = json_loads(data)
            except Exception:
                printExc()
        
        urls = []
        baseName = urlparser.getDomain(cUrl)
        for key in jsData:
            if 'preview' in key: continue
            url = jsData[key]
            if self.cm.isValidUrl(url):
                urls.append({'name':baseName + ' ' + key, 'url':url})
        return urls
        
    def parserCLOUDSTREAMUS(self, baseUrl):
        printDBG("parserCLOUDSTREAMUS baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        cUrl = baseUrl
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        
        jscode = ['eval=function(t){return function(){print(arguments[0]);try{return t.apply(this,arguments)}catch(t){}}}(eval);']
        sts, data = self.cm.getPage(baseUrl, {'header':HTTP_HEADER})
        if not sts: return False
        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in data:
            if 'eval(' in item:
                jscode.append(item)
        ret = js_execute( '\n'.join(jscode) )
        if ret['sts'] and 0 == ret['code']:
            data = ret['data']
        
        urlsTab = []
        googleDriveFiles = []
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, 'sources:', '],', False)
        for sourceData in data:
            sourceData = self.cm.ph.getAllItemsBeetwenMarkers(sourceData, '{', '}')
            for item in sourceData:
                type = self.cm.ph.getSearchGroups(item, '''['"\{\,\s]type['"]?\s*:\s*['"]([^'^"]+?)['"]''')[0].lower()
                if type != 'mp4': continue
                url = self.cm.ph.getSearchGroups(item, '''['"\{\,\s]file['"]?\s*:\s*['"]([^'^"]+?)['"]''')[0]
                if 'googleapis.com/drive' in url  and'/files/' in url:
                    fileId = url.split('/files/', 1)[-1].split('?', 1)[0]
                    if fileId != '':
                        if fileId in googleDriveFiles: continue
                        googleDriveFiles.append(fileId)
                        continue
                name = self.cm.ph.getSearchGroups(item, '''['"\{\,\s]label['"]?\s*:\s*['"]([^'^"]+?)['"]''')[0]
                if name == '': name = urlparser.getDomain(url)
                urlsTab.append({'name':name, 'url':url})
        printDBG(googleDriveFiles)
        for fileId in googleDriveFiles:
            tmp = urlparser().getVideoLinkExt('https://drive.google.com/file/d/%s/view' % fileId)
            if len(tmp):
                tmp.extend( urlsTab )
                urlsTab = tmp
        return urlsTab
    
    def parserSPORTSTREAM365(self, baseUrl):
        printDBG("parserSPORTSTREAM365 baseUrl[%r]" % baseUrl)
        if self.sportStream365ServIP == None: retry = False
        else: retry = True
        
        COOKIE_FILE = GetCookieDir('sportstream365.com.cookie')
        lang = self.cm.getCookieItem(COOKIE_FILE, 'lng')
        
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader(browser='iphone_3_0')
        if 'Referer' in baseUrl.meta: HTTP_HEADER['Referer'] = baseUrl.meta['Referer']
        
        defaultParams = {'header':HTTP_HEADER, 'cookiefile':COOKIE_FILE, 'use_cookie': True, 'save_cookie':True}
        if 'cookie_items' in baseUrl.meta: defaultParams['cookie_items'] = baseUrl.meta['cookie_items']
        
        sts, data = self.cm.getPage(baseUrl, defaultParams)
        if not sts: return
        
        vi = self.cm.ph.getSearchGroups(baseUrl, '''data\-vi=['"]([0-9]+)['"]''')[0]
        
        cUrl = self.cm.meta['url']
        if 'Referer' not in HTTP_HEADER:  HTTP_HEADER['Referer'] = cUrl
        mainUrl = self.cm.getBaseUrl(cUrl)
        if None == self.sportStream365ServIP:
            url = self.cm.getFullUrl('/cinema', mainUrl)
            sts, data = self.cm.getPage(url, MergeDicts(defaultParams, {'raw_post_data':True}), post_data='')
            if not sts: return False
            vServIP = data.strip()
            printDBG('vServIP: "%s"' % vServIP)
            if len(vServIP):
                self.sportStream365ServIP = vServIP
            else:
                return
        
        if vi == '':
            game = self.cm.ph.getSearchGroups(baseUrl, '''game=([0-9]+)''')[0]
            if game == '':
                printDBG("Unknown game id!")
                return False

            url = self.cm.getFullUrl('/LiveFeed/GetGame?id=%s&partner=24' % game, mainUrl)
            if lang != '': url += '&lng=' + lang
            sts, data = self.cm.getPage(url, defaultParams)
            if not sts: return False
            
            data = json_loads(data)
            printDBG(data)
            vi = data['Value']['VI']
        
        url = '//' + self.sportStream365ServIP + '/hls-live/xmlive/_definst_/' + vi + '/' + vi + '.m3u8?whence=1001'
        url = strwithmeta(self.cm.getFullUrl(url, mainUrl), {'User-Agent': HTTP_HEADER['User-Agent'], 'Referer':cUrl})
        linksTab = getDirectM3U8Playlist(url, checkContent=True)
        if 0 == len(linksTab) and retry:
            self.sportStream365ServIP = None
            return self.parserSPORTSTREAM365(baseUrl)
        
        return linksTab
        
    def parserNXLOADCOM(self, baseUrl):
        printDBG('parserNXLOADCOM baseUrl[%s]' % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader()
        if 'Referer' in baseUrl.meta: HTTP_HEADER['Referer'] = baseUrl.meta['Referer']
        params = {'header' : HTTP_HEADER}
        
        if 'embed' not in baseUrl:
            sts, data = self.cm.getPage(baseUrl, params)
            if not sts: return False
            videoId = self.cm.ph.getSearchGroups(baseUrl+'/', '[/\-\.]([A-Za-z0-9]{12})[/\-\.]')[0]
            url = self.cm.getBaseUrl(self.cm.meta['url']) + 'embed-{0}.html'.format(videoId)
        else:
            url = baseUrl 
        
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        
        tmp = self.cm.ph.getSearchGroups(data, '''externalTracks['":\s]*?\[([^\]]+?)\]''')[0]
        printDBG(tmp)
        tmp = re.compile('''\{([^\}]+?)\}''', re.I).findall(tmp)
        subTracks = []
        for item in tmp:
            lang = self.cm.ph.getSearchGroups(item, r'''['"]?lang['"]?\s*?:\s*?['"]([^"^']+?)['"]''')[0].lower()
            src = self.cm.ph.getSearchGroups(item, r'''['"]?src['"]?\s*?:\s*?['"](https?://[^"^']+?)['"]''')[0]
            label = self.cm.ph.getSearchGroups(item, r'''label['"]?\s*?:\s*?['"]([^"^']+?)['"]''')[0]
            format = src.split('?', 1)[0].split('.')[-1].lower()
            if format not in ['srt', 'vtt']: continue
            if 'empty' in src.lower(): continue
            subTracks.append({'title':label, 'url':src, 'lang':lang.lower()[:3], 'format':'srt'})
        
        urlTab = []
        tmp = self.cm.ph.getSearchGroups(data, '''sources['":\s]*?\[([^\]]+?)\]''')[0]
        printDBG(tmp)
        tmp = re.compile('''['"]([^'^"]+?\.(?:m3u8|mp4|flv)(?:\?[^'^"]*?)?)['"]''', re.I).findall(tmp)
        for url in tmp:
            type = url.split('?', 1)[0].rsplit('.', 1)[-1].lower()
            url = self.cm.getFullUrl(url, self.cm.getBaseUrl(self.cm.meta['url']))
            if type in ['mp4', 'flv']:
                urlTab.append({'name':'mp4', 'url':url})
            elif type == 'm3u8':
                urlTab.extend(getDirectM3U8Playlist(url, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999))
        
        if len(subTracks):
            for idx in range(len(urlTab)):
                urlTab[idx]['url'] = urlparser.decorateUrl(urlTab[idx]['url'], {'external_sub_tracks':subTracks})
        
        return urlTab
        
    def parserCLICKOPENWIN(self, baseUrl):
        printDBG('parserCLICKOPENWIN baseUrl[%s]' % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader()
        if 'Referer' in baseUrl.meta: HTTP_HEADER['Referer'] = baseUrl.meta['Referer']
        params = {'header' : HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        cUrl = self.cm.meta['url']
        if str(self.cm.meta['status_code'])[0] == '5':
            SetIPTVPlayerLastHostError(_('Internal Server Error. Server response code: %s') % self.cm.meta['status_code'])
        
        domain = self.cm.getBaseUrl(cUrl)
        
        jscode = [self.jscode['jwplayer']]
        tmp = self.cm.ph.getAllItemsBeetwenMarkers(data, '<script', '</script>')
        for item in tmp:
            scriptUrl =  self.cm.getFullUrl(self.cm.ph.getSearchGroups(item, '''<script[^>]+?src=['"]([^'^"]+?\.js[^'^"]*?)['"]''')[0], domain)
            if scriptUrl == '':
                jscode.append(self.cm.ph.getDataBeetwenNodes(item, ('<script', '>'), ('</script', '>'), False)[1])
            elif 'codes' in scriptUrl:
                params['header']['Referer'] = cUrl
                sts, item = self.cm.getPage(scriptUrl, params)
                if sts: jscode.append(item)
        
        urlTab = []
        jscode = '\n'.join(jscode)
        ret = js_execute( jscode )
        if ret['sts'] and 0 == ret['code']:
            data = json_loads(ret['data'])
            for item in data['sources']:
                url = item['file']
                type = item.get('type', '')
                if type == '': type = url.split('.')[-1].split('?', 1)[0]
                type = type.lower()
                label = item['label']
                if 'mp4' not in type: continue
                if url == '': continue
                url = urlparser.decorateUrl(self.cm.getFullUrl(url, cUrl), {'Range':'bytes=0-', 'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
                urlTab.append({'name':'{0} {1}'.format(domain, label), 'url':url})
        
        return urlTab
        
    def parserCLOUDCARTELNET(self, baseUrl):
        printDBG('parserCLOUDCARTELNET baseUrl[%s]' % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader()
        if 'Referer' in baseUrl.meta: HTTP_HEADER['Referer'] = baseUrl.meta['Referer']
        params = {'header' : HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, params)
        if not sts: return False
        cUrl = self.cm.meta['url']
        domain = self.cm.getBaseUrl(cUrl)
        videoId = self.cm.ph.getSearchGroups(baseUrl + '/', '''(?:/video/|/link/)([^/]+?)/''')[0]
        apiUrl = self.cm.getFullUrl(self.cm.ph.getSearchGroups(data, '''<video[^>]+?poster=['"]([^'^"]+?)['"]''')[0], domain)
        apiDomain = self.cm.getBaseUrl(apiUrl)
        
        url = self.cm.getFullUrl('/download/link/' + videoId, apiDomain)
        sts, data = self.cm.getPage(url, params)
        if not sts: return False
        
        data = json_loads(data)
        if 'mp4' in data['content_type']:
            return self.cm.getFullUrl(data['url'], apiDomain)
        
        return False
        
    def parserHAXHITSCOM(self, baseUrl):
        printDBG("parserHAXHITSCOM baseUrl[%r]" % baseUrl)
        
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        
        cUrl = self.cm.getBaseUrl(data.meta['url'])
        domain = urlparser.getDomain(cUrl)
        
        jscode = [self.jscode['jwplayer']]
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'eval(' in item and 'setup' in item:
                jscode.append(item)
        urlTab = []
        jscode = '\n'.join(jscode)
        ret = js_execute( jscode )
        data = json_loads(ret['data'])
        for item in data['sources']:
            url = item['file']
            type = item.get('type', '')
            if type == '': type = url.split('.')[-1].split('?', 1)[0]
            type = type.lower()
            label = item['label']
            if 'mp4' not in type: continue
            if url == '': continue
            url = urlparser.decorateUrl(self.cm.getFullUrl(url, cUrl), {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
            urlTab.append({'name':'{0} {1}'.format(domain, label), 'url':url})
        return urlTab
        
    def parserJAWCLOUDCO(self, baseUrl):
        printDBG("parserJAWCLOUDCO baseUrl[%r]" % baseUrl)
        
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'with_metadata':True, 'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']
        domain = urlparser.getDomain(cUrl)
        
        linksTab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, '<video', '</video>')[1]
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<source', '>', False)
        for item in data:
            url = self.cm.getFullUrl(self.cm.ph.getSearchGroups(item, '''src=['"]([^'^"]+?)['"]''')[0], domain)
            type = self.cm.ph.getSearchGroups(item, '''type=['"]([^'^"]+?)['"]''')[0].lower()
            if 'video' not in type and 'x-mpeg' not in type: continue
            if url == '': continue
            if 'video' in type:
                linksTab.append({'name':'[%s]' % type, 'url':url})
            elif 'x-mpeg' in type:
                linksTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))
        return linksTab
        

    def parserKRAKENFILESCOM(self, baseUrl):
        printDBG("parserKRAKENFILESCOM baseUrl[%r]" % baseUrl)
        
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}
        
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']
        domain = urlparser.getDomain(cUrl)
        
        urlTab = []
        data = re.compile('''['"]([^'^"]+?/uploads/[^'^"]+?\.(?:m4a|mp3)(?:\?[^'^"]*?)?)['"]''').findall(data)
        for url in data:
            url = strwithmeta(self.cm.getFullUrl(url, self.cm.meta['url']), {'Referer':baseUrl, 'User-Agent':HTTP_HEADER['User-Agent']})
            urlTab.append({'name':'%s %s' % (domain, len(urlTab)+1), 'url':url})
        
        return urlTab

    def parserFILEFACTORYCOM(self, baseUrl):
        printDBG("parserFILEFACTORYCOM baseUrl[%r]" % baseUrl)

        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']
        domain = urlparser.getDomain(cUrl)

        videoUrl = self.cm.getFullUrl(self.cm.ph.getSearchGroups(data, '''data\-href=['"]([^'^"]+?)['"]''')[0], self.cm.meta['url'])
        if not videoUrl: return False

        sleep_time = self.cm.ph.getSearchGroups(data, '''data\-delay=['"]([0-9]+?)['"]''')[0]
        try: GetIPTVSleep().Sleep(int(sleep_time))
        except Exception: printExc()

        sts, data = self.cm.getPage(videoUrl, {'max_data_size':200*1024})
        if sts:
            if 'text' not in self.cm.meta['content-type']:
                return [{'name':domain, 'url':videoUrl}]
            else:
                printDBG(data)
                msg = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'box-message'), ('</div', '>'), False)[1])
                SetIPTVPlayerLastHostError(msg)

        return False

    def parserSHAREONLINEBIZ(self, baseUrl):
        printDBG("parserSHAREONLINEBIZ baseUrl[%s]" % baseUrl)
        HTTP_HEADER = {'User-Agent': 'Mozilla/5.0', 'Accept': 'text/html', 'Accept-Encoding':'gzip, deflate'}
        COOKIE_FILE = GetCookieDir('share-online.biz')
        rm(COOKIE_FILE)
        defaultParams = {'header': HTTP_HEADER, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        
        sts, data = self.cm.getPage(baseUrl, defaultParams)
        if not sts: return False
        baseUrl = self.cm.meta['url']
        defaultParams['header']['Referer'] = baseUrl
        mainUrl = baseUrl
        
        data = self.cm.ph.getSearchGroups(data, '''function\s+?go_free\(\s*?\)\s*?\{([^\}]+?)\}''')[0]
        action = self.cm.ph.getSearchGroups(data, '''var\s+?url\s*?=\s*?['"]([^'^"]+?)['"]''')[0]
        action = self.cm.getFullUrl(action, baseUrl)
        
        post_data = {}
        data = self.cm.ph.getAllItemsBeetwenMarkers(data, '$', ';')
        for item in data:
            name  = self.cm.ph.getSearchGroups(item, '''['"]?name['"]?\s*?,\s*?['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            value  = self.cm.ph.getSearchGroups(item, '''['"]?name['"]?\s*?,\s*?['"]([^'^"]+?)['"]''', ignoreCase=True)[0]
            if name != '':
                post_data[name] = value
         
        sts, data = self.cm.getPage(action, defaultParams, post_data)
        if not sts: return False
        cUrl = self.cm.meta['url']
        defaultParams['header']['Referer'] = cUrl
        
        timestamp = time.time()
        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in tmp:
            if 'finish' in item:
                jscode = item + '\n' +  "retObj={};for(var name in global) { if (global[name] != retObj) {retObj[name] = global[name];} } retObj['real_wait'] = Math.ceil((retObj['finish'].getTime() - Date.now()) / 1000);print(JSON.stringify(retObj));"
                ret = js_execute( jscode )
                downloadData = json_loads(ret['data'])
        sleep_time = downloadData['real_wait']
        captcha = base64.b64decode(downloadData['dl']).split('hk||')[1]
        url = "/free/captcha/".join(downloadData['url'].split("///"))
        sleep_time2 = downloadData['wait']
        
        tmp = re.compile('(<[^>]+?data\-sitekey[^>]*?>)').findall(data)
        for item in tmp:
            if 'hidden' not in item:
                sitekey = self.cm.ph.getSearchGroups(item, 'data\-sitekey="([^"]+?)"')[0]
                break

        if sitekey == '': sitekey = self.cm.ph.getSearchGroups(data, 'data\-sitekey="([^"]+?)"')[0]
        if sitekey != '': 
            token, errorMsgTab = self.processCaptcha(sitekey, mainUrl)
            if token == '':
                SetIPTVPlayerLastHostError('\n'.join(errorMsgTab)) 
                return False
        else:
            token = ''
            
        post_data = {'dl_free':'1', 'captcha':captcha, 'recaptcha_challenge_field':token, 'recaptcha_response_field': token}
        
        sleep_time -= time.time() - timestamp
        if  sleep_time > 0:
            GetIPTVSleep().Sleep(int(math.ceil(sleep_time)))
        
        defaultParams['header'] = MergeDicts(defaultParams['header'], {'Accept':'*/*', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With':'XMLHttpRequest'})
        sts, data = self.cm.getPage(url, defaultParams, post_data)
        if not sts: return False
        
        data = base64.b64decode(data)
        printDBG('CAPTCHA CHECK: ' + data)
        if self.cm.isValidUrl(data):
            GetIPTVSleep().Sleep(sleep_time2)
            return strwithmeta(data, {'Referer':defaultParams['header']['Referer'], 'User-Agent':defaultParams['header']['User-Agent']})
        return False

    def parserTELERIUMTV(self, baseUrl):
        printDBG("parserTELERIUMTV baseUrl[%r]" % baseUrl)

        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        
        
        HTTP_HEADER['User-Agent'] = 'Mozilla / 5.0 (SMART-TV; Linux; Tizen 2.4.0) AppleWebkit / 538.1 (KHTML, podobnie jak Gecko) SamsungBrowser / 1.1 TV Safari / 538.1'
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']

        js_params = [{'code':'var e2i_obj={resp:"", agent:"%s", ref:"%s"};' % (HTTP_HEADER['User-Agent'], HTTP_HEADER['Referer'])}]
        js_params.append({'path':GetJSScriptFile('telerium1.byte')})
        js_params.append({'hash':str(time.time()), 'name':'telerium2', 'code':''})

        HTTP_HEADER['Referer'] = cUrl

        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        for item in data:
            if 'eval(' in item:
                js_params[2]['code'] = item

        ret = js_execute_ext( js_params )
        data = json_loads(ret['data'])

        url = self.cm.getFullUrl(data['url'], cUrl)
        
        
        sts, data = self.cm.getPage(url, urlParams)
        if not sts: return False

        data= json_loads(data)
        printDBG(">>>: " + data)
        js_params[0]['code'] = js_params[0]['code'].replace('resp:""', 'resp:"%s"' % data)

        ret = js_execute_ext( js_params )
        data = json_loads(ret['data'])

        url = self.cm.getFullUrl(data['source'], cUrl)
        
        
        if url.split('?', 1)[0].lower().endswith('.m3u8'):
            url = strwithmeta(url, {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':HTTP_HEADER['Referer'], 'Origin':self.cm.getBaseUrl(HTTP_HEADER['Referer'])[:-1], 'Accept':'*/*'})
            return getDirectM3U8Playlist(url, checkExt=False, checkContent=True)

        return False

    def parserVIDSTODOME(self, baseUrl):
        printDBG("parserVIDSTODOME baseUrl[%r]" % baseUrl)
        # example video: https://vidstodo.me/embed-6g0hf5ne3eb2.html
        def _findLinks(data):
            linksTab = []
            data = self.cm.ph.getDataBeetwenMarkers(data, 'sources:', ']', False)[1]
            data = re.compile('"(http[^"]+?)"').findall(data)
            for link in data:
                if link.split('?')[0].endswith('m3u8'):
                    linksTab.extend(getDirectM3U8Playlist(link, checkContent=True))
                elif link.split('?')[0].endswith('mp4'):
                    linksTab.append({'name':'mp4', 'url': link})
            return linksTab
        return self._parserUNIVERSAL_A(baseUrl, 'https://vidstodo.me/embed-{0}.html', _findLinks)

    def parserCLOUDVIDEOTV(self, baseUrl):
        printDBG("parserCLOUDVIDEOTV baseUrl[%r]" % baseUrl)
        # example video: https://cloudvideo.tv/embed-1d3w4w97woun.html

        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: 
            return False
        
        printDBG("------------------------------------")
        printDBG(data)
        printDBG("------------------------------------")
        cUrl = self.cm.meta['url']
        domain = urlparser.getDomain(cUrl)

        retTab = []
        tmp = ph.find(data, '<video', '</video>', flags=ph.IGNORECASE)[1]
        tmp = ph.findall(tmp, '<source', '>', flags=ph.IGNORECASE)
        for item in tmp:
            url = ph.getattr(item, 'src')
            type = ph.getattr(item, 'type') 
            if 'video' not in type and 'x-mpeg' not in type: continue
            if url:
                url = self.cm.getFullUrl(url, cUrl)
                if 'video' in type:
                    retTab.append({'name':'[%s]' % type, 'url':url})
                elif 'x-mpeg' in type:
                    retTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))
        
        if retTab: 
            return retTab
        
        # search for packed javascript code
        scripts = re.findall("<script type=[\"'][a-z0-9]{12,}-text/javascript[\"']>.*?(eval\(function.*?)</script>", data, re.S)
            
        if scripts:
            for script in scripts:
                printDBG("----------- pack -----------------")
                printDBG(script)

                script = script + "\n"
                # mods
                script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                script = script.replace("return p}(", "print(p)}\n\npippo(")
                script = script.replace("))\n",");\n")

                # duktape
                ret = js_execute( script )
                decoded = ret['data']
                printDBG('------------------------------')
                printDBG(decoded)
                printDBG('------------------------------')

                # stream search
                s = re.findall("sources\s?:\s?\[(.*?)\]", decoded, re.S)
                if s:
                    txt = "[" + s[0] + "]"
                    printDBG(txt)
                    
                    links = demjson_loads(txt)
                    printDBG(str(links))
                    
                    for l in links:
                        if 'file' in l:
                            url = urlparser.decorateUrl(l['file'], {'Referer' : baseUrl})
                            if url.endswith('.m3u8'):
                                retTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
                            else:
                                params = {'name': l.get('label', 'link') , 'url': url}
                                printDBG(params)
                                retTab.append(params)
        
        return retTab

    def parserGOGOANIMETO(self, baseUrl):
        printDBG("parserGOGOANIMETO baseUrl[%r]" % baseUrl)
        # example video: http://easyvideome.gogoanime.to/gogo/new/?w=647&h=500&vid=at_bible_town_part3.mp4&
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']
        domain = urlparser.getDomain(cUrl)

        retTab = []
        try:
            tmp = json_loads(ph.find(data, 'var video_links =', '};', flags=0)[1] + '}')
            for subItem in tmp.itervalues():
                for item in subItem.itervalues():
                    for it in item:
                        url = strwithmeta(it['link'], {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':self.cm.meta['url']})
                        type = url.split('?', 1)[0].rsplit('.', 1)[-1].lower()
                        if 'mp4' in type:
                            retTab.append({'name':'[%s] %s' % (it.get('quality', type), it.get('filename')), 'url':url})
                        elif 'mpeg' in type:
                            retTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))
        except Exception:
            printExc()

        if not retTab:
            tmp = ph.findall(data, ('<script', '>'), ('</script', '>'), flags=0)
            for item in tmp:
                if '|mp4|' in item:
                    tmp = item
                    break

            jscode = tmp.replace('eval(', 'print(')
            ret = js_execute( jscode )
            tmp = re.compile('''['"](https?://[^'^"]+?\.mp4(?:\?[^'^"]*?)?)['"]''', re.IGNORECASE).findall(ret['data'])
            for item in tmp:
                url = strwithmeta(item, {'User-Agent':HTTP_HEADER['User-Agent'], 'Referer':self.cm.meta['url']})
                retTab.append({'name':urlparser.getDomain(url), 'url':url})
        return retTab

    def parserMEDIASET(self, baseUrl):
        printDBG("parserMEDIASET baseUrl[%r]" % baseUrl)
        guid  = ph.search(baseUrl, r'''https?://(?:(?:www|static3)\.)?mediasetplay\.mediaset\.it/(?:(?:video|on-demand)/(?:[^/]+/)+[^/]+_|player/index\.html\?.*?\bprogramGuid=)([0-9A-Z]{16})''')[0]
        if not guid: return

        tp_path = 'PR1GhC/media/guid/2702976343/' + guid
        
        uniqueUrls = set()
        retTab = []
        for asset_type in ('SD', 'HD'):
            for f in ('MPEG4'): #, 'MPEG-DASH', 'M3U', 'ISM'):
                url = 'http://link.theplatform.%s/s/%s?mbr=true&formats=%s&assetTypes=%s' % ('eu', tp_path, f, asset_type)
                sts, data = self.cm.getPage(url, post_data={'format': 'SMIL'})
                if not sts: continue
                if 'GeoLocationBlocked' in data:
                    SetIPTVPlayerLastHostError(ph.getattr(data, 'abstract'))
                printDBG("++++++++++++++++++++++++++++++++++")
                printDBG(data)
                tmp = ph.findall(data, '<video', '>')
                for item in tmp:
                    url = ph.getattr(item, 'src')
                    if not self.cm.isValidUrl(url): continue
                    if url not in uniqueUrls:
                        uniqueUrls.add(url)
                        retTab.append({'name':'%s - %s' % (f, asset_type), 'url':url})
        return retTab

    def parserVIDEOMORERU(self, baseUrl):
        printDBG("parserVIDEOMORERU baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']

        track_id = ph.search(data, '"track_id"\s*:\s*"?([0-9]+)')[0]
        url = self.cm.getFullUrl('/video/tracks/709253.json', cUrl)
        urlParams['header']['Referer'] = cUrl

        videoUrls = []

        urlParams2 = {'header': MergeDicts(self.cm.getDefaultHeader(browser='iphone_3_0'), {'Referer':cUrl})}
        sts, data = self.cm.getPage(url, urlParams2)
        if sts:
            try:
                data = json_loads(data)
                hlsUrl = data['data']['playlist']['items'][0]['hls_url']
                hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto':'m3u8', 'User-Agent':urlParams2['header']['User-Agent'], 'Referer':cUrl, 'Origin':urlparser.getDomain(cUrl, False)})
                videoUrls = getDirectM3U8Playlist(hlsUrl, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999, cookieParams={'header':urlParams2['header']})
            except Exception:
                printExc()
        
        return videoUrls
        sts, data = self.cm.getPage(url, urlParams)
        if sts:
            try:
                data = json_loads(data)
                dashUrl = data['data']['playlist']['items'][0]['dash_url']
                dashUrl = urlparser.decorateUrl(dashUrl, {'iptv_proto':'m3u8', 'User-Agent':urlParams['header']['User-Agent'], 'Referer':cUrl, 'Origin':urlparser.getDomain(cUrl, False)})
                videoUrls.extend( getMPDLinksWithMeta(dashUrl, checkExt=False, sortWithMaxBandwidth=999999999, cookieParams={'header':urlParams['header']}) )
                
                f4mUrl = data['data']['playlist']['items'][0]['video_url']
                if f4mUrl.split('?', 1)[0].rsplit('.', 1)[-1] == 'f4m':
                    f4mUrl = urlparser.decorateUrl(f4mUrl, {'iptv_proto':'m3u8', 'User-Agent':urlParams['header']['User-Agent'], 'Referer':cUrl, 'Origin':urlparser.getDomain(cUrl, False)})
                    videoUrls.extend( getF4MLinksWithMeta(f4mUrl, checkExt=False, sortWithMaxBitrate=999999999, cookieParams={'header':urlParams['header']}) )
            except Exception:
                printExc()
                
        return videoUrls

    def parserNTVRU(self, baseUrl):
        printDBG("parserNTVRU baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}

        if '/embed/' not in baseUrl:
            video_id = ph.search(baseUrl, '[^0-9]([0-9]{3}[0-9]+)')[0]
            url = 'https://www.ntv.ru/embed/' + video_id
        else:
            url = baseUrl

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']

        videoUrls = []
        for prefix in ('hi', ''):
            size = ph.clean_html(ph.find(data, ('<%ssize' % prefix, '>'), '</%ssize>' % prefix, flags=0)[1])
            file = ph.find(data, ('<%sfile' % prefix, '>'), '</%sfile>' % prefix, flags=0)[1]
            file = ph.clean_html(ph.find(file, '<![CDATA[', ']]', flags=0)[1])
            if file.startswith('//'): file = self.cm.getFullUrl(file, cUrl)
            elif file.startswith('/'): file = self.cm.getFullUrl('//media.ntv.ru/vod' + file, cUrl)
            elif file != '' and not self.cm.isValidUrl(file): file = self.cm.getFullUrl('//media.ntv.ru/vod/' + file, cUrl)
            if file != '': videoUrls.append({'name':size, 'url':file})
        return videoUrls

    def parserFILECANDYNET(self, baseUrl):
        printDBG("parserFILECANDYNET baseUrl[%s]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        baseUrl = self.cm.meta['url']
        urlParams['header']['Referer'] = baseUrl
        mainUrl = baseUrl

        markers = ('File Not Found', 'not be found')
        for marker in markers:
            if marker in data: SetIPTVPlayerLastHostError(_(markers[0]))
        
        sts, tmp = ph.find(data, ('<form', '>', 'post'), '</form>', flags=ph.I)
        if not sts: return False
        tmp = ph.findall(tmp, '<input', '>', flags=ph.I)
        post_data = {}
        for item in tmp:
            name  = ph.getattr(item, 'name', flags=ph.I)
            value = ph.getattr(item, 'value', flags=ph.I)
            if name != '' and 'premium' not in name:
                if 'adblock' in name and value == '':
                    value = '0'
                post_data[name] = value

        # sleep
        try:
            sleep_time = self.cm.ph.getDataBeetwenNodes(data, ('<span', '>', 'countdown'), ('</span', '>'), False, caseSensitive=False)[1]
            sleep_time = int(self.cm.ph.getSearchGroups(sleep_time, '>\s*([0-9]+?)\s*<')[0])
        except Exception:
            sleep_time = 0

        if  sleep_time > 0:
            GetIPTVSleep().Sleep(int(math.ceil(sleep_time)))

        sts, data = self.cm.getPage(baseUrl, urlParams, post_data)
        if not sts: return False
        baseUrl = self.cm.meta['url']

        errorMessage = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'alert-danger'), ('</div', '>'), False)[1])
        SetIPTVPlayerLastHostError(errorMessage)

        data = re.sub("<!--[\s\S]*?-->", "", data)
        data = re.sub("/\*[\s\S]*?\*/", "", data)

        videoUrl = self.cm.ph.rgetDataBeetwenMarkers2(data, '>download<', '<a ', caseSensitive=False)[1]
        videoUrl = self.cm.ph.getSearchGroups(videoUrl, '''href=['"]([^"^']+?)['"]''')[0]
        if self.cm.isValidUrl(videoUrl):
            return videoUrl

        sts, videoUrl = self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', 'download-btn'), ('</a', '>'), caseSensitive=False)
        if not sts:
            sts, videoUrl = self.cm.ph.getDataBeetwenNodes(data, ('<a', '>', 'downloadbtn'), ('</a', '>'), caseSensitive=False)
        if sts:
            return self.cm.ph.getSearchGroups(videoUrl, '''href=['"]([^"^']+?)['"]''')[0]
        else:
            printDBG(data)
            printDBG('<<<')
            looksGood = ''
            data = self.cm.ph.getAllItemsBeetwenMarkers(data, '<a', '</a>')
            for item in data:
                url = self.cm.ph.getSearchGroups(item, '''href=['"]([^"^']+?)['"]''')[0]
                title = clean_html(item)
                printDBG(url)
                if title == url and url != '':
                    videoUrl = url
                    break
                if '/d/' in url:
                    looksGood = videoUrl
            if videoUrl == '': videoUrl = looksGood

        return videoUrl

    def parser1TVRU(self, baseUrl):
        printDBG("parser1TVRU baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER= self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header':HTTP_HEADER}

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']

        video_id = ph.search(baseUrl, '[^0-9]([0-9]{3}[0-9]+)')[0]

        url = self.cm.getFullUrl('/video_materials.json?video_id=' + video_id, cUrl)
        sts, data = self.cm.getPage(url, urlParams)
        if not sts: return False

        videoUrls = []
        data = json_loads(data)
        for item in data[0]['mbr']:
            url = strwithmeta(self.cm.getFullUrl(item['src'], cUrl), {'Referer':cUrl})
            name = ph.clean_html(item['name'])
            videoUrls.append({'name':name, 'url':url})

        return videoUrls

    def parserSUPERVIDEO(self, baseUrl):
        printDBG("parserSUPERVIDEO baseUrl[%s]" % baseUrl)
        #example  https://supervideo.tv/embed-k9aicjz32dcj.html
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts: 
            return False

        printDBG(data)
        
        vidTab = []
        
        # readable script
        if 'player.updateSrc({src:' in data:
            
            url = self.cm.ph.getSearchGroups(data, "player.updateSrc\({src: \"([^\"]+?)\"")[0]
            printDBG(url)
            if url[-4:] == 'm3u8':
                vidTab.extend(getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
            else:
                vidTab.append({'name': 'link', 'url':url})
        
            return vidTab
    
        # with crypted script
        tmpTab = re.findall("(>eval\(.*?</script>)", data, re.S)
        
        #printDBG("=======================================")
        #printDBG(str(tmpTab))
        
        for tmp in tmpTab:
            tmp2 = unpackJSPlayerParams(tmp, VIDUPME_decryptPlayerParams, 0, r2=True)

            printDBG("=======================================")
            printDBG(tmp2)
            printDBG("=======================================")

            title = self.cm.ph.getSearchGroups(tmp2, 'media:{title:"([^"]+?)"')[0]
            urls_text = self.cm.ph.getDataBeetwenNodes(tmp2, 'sources:[', ']')[1]
            
            printDBG(urls_text)

            if urls_text.startswith("sources:"):
                urls = demjson_loads(urls_text[8:])
                for u in urls:
                    printDBG(u)

                    if 'file' in u:
                        url = u.get('file','')
                    else:
                        url = u
                    
                    if 'label' in u:
                        title = u.get('label', '')
                    
                    if not title:
                        title='link'
                    
                    if url[-4:] == 'm3u8':
                        vidTab.extend(getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
                    else:
                        vidTab.append({'name': title, 'url':url})

        return vidTab

    def parserPRIMEVIDEOS(self, baseUrl):
        printDBG("parserPRIMEVIDEOS baseUrl[%s]" % baseUrl)
        #example  http://vdl.primevideos.net/files/rrlMJoCJMTDeCel.html

        code = re.findall('/(\w*?).html',baseUrl)

        vidTab = []
        if len(code)>0:
            code = code[0]
            url = "http://server3.primevideos.net/x264/{code}/{code}.m3u8".replace("{code}",code)
            url = strwithmeta(url, { 'Referer' : 'http://server3.primevideos.net/', 'Accept':'*/*', 'Accept-Encoding':'gzip' })

            vidTab.extend(getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return vidTab


    def parserLIVESTREAMCOM(self, baseUrl):
        printDBG("parserLIVESTREAMCOM baseUrl[%s]" % baseUrl)
        # example https://livestream.com/accounts/3312258/events/8705395

        URL_MODEL = r'https?://(?:new\.)?(?:www\.)?livestream\.com/(?:accounts/(?P<account_id>\d+)|(?P<account_name>[^/]+))/(?:events/(?P<event_id>\d+)|(?P<event_name>[^/]+))(?:/videos/(?P<id>\d+))?'  
        API_URL_MODEL= 'https://livestream.com/api/accounts/%s/events/%s'
        vidTab=[]

        m = re.match(URL_MODEL, baseUrl)

        if m:
            video_id = m.group('id')
            if video_id:
                printDBG('---> video_id:  ' + video_id)
            else:
                video_id = ''
            event_id = m.group('event_id') or m.group('event_name')
            account_id = m.group('account_id') or m.group('account_name')
            pp=[]

            feed_url = API_URL_MODEL % (account_id, event_id) 

            printDBG(feed_url)
            
            sts, data = self.cm.getPage(feed_url)
            if not sts: 
                return vidTab

            #printDBG(data)
            data = json_loads(data)

            # key stream_info
            if 'stream_info' in data:
                if data['stream_info'] != None :
                    i = data['stream_info']
                    title = i['stream_title']
                    url = i['m3u8_url']
                    pp.append({'name': title + " hls", "url": url})

                    params = getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                    for p in params:
                        p["name"]= title + " " + p["name"]
                        #p["url"] = strwithmeta(p["url"], {'Connection': 'keep-alive', 'Accept-Encoding': 'gzip, deflate', 'Accept': '*/*', 'User-Agent': 'python-requests/2.9.1'})
                        pp.append(p)
                                        
            
            # key feeds - others streams
            for i in data['feed']['data']:
                #printDBG(str(i))
                if i['type']=='video':
                    item = i['data']
                    id = item['id']
                    if len(video_id) == 0 or (video_id == str(id)):
                        title = item['caption']
                        url = item['m3u8_url']
                        params = getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                        for p in params:
                            p["name"]= title + " " + p["name"]
                            pp.append(p)

            vidTab.extend(pp)
        return vidTab

    def parserVIUCLIPS(self, baseUrl):
        printDBG("parserVIUCLIPS baseUrl[%s]" % baseUrl)
        # example http://oms.viuclips.net/player/PopUpIframe/JwB2kRDt7Y?iframe=popup&u=
        #         http://oms.veuclips.com/player/PopUpIframe/HGXPBPodVx?iframe=popup&u=
        #         https://footy11.viuclips.net/player/html/D7o5OVWU9C?popup=yes&autoplay=1
        #         http://player.veuclips.com/embed/JwB2kRDt7Y

        if 'parserVIUCLIPS' in baseUrl:
            baseUrl = ph.search(baseUrl, r'''https?://.*parserVIUCLIPS\[([^"]+?)\]''')[0]
            printDBG("force parserVIUCLIPS baseUrl[%s]" % baseUrl)

        if 'embed' not in baseUrl:
            video_id  = ph.search(baseUrl, r'''https?://.*/player/.*/([a-zA-Z0-9]{13})\?''')[0]
            printDBG("parserVIUCLIPS video_id[%s]" % video_id)
            baseUrl = '{0}embed/{1}'.format(urlparser.getDomain(baseUrl, False), video_id)

        sts, data = self.cm.getPage(baseUrl)
        if not sts: return False

        if 'This video has been removed' in data:
            SetIPTVPlayerLastHostError( 'This video has been removed')
            return False
        
        vidTab=[]
        hlsUrl = self.cm.ph.getSearchGroups(data, '''["']([^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
        tmpUrl = urlparser.getDomain(hlsUrl)
        hlsUrl = hlsUrl.replace(tmpUrl + '//', tmpUrl + '/')
        if hlsUrl != '':
            if hlsUrl.startswith("//"):
                hlsUrl = "https:" + hlsUrl
            hlsUrl = strwithmeta(hlsUrl, {'Origin':"https://" + urlparser.getDomain(baseUrl), 'Referer':baseUrl})
            vidTab.extend(getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
        return vidTab

    def parserWOOFTUBE(self, baseUrl):
        printDBG("parserWOOFTUBE baseUrl[%s]" % baseUrl)
        # example https://woof.tube/stream/eAqP9XtSbC2/John_Wick_3_%E2%80%93_Parabellum_%5Bm1080p%5D_%282019%29.mp4

        sts, data = self.cm.getPage(baseUrl)
        if not sts: 
            return []
        
        videoLink = re.findall("id=\"videolink\">(.*?)</p>",data)
        if videoLink:
            url = "https://woof.tube/gettoken/" + videoLink[0] + "?mime=true"
        
        return url
    
    def parserHDPASSONLINE(self, baseUrl):
        printDBG("parserHDPASSONLINE baseUrl[%s]" % baseUrl)
        # example https://hdload.hdpass.online/public/dist/index.html?id=a84def6cc4cad7e61add7f9315299d25
        
        videoId = re.findall("id=(.*?)$",baseUrl)
        if not videoId:
            videoId = re.findall("id=(.*?)&",baseUrl)
        
        if videoId:
            vidTab = []
            videoId = videoId[0]
            url = 'https://hdload.hdpass.online/hls/' + videoId + '/' + videoId + ".playlist.m3u8"
            vidTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
            return vidTab
        else:
            return []

    def parserSWZZ(self, baseUrl):
        printDBG("parserSWZZ baseUrl[%s]" % baseUrl)
        # example http://swzz.xyz/link/22D1N/
        # http://swzz.xyz/HR/go.php?id=84662
        # http://swzz.xyz/RG/go.php?id=35096
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts:
            return []
        
        url = ""
        urlsTab =[]
        link = re.findall('link = "([^"]+)"',data)
        if link:
            url = link[0]
        else:
            link = re.findall(r'<meta name="og:url" content="([^"]+)"', data)
            if link:
                url = link[0]
            else:
                link = re.findall(r'URL=([^"]+)">', data)
                if link:
                    url = link[0]
                else:
                    link = re.findall(r'<a href="(.*?)" class="btn-wrapper">', data)
                    if link:
                        url = link[0]

        if not url:
            # need to unpack
            printDBG("-----------------------")
            script = re.findall(r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>",data.replace('\n', ''),re.S)
            if script:
                script = script[0] + "\n"
                # mods
                script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                script = script.replace("return p}(", "print(p)}\n\npippo(")
                script = script.replace("))\n",");\n")

                printDBG("-----------------------")
                printDBG(script)
                printDBG("-----------------------")

                # duktape
                ret = js_execute( script )
                #printDBG(ret['data'])
                link = re.findall(r'var link(?:\s)?=(?:\s)?"([^"]+)";', ret['data'])
                if link:
                    url = link[0]
        if url:
            printDBG("found url %s " % url)
            
            return urlparser().getVideoLinkExt(url)
        else:
            return []
    
    def parserEDUCADEGREE(self, baseUrl):
        printDBG("parserEDUCADEGREE baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts:
            return []
        
        #<iframe width='640' height='360' src='https://verystream.com/e/cvJAjWreM3N' frameborder='0' allowfullscreen></iframe><br />
        url = self.cm.ph.getSearchGroups(data, "<iframe[^>]+?src=[\"']([^\"^']+?)[\"']", 1, True)[0]

        if url:
            printDBG("found url %s " % url)
            url = strwithmeta(url, {'Referer': baseUrl})
            return urlparser().getVideoLinkExt(url)
        else:
            return []
    
    def parserFEMBED(self, baseUrl):
        printDBG("parserFEMBED baseUrl[%s]" % baseUrl)
        #example:
        #https://www.fembed.com/v/e706eb-elm180dp
        #https://www.fembed.com/api/source/e706eb-elm180dp
        #https://streamhoe.online/v/0w6p8blx3krz3r0
        #https://cercafilm.net/v/80w1lh8z4w8-1en
        #https://sonline.pro/v/g3drwf-mwjelpwr
        #https://gcloud.live/v/ln5grsnn05rp1w8
        #https://vidsrc.xyz/v/wp2jrsnr8j583g6
        #https://youvideos.ru/v/nrppxf2x11nlj1z
        
        sts, data = self.cm.getPage(baseUrl, {'with_metadata': True})
        
        if sts:
            new_url = data.meta['url']
            if new_url != baseUrl:
                printDBG("redirect to %s" % new_url)
                baseUrl = new_url
            
        
        baseUrl = baseUrl + '?'
        m = re.search("/(v|api/source)/(?P<id>.+)\?", baseUrl)
        
        if not m:
            return []
        
        video_id = m.group('id')
        url = urlparser.getDomain(baseUrl, False) + 'api/source/' + video_id
        h = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
                'Accept': '*/*',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer' : baseUrl,
                'X-Requested-With': 'XMLHttpRequest',
        }
        
        sts, data = self.cm.getPage(url, {'header': h},post_data={'r':'', 'd': 'www.fembed.com'})
        
        if not sts:
            return []
        
        printDBG(data)
        data = json_loads(data)
        
        if ('not found' in data['data']) or ('removed' in data['data']):
            SetIPTVPlayerLastHostError(data['data'])
            
            return []
        
        urlsTab=[]
        for v in data['data']:
            urlsTab.append({'name': v['label'], 'url': v['file']})
            
        
        return urlsTab

    def parserONLYSTREAM(self, baseUrl):
        printDBG("parserONLYSTREAM baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer: HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False

        if "eval(function(p,a,c,k,e,d)" in data:
            printDBG( 'Host resolveUrl packed' )
            packed = re.compile('>eval\(function\(p,a,c,k,e,d\)(.+?)</script>', re.DOTALL).findall(data)
            if packed:
                data2 = packed[-1]
            else:
                return ''
            printDBG( 'Host pack: [%s]' % data2)
            try:
                data = unpackJSPlayerParams(data2, TEAMCASTPL_decryptPlayerParams, 0, True, True)
                printDBG( 'OK unpack: [%s]' % data)
            except Exception: pass

        urlTab = self._findLinks(data, meta={'Referer':baseUrl})
        if 0 == len(urlTab):
            url = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.mp4(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
            if url != '':
                url = strwithmeta(url, {'Origin':"https://" + urlparser.getDomain(baseUrl), 'Referer':baseUrl})
                urlTab.append({'name':'mp4', 'url':url})
            hlsUrl = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
            if hlsUrl != '':
                hlsUrl = strwithmeta(hlsUrl, {'Origin':"https://" + urlparser.getDomain(baseUrl), 'Referer':baseUrl})
                urlTab.extend(getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return urlTab

    def parserSTREAMSB(self, baseUrl):
        printDBG("parserSTREAMSB baseUrl[%s]" % baseUrl)
        urlTab = []
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        urlParams = {'header': HTTP_HEADER}

        media_id = self.cm.ph.getSearchGroups(baseUrl + '/', '(?:embed|e|play|d|sup)[/-]([A-Za-z0-9]+)[^A-Za-z0-9]')[0]
        if not media_id:
            media_id = self.cm.ph.getSearchGroups(baseUrl + '/', urlparser.getDomain(baseUrl) + '/([A-Za-z0-9]+)[/.]')[0]
        printDBG("parserSTREAMSB media_id[%s]" % media_id)

        def get_embedurl(media_id):
            def makeid(length):
                return ''.join([random_choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for i in range(length)])

            x = '{0}||{1}||{2}||streamsb'.format(makeid(12), media_id, makeid(12))
            c1 = hexlify(x.encode('utf8')).decode('utf8')
            x = '{0}||{1}||{2}||streamsb'.format(makeid(12), makeid(12), makeid(12))
            c2 = hexlify(x.encode('utf8')).decode('utf8')
            x = '{0}||{1}||{2}||streamsb'.format(makeid(12), c2, makeid(12))
            c3 = hexlify(x.encode('utf8')).decode('utf8')
#            return 'https://{0}/sources43/{1}/{2}'.format(urlparser.getDomain(baseUrl), c1, c3)
            return 'https://{0}/sources49/{1}'.format(urlparser.getDomain(baseUrl), c1)

        eurl = get_embedurl(media_id)
        urlParams['header']['watchsb'] = 'sbstream'
        sts, data = self.cm.getPage(eurl, urlParams)
        printDBG("parserSTREAMSB data[%s]" % data)
        if not sts:
            return False

        data = json_loads(data).get("stream_data", {})
        videoUrl = data.get('file') or data.get('backup')
        if videoUrl:
            urlTab.extend(getDirectM3U8Playlist(videoUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return urlTab
  
    def parserMIXDROP(self, baseUrl):
        printDBG("parserMIXDROP baseUrl[%s]" % baseUrl)
        # example :https://mixdrop.co/f/1f13jq
        #          https://mixdrop.co/e/1f13jq
        #          https://mixdrop.club/f/vn7de6q7t0j868/2/La_Missy_sbagliata_HD_2020_WEBDL_1080p.mp4
        
        m = re.search("mixdrop\.(co|club|ch)/[ef]/(?P<id>.*?)($|/)", baseUrl)
        
        if m:
            video_id = m.group('id')
            url = "https://mixdrop.co/e/%s" % video_id
        else:
            url = baseUrl
            
        sts, data = self.cm.getPage(url)
        if not sts:
            return []

        #<script>window.location = "/e/952om2mbm9oqc?k=1a8724a6fc293ed495a0cd33921cb4a7&t=1595245658&referrer=";</script>
        redirectUrl = self.cm.ph.getSearchGroups(data, '''<script>\s?window\.location\s?=\s?['"]([^"^']+?)['"]''')[0]
        if redirectUrl:
            redirectUrl = self.cm.getFullUrl(redirectUrl,baseUrl)
            if redirectUrl != baseUrl:
                url = redirectUrl
                sts, data = self.cm.getPage(url)
                if not sts:
                    return []
                
        printDBG("--------------------------")
        printDBG(data)
        printDBG("--------------------------")
        
        error = self.cm.ph.getDataBeetwenNodes(data, '<div class="tb error">', '</p>')[1]

        if error:
            text = clean_html(error)
            SetIPTVPlayerLastHostError(text)
            return []


        urlsTab=[]
        # decrypt packed scripts
        scripts = re.findall(r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>", data,re.S)
        for script in scripts:
            script = script + "\n"
            # mods
            script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
            script = script.replace("return p}(", "print(p)}\n\npippo(")
            script = script.replace("))\n",");\n")

            # duktape
            ret = js_execute( script )
            decoded = ret['data']
            printDBG('------------------------------')
            printDBG(decoded)
            printDBG('------------------------------')
            
            # found a part similar to this one:
            #MDCore.vsrc="//s-delivery4.mixdrop.co/v/cd5b9db3d4d79b8e27f4b8e9e01b0f89.mp4?s=n4gHzKKmauonkMNudSwDkQ&e=1573868130"
            link = re.findall("vsrc=\"([^\"]+?)\"", decoded)
            
            if not link:
                link = re.findall(r'MDCore\.\w+\s*=\s*"([^"]+)"', decoded)
                i=0
                while i < len(link):
                    if not ('mp4' in link[i] and '//' in link[i]):
                        link.pop(i)
                    else:
                        i = i + 1
            
            if link:
                if link[0].startswith('//'):
                    video_url = "https:" + link[0]
                else:
                    video_url = link[0]
                video_url = urlparser.decorateUrl(video_url, {'Referer' : url})
                
                params = {'name': 'link', 'url': video_url}
                printDBG(params)
                urlsTab.append(params)
        
        return urlsTab
                
    def parserVCRYPT(self, baseUrl):
        printDBG("parserVCRYPT baseUrl[%s]" % baseUrl)

        sts, data = self.cm.getPage(baseUrl, {'header':{'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}, 'use_cookie':1, 'save_cookie':1,'load_cookie':1, 'cookiefile': GetCookieDir("vcrypt.cookie"), 'with_metadata':1})
        #if not sts:
        #    return []

        red_url = self.cm.meta['url']
        printDBG('redirect to url: %s' % red_url)
                    
        if red_url != baseUrl:
            return urlparser().getVideoLinkExt(red_url)
        else:
            # search <meta http-equiv="refresh" content="1;URL=https://vcrypt.net/wss1/uadzaa31nr4r">
            red_url = re.findall("URL=([^\"]+)",data)
            if red_url:
                return urlparser().getVideoLinkExt(red_url[0])
            else:
                printDBG(data)
                return []

    def parserWSTREAMVIDEO(self, baseUrl):
        printDBG("parserWSTREAMVIDEO baseUrl[%s]" % baseUrl)

        sts, data = self.cm.getPage(baseUrl)
        if not sts:
            return []

        printDBG("*************************************")
        printDBG(data)
        printDBG("*************************************")

        if 'recaptcha' in data:
            # need to solve a recaptcha to get token
            # search site key grecaptcha.execute('6Lc90MkUAAAAAOrqIJqt4iXY_fkXb7j3zwgRGtUI'
            sitekey = re.findall("data-sitekey='([^']+)'", data)
            if sitekey:
                # solve captcha to login
                #(token, errorMsgTab) = CaptchaHelper().processCaptcha(sitekey[0], baseUrl)
                token = UnCaptchaReCaptcha(lang=GetDefaultLang()).processCaptcha(sitekey[-1], referer=baseUrl, lang=GetDefaultLang())

                printDBG("----------- Recaptcha token -----------------")
                printDBG(token)

                if token:
                    sts, data = self.cm.getPage(baseUrl, {'header':{'content-type': 'application/x-www-form-urlencoded'}} , post_data = {'g-recaptcha-response': token })
                    if not sts:
                        return []

                    printDBG("*************************************")
                    printDBG(data)
                    printDBG("*************************************")
                else:
                    return []
                    
        urlsTab = []
        # decrypt packed scripts
        scripts = re.findall(r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>", data,re.S)
        printDBG("Packed scripts found :%s" % len(scripts))
        
        for script in scripts:
            script = script + "\n"
            # mods
            script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
            script = script.replace("return p}(", "print(p)}\n\npippo(")
            script = script.replace("))\n",");\n")

            # duktape
            ret = js_execute( script )
            decoded = ret['data']
            printDBG('------------------------------')
            printDBG(decoded)
            printDBG('------------------------------')
            
            data = data + '\n' + decoded
            
        # stream search
        s = re.findall("sources: ?\[(.*?)\]", data, re.S)
        if s:
            txt = "[" + s[0] + "]"
            printDBG(txt)

            links = demjson_loads(txt)
            #printDBG(str(links))
            for l in links:
                if 'src' in l:
                    url = l['src']
                elif 'file' in l:
                    url = l['file']
                else:
                    url=''
                
                if url:
                    url = urlparser.decorateUrl(url, {'Referer' : baseUrl})
                    if url.endswith('.m3u8'):
                        urlsTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
                    else:
                        params = {'name': l.get('label', 'link') , 'url': url}
                        printDBG(params)
                        urlsTab.append(params)

        return urlsTab

    def parserJETLOAD(self, baseUrl):
        printDBG("parserJETLOAD baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)
        if not sts:
            return []

        printDBG(data)
        
        urlsTab=[]
        
        #<video src="https://nlw02.hlssrv.com/hls_serve_mp4/d13TcR4aZH4zfHvRTgvQ.mp4" preload="none"
        
        videoUrls = re.findall("<video.*?src=\"([^\"]+?)\"", data)
        
        if videoUrls:
            for l in videoUrls:
                url = urlparser.decorateUrl(l, {'Referer' : baseUrl})
                if l.endswith('.m3u8'):
                    urlsTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
                else:
                    params = {'name': 'link' , 'url': url}
                    printDBG(params)
                    urlsTab.append(params)
         
            return urlsTab
        
        if 'recaptcha' in data:
            # need to solve a recaptcha to get token
            # search site key grecaptcha.execute('6Lc90MkUAAAAAOrqIJqt4iXY_fkXb7j3zwgRGtUI'
            sitekey = re.findall("grecaptcha.execute\('([^']+)'", data)
            if sitekey:
                # solve captcha to login
                #(token, errorMsgTab) = CaptchaHelper().processCaptcha(sitekey[-1], baseUrl)

                token = UnCaptchaReCaptcha(lang=GetDefaultLang()).processCaptcha(sitekey[-1], referer= baseUrl, lang=GetDefaultLang() )

                printDBG("----------- Recaptcha token -----------------")
                printDBG(token)
                
                if token:
                    sts, data = self.cm.getPage(baseUrl, {'header':{'content-type': 'application/x-www-form-urlencoded'}} , post_data = {'g-recaptcha-response': token })
                    if not sts:
                        return []

                    printDBG("*************************************")
                    printDBG(data)
                    printDBG("*************************************")
                else:
                    return []
                
        return urlsTab
    
    def parserHLSTESTER(self, baseUrl):
        printDBG("parserHLSTESTER baseUrl[%s]" % baseUrl)
                #example: https://hlstester.com/embed/?url=https://1107942067.rsc.cdn77.org/UpFiles/2019/12/7/34/131917/720p.m3u8
        
        link = re.findall("url=(.*?)&", baseUrl + "&")
        
        urlsTab=[]
        
        if link:
            params = {'name': 'link' , 'url': link[0]}
            printDBG(params)
            urlsTab.append(params)
        
        return urlsTab

    def parserVIDSRC(self, baseUrl):
        printDBG("parserVIDSRC baseUrl[%s]" % baseUrl)
        #example: https://vidsrc.me/embed/tt8080122/1-1/

        
        sts, data = self.cm.getPage(baseUrl, {'with_metadata': True})
        
        if not sts:
            return []
        
        if baseUrl != data.meta['url']:
            printDBG("new url: %s" % data.meta['url'])
            baseUrl = data.meta['url']
            
        tmp = self.cm.ph.getDataBeetwenNodes(data, '<iframe', ('</iframe', '>'))[1]
        serverNumber = re.findall("/server([0-9]{1,2}?)/", tmp)
        
        if serverNumber:
            serverNumber = serverNumber[0]

            baseUrl = baseUrl + "/"
            
            video_id = re.findall('embed/(.*?)/', baseUrl)
            if video_id:
                video_id = video_id[0]
                url = "https://vidsrc.me/watching?i=%videoId%&srv=%num%".replace("%videoId%", video_id).replace("%num%", serverNumber) 
                
                refererUrl = baseUrl.replace("embed", "server" + serverNumber).replace('//','/').replace('//','/').replace(":/","://")
                
                httpParams = {
                    'header': {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
                        'Referer' : refererUrl
                    },
                    'with_metadata':True
                }
                sts, data = self.cm.getPage(url, httpParams )
                
                if sts:
                    newUrl = data.meta['url']
                    printDBG("Redirect to url %s " % newUrl) 

                    if newUrl != baseUrl and newUrl != url:
                        return urlparser().getVideoLinkExt(newUrl)
                    else:
                        printDBG("New url is equal to previous one!")
                        return []

        else:
            serverNumber = "1"
            #example
            #<iframe src="/server2/tt13624054/1-1/" id="myFrame" frameborder="0" scrolling='no' allowfullscreen='yes' height='100%' width='100%'></iframe>
            
            if newUrl:
                
                newUrl = self.cm.getFullUrl(newUrl, self.cm.getBaseUrl(baseUrl))
                printDBG("redirect to %s" % newUrl)

                httpParams = {
                    'header': {
                        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
                        'Referer' : baseUrl
                    },
                    'with_metadata':True
                }
                
                sts, data = self.cm.getPage(newUrl, httpParams )
                
                printDBG(data)
                
                
        return []
        
    
    def parserVIDSOURCE(self, baseUrl):
        printDBG("parserVIDSOURCE baseUrl[%s]" % baseUrl)
        # https://www.vidsource.me/v/4lo00l6l-xo
        # https://www.vidsource.me/api/source/4lo00l6l-xo

        httpParams = {
            'header': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
            }
        }
        
        urlsTab=[]
        
        if not '/api/' in baseUrl:
            url = 'https://www.vidsource.me/api/source/' +baseUrl.split('/')[-1]
        else:
            url = baseUrl
            
        pd={'d':'www.vidsource.me'}
        sts, data = self.cm.getPage(url, httpParams , post_data = pd)
        
        if sts:
            printDBG("********************")
            printDBG(data)
            printDBG("********************")
        
            response = json_loads(data)
            json_data = response.get('data','')
            if json_data:
                for j in json_data:
                    url = j.get('file','')
                    if self.cm.isValidUrl(url):
                        label = j.get('label','link')
                        url_type = j.get('type','')

                        printDBG("Found link %s" % url)
                        url = urlparser.decorateUrl(url, {'Referer': baseUrl})
                        urlsTab.append({'name': label , 'url': url}) 
                         
        
        return urlsTab
            
    def parserTRONPRICE(self, baseUrl):
        printDBG("parserTRONPRICE baseUrl[%s]" % baseUrl)

        sts, data = self.cm.getPage(baseUrl)
        
        if sts:
            #printDBG(data)

            next_link = re.findall("<script src=\"(.*tronprice.*)\">", data)
            if next_link:
                sts, data = self.cm.getPage(next_link[0])

                if not sts:
                    return []
                
                printDBG("********************")
                printDBG(data)
                next_link = re.findall("src=([a-zA-Z0-9/:.]+)", data)
                
                if next_link:
                    sts, data = self.cm.getPage(next_link[0])
                    
                    if not sts:
                        return[]
                    
                    printDBG("********************")
                    printDBG(data)
                    
                    m3u_url = re.findall("\"(.*charte.*).php\"", data)
                    if m3u_url:
                        m3u_url = m3u_url[0] + ".php"
                        printDBG("Found link '%s'" % m3u_url)
                        
                        #return urlparser.decorateUrl(m3u_url, {'iptv_proto':'m3u8'})
                        
                        urlTabs = getDirectM3U8Playlist(m3u_url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                        printDBG(str(urlTabs))
                        #urlTabs.extend()
                        return urlTabs
                    
                    else:
                        return []
                    
                else:
                    return []
            else:
                return []


        else:
            return []
        
    def parserTXNEWSNETWORK(self, baseUrl):
        printDBG("parserTXNEWSNETWORK baseUrl[%s]" % baseUrl)
        #http://txnewsnetwork.net/ada5.php
        #http://superfastvideos.xyz/avi5.php
        #http://cryptodialynews.com/2021/name5.html
        
        httpParams = {'header':{'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}, 'use_cookie':1, 'save_cookie':1,'load_cookie':1, 'cookiefile': GetCookieDir("TXNEWSNETWORK.cookie")}
        
        urlTabs= []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            printDBG("********************")
            printDBG(data)
            printDBG("********************")
            
            #<script src="http://jscdn-master.today/n1.php?hash=ada5"></script>
            #<script src="http://mastercdn.hu/n1.php?hash=avi2"></script>
            #<script src="http://cryptodialynews.com/js/trxnews5.js">
            #<script src="http://mastercdn.hu/n1.js?hash=z110"></script>
            
            link = re.findall("<script src=\"(.*?ada.*?)\"></script>", data)
            if not link:
                link = re.findall("<script src=\"(.*?avi.*?)\"></script>", data)
            if not link:
                link = re.findall("<script src=\"(.*?trx.*?)\"></script>", data)
            if not link:
                link = re.findall("<script src=\"(.*?hash.*?)\"></script>", data)
            
            if link:
                printDBG("Found link %s" % link[0])
                sts, data = self.cm.getPage(link[0], httpParams)
                
                if sts:
                    printDBG("********************")
                    printDBG(data)
                    
                    #'src="http://www.vaudevile.cz/page.php?hash=ada5&ad=3587580&ud=OTUuMjUyLjEwMi43&td=1581017743">
                    link2 = re.findall("src=\"([^\"]+?)\"", data)
                    if not link2:
                        link2 = re.findall("src=([a-zA-Z0-9/:\.]+?)\s?>", data)
                    
                    if link2:
                        printDBG("Found link %s" % link2[0])
                        httpParams['header']['Referer'] = baseUrl
                        sts, data = self.cm.getPage(link2[0], httpParams)
                
                        if sts:
                            printDBG("********************")
                            printDBG(data)
                            #source: "http://www.vaudevile.cz/mount/ada5/index.m3u8"
                            #var data = {source:"http://www.cryptodialynews.com/charte/charte5.php",
                            
                            link3 = re.findall("source:\s?\"([^\"]+?)\"", data)
                            
                            if link3:
                                printDBG("Found link %s" % link3[0])
                                httpParams['header']['Referer'] = link2[0]
                                m3u_url = urlparser.decorateUrl(link3[0], {'Referer': link2[0]})
                                tabs = getDirectM3U8Playlist(m3u_url, checkExt=False, variantCheck=False, checkContent=True, sortWithMaxBitrate=99999999)
                                printDBG(str(tabs))
                                if len(tabs)>0:
                                    urlTabs.append(tabs[0])
        
        return urlTabs



    def parserRAPIDCRYPT(self, baseUrl):
        printDBG("parserRAPIDCRYPT baseUrl[%s]" % baseUrl)

        sts, data = self.cm.getPage(baseUrl)

        if sts:
            printDBG("---------")
            printDBG(data)
            printDBG("---------")

            next_link = re.findall("class=\"push_button blue\" href=([^>^ ]+)", data)
            if not next_link:
                next_link = re.findall("class=\"play-btn\" href=([^>^ ]+)", data)
                
            if next_link:
                printDBG('redirect to url: %s' % next_link[0])

                return urlparser().getVideoLinkExt(next_link[0])
            else:
                return []
        else:
            return []

    
    def parserLINKHUB(self, baseUrl):
        printDBG("parserLINKHUB baseUrl[%s]" % baseUrl)
        
        #https://linkhub.icu/get/v7k65hI6r4
        sts, data = self.cm.getPage(baseUrl)

        if sts:
            #printDBG("---------")
            #printDBG(data)
            #printDBG("---------")
            
            #search view url
            id = re.findall("/view/([^\"]+)\"", data)
            
            if id:
                view_url = "https://linkhub.icu/view/%s" % id[0]
                
                sts, data = self.cm.getPage(view_url)
                
                if sts:
                    #printDBG("---------")
                    #printDBG(data)
                    #printDBG("---------")
                    
                    anchors = re.findall("(<a.*?>)",data)
                    
                    for a in anchors:
                        if 'title' in a:
                            new_url = self.cm.ph.getSearchGroups(a, '''href=['"]([^'^"]+?)['"]''')[0]  
                            printDBG(new_url)
                            if self.cm.isValidUrl(new_url):
                                return urlparser().getVideoLinkExt(new_url)
                          
                    
            return []
        
        else:
            return []
        
    def parserSTAYONLINE(self, baseUrl):
        printDBG("parserSTAYONLINE baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)

        if sts:
            printDBG("---------")
            printDBG(data)
            printDBG("---------")
            
            #var endpoint = "/ajax/linkView.php"
            endpoint = re.findall("endpoint = [\"']([^\"^']+)[\"']", data)
            if not endpoint:
                printDBG("Stayonline: ajax url not found!")
                return []
            
            endpoint = "https://stayonline.pro" + endpoint[0]
            #var linkId = "PLV9z"
            id = re.findall("linkId = [\"']([^\"^']+)[\"']", data)
            if not id:
                printDBG("Stayonline: id not found!")
                return []
            
            params = {'header': {'Referer': baseUrl, 'x-requested-with': 'XMLHttpRequest', 'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.106 Safari/537.36'}}
            sts, data= self.cm.getPage(endpoint, params, post_data = {'id': id[0], 'ref':''})
            
            if sts:
                response = json_loads(data)
                printDBG(str(response))
                #{
                #   "status": "success",
                #    "data": {
                #    "value": "https:\/\/vcrypt.net\/aki\/54755.html"
                #    }
                #}
                
                if response.get('status','') == "success":
                    data = response.get('data', {})
                    url = data.get('value','')
                    
                    if self.cm.isValidUrl(url):
                        return urlparser().getVideoLinkExt(url)
                
                return []
        
        else:
            return []

    def parser4SNIP(self, baseUrl):
        printDBG("parser4SNIP baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)

        if sts:
            printDBG("---------")
            printDBG(data)
            printDBG("---------")
            
            value = re.findall("/([^/]+)$", baseUrl)
            if value:
                url = "https://4snip.pw/outlink/" + value[0]
                
                printDBG("new url %s" % url)
                
                postData = {'url': value[0]}
                
                sts, data = self.cm.getPage(url, {'with_metadata':True}, post_data=postData)
                
                red_url = data.meta['url']
                printDBG("redirect to url %s" % red_url)
                    
                if self.cm.isValidUrl(red_url):
                    return urlparser().getVideoLinkExt(red_url)

        return []
    
    def parserMSTREAMICU(self, baseUrl):
        printDBG("parserMSTREAMICU baseUrl[%s]" % baseUrl)
        
        sts, data = self.cm.getPage(baseUrl)

        urlTabs=[]
        
        if sts:
            printDBG("---------")
            printDBG(data)
            printDBG("---------")

            if "unable to find the video" in data:
                printDBG("We are unable to find the video you're looking for")
                SetIPTVPlayerLastHostError("We are unable to find the video you're looking for")
                return []

            #search if there is an iframe with a link to mystream
            new_link = re.findall("src=\"([^\"]+mystream.premiumserver[^\"]+?)\"", data)
            
            if new_link:
                new_link = new_link[0]
                if new_link != baseUrl:
                    printDBG("redirect to %s" % new_link)
                    return urlparser().getVideoLinkExt(new_link)
            
            # find string to decode
            decode = re.findall('(\$=~\[\];.*?\(\)\))\(\);', data)

            for d in decode:
                printDBG("---------")
                printDBG(d)
                
                d = re.sub("\$\.\$\(\$\.\$\(", "print(", d)
                d = re.sub("\)\(\)\)", ");", d)
                
                printDBG(d)
                
                ret = js_execute( d )
                if ret['sts'] and 0 == ret['code']:
                    decoded = ret['data'].decode('string_escape') 
                    printDBG("--------- decoded -----------")
                    printDBG(decoded)
                    
                    urls = re.findall("setAttribute\('src', '([^']+)'", decoded)
                    
                    for u in urls:
                        if self.cm.isValidUrl(u):
                            printDBG("Found link %s" % u)
                            u = urlparser.decorateUrl(u, {'Referer': baseUrl})
                            urlTabs.append({'name': 'link' , 'url': u}) 
                            
        return urlTabs

    def parserBACKIN(self, baseUrl):
        printDBG("parserBACKIN baseUrl[%s]" % baseUrl)
        
        # examples:
        # "http://backin.net/nplr7n8c1qla"
        # "http://backin.net/s/nplr7n8c1qla"
        # "http://backin.net/s/streams.php?s=nplr7n8c1qla"

        
        USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
        COOKIE_FILE = GetCookieDir('backin.cookie')
        HttpHeader = {
            'User-Agent': USER_AGENT, 
            'Accept': 'text/html', 
            'Accept-Encoding': 'gzip', 
            'Referer': baseUrl
        }
        
        #AJAX_HEADER = MergeDicts(self.HEADER, {'X-Requested-With':'XMLHttpRequest', 'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8'})
        HttpParams = {'header': HttpHeader , 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': COOKIE_FILE}
        HttpParams['cloudflare_params'] = {'domain':'backin.net', 'cookie_file': COOKIE_FILE, 'User-Agent': USER_AGENT}

        sts, data = self.cm.getPageCFProtection(baseUrl, HttpParams)

        urlTabs=[]

        if sts:
            printDBG("--------- html page after cloudflare javascript challenge ---------")
            printDBG(data)
            printDBG("-------------------------------------------------------------------")
        
        m = re.search("backin\.net/(s/streams\.php\?s=|s/|)(?P<id>.*)$", baseUrl)
        
        if m:
            video_id = m.group('id')
            #http://backin.net/stream-nplr7n8c1qla-500x400.html
            red_url = "http://backin.net/stream-%s-500x400.html" % video_id 
            
            sts, data = self.cm.getPageCFProtection(red_url, HttpParams)
            
            if sts:
                printDBG("--------- ")
                printDBG(data)
                printDBG("----------")

                scripts = re.findall(r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>", data,re.S)
                printDBG("Packed scripts found :%s" % len(scripts))
        
                for script in scripts:
                    script = script + "\n"
                    # mods
                    script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                    script = script.replace("return p}(", "print(p)}\n\npippo(")
                    script = script.replace("))\n",");\n")

                    # duktape
                    ret = js_execute( script )
                    decoded = ret['data']
                    printDBG('------------------------------')
                    printDBG(decoded)
                    printDBG('------------------------------')

                    data = data + '\n' + decoded

                # stream search
                urls = re.findall(r'file\s*:\s*"([^"]+)"', data, re.S)

                for u in urls:
                    if self.cm.isValidUrl(u):
                        printDBG("Found link %s" % u)
                        u = urlparser.decorateUrl(u, {'Referer': baseUrl})
                        params = {'name': 'link' , 'url': u}
                        printDBG(params)
                        urlTabs.append(params)

        return urlTabs


    def parserSTREAMTAPE(self, baseUrl):
        printDBG("parserSTREAMTAPE baseUrl[%s]" % baseUrl)

        COOKIE_FILE = GetCookieDir("streamtape.cookie")
        httpParams = {
            'header': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer': baseUrl.meta.get('Referer', baseUrl)
            },
            'use_cookie': True,
            'load_cookie': True,
            'save_cookie': True,
            'cookiefile': COOKIE_FILE
        }

        sts, data = self.cm.getPage(baseUrl, httpParams)

        urlTabs = []

        if sts:
#            printDBG("---------")
#            printDBG(data)
#            printDBG("---------")

            #search url in tag like <div id="videolink" style="display:none;">//streamtape.com/get_video?id=27Lbk7KlQBCZg02&expires=1589450415&ip=DxWsE0qnDS9X&token=Og-Vxdpku4x8</div>
            t = self.cm.ph.getSearchGroups(data, '''innerHTML = ([^;]+?);''')[0] + ';'
            printDBG("parserSTREAMTAPE t[%s]" % t)
            t = t.replace('.substring(', '[', 1).replace(').substring(', ':][').replace(');', ':]') + '[1:]'
            t = eval(t)
            if t.startswith('/'):
                t = "https:/" + t
            if self.cm.isValidUrl(t):
                cookieHeader = self.cm.getCookieHeader(COOKIE_FILE, unquote=False)
                t = urlparser.decorateUrl(t, {'Cookie': cookieHeader, 'Referer': httpParams['header']['Referer'], 'User-Agent': httpParams['header']['User-Agent']})
                params = {'name': 'link', 'url': t}
                printDBG(params)
                urlTabs.append(params)

        return urlTabs



    def parserBUCKLER(self, baseUrl):
        printDBG("parserBUCKLER baseUrl[%s]" % baseUrl)

        sts, data = self.cm.getPage(baseUrl, {'header':{'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}, 'use_cookie':1, 'save_cookie':1,'load_cookie':1, 'cookiefile': GetCookieDir("buckler.cookie"), 'with_metadata':1})
        #if not sts:
        #    return []

        red_url = self.cm.meta['url']
        printDBG('redirect to url: %s' % red_url)
                    
        if red_url != baseUrl:
            return urlparser().getVideoLinkExt(red_url)
        else:
            printDBG(data)
            return []

    def parserMOVCLOUD(self, baseUrl):
        printDBG("parserMOVCLOUD baseUrl[%s]" % baseUrl)
        #example: https://movcloud.net/embed/ei-RkZ9lI_Bg
        #api url format: https://api.movcloud.net/v1/count/movie/en/episode/349337
        
        urlTabs=[]
        m = re.search("embed/(?P<id>[^/]+)($|/)",baseUrl)
        
        if m:
            video_id = m.groupdict().get('id','')
            if video_id:
                url = "https://api.movcloud.net/stream/" + video_id
                
                sts, data = self.cm.getPage(url)
                if sts:
                    response = json_loads(data)
                    printDBG(str(response))
                    
                    if response.get('success', False):
                        for s in response['data']['sources']:
                            link_url = s.get('file','')
                            if  self.cm.isValidUrl(link_url):
                                link_url = urlparser.decorateUrl(link_url, {'Referer': baseUrl})
                                if 'm3u8' in link_url:
                                    params = getDirectM3U8Playlist(link_url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                                    printDBG(str(params))    
                                    urlTabs.extend(params)
                                else:
                                    params = {'name': 'link' , 'url': link_url}
                                    printDBG(str(params))
                                    urlTabs.append(params)
                               
        
        return urlTabs
        
    def parserMIRRORACE(self, baseUrl):
        printDBG("parserMIRRORACE baseUrl [%s]" % baseUrl)
 
        params = {'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('mirrorace.cookie')}
        ajax_url = "https://mirrorace.com/ajax/embed_link"
        
        ajax_header = {
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip',
                    'Referer': baseUrl,
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest'
        }
        ajax_params = {'header': ajax_header, 'use_cookie': True, 'load_cookie': True, 'save_cookie': True, 'cookiefile': GetCookieDir('mirrorace.cookie')}
        
        urlTabs=[]
        
        sts, data = self.cm.getPage(baseUrl, params)
        
        if sts:
            tmp = self.cm.ph.getDataBeetwenNodes(data, ('<ul', '>', 'slider'), ('</ul', '>'))[1]
            #printDBG(tmp)
            
            mirrors = self.cm.ph.getAllItemsBeetwenMarkers(tmp, ('<li','>'), '</li>', False)
            for m in mirrors:
                # example
                # <button class="..." data-file="2iL2g" data-link="58066810" data-t="39208f664a39a86752b03063296b573aae3440a7"  type="button">

                mirror_name = clean_html(m)
                printDBG("--------------------")
                printDBG(mirror_name)
                
                mirror_file = self.cm.ph.getSearchGroups(m, '''data-file=['"]([^'^"]+?)['"]''')[0]
                mirror_link = self.cm.ph.getSearchGroups(m, '''data-link=['"]([^'^"]+?)['"]''')[0]
                mirror_t = self.cm.ph.getSearchGroups(m, '''data-t=['"]([^'^"]+?)['"]''')[0]
                
                if (mirror_file != "") and (mirror_link !="") and (mirror_t != "") :
                    ajax_pd = {'file': mirror_file, 'link': mirror_link, 't': mirror_t}
                    
                    sts, ajax_data = self.cm.getPage(ajax_url, ajax_params, post_data=ajax_pd)
                    
                    if sts:
                        #{"type":"success","msg":"https:\/\/uptostream.com\/iframe\/ku43i8szvyjx"}
                        response = json_loads(ajax_data)
                        printDBG(str(response))
                        
                        if response.get('type','') == "success":
                            mirror_url = response.get("msg","")
                            if self.cm.isValidUrl(mirror_url):
                                url2 = urlparser().getVideoLinkExt(mirror_url)
                                if url2:
                                    for u in url2:
                                        params = {'name': mirror_name , 'url': u.get('url','')}
                                        printDBG(str(params))
                                        urlTabs.append(params)
                                else:
                                    params = {'name': mirror_name + "*", 'url': mirror_url, 'need_resolve': True}
                                    printDBG(str(params))
                                    urlTabs.append(params)
                                
        return urlTabs

    def parserVIDEOBIN(self, baseUrl):
        printDBG("parserVIDEOBIN baseUrl [%s]" % baseUrl)
        # example: https://videobin.co/embed-n7uoq6qlj2du.html
        #          https://videobin.co/n7uoq6qlj2du

        urlTabs = []
        
        sts, data = self.cm.getPage(baseUrl)
        
        if sts:
            s = re.findall("sources: ?\[(.*?)\]", data, re.S)
            if s:
                for ss in s:
                    printDBG("Found sources: %s" % ss)
                    links = re.findall("[\"']([^\"']+?)[\"']",ss)
                    for link_url in links:
                        if  self.cm.isValidUrl(link_url):
                            link_url = urlparser.decorateUrl(link_url, {'Referer': baseUrl})
                            if 'm3u8' in link_url:
                                params = getDirectM3U8Playlist(link_url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                                printDBG(str(params))    
                                urlTabs.extend(params)
                            else:
                                params = {'name': 'link' , 'url': link_url}
                                printDBG(str(params))
                                urlTabs.append(params)

                
        return urlTabs

    def parserGDRIVEPLAYER(self, baseUrl):
        printDBG("parserGDRIVEPLAYER baseUrl [%s]" % baseUrl)
        
        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip'
            },
            'use_cookie':True,
            'load_cookie':True,
            'save_cookie':True,
            'cookiefile': GetCookieDir('gdriveplayer.cookie')
        }
        
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
        
        urlTabs = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            printDBG("-----------------------")
            printDBG(data)
            printDBG("-----------------------")
            
            scripts = re.findall("<script type=[\"']text/javascript[\"']>.*?(eval.*?)</script>", data, re.S)
            
            if scripts:
                for script in scripts:
                    
                    num = 0
                    while len(script)>0 and num < 2:
                        printDBG("----------- pack -----------------")
                        printDBG(script)

                        script = script + "\n"
                        # mods
                        script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                        script = script.replace("return p}(", "print(p)}\n\npippo(")
                        script = script.replace("))\n",");\n")

                        # duktape
                        ret = js_execute( script )
                        decoded = ret['data']
                        printDBG('------------------------------')
                        printDBG(decoded)
                        printDBG('------------------------------')
                
                        if num == 0:
                            #reading cypher informations in decoded 
                            dataStr = self.cm.ph.getSearchGroups(decoded, "data='(\{.*?\})")[0]
                            linkData = json_loads(dataStr)
                            printDBG(str(linkData))

                            bigString = self.cm.ph.getSearchGroups(decoded.split(';')[1], "[a-zA-Z0-9]{40,}" )[0]
                            printDBG(str(bigString))
                            numList = re.split("[a-zA-Z]{1,}", bigString)
                            charList = []
                            for n in numList:
                                if n:
                                    charList.append(int(n))
                            
                            decypher_code = ''.join(map(unichr, charList))
                            
                            #printDBG(" --------- decypher code --------")
                            #printDBG(decypher_code)
                            #printDBG(" ---------------------------------")

                            aesKey = re.findall("var pass = \"([^\"]+?)\"", decypher_code)
                            
                            if aesKey:
                                aesKey = aesKey[0]
                            else:
                                aesKey = "alsfheafsjklNIWORNiolNIOWNKLNXakjsfwnBdwjbwfkjbJjkopfjweopjASoiwnrflakefneiofrt"
                            
                            printDBG(" ----------- AES key -------------")
                            printDBG(aesKey)
                            printDBG(" ---------------------------------")
                            
                            ciphertext = base64.b64decode(linkData['ct'])
                            iv         = a2b_hex(linkData['iv'])
                            salt       = a2b_hex(linkData['s'])
                    
                            script = cryptoJS_AES_decrypt(ciphertext, aesKey, salt)
                            
                            script = json_loads(script) 
                            
                        num = num + 1
                
                # stream search
                srcJson = re.findall("sources\s*:\s*\[(.*?)\]", decoded, re.S)
                
                if srcJson:
                    srcJson = srcJson[0]
                    printDBG(srcJson)
                    
                    sources = json_loads("[" + srcJson + "]")
                    
                    for s in sources:
                        u = s.get('file','')
                        if self.cm.isValidUrl(u):
                            printDBG("Found link %s" % u)
                            if 'redirector.gdriveplayer.me' in u:
                                # try to read redirection 
                                httpParams['header']['Referer'] = baseUrl
                                httpParams['with_metadata'] = True
                                
                                sts, data = self.cm.getPage(u, httpParams)
                                
                                if sts:
                                    printDBG(data.meta['url'])
                                    printDBG(data)
                                else:
                                    printDBG("PROBLEMS!!!")
                                    
                            label = s.get('label','')
                            u = urlparser.decorateUrl(u, {'Referer': baseUrl})
                            params = {'name': label , 'url': u}
                            printDBG(str(params))
                            urlTabs.append(params)
                        
        return urlTabs

    def parserSPEEDWATCH(self, baseUrl):
        printDBG("parserSPEEDWATCH baseUrl [%s]" % baseUrl)
        #example https://www.speedwatch.io/e/41GbMdRzHUZY.html
        
        urlTabs = []
        
        sts, data = self.cm.getPage(baseUrl)
        
        if sts:
            printDBG("-----------------------")
            printDBG(data)
            printDBG("-----------------------")
        
            sources = re.findall("sources\s?:\s?\[(.*?)\]", data)  
            
            if sources:
                sources = eval("[" + sources[0] + "]")
                for s in sources:
                    if s.startswith('//'):
                        s = "https:" + s
                        if self.cm.isValidUrl(s): 
                            s = urlparser.decorateUrl(s, {'Referer': baseUrl})
                            if '.m3u8' in s:
                                urlTabs.extend(getDirectM3U8Playlist(s, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999))
                            else:
                                urlTabs.append({'name':'link', 'url': s})
        
        return urlTabs
        
    def parserEASYLOAD(self, baseUrl):
        printDBG("parserEASYLOAD baseUrl [%s]" % baseUrl)
        
        def xor_string(a, b):     
            if len(a) > len(b):
                return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(a[:len(b)], b)])
            else:
                return "".join([chr(ord(x) ^ ord(y)) for (x, y) in zip(a, b[:len(a)])])
        
        def real_url(encoded_url):
            # search string to xor with
            xurl_tmp = xor_string(encoded_url[:4],"http")
            xurl= "" 
            for i in range(int(len(encoded_url) / 4 + 1)):
                xurl = xurl + xurl_tmp
            printDBG("pattern to xor: %s " % xurl)
            final_url = xor_string(encoded_url, xurl)
            printDBG("final url: %s " % final_url)
            return final_url
        
        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip'
            },
            'use_cookie':True,
            'load_cookie':True,
            'save_cookie':True,
            'cookiefile': GetCookieDir('easyload.cookie')
        }
      
        m = re.search("/(e|f)/(?P<id>[a-zA-Z0-9]{9,12})", baseUrl)
        
        if m:
            video_id = m.groupdict().get('id','')
            url = self.cm.getBaseUrl(baseUrl) + "e/" + video_id
            httpParams['header']['Referer'] = baseUrl
        else:
            url = baseUrl
            
        urlTabs = []
        
        sts, data = self.cm.getPage(url, httpParams)
        
        if sts:
            printDBG("-----------------------")
            printDBG(data)
            printDBG("-----------------------")
        
            code = re.findall("exdata=\"(.*?)\"", data)
            
            if code:
                code = code[0]
                printDBG("Code : %s" % code)
                c2 =  base64.b64decode(code)
                printDBG("First conversion from b64: %s" % c2)
                c3 = base64.b64decode(c2)
                printDBG("Second conversion from b64: %s" % c3)
        
                j = json_loads(c3)
                printDBG("------------ json ------------")
                printDBG(str(j))
        
                url = real_url(j['streams']['0']['src'])
                if self.cm.isValidUrl(url):
                    url = urlparser.decorateUrl(url, {'Referer': baseUrl})
                    if 'm3u8' in url:
                        params = getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                        printDBG(str(params))    
                        urlTabs.extend(params)
                    else:
                        params = {'name': 'link' , 'url': url}
                        printDBG(str(params))
                        urlTabs.append(params)
    
        return urlTabs

    def parserUPLOADIT(self, baseUrl):
        printDBG("parserUPLOADIT baseUrl [%s]" % baseUrl)
        
        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            }
        }

        urlTabs = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            printDBG("-----------------------")
            printDBG(data)
            printDBG("-----------------------")
        
            urls = re.findall("<source src=\"(.*?)\"", data)
            
            for url in urls:
                if self.cm.isValidUrl(url):
                    url = urlparser.decorateUrl(url, {'Referer': baseUrl})
                    if 'm3u8' in url:
                        params = getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                        printDBG(str(params))    
                        urlTabs.extend(params)
                    else:
                        url = strwithmeta(url, {'Referer':baseUrl, 'iptv_wget_continue':True, 'iptv_wget_timeout':100})
                        params = {'name': 'link' , 'url': url}
                        printDBG(str(params))
                        urlTabs.append(params)

        return urlTabs
        
    def parserOPENDRIVE(self, baseUrl):
        printDBG("parserOPENDRIVE baseUrl [%s]" % baseUrl)
        
        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            }
        }

        urlTabs = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            #printDBG("-----------------------")
            #printDBG(data)
            #printDBG("-----------------------")

            urls = re.findall("<source src=[\"'](.*?)[\"']", data)

            if not urls:
                # search data to post

                form = self.cm.ph.getDataBeetwenMarkers(data, ('<form', '>'), ('</form', '>'), caseSensitive=False)[1]
                # little trick
                form = form.replace('>>"','!!"')
                printDBG(form)
                
                inputs = self.cm.ph.getAllItemsBeetwenMarkers(form, '<input', '>', withMarkers=True)
                postData={}
                for i in inputs:
                    inputName = self.cm.ph.getSearchGroups(i, "name=['\"]([^\"^']+?)['\"]")[0]
                    inputValue = self.cm.ph.getSearchGroups(i, "value=['\"]([^\"^']+?)['\"]")[0]
                    if inputName:
                        inputValue = inputValue.replace("!!",">>")
                        postData[inputName]=inputValue
                        
                printDBG("post data : %s" % json_dumps(postData))
            
                sts, data = self.cm.getPage(baseUrl, httpParams, post_data=postData)
                
                if sts:
                    #printDBG("------------ after post  -----------")
                    #printDBG(data)
                    #printDBG("------------------------------------")
                
                    urls = re.findall("<source src=[\"'](.*?)[\"']", data)

            for url in urls:
                if self.cm.isValidUrl(url):
                    url = urlparser.decorateUrl(url, {'Referer': baseUrl})
                    if 'm3u8' in url:
                        params = getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                        printDBG(str(params))    
                        urlTabs.extend(params)
                    else:
                        params = {'name': 'link' , 'url': url}
                        printDBG(str(params))
                        urlTabs.append(params)
        
        return urlTabs

    def parserSTREAMZ(self, baseUrl):
        printDBG("parserSTREAMZ baseUrl [%s]" % baseUrl)
        
        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            }
        }

        urlsTab = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            printDBG("-----------------------")
            printDBG(data)
            printDBG("-----------------------")
        
            #search for packed code
            scripts = re.findall("<script>.*?(eval\(function.*?)</script>", data, re.S)
            
            if scripts:
                for script in scripts:
                    printDBG("----------- pack -----------------")
                    printDBG(script)

                    script = script + "\n"
                    # mods
                    script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                    script = script.replace("return p}(", "print(p)}\n\npippo(")
                    script = script.replace("))\n",");\n")

                    # duktape
                    ret = js_execute( script )
                    decoded = ret['data']
                    printDBG('------------------------------')
                    printDBG(decoded)
                    printDBG('------------------------------')

                    #video.src({type:'video/mp4',src:'stream9253bce1c89c262dc27e84e36a137f23.mp4'})
                    sources = re.findall("src\((\{.*?\})\)", decoded, re.S)

                    for s in sources:
                        src = demjson_loads(s)
                        url = src.get('src','')
                        if url:
                            if not url.startswith('http'):
                                url = self.cm.getFullUrl(url, self.cm.getBaseUrl(baseUrl))
                            
                            srcType = src.get('type','')
                            
                        url = urlparser.decorateUrl(url, {'Referer': baseUrl})
                        if 'm3u' in srcType or 'hls' in srcType:
                            params = getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                            printDBG(str(params))    
                            urlsTab.extend(params)
                        else:
                            params = {'name': 'link' , 'url': url}
                            printDBG(str(params))
                            urlsTab.append(params)
        
        return urlsTab

    def parserHDPLAYERCASA(self, baseUrl):
        printDBG("parserHDPLAYERCASA baseUrl [%s]" % baseUrl)
        
        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            }
        }

        urlsTab = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            #printDBG("-----------------------")
            #printDBG(data)
            #printDBG("-----------------------")
        
            # find embedded video
            iframes = self.cm.ph.getAllItemsBeetwenMarkers(data, '<iframe', '>', withMarkers=True)
            
            for iframe in iframes:
                url = self.cm.ph.getSearchGroups(iframe, "src=['\"]([^\"^']+?)['\"]")[0]
                printDBG("Found url: %s" % url)
                if self.cm.isValidUrl(url):
                    if  urlparser().checkHostSupport(url)== 1:
                        urls = urlparser().getVideoLinkExt(url)
                        for u in urls:
                            urlsTab.append({'name': self.cm.getBaseUrl(url) + " " + u.get("name","") , 'url' : u.get('url','')})
                    else:
                        urlsTab.append({'name': self.cm.getBaseUrl(url) + "(not in urlparser)", 'url' : url})
        
        
            # find alternative mirrors
            #<li class="dropdown"> 
            #<a class="" href="https://nuovo-indirizzo.com/serietv/series/names/2993/6831/100309/label1/Player"><i class="fa fa-home fa-fw"></i> Player</a>
            #</li>
            #<li class="dropdown">
            #<a class="" href="https://nuovo-indirizzo.com/serietv/series/names/2993/6831/100309/label2/Tantifilm"><i class="fa fa-home fa-fw"></i> Tantifilm</a>
            #</li>
            #<li class="dropdown">
            #<a class="" href="https://nuovo-indirizzo.com/serietv/series/names/2993/6831/100309/label3/Mystream"><i class="fa fa-home fa-fw"></i> Mystream</a>
            #<li>
            mirrors = self.cm.ph.getAllItemsBeetwenMarkers(data, ('<li','>','"dropdown"'), '</li>')
            for m in mirrors:
                mirrorUrl = self.cm.ph.getSearchGroups(m, "href=['\"]([^\"^']+?)['\"]")[0]
                if self.cm.isValidUrl(mirrorUrl):
                    if not 'label1' in mirrorUrl:
                        sts, mirrorData = self.cm.getPage(mirrorUrl, httpParams)

                        # find embedded videos
                        iframes = self.cm.ph.getAllItemsBeetwenMarkers(mirrorData, '<iframe', '>', withMarkers=True)
                        
                        for iframe in iframes:
                            url = self.cm.ph.getSearchGroups(iframe, "src=['\"]([^\"^']+?)['\"]")[0]
                            if url.startswith('//'):
                                url = 'http:' + url
                                
                            printDBG("HDPLAYERCASA --> Found url: %s" % url)
                            if self.cm.isValidUrl(url):
                                if  urlparser().checkHostSupport(url)== 1:
                                    urls = urlparser().getVideoLinkExt(url)
                                    printDBG(str(urls))
                                    for u in urls:
                                        urlsTab.append({'name': self.cm.getBaseUrl(url) + " " + u.get("name","") , 'url' : u.get('url','')})
                                else:
                                    urlsTab.append({'name': self.cm.getBaseUrl(url) + " (" + _("not in urlparser") + ")", 'url' : url})
                
        return urlsTab

    def parserTANTIFILM(self, baseUrl):
        printDBG("parserTANTIFILM baseUrl [%s]" % baseUrl)
        
        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            }, 
            'use_cookie':True,
            'load_cookie':True,
            'save_cookie':True,
            'cookiefile': GetCookieDir("tantifilm.cookie")
        }

        urlsTab = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            printDBG("-----------------------")
            printDBG(data)
            printDBG("-----------------------")

            # search data to auth stream
            scripts = re.findall("window.application\s?=\s?\{(.*?)\};", data)
            if scripts:
                apiJson = json_loads("{" + scripts[0] + "}")
                printDBG("----------- api data ------------")
                printDBG(str(apiJson))
                printDBG("---------------------------------")
                
                video_uuid = apiJson["data"]["uuid"]
                apiPingUrl = apiJson["baseURL"] + "/" + apiJson["routes"]["api.videos.ping"].replace('{video}', video_uuid)
                apiLinksUrl = apiJson["baseURL"] + "/" + apiJson["routes"]["api.videos.links"].replace('{video}', video_uuid)
                token = apiJson['token']
                
                #post to apiPingUrl
                postData = {'pingId': token ,'__type':'dawn'}
                sts, pingData = self.cm.getPage(apiPingUrl, httpParams, post_data=postData)
                
                if sts:
                    printDBG("-----------------------")
                    printDBG(pingData)
                    printDBG("-----------------------")
                    
                    
            #search script with juicycodes
            scripts = re.findall("juicycodes\((.*?)\)", data, re.S)
            for s in scripts:
                try:
                    code = eval(s)
                    tmpCode = code[0:-3]
                    tmpCode += "==="[((len(tmpCode) + 3) % 4):]
                    
                    jsCode = base64.b64decode(tmpCode)
                    symbolMap = ["`", "%", "-", "+", "*", "$", "!", "_", "^", "="]
                    ordString=""
                    for x in jsCode:
                        ordString += '%d' % symbolMap.index(x)
                    
                    decoded = ""
                    tmpSalt = code[-3:]
                    salt = 0
                    for x in tmpSalt:
                        salt = salt * 10 + ord(x)-100
                    
                    splittedOrd = [ordString[i:i+4] for i in range(0, len(ordString), 4)]
                    
                    for x in splittedOrd:
                        j = int(x) % 1000 - salt
                        decoded += chr(j)
                    
                    printDBG(" ------------------ decoded ------------------")
                    printDBG(decoded)
                    printDBG(" ------------------------------------")

                except:
                    printExc()   

                srcJson = re.findall("sources\"\s?:\s?\[(.*?)\]", decoded, re.S)
                
                if srcJson:
                    srcJson = srcJson[0]
                    sources = json_loads("[" + srcJson + "]")
                    printDBG(str(sources))
                    
                    for s in sources:
                        u = s.get('src','')
                        if not u:
                            u = s.get('file','')
                            
                        if self.cm.isValidUrl(u):
                            u = urlparser.decorateUrl(u, {'Referer': baseUrl})
                            label = s.get('label','')
                            srcType = s.get('type','')
                            if 'm3u' in srcType or 'hls' in srcType:
                                params = getDirectM3U8Playlist(u, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                                printDBG(str(params))    
                                urlsTab.extend(params)
                            else:
                                params = {'name': label , 'url': u}
                                printDBG(str(params))
                                urlsTab.append(params)
                    
        return urlsTab



    def parserDOOD(self, baseUrl):
        printDBG("parserDOOD baseUrl [%s]" % baseUrl)

        httpParams = {
            'header': {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer': baseUrl
            },
            'use_cookie': True,
            'load_cookie': True,
            'save_cookie': True,
            'cookiefile': GetCookieDir("dood.cookie"),
            'max_data_size': 0,
            'no_redirection': True
        }

        urlsTab = []

        if '/d/' in baseUrl:
            baseUrl = baseUrl.replace('/d/', '/e/')

        sts, data = self.cm.getPage(baseUrl, httpParams)
        url = self.cm.meta.get('location', '')
        if url != '':
            baseUrl = url
            httpParams['header']['Referer'] = baseUrl
        del httpParams['max_data_size']
        del httpParams['no_redirection']
        sts, data = self.cm.getPage(baseUrl, httpParams)

#        if sts:
#            printDBG("-----------------------")
#            printDBG(data)
#            printDBG("-----------------------")

        subTracks = []
        #<track kind="captions" src="https://doodstream.com/srt/00705/s72n7d5hi6qc_Serbian.vtt" srclang="en" label="Serbian" default>
        tracks = self.cm.ph.getAllItemsBeetwenMarkers(data, '<track', '>', withMarkers=True)
        for track in tracks:
            track_kind = self.cm.ph.getSearchGroups(track, '''kind=['"]([^'^"]+?)['"]''')[0]
            if 'caption' in track_kind:
                srtUrl = self.cm.ph.getSearchGroups(track, '''src=['"]([^'^"]+?)['"]''')[0]
                srtLabel = self.cm.ph.getSearchGroups(track, '''label=['"]([^'^"]+?)['"]''')[0]
                srtFormat = srtUrl[-3:]
                params = {'title': srtLabel, 'url': srtUrl, 'lang': srtLabel.lower()[:3], 'format': srtFormat}
                printDBG(str(params))
                subTracks.append(params)

        #$.get('/pass_md5/3526522-87-9-1595176733-d1cadb0bad545cdcc61809e26c0ccf93/p3yuk59uqm525k1zc9boovu4'
        #function makePlay(){for(var a="",t="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",n=t.length,o=0;10>o;o++)a+=t.charAt(Math.floor(Math.random()*n));return a+"?token=p3yuk59uqm525k1zc9boovu4&expiry="+Date.now();};
        pass_md5_url = self.cm.ph.getSearchGroups(data, "\$\.get\('(/pass_md5[^']+?)'")[0]
        makePlay = self.cm.ph.getSearchGroups(data, "(function makePlay\(\)\{.*?\};)")[0]
        if pass_md5_url and makePlay:
            pass_md5_url = self.cm.getFullUrl(pass_md5_url, self.cm.getBaseUrl(baseUrl))
            sts, new_url = self.cm.getPage(pass_md5_url, httpParams)

            if sts:
                code = "var url = '%s';\n%s\nconsole.log(url + makePlay());" % (new_url, makePlay)

                printDBG("-----------------------")
                printDBG(code)
                printDBG("-----------------------")

                ret = js_execute(code)
                newUrl = ret['data'].replace("\n", "")
                if newUrl:
                    if subTracks:
                        newUrl = urlparser.decorateUrl(newUrl, {'Referer': baseUrl, 'external_sub_tracks': subTracks})
                    else:
                        newUrl = urlparser.decorateUrl(newUrl, {'Referer': baseUrl})
                    params = {'name': 'link', 'url': newUrl}
                    printDBG(str(params))
                    urlsTab.append(params)

        return urlsTab
        

    def parserAPARAT(self, baseUrl):
        printDBG("parserAPARAT baseUrl[%r]" % baseUrl)

        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            } 
        }

        urlsTab = []

        if '/videohash/' not in baseUrl and '/showvideo/' not in baseUrl:
            sts, data = self.cm.getPage(baseUrl, httpParams)
            if not sts:
                return False
            
            cUrl = self.cm.meta['url']
            baseUrl = self.cm.getFullUrl(ph.search(data, '''['"]([^'^"]+?/videohash/[^'^"]+?)['"]''')[0], cUrl)
            if not baseUrl:
                baseUrl = self.cm.getFullUrl(ph.search(data, '''['"]([^'^"]+?/showvideo/[^'^"]+?)['"]''')[0], cUrl)

        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            #printDBG("-----------------------")
            #printDBG(data)
            #printDBG("-----------------------")
        
            srcJson = re.findall("sources\s?:\s?\[(.*?)\]", data, re.S)
            if not srcJson:
                srcJson = re.findall("multiSRC\"?\s?:\s?\[\[(.*?)\]\]", data, re.S)
                if srcJson:
                    sources = re.findall("(\{\"src\":.*?\})", srcJson[0])
                    if sources:
                        srcJson = [",".join(sources)]  
                
            if srcJson:
                srcJson = srcJson[0]
                sources = demjson_loads("[" + srcJson + "]")
                printDBG(str(sources))
                
                for s in sources:
                    u = s.get('src','')
                    if self.cm.isValidUrl(u):
                        u = urlparser.decorateUrl(u, {'Referer': baseUrl})
                        label = s.get('label','')
                        srcType = s.get('type','')
                    if 'm3u' in u or 'hls' in srcType or 'x-mpeg' in srcType :
                        params = getDirectM3U8Playlist(u, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                        printDBG(str(params))    
                        urlsTab.extend(params)
                    else:
                        params = {'name': label , 'url': u}
                        printDBG(str(params))
                        urlsTab.append(params)
        
        return urlsTab

    def parserABCVIDEO(self, baseUrl):
        printDBG("parserABCVIDEO baseUrl[%r]" % baseUrl)

        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            } 
        }

        urlsTab = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)

        if "eval(function(p,a,c,k,e,d)" in data:
            printDBG( 'Host resolveUrl packed' )
            packed = re.compile('>eval\(function\(p,a,c,k,e,d\)(.+?)</script>', re.DOTALL).findall(data)
            if packed:
                data2 = packed[-1]
            else:
                return ''
            printDBG( 'Host pack: [%s]' % data2)
            try:
                data = unpackJSPlayerParams(data2, TEAMCASTPL_decryptPlayerParams, 0, True, True)
                printDBG( 'OK unpack: [%s]' % data)
            except Exception: pass

        if sts:
            sitekey = ph.search(data, '''grecaptcha.execute\(['"]([^"^']+?)['"]''')[0]
            action = ph.search(data, '''grecaptcha.execute.*?action:\s['"]([^"^']+?)['"]''')[0]
            if not sitekey:
                printDBG("-----------------------")
                printDBG(data)
                printDBG("-----------------------")
                printDBG("parserABCVideo.Catpcha sitekey not found")
            else:    
                #process captcha
                printDBG("parserABCVideo.sitekey: % s" % sitekey)
                query_url = self.cm.ph.getSearchGroups(data, "jQuery.get\(([^,]+?),")[0]
                printDBG("parserABCVideo.query url: % s" % query_url)
                
                from Plugins.Extensions.IPTVPlayer.libs.recaptcha_v3_2captcha import UnCaptchaReCaptcha
                recaptcha = UnCaptchaReCaptcha(lang=GetDefaultLang())
                token = recaptcha.processCaptcha(sitekey, baseUrl, action)
                if token == '':
                    SetIPTVPlayerLastHostError('\n'.join(errorMsgTab)) 
                    return False
                
                query_url = self.cm.getFullUrl(eval(query_url), baseUrl)
                printDBG("parserABCVideo.query url after captcha: %s" % query_url)
                
                if self.cm.isValidUrl(query_url):
                    httpParams['header'].update({
                                'x-requested-with': 'XMLHttpRequest',
                                'Referer': baseUrl
                                })
                                
                    sts, data = self.cm.getPage(query_url, httpParams)
                    
                    if sts:
                        printDBG("-----------------------")
                        printDBG(data)
                        printDBG("-----------------------")
                        
                        try:
                            response = json_loads(data)
                            for u in response:
                                url = u.get('file','')
                                if self.cm.isValidUrl(url):
                                    url = urlparser.decorateUrl(url, {'Referer': baseUrl})
                                    label = u.get('label','')
                                if 'm3u' in url :
                                    params = getDirectM3U8Playlist(url, checkExt=True, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999)
                                    printDBG(str(params))    
                                    urlsTab.extend(params)
                                else:
                                    params = {'name': label , 'url': url}
                                    printDBG(str(params))
                                    urlsTab.append(params)
                                
                        except:
                            printExc()
        return urlsTab

    def parserPLAYHYDRAX(self, baseUrl):
        printDBG("parserPLAYHYDRAX baseUrl[%r]" % baseUrl)

        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            } 
        }

        urlsTab = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
            #printDBG("-------------------------------")
            #printDBG(data)
            #printDBG("-------------------------------")

            scripts = self.cm.ph.getAllItemsBeetwenMarkers(data, ('<script', '>'), '</script>', withMarkers=True)
            
            apiUrl = ""
            paramsScript =""
            
            for s in scripts:
                printDBG(s)
                tmp =  self.cm.ph.getSearchGroups(s, "src='([^']+?api\.js)'")[0]
                if tmp:
                    apiUrl = self.cm.getFullUrl(tmp, baseUrl)
                
                if '__CF$cv$params' in s:
                    paramsScript = clean_html(s)
                        
            printDBG("api Url: %s " % apiUrl)
            printDBG("-------------------")
            printDBG(paramsScript)
            printDBG("-------------------")
            
            if apiUrl:
                sts, apiCode = self.cm.getPage(apiUrl, httpParams)
        
                if sts:
                    #printDBG("-------------------------------")
                    #printDBG(apiCode)
                    #printDBG("-------------------------------")
                    
                    code1 = apiCode[:apiCode.find("!function")]
                    varNames = re.findall("var\s([a-z0-9_]{8,10}?)=",code1)
                    
                    if len(varNames) == 4 and varNames[1]==varNames[3]:
                        apiCode = re.sub(varNames[0],"vvv",apiCode)
                        apiCode = re.sub(varNames[1],"vv",apiCode)
                        apiCode = re.sub(varNames[2],"v",apiCode)
                        
                        #printDBG("-------------------------------")
                        #printDBG(apiCode)
                        #printDBG("-------------------------------")

                        code1 = apiCode[:apiCode.find("!function")]
                    
                        jsCode = code1 + '''
                        for (var i=0; i<vvv.length; i++){
                            console.log(v(i));
                        }
                        '''
                        ret = js_execute(jsCode)
                        strings = ret['data'].split('\n')
                        
                        printDBG(str(strings))
                        
                        for i in range(len(strings)):
                            apiCode = re.sub("v\('" + hex(i) +"'\)", "'" + strings[i] + "'", apiCode)

                        printDBG("-------------------------------")
                        printDBG(apiCode)
                        printDBG("-------------------------------")


        return urlsTab

    def parserMULTIKLAND(self, baseUrl):
        printDBG("parserMULTIKLAND baseUrl[%r]" % baseUrl)

        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            } 
        }

        urlsTab = []
        
        sts, data = self.cm.getPage(baseUrl, httpParams)
        
        if sts:
        
            playerData = re.findall("makePlayer\((\{.*?\})\);", data, re.S)
            if playerData:
                playerData = playerData[0].replace(' * ','') 
                printDBG(playerData)
                try:
                    playerJson = demjson_loads( playerData)
                    # title
                    title = playerJson.get('title','')
                    
                    #playlist:
                    if 'playlist' in playerJson:
                        playlist = playerJson['playlist']
                        printDBG(json_dumps(playlist))
                        seasons = playlist.get('seasons',[])
                        for season in seasons:
                            season_number = season.get('season',0)
                            eps = season.get('episodes',[])
                            for ep in eps:
                                ep_number = ep.get('episode','0')
                                ep_title = ep.get('title', '')
                                if 'hlsList' in ep:
                                    hlslist = ep['hlsList']
                                for label in hlslist:
                                    url = urlparser.decorateUrl(hlslist[label], {'Referer': baseUrl})

                                    params = {'title' :title + " " + label, 'name': title + " " + label, 'label': label, 'url': url}
                                    printDBG(str(params)) 
                                    urlsTab.append(params)
                        
                    else:
                        source = playerJson.get('source','')
                        if 'hlsList' in source:
                            hlslist = source['hlsList']
                            for label in hlslist:
                                url = urlparser.decorateUrl(hlslist[label], {'Referer': baseUrl})

                                params = {'title' :title + " " + label, 'name': title + " " + label, 'label': label, 'url': url}
                                printDBG(str(params)) 
                                urlsTab.append(params)

                except:
                    printExc()
        return urlsTab



    def parserM2LIST(self, baseUrl):
        printDBG("parserM2LIST baseUrl[%r]" % baseUrl)

        #example: http://www.m2list.com/embed.php?datab=y&lister=none&mirror=olv1&mainid=833795

        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl
            } 
        }

        urlsTab = []
        
        urlparts = baseUrl.split('?')
        query = dict(parse_qsl(urlparts[-1]))
        
        if 'mainid' in query and 'lister' in query and 'mirror' in query:
            #playerUrl = "http://player.m2list.com/mv/" + query.get('mainid','') + "?lister=" + query.get('lister','none') + "&mirror=" + query.get('mirror','') 
        
            #example: http://player.m2list.com/mv/833795?lister=none&mirror=olv1
            #         http://player.m2list.com/ajax/movie/get_sources/833795/olv1

            playerUrl = "http://player.m2list.com/ajax/movie/get_sources/" + query.get('mainid','') + "/" + query.get('mirror','') 
            
            printDBG("M2list: player Url: %s " % playerUrl)

            sts, data = self.cm.getPage(playerUrl, httpParams)
            
            if sts:

                try:
                    jsonData = json_loads(data)

                    printDBG("---------------------")
                    printDBG(data)
                    printDBG("---------------------")
                    
                    url = jsonData.get('sources','')
                    
                    if url:
                        if url.startswith('//'):
                            url = 'http:' + url
                        
                        sts, data = self.cm.getPage(url, httpParams)

                        printDBG("---------------------")
                        printDBG(data)
                        printDBG("---------------------")

                    
                except:
                    printExc
                    
                '''
                scripts = self.cm.ph.getAllItemsBeetwenMarkers(data, ('<script','>'), '</script>', withMarkers=False)
                
                for script in scripts:
                    if "eval(function" in script:
                        printDBG("----------- pack -----------------")
                        printDBG(script)

                        script = script + "\n"
                        # mods
                        script = script.replace("eval(function(p,a,c,k,e,d","pippo = function(p,a,c,k,e,d")
                        script = script.replace("return p}(", "print(p)}\n\npippo(")
                        script = script.replace("))\n",");\n")

                        # duktape
                        ret = js_execute( script )
                        decoded = ret['data']
                        printDBG('------------------------------')
                        printDBG(decoded)
                        printDBG('------------------------------')

                '''
                
                
        return urlsTab

    def parserGLORIATV(self, baseUrl):
        printDBG("parserGLORIATV baseUrl[%r]" % baseUrl)
        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader(browser='firefox')
        referer = baseUrl.meta.get('Referer')
        if referer: HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False
        cUrl = self.cm.meta['url']
        retTab = []
        data = ph.find(data, ('<video', '>'), '</video>', flags=0)[1]
        data = ph.findall(data, '<source', '>', flags=0)
        for item in data:
            url = self.cm.getFullUrl(ph.getattr(item, 'src').replace('&amp;', '&'), cUrl)
            type = ph.clean_html(ph.getattr(item, 'type').lower())
            if 'video' not in type and 'x-mpeg' not in type: continue
            url = strwithmeta(url, {'Referer': cUrl, 'User-Agent': HTTP_HEADER['User-Agent']})
            if 'video' in type:
                width = ph.getattr(item, 'width')
                height = ph.getattr(item, 'height')
                bitrate = ph.getattr(item, 'bitrate')
                retTab.append({'name': '[%s] %sx%s %s' % (type, width, height, bitrate), 'url': url})
            elif 'x-mpeg' in type:
                retTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))

        return retTab

    def parserNINJASTREAMTO(self, baseUrl):
        printDBG("parserNINJASTREAMTO baseUrl [%s]" % baseUrl)

        httpParams = {
            'header' : {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.61 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip',
                'Referer' : baseUrl.meta.get('Referer', baseUrl)
            }
        }

        urlsTab = []

        sts, data = self.cm.getPage(baseUrl, httpParams)
        if sts:
            r = self.cm.ph.getSearchGroups(data, r'v-bind:[n|s]*stream="([^"]+?)"')[0].replace('&quot;', '"')
            if r:
                data = json_loads(r)
                hash = data.get('hash')
                host = "".join([chr(ord(i) ^ ord(str(idx%2+1))) for idx, i in enumerate(data.get('host'))])
                url = '%s%s/index.m3u8' % (host, hash)
                urlsTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))

        return urlsTab

    def parserKINOGERRE(self, baseUrl):
        urlTab=[]
        url = baseUrl.replace('/v/', '/api/source/')
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        urlParams = {'header': HTTP_HEADER}
        post_data = { 'r':'https://kinoger.com/', 'd': 'kinoger.re'}
        sts, data = self.cm.getPage(url, urlParams, post_data=post_data)
        if not sts: return []

        #printDBG("kinogerto.getVideoLinks data[%s]" % data)
        files = self.cm.ph.getAllItemsBeetwenMarkers(data, '{"file":', '}')
        for f in files:
            link, quality = self.cm.ph.getSearchGroups(f, '''file":"([^"]+)","label":"([^"]+)''', grupsNum=2 )
            link = link.replace('\\', '')
            urlTab.append({'name':'[%s]' % quality, 'url':strwithmeta(link, {'Referer':url})})
            #printDBG("kinogerto.getVideoLinks [typ: %s link: %s]" % ( typ, link))
        return urlTab

    def parserEVOLOADIO(self, baseUrl):
        printDBG("parserEVOLOADIO baseUrl[%s]" % baseUrl)
        urlTab = []
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        urlParams = {'header': HTTP_HEADER}

        media_id = self.cm.ph.getSearchGroups(baseUrl + '/', '(?:e|f|v)[/-]([A-Za-z0-9]+)[^A-Za-z0-9]')[0]
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return False

        passe = re.search('<div id="captcha_pass" value="(.+?)"></div>', data).group(1)
        sts, crsv = self.cm.getPage('https://csrv.evosrv.com/captcha?m412548', urlParams)
        if not sts:
            return False

        post_data = {"code": media_id, "csrv_token": crsv, "pass": passe, "token": "ok", "reff": baseUrl}
        sts, data = self.cm.getPage('https://evoload.io/SecurePlayer', urlParams, post_data)
        printDBG(str(data))
        if not sts:
            return False

        r = json_loads(data).get('stream')
        if r:
            surl = r.get('backup') if r.get('backup') else r.get('src')
            if surl:
                params = {'name': 'mp4', 'url': surl}
                urlTab.append(params)

        return urlTab

    def parserUSERLOADCO(self, baseUrl):
        printDBG("parserUSERLOADCO baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer: HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts: return False

        if "eval(function(p,a,c,k,e,d)" in data:
            printDBG( 'Host resolveUrl packed' )
            packed = re.compile('>eval\(function\(p,a,c,k,e,d\)(.+?)</script>', re.DOTALL).findall(data)
            if packed:
                data2 = packed[-1]
            else:
                return ''
            printDBG( 'Host pack: [%s]' % data2)
            try:
                data = unpackJSPlayerParams(data2, TEAMCASTPL_decryptPlayerParams, 0, True, True)
                printDBG( 'OK unpack: [%s]' % data)
            except Exception: pass

            morocco = self.cm.ph.getSearchGroups(data, '''['"](AO.+?Aa)['"]''')[0]
            if morocco =='': morocco = self.cm.ph.getSearchGroups(data, '''['"]([0-9a-zA-Z]{31})['"]''')[0]
            tmp = re.findall('''['"]([0-9a-z]{32})['"]''', data)
            for item in tmp:
                post_data = {'morocco':morocco, 'mycountry':item}
                sts, data = self.cm.getPage('https://userload.co/api/request/', urlParams, post_data)
                if not sts: return False
                if 'http' in data: break
            data = data.splitlines()[0]

        urlTab = []
        url = strwithmeta(data, {'Origin':"https://" + urlparser.getDomain(baseUrl), 'Referer':baseUrl})
        if 'm3u8' in url:
            urlTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
        else:
            urlTab.append({'name':'mp4', 'url':url})

        return urlTab

    def parserMATCHATONLINE(self, baseUrl):
        printDBG("parserMATCHATONLINE baseUrl[%r]" % baseUrl)
        sts, data = self.cm.getPage(baseUrl)
        if not sts:
            return False

        hlsUrl = self.cm.ph.getSearchGroups(data, '''['"]?hls['"]?\s*?:\s*?['"]([^'^"]+?)['"]''')[0]
        if hlsUrl.startswith('//'):
            hlsUrl = 'http:' + hlsUrl
        if self.cm.isValidUrl(hlsUrl):
            hlsUrl = urlparser.decorateUrl(hlsUrl, {'iptv_proto': 'm3u8', 'Referer': baseUrl, 'Origin': urlparser.getDomain(baseUrl, False)})
            return getDirectM3U8Playlist(hlsUrl, checkExt=False, checkContent=True, sortWithMaxBitrate=999999999)
        return False

    def parserSHOWSPORTXYZ(self, baseUrl):
        printDBG("parserSHOWSPORTXYZ baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        urlTab = []
        url = self.cm.ph.getSearchGroups(data, '''\swindow.atob\(['"]([^"^']+?)['"]''')[0]
        if url != '':
            urlTab.extend(getDirectM3U8Playlist(urllib.unquote(base64.b64decode(url).replace("playoutengine.sinclairstoryline", "playoutengine-v2.sinclairstoryline")), checkContent=True, sortWithMaxBitrate=999999999))

        return urlTab

    def parserASSIAORG(self, baseUrl):
        printDBG("parserASSIAORG baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        urlTab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Clappr.Player', ('</script', '>'), False)[1]
        url = self.cm.ph.getSearchGroups(data, '''source:\s?['"]([^"^']+?)['"]''')[0]
        url = strwithmeta(url, {'Origin': urlparser.getDomain(baseUrl, False), 'Referer': baseUrl, 'User-Agent': 'Wget/1.20.3 (linux-gnu)'})
        if url != '':
            urlTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))

        return urlTab

    def parserEMBEDSTREAMME(self, baseUrl):
        printDBG("parserEMBEDSTREAMME baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        urlTab = []

        pdettxt = re.findall('pdettxt\s*=\s*"(.+?)"', data, re.DOTALL)[0]
        zmid = re.findall('zmid\s*=\s*"(.+?)"', data, re.DOTALL)[0]
        edm = re.findall('edm\s*=\s*"(.+?)"', data, re.DOTALL)[0]
        pid = re.findall('pid\s*=\s*(\d+);', data, re.DOTALL)[0]

        qbc = 'https://www.tvply.me/' if 'cdn.tvply.me' in data else'https://www.plytv.me/'
        headers = {
            'authority': 'www.plytv.me',
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'origin': 'https://embedstream.me',
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-gpc': '1',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'iframe',
            'referer': 'https://embedstream.me/',
            'accept-language': 'en-US,en;q=0.9',
        }
        urlParams = {'header': headers}
        post_data = {'pid': (str(pid)), 'ptxt': pdettxt}
        urlk = 'https://%s/sdembed' % (edm) + '?v=' + str(zmid)
        sts, data = self.cm.getPage(urlk, urlParams, post_data)
        if not sts:
            return []
        errorMessage = clean_html(self.cm.ph.getDataBeetwenNodes(data, ('<h4', '>'), ('</h4', '>'), False)[1])
        SetIPTVPlayerLastHostError(errorMessage)
#        printDBG("parserEMBEDSTREAMME data 2[%s]" % data)

        skrypty = re.findall('<script>(.+?)<\/script>\\n', data, re.DOTALL)#<script>([^<]+)<\/script>',response_content,re.DOTALL)

        payload = """function abs() {%s};\n console.log(abs())"""
        a = ''
        for skrypt in skrypty:
            if 'let' in skrypt and 'eval' in skrypt:
                a = payload % (skrypt)
                a = a[::-1].replace("eval"[::-1], "return"[::-1], 1)[::-1]
                break
        jscode = a.replace('let ', '')
#        printDBG("parserEMBEDSTREAMME jscode[%s]" % jscode)
        ret = js_execute(jscode, {'timeout_sec': '30 -m 0'})

        if ret['sts'] and 0 == ret['code']:
            if 'function(h,u,n,t,e,r)' in ret['data']:

                ff = re.findall('function\(h,u,n,t,e,r\).*?}\((".+?)\)\)', ret['data'], re.DOTALL)[0]
                ff = ff.replace('"', '')
                h, u, n, t, e, r = ff.split(',')

                cc = dehunt(h, int(u), n, int(t), int(e), int(r))

                cc = cc.replace("\'", '"')

                fil = re.findall('file:\s*window\.atob\((.+?)\)', cc, re.DOTALL)[0]

                src = re.findall(fil + '\s*=\s*"(.+?)"', cc, re.DOTALL)[0]
                url = base64.b64decode(src)

                str1 = re.findall('"?stream="\s*\+\s*(\w+)\s*\+\s*"', cc, re.DOTALL)[0]
                strName = re.findall('const\s*%s\s*=\s*"([^"]+)"' % (str1), cc, re.DOTALL)[0]

                scode, expires = re.findall('formauthurl\({"scode":\s*"([^"]+)",\s"ts":\s(\d+)\}', cc, re.DOTALL)[0]

                headers = {
                    "Referer": urlk,
                    "Origin": qbc,
                    "User-Agent": 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.101 Safari/537.36',
                    "Accept-Language": "en",
                    "Accept": "application/json, text/javascript, */*; q=0.01",
                }
                urlParams = {'header': headers}
                kurl = 'https://key.seckeyserv.me/?stream=%s&scode=%s&expires=%s' % (strName, scode, expires)
                sts, data = self.cm.getPage(kurl, urlParams)
                printDBG("parserEMBEDSTREAMME key.seckeyserv.me[%s]" % data)# cloudflare protection?

                if url != '':
                    url = strwithmeta(url, {'Origin': qbc, 'Referer': urlk, 'Accept-Language': 'en'})
                    urlTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))
                    urlParams['header']['Referer'] = urlk
                    urlParams['header']['Origin'] = qbc
                    urlParams['header']['Accept-Language'] = 'en'
                    sts, data = self.cm.getPage(url, urlParams)
                    printDBG("parserEMBEDSTREAMME m3u8[%s]" % data)

        return urlTab

    def parserDADDYLIVE(self, baseUrl):
        printDBG("parserDADDYLIVE baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []
        cUrl = self.cm.meta['url']

        data = self.cm.ph.getDataBeetwenNodes(data, ('<iframe', '>', 'src'), ('</iframe', '>'))[1]
        url = self.cm.ph.getSearchGroups(data, '''src=['"]([^"^']+?)['"]''')[0]
        HTTP_HEADER['Referer'] = cUrl
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return []
        printDBG("parserEMBEDSTREAMME data[%s]" % data)
        urlTab = []
        data = self.cm.ph.getDataBeetwenMarkers(data, 'Clappr.Player', ('</script', '>'), False)[1]
        url = self.cm.ph.getSearchGroups(data, '''source:\s?['"]([^"^']+?)['"]''')[0]
        url = strwithmeta(url, {'Origin': urlparser.getDomain(baseUrl, False), 'Referer': cUrl})
        if url != '':
            urlTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))

        return urlTab

    def parserLIVEONSCORETV(self, baseUrl):
        printDBG("parserLIVEONSCORETV baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        data = self.cm.ph.getDataBeetwenMarkers(data, 'var player', ('</script', '>'), False)[1]
        url = self.cm.ph.getSearchGroups(data, '''url:\s*['"]([^"^']+?)['"]''')[0]
        UrlID = self.cm.ph.getSearchGroups(data, '''var\svidgstream\s?=\s?['"]([^"^']+?)['"]''')[0]
        url = url + '?idgstream=' + UrlID

        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return []

        urlTab = []
        url = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.mp4(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
        if url != '':
            url = strwithmeta(url, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
            urlTab.append({'name': 'mp4', 'url': url})
        hlsUrl = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
        if hlsUrl != '':
            hlsUrl = strwithmeta(hlsUrl, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
            urlTab.extend(getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return urlTab

    def parserTELERIUMTVCOM(self, baseUrl):
        printDBG("parserTELERIUMTVCOM baseUrl[%s]" % baseUrl)

        from Plugins.Extensions.IPTVPlayer.libs import getkeyTelerium as TRD

        domain = urlparser.getDomain(baseUrl)
        if 'embed.' in domain:
            domain = 'telerium.digital'

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        cid = re.findall('''cid\s*=\s['"](.+?)['"]''', data)

        script = re.findall('(var _0x.*?)<\/script>', data, re.DOTALL)[0]
        decscript = TRD.getkey(script)
        scriptdeco = decscript.replace("'+'", '').replace("\'", '"')
#        printDBG("parserTELERIUMTVCOM scriptdeco[%s]" % scriptdeco)
        azz = re.findall('token\s*=\s*_0x.+?\(reverse\s*\,\s*_0x.+?\[(.+?)\]', scriptdeco)#[0]
        azz = azz[0] if azz else re.findall('token\s*=\s*reverse.*?\[(.+?)\]', scriptdeco)[0]

        abcz = re.findall('(0[xX][0-9a-fA-F]+)', azz)

        def unhex(txt):
            ab = re.sub('\\\\x[a-f0-9][a-f0-9]', lambda m: m.group()[2:].decode('hex'), txt)
            return ab

        for az in abcz:
            x = str(int(unhex(az), 16))
            azz = re.sub(az + '(?![a-f0-9])', x, azz)

        spech = eval(azz)
        printDBG("parserTELERIUMTVCOM spech[%s]" % spech)
        timeurls = eval(re.findall('var timeUrls=(\[.+?\])', scriptdeco)[0])
        printDBG("parserTELERIUMTVCOM timeurls[%s]" % str(timeurls))

        tur = re.findall('''['"]head['"].+?\[['"]ajax['"]\]\(\{['"]url['"]:_0[xX][0-9a-fA-F]+\[(.+?)\]''', scriptdeco)[0]
        turls = re.findall('(0[xX][0-9a-fA-F]+)', tur)
        for turl in turls:
            x = str(int(unhex(turl), 16))
        #tur = tur.replace(turl,x)
            tur = re.sub(turl + '(?![a-f0-9])', x, tur)
        tur = eval(tur)
        printDBG("parserTELERIUMTVCOM tur[%s]" % tur)

        sessx = {
    #    'authority': 'bamtech.sc.omtrdc.net',
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'origin': 'https://' + domain,
            'sec-fetch-site': 'cross-site',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': baseUrl,
            'accept-language': 'en-US,en;q=0.9,pl;q=0.8',
        }
        sessxParams = {'header': sessx}
        sts, data = self.cm.getPage(timeurls[tur], sessxParams)
        if not sts:
            return []
        date_time_str = self.cm.meta.get('last-modified', '')
        printDBG("parserTELERIUMTVCOM date_time_str[%s]" % str(date_time_str))

        import datetime
        try:
            date_time_obj = datetime.datetime.strptime(date_time_str, '%a, %d %b %Y %H:%M:%S %Z')
        except TypeError:
            date_time_obj = datetime.datetime(*(time.strptime(date_time_str, '%a, %d %b %Y %H:%M:%S %Z')[0:6]))
        printDBG("parserTELERIUMTVCOM date_time_obj[%s]" % date_time_obj)

        def to_timestamp(a_date):
            from datetime import datetime
            try:
                import pytz
            except:
                pass
            if a_date.tzinfo:
                epoch = datetime(1970, 1, 1, tzinfo=pytz.UTC)
                diff = a_date.astimezone(pytz.UTC) - epoch
            else:
                epoch = datetime(1970, 1, 1)
                diff = a_date - epoch
            return int((diff.microseconds + 0.0 + (diff.seconds + diff.days * 24 * 3600) * 10 ** 6) / 10 ** 3)

        tst4 = to_timestamp(date_time_obj)
        printDBG("parserTELERIUMTVCOM tst4[%s]" % tst4)

        nturl = 'https://%s/streams/%s/%s.json' % (domain, str(cid[0]), str(tst4))

        sts, data = self.cm.getPage(nturl, sessxParams)
        if not sts:
            return []
        printDBG("parserTELERIUMTVCOM nturl[%s]" % data)

        data = json_loads(data)
        urln = data.get('url', '')
        tokenurl = data.get('tokenurl', '')
        printDBG("parserTELERIUMTVCOM url[%s]" % urln)
        printDBG("parserTELERIUMTVCOM tokenurl[%s]" % tokenurl)

        burl = 'https://%s' % (domain)
        nxturl = burl + tokenurl

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            'Accept': '*/*',
            'Accept-Language': 'pl,en-US;q=0.7,en;q=0.3',
            'Referer': baseUrl,
            'Alt-Used': burl,
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        }
        tokenParams = {'header': headers, 'cookie': {'volume': '0'}}
        sts, realResp = self.cm.getPage(nxturl, tokenParams)
        if not sts:
            return []
        printDBG("parserTELERIUMTVCOM token[%s]" % realResp)
        realResp = re.findall('"(.+?)"', realResp)[spech]
        url = 'https:' + urln + realResp[::-1]
        urlTab = []
        url = strwithmeta(url, {'Origin': burl, 'Referer': baseUrl, 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0 Waterfox/56.5', 'Connection': 'keep-alive'})
        if url != '':
            urlTab.extend(getDirectM3U8Playlist(url, checkContent=True, sortWithMaxBitrate=999999999))

        return urlTab

    def parserF1LIVEGPME(self, baseUrl):
        printDBG("parserF1LIVEGPMEself baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        tmp = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)

        vplayerData = ''
        for item in tmp:
            if 'forEach' in item and 'atob' in item:
                vplayerData = item

        if vplayerData != '':
            jscode = base64.b64decode('''d2luZG93PXRoaXM7ZG9jdW1lbnQ9e307ZG9jdW1lbnQud3JpdGU9ZnVuY3Rpb24oKXtwcmludChhcmd1bWVudHNbMF0pO307YXRvYj1mdW5jdGlvbihlKXtlLmxlbmd0aCU0PT0zJiYoZSs9Ij0iKSxlLmxlbmd0aCU0PT0yJiYoZSs9Ij09IiksZT1EdWt0YXBlLmRlYygiYmFzZTY0IixlKSxkZWNUZXh0PSIiO2Zvcih2YXIgdD0wO3Q8ZS5ieXRlTGVuZ3RoO3QrKylkZWNUZXh0Kz1TdHJpbmcuZnJvbUNoYXJDb2RlKGVbdF0pO3JldHVybiBkZWNUZXh0fTsK''')
            jscode += vplayerData
            ret = js_execute(jscode, {'timeout_sec': 40})
            if ret['sts'] and 0 == ret['code']:
                vplayerData = ret['data'].strip()

        urlTab = []
        hlsUrl = self.cm.ph.getSearchGroups(vplayerData, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
        if hlsUrl != '':
            hlsUrl = strwithmeta(hlsUrl, {'Origin': urlparser.getDomain(baseUrl, False), 'Referer': baseUrl})
            urlTab.extend(getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
        mpdUrl = self.cm.ph.getSearchGroups(vplayerData, '''["'](https?://[^'^"]+?\.mpd(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
        if mpdUrl != '':
            mpdUrl = strwithmeta(mpdUrl, {'Origin': urlparser.getDomain(baseUrl, False), 'Referer': baseUrl})
            urlTab.extend(getMPDLinksWithMeta(mpdUrl, False, sortWithMaxBandwidth=999999999))

        return urlTab

    def parserHIGHLOADTO(self, baseUrl):
        printDBG("parserHIGHLOADTO baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        jsUrl = self.cm.getFullUrl(self.cm.ph.getSearchGroups(data, '''src=\s?['"]([^'^"]+?master\.js)['"]''')[0], baseUrl)
        sts, jsdata = self.cm.getPage(jsUrl, urlParams)
        if not sts:
            return []

        if 'function(h,u,n,t,e,r)' in jsdata:
            ff = re.findall('function\(h,u,n,t,e,r\).*?}\((".+?)\)\)', jsdata, re.DOTALL)[0]
            ff = ff.replace('"', '')
            h, u, n, t, e, r = ff.split(',')
            jsdata = dehunt(h, int(u), n, int(t), int(e), int(r))
#        printDBG("parserHIGHLOADTO jsdata[%s]" % jsdata)
        jscode = self.cm.ph.getSearchGroups(jsdata, '''var\s[^=]+?=\s?([^;]+?);''', ignoreCase=True)[0]
        jsvar = self.cm.ph.getSearchGroups(jscode, '''([^.]+?)\.replace''', ignoreCase=True)[0]
        printDBG("parserHIGHLOADTO jscode[%s]  jsvar[%s]" % (jscode, jsvar))

        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        script = ''
        for item in data:
            if 'function(h,u,n,t,e,r)' in item:
                ff = re.findall('function\(h,u,n,t,e,r\).*?}\((".+?)\)\)', item, re.DOTALL)[0]
                ff = ff.replace('"', '')
                h, u, n, t, e, r = ff.split(',')
                script = dehunt(h, int(u), n, int(t), int(e), int(r))
                if jsvar in script:
                    break
        printDBG("parserHIGHLOADTO script[%s]" % script)

        url = self.cm.ph.getDataBeetwenMarkers(script, 'var %s="' % jsvar, '";', False)[1]
        url = eval(jscode.replace(jsvar, 'url'))
        url = urlparser.getDomain(baseUrl, False) + base64.b64decode(url)
        urlTab = []
        if url != '':
            urlTab.append({'name': 'mp4', 'url': strwithmeta(url, {'Referer': baseUrl})})

        return urlTab




    def parserSPORTSONLINETO(self, baseUrl):
        printDBG("parserSPORTSONLINETO baseUrl[%r]" % baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return False
        cUrl = self.cm.meta['url']

        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
        HTTP_HEADER['Referer'] = cUrl
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return False

        urlTab = []
        if "eval(function(p,a,c,k,e,d)" in data:
            printDBG('Host resolveUrl packed')
            scripts = re.findall(r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>", data, re.S)
            for packed in scripts:
                data2 = packed
                printDBG('Host pack: [%s]' % data2)
                try:
                    data = unpackJSPlayerParams(data2, TEAMCASTPL_decryptPlayerParams, 0, True, True)
                    printDBG('OK unpack: [%s]' % data)
                except Exception:
                    pass

                url = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.mp4(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
                if url != '':
                    url = strwithmeta(url, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
                    urlTab.append({'name': 'mp4', 'url': url})
                hlsUrl = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
                if hlsUrl != '':
                    hlsUrl = strwithmeta(hlsUrl, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
                    urlTab.extend(getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return urlTab
    
    def parserSTREAMCRYPTNET(self, baseUrl):
        printDBG("parserSTREAMCRYPTNET baseUrl[%s]" % baseUrl)

        sts, data = self.cm.getPage(baseUrl, {'header':{'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36'}, 'use_cookie':1, 'save_cookie':1,'load_cookie':1, 'cookiefile': GetCookieDir("streamcrypt.cookie"), 'with_metadata':1})
        #if not sts:
        #    return []

        red_url = self.cm.meta['url']
        printDBG('redirect to url: %s' % red_url)

        if red_url == baseUrl:
            red_url = re.findall("URL=([^\"]+)",data)[0]

        return urlparser().getVideoLinkExt(red_url)
    
    def parserTUBELOADCO(self, baseUrl):
        printDBG("parserTUBELOADCO baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        domain = urlparser.getDomain(baseUrl, False)
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        jsUrl = self.cm.getFullUrl(self.cm.ph.getSearchGroups(data, '''src=\s?['"]([^'^"]+?main\.min\.js)['"]''')[0], baseUrl)
        sts, jsdata = self.cm.getPage(jsUrl, urlParams)
        if not sts:
            return []

        if 'function(h,u,n,t,e,r)' in jsdata:
            ff = re.findall('function\(h,u,n,t,e,r\).*?}\((".+?)\)\)', jsdata, re.DOTALL)[0]
            ff = ff.replace('"', '')
            h, u, n, t, e, r = ff.split(',')
            jsdata = dehunt(h, int(u), n, int(t), int(e), int(r))
#        printDBG("parserTUBELOADCO jsdata[%s]" % jsdata)
        jscode = self.cm.ph.getSearchGroups(jsdata, '''var\s[^=]+?=\s?([^;]+?);''', ignoreCase=True)[0]
        jsvar = self.cm.ph.getSearchGroups(jscode, '''([^.]+?)\.replace''', ignoreCase=True)[0]
        printDBG("parserTUBELOADCO jscode[%s]  jsvar[%s]" % (jscode, jsvar))

        data = self.cm.ph.getAllItemsBeetwenNodes(data, ('<script', '>'), ('</script', '>'), False)
        script = ''
        for item in data:
            if 'function(h,u,n,t,e,r)' in item:
                ff = re.findall('function\(h,u,n,t,e,r\).*?}\((".+?)\)\)', item, re.DOTALL)[0]
                ff = ff.replace('"', '')
                h, u, n, t, e, r = ff.split(',')
                script = dehunt(h, int(u), n, int(t), int(e), int(r))
                if jsvar in script:
                    break
#        printDBG("parserTUBELOADCO script[%s]" % script)

        jscode = script + '\n' + jsdata
        jscode = jscode.replace('atob', 'base64.b64decode')
        decode = ''
        vars = re.compile('var\s(.*?=[^{]+?;)').findall(jscode)
        exec('\n'.join(vars))

        urlTab = []
        if decode:
            urlTab.append({'name': 'mp4', 'url': strwithmeta(decode, {'Referer': baseUrl})})

        return urlTab

    def parserVIDEOVARDSX(self, baseUrl):
        printDBG("parserVIDEOVARDSX baseUrl[%r]" % baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}

        domain = urlparser.getDomain(baseUrl)
        video_id = ph.search(baseUrl, r'''/[vef]/([0-9a-zA-Z]+)''')[0]

        def tear_decode(data_file, data_seed):

            def replacer(match):
                chars = {
                    '0': '5',
                    '1': '6',
                    '2': '7',
                    '5': '0',
                    '6': '1',
                    '7': '2'
                }
                return chars[match.group(0)]

            def str2bytes(a16):
                a21 = []
                for i in a16:
                    a21.append(ord(i))
                return a21

            def bytes2str(a10):
                a13 = 0
                a14 = len(a10)
                a15 = ''
                while True:
                    if a13 >= a14:
                        break
                    a15 += chr(255 & a10[a13])
                    a13 += 1
                return a15

            def digest_pad(a36):
                a41 = []
                a39 = 0
                a40 = len(a36)
                a43 = 15 - (a40 % 16)
                a41.append(a43)
                while a39 < a40:
                    a41.append(a36[a39])
                    a39 += 1
                a45 = a43
                while a45 > 0:
                    a41.append(0)
                    a45 -= 1
                return a41

            def blocks2bytes(a29):
                a34 = []
                a33 = 0
                a32 = len(a29)
                while a33 < a32:
                    a34 += [255 & rshift(int(a29[a33]), 24)]
                    a34 += [255 & rshift(int(a29[a33]), 16)]
                    a34 += [255 & rshift(int(a29[a33]), 8)]
                    a34 += [255 & a29[a33]]
                    a33 += 1
                return a34

            def bytes2blocks(a22):
                a27 = []
                a28 = 0
                a26 = 0
                a25 = len(a22)
                while True:
                    a27.append(((255 & a22[a26]) << 24) & 0xFFFFFFFF)
                    a26 += 1
                    if a26 >= a25:
                        break
                    a27[a28] |= ((255 & a22[a26]) << 16 & 0xFFFFFFFF)
                    a26 += 1
                    if a26 >= a25:
                        break
                    a27[a28] |= ((255 & a22[a26]) << 8 & 0xFFFFFFFF)
                    a26 += 1
                    if a26 >= a25:
                        break
                    a27[a28] |= (255 & a22[a26])
                    a26 += 1
                    if a26 >= a25:
                        break
                    a28 += 1
                return a27

            def xor_blocks(a76, a77):
                return [a76[0] ^ a77[0], a76[1] ^ a77[1]]

            def unpad(a46):
                a49 = 0
                a52 = []
                a53 = (7 & a46[a49])
                a49 += 1
                a51 = (len(a46) - a53)
                while a49 < a51:
                    a52 += [a46[a49]]
                    a49 += 1
                return a52

            def rshift(a, b):
                return (a % 0x100000000) >> b

            def tea_code(a79, a80):
                a85 = a79[0]
                a83 = a79[1]
                a87 = 0

                for a86 in range(32):
                    a85 += int((((int(a83) << 4) ^ rshift(int(a83), 5)) + a83) ^ (a87 + a80[(a87 & 3)]))
                    a85 = int(a85 | 0)
                    a87 = int(a87) - int(1640531527)
                    a83 += int(
                        (((int(a85) << 4) ^ rshift(int(a85), 5)) + a85) ^ (a87 + a80[(rshift(a87, 11) & 3)]))
                    a83 = int(a83 | 0)
                return [a85, a83]

            def binarydigest(a55):
                a63 = [1633837924, 1650680933, 1667523942, 1684366951]
                a62 = [1633837924, 1650680933]
                a61 = a62
                a66 = [0, 0]
                a68 = [0, 0]
                a59 = bytes2blocks(digest_pad(str2bytes(a55)))
                a65 = 0
                a67 = len(a59)
                while a65 < a67:
                    a66[0] = a59[a65]
                    a65 += 1
                    a66[1] = a59[a65]
                    a65 += 1
                    a68[0] = a59[a65]
                    a65 += 1
                    a68[1] = a59[a65]
                    a65 += 1
                    a62 = tea_code(xor_blocks(a66, a62), a63)
                    a61 = tea_code(xor_blocks(a68, a61), a63)
                    a64 = a62[0]
                    a62[0] = a62[1]
                    a62[1] = a61[0]
                    a61[0] = a61[1]
                    a61[1] = a64

                return [a62[0], a62[1], a61[0], a61[1]]

            def ascii2bytes(a99):
                a2b = {'A': 0, 'B': 1, 'C': 2, 'D': 3, 'E': 4, 'F': 5, 'G': 6, 'H': 7, 'I': 8, 'J': 9, 'K': 10,
                       'L': 11, 'M': 12, 'N': 13, 'O': 14, 'P': 15, 'Q': 16, 'R': 17, 'S': 18, 'T': 19, 'U': 20,
                       'V': 21, 'W': 22, 'X': 23, 'Y': 24, 'Z': 25, 'a': 26, 'b': 27, 'c': 28, 'd': 29, 'e': 30,
                       'f': 31, 'g': 32, 'h': 33, 'i': 34, 'j': 35, 'k': 36, 'l': 37, 'm': 38, 'n': 39, 'o': 40,
                       'p': 41, 'q': 42, 'r': 43, 's': 44, 't': 45, 'u': 46, 'v': 47, 'w': 48, 'x': 49, 'y': 50,
                       'z': 51, '0': 52, '1': 53, '2': 54, '3': 55, '4': 56, '5': 57, '6': 58, '7': 59, '8': 60,
                       '9': 61, '-': 62, '_': 63}
                a6 = -1
                a7 = len(a99)
                a9 = 0
                a8 = []

                while True:
                    while True:
                        a6 += 1
                        if a6 >= a7:
                            return a8
                        if a99[a6] in a2b.keys():
                            break
                    a8.insert(a9, int(int(a2b[a99[a6]]) << 2))
                    while True:
                        a6 += 1
                        if a6 >= a7:
                            return a8
                        if a99[a6] in a2b.keys():
                            break
                    a3 = a2b[a99[a6]]
                    a8[a9] |= rshift(int(a3), 4)
                    a9 += 1
                    a3 = (15 & a3)
                    if (a3 == 0) and (a6 == (a7 - 1)):
                        return a8
                    a8.insert(a9, int(a3) << 4)
                    while True:
                        a6 += 1
                        if a6 >= a7:
                            return a8
                        if a99[a6] in a2b.keys():
                            break
                    a3 = a2b[a99[a6]]
                    a8[a9] |= rshift(int(a3), 2)
                    a9 += 1
                    a3 = (3 & a3)
                    if (a3 == 0) and (a6 == (a7 - 1)):
                        return a8
                    a8.insert(a9, int(a3) << 6)
                    while True:
                        a6 += 1
                        if a6 >= a7:
                            return a8
                        if a99[a6] in a2b.keys():
                            break
                    a8[a9] |= a2b[a99[a6]]
                    a9 += 1

                return a8

            def ascii2binary(a0):
                return bytes2blocks(ascii2bytes(a0))

            def tea_decode(a90, a91):
                a95 = a90[0]
                a96 = a90[1]
                a97 = int(-957401312)
                for a98 in range(32):
                    a96 = int(a96) - ((((int(a95) << 4) ^ rshift(int(a95), 5)) + a95) ^ (
                        a97 + a91[(rshift(int(a97), 11) & 3)]))
                    a96 = int(a96 | 0)
                    a97 = int(a97) + 1640531527
                    a97 = int(a97 | 0)
                    a95 = int(a95) - int(
                        (((int(a96) << 4) ^ rshift(int(a96), 5)) + a96) ^ (a97 + a91[(a97 & 3)]))
                    a95 = int(a95 | 0)
                return [a95, a96]

            data_seed = re.sub('[012567]', replacer, data_seed)
            new_data_seed = binarydigest(data_seed)
            new_data_file = ascii2binary(data_file)
            a69 = 0
            a70 = len(new_data_file)
            a71 = [1633837924, 1650680933]
            a73 = [0, 0]
            a74 = []
            while a69 < a70:
                a73[0] = new_data_file[a69]
                a69 += 1
                a73[1] = new_data_file[a69]
                a69 += 1
                a72 = xor_blocks(a71, tea_decode(a73, new_data_seed))
                a74 += a72
                a71[0] = a73[0]
                a71[1] = a73[1]
            return re.sub('[012567]', replacer, bytes2str(unpad(blocks2bytes(a74))))


        sts, data = self.cm.getPage('https://%s/api/make/hash/%s' % (domain, video_id), urlParams)
        if not sts:
            return False
        cUrl = self.cm.meta['url']
        printDBG("parserVIDEOVARDSX data[%r]" % data)

        data = json_loads(data)
        r = data.get('hash', '')
        if not r:
            return False

        url = 'https://%s/api/player/setup' % domain
        post_data = {'cmd': 'get_stream', 'file_code': video_id, 'hash': r}

        HTTP_HEADER['Origin'] = 'https://' + domain
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(url, urlParams, post_data)
        if not sts:
            return False
        printDBG("parserVIDEOVARDSX data[%r]" % data)

        resp = json_loads(data)
        vfile = resp.get('src')
        seed = resp.get('seed')
        data = tear_decode(vfile, seed)
        printDBG("parserVIDEOVARDSX tear_decode[%r]" % data)
        urlTab = []
        if data != '':
            hlsUrl = strwithmeta(data, {'Origin': "https://" + domain, 'Referer': baseUrl})
            urlTab.extend(getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return urlTab  

    def parserCASTFREEME(self, baseUrl):
        printDBG("parserCASTFREEME baseUrl[%r]" % baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return False
        cUrl = self.cm.meta['url']

        url = eval(re.findall('return\((\[.+?\])', data)[0])
        url = ''.join(url).replace('\/', '/')

        urlTab = []
        if 'm3u' in url:
            url = strwithmeta(url, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
            urlTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))
        else:
            url = strwithmeta(url, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
            urlTab.append({'name': 'mp4', 'url': url})

        return urlTab
    
    def parserMEMBED(self, url):
        printDBG("parserMEMBED url: " + url)
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = url.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return
        urlTab = []
        all = self.cm.ph.getDataBeetwenMarkers(data, '<ul class="list-server-items">', '</ul>', False)[1]
        links = self.cm.ph.getAllItemsBeetwenMarkers(all, 'data-video="', '">', False)
        names = self.cm.ph.getAllItemsBeetwenMarkers(all, '">', '</li>', False)
        for i in names:
            if links[names.index(i)] == "":
                pass
            else:
               url = [{'url': None}]
               if "https://dood.wf" in links[names.index(i)]:
                   url = self.parserDOOD(links[names.index(i)])
               if "https://mixdrop.co" in links[names.index(i)]:
                   url = self.parserMIXDROP(links[names.index(i)])
               if "https://embedsito.com" in links[names.index(i)]:
                   url = self.parserFEMBED(links[names.index(i)])
               if "https://streamsss.net" in links[names.index(i)]:
                   url = self.parserSTREAMSB(links[names.index(i)])
               if url == []:
                   url = [{'url': None}]
               urlTab.append({'name': i, 'url': url[0]['url']})
        return urlTab
        

    def parserHLSPLAYER(self, baseUrl):
        printDBG("parserHLSPLAYER baseUrl[%r]" % baseUrl)

        url = baseUrl.split('url=')[-1]
        url = urllib.unquote(url)

        urlTab = []
        url = strwithmeta(url, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
        urlTab.extend(getDirectM3U8Playlist(url, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return urlTab

    def parserONLYSTREAMTV(self, baseUrl):
        printDBG("parserONLYSTREAMTV baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return False

        if "eval(function(p,a,c,k,e,d)" in data:
            printDBG('Host resolveUrl packed')
            packed = re.compile('>eval\(function\(p,a,c,k,e,d\)(.+?)</script>', re.DOTALL).findall(data)
            if packed:
                data2 = packed[-1]
            else:
                return ''
            printDBG('Host pack: [%s]' % data2)
            try:
                data = unpackJSPlayerParams(data2, TEAMCASTPL_decryptPlayerParams, 0, True, True)
                printDBG('OK unpack: [%s]' % data)
            except Exception:
                pass

        urlTab = self._findLinks(data, meta={'Referer': baseUrl})
        if 0 == len(urlTab):
            url = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.mp4(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
            if url != '':
                url = strwithmeta(url, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
                urlTab.append({'name': 'mp4', 'url': url})
            hlsUrl = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
            if hlsUrl != '':
                hlsUrl = strwithmeta(hlsUrl, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': baseUrl})
                urlTab.extend(getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return urlTab
        
    def parserSTARLIVEXYZ(self, baseUrl):
        printDBG("parserSTARLIVEXYZ baseUrl[%r]" % baseUrl)

        baseUrl = strwithmeta(baseUrl)
        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        HTTP_HEADER['Referer'] = baseUrl.meta.get('Referer', baseUrl)
        urlParams = {'header': HTTP_HEADER}

        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return False
        cUrl = self.cm.meta['url']
        domain = urlparser.getDomain(cUrl)

        url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
        if url.startswith('//'):
            url = 'http:' + url
        HTTP_HEADER['Referer'] = cUrl
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return False

        _url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
        if _url:
            if _url.startswith('//'):
                _url = 'http:' + _url
            HTTP_HEADER['Referer'] = url
            urlParams = {'header': HTTP_HEADER}
            sts, data = self.cm.getPage(_url, urlParams)
            if not sts:
                return False
        else:
            _url = url

        urlTab = []

        if "eval(function(p,a,c,k,e,d)" in data:
            printDBG('Host resolveUrl packed')
            scripts = re.findall(r"(eval\s?\(function\(p,a,c,k,e,d.*?)</script>", data, re.S)
            for packed in scripts:
                data2 = packed
                printDBG('Host pack: [%s]' % data2)
                try:
                    data = unpackJSPlayerParams(data2, TEAMCASTPL_decryptPlayerParams, 0, True, True)
                    printDBG('OK unpack: [%s]' % data)
                except Exception:
                    pass

                url = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.mp4(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
                if url != '':
                    url = strwithmeta(url, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': _url})
                    urlTab.append({'name': 'mp4', 'url': url})
                hlsUrl = self.cm.ph.getSearchGroups(data, '''["'](https?://[^'^"]+?\.m3u8(?:\?[^"^']+?)?)["']''', ignoreCase=True)[0]
                if hlsUrl != '':
                    hlsUrl = strwithmeta(hlsUrl, {'Origin': "https://" + urlparser.getDomain(baseUrl), 'Referer': _url})
                    urlTab.extend(getDirectM3U8Playlist(hlsUrl, checkExt=False, variantCheck=True, checkContent=True, sortWithMaxBitrate=99999999))

        return urlTab

    def parserJOKERSWIDGETORG(self, baseUrl):
        printDBG("parserJOKERSWIDGETORG baseUrl[%s]" % baseUrl)

        HTTP_HEADER = self.cm.getDefaultHeader(browser='chrome')
        referer = baseUrl.meta.get('Referer')
        if referer:
            HTTP_HEADER['Referer'] = referer
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(baseUrl, urlParams)
        if not sts:
            return []

        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<body', '>'), ('<div', '>'), False)[1]
        jscode = self.cm.ph.getAllItemsBeetwenNodes(tmp, ('<script', '>'), ('</script', '>'), False)
        jscode = '\n'.join(jscode)
        jscode = 'var document={}; document.write=function(txt){print(txt);};' + jscode
        url = self.cm.ph.getSearchGroups(tmp, '''src=['"]([^"^']+?)['"]''')[0]
        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return []
        jscode = jscode + data

        ret = js_execute(jscode)
        if ret['sts'] and 0 == ret['code']:
            tmp = ret['data'].strip()
        url = self.cm.ph.getSearchGroups(tmp, '''<iframe[^>]+?src=['"]([^"^']+?)['"]''', 1, True)[0]
        HTTP_HEADER['Referer'] = baseUrl
        urlParams = {'header': HTTP_HEADER}
        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return []

        HTTP_HEADER['Referer'] = url
        urlParams = {'header': HTTP_HEADER}
        tmp = self.cm.ph.getDataBeetwenNodes(data, ('<div', '>', 'player'), ('</iframe', '>'), False)[1]
        url = self.cm.ph.getSearchGroups(tmp, '''<iframe[^>]+?src=([^\s]+?)\s''', 1, True)[0]
        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return []

        HTTP_HEADER['Referer'] = url
        urlParams = {'header': HTTP_HEADER}
        _url = self.cm.ph.getSearchGroups(data, '''<iframe[^>]+?src=([^\s]+?)\s''', 1, True)[0]
        url = self.cm.getFullUrl(_url, url)
        sts, data = self.cm.getPage(url, urlParams)
        if not sts:
            return []

        urlTab = []
        videoUrl = self.cm.ph.getSearchGroups(data, '''source:\s?['"]([^"^']+?)['"]''')[0]
        videoUrl = strwithmeta(videoUrl, {'Referer': url})
        if videoUrl != '':
            urlTab.extend(getDirectM3U8Playlist(videoUrl, checkContent=True, sortWithMaxBitrate=999999999))

        return urlTab
