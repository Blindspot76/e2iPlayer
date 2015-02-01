# -*- coding: utf-8 -*-
#
#  IPTV download manager List UI
#
#  $Id$
#
# 
###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.iptvdm.iptvdh import DMHelper
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, formatBytes, GetIPTVDMImgDir
from Plugins.Extensions.IPTVPlayer.components.iptvlist import IPTVListComponentBase
from Plugins.Extensions.IPTVPlayer.components.iptvplayerinit import TranslateTXT as _
###################################################

###################################################
# FOREIGN import
###################################################
from enigma import eListboxPythonMultiContent, eListbox, gFont, RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_VALIGN_CENTER
from Tools.LoadPixmap import LoadPixmap
###################################################

class IPTVDownloadManagerList(IPTVListComponentBase):

    def __init__(self):
        IPTVListComponentBase.__init__(self)
    
        self.l.setFont(2, gFont("Regular", 20))
        self.l.setFont(1, gFont("Regular", 26))
        self.l.setFont(0, gFont("Regular", 16))
        self.l.setItemHeight(115)
        
        self.waitingPIX = None
        self.downloadingPIX = None
        self.downloadedPIX = None
        self.errorPIX = None
        self.interruptedPIX = None

    def onCreate(self):
        try:
            self.waitingPIX     = LoadPixmap(cached=True, path=GetIPTVDMImgDir('iconwait1.png'))
            self.downloadingPIX = LoadPixmap(cached=True, path=GetIPTVDMImgDir('iconwait2.png'))
            self.downloadedPIX  = LoadPixmap(cached=True, path=GetIPTVDMImgDir('icondone.png'))
            self.errorPIX       = LoadPixmap(cached=True, path=GetIPTVDMImgDir('iconerror.png'))
            self.interruptedPIX = LoadPixmap(cached=True, path=GetIPTVDMImgDir('iconwarning.png'))
        except:
            printExc()
        
    def onDestroy(self):
        try:
            self.waitingPIX = None
            self.downloadingPIX = None
            self.downloadedPIX = None
            self.errorPIX = None
            self.interruptedPIX = None
        except:
            printExc()
            
    def buildEntry(self, item):
        width = self.l.getItemSize().width()
        res = [ None ]
        
        if item.fileSize > 0:
            strFileSize = formatBytes(item.fileSize)
        else:
            strFileSize = '??'
        strDownloadedSize = formatBytes(item.downloadedSize)
        if item.downloadedProcent >= 0:
            strDownloadedProcent = str(item.downloadedProcent) + "%"
        else:
            strDownloadedProcent = '??%'
        strDownloadedSpeed = formatBytes(item.downloadedSpeed) + "/s"
        
        info1 = strDownloadedSize + "/" + strFileSize + ", " + strDownloadedProcent
        info2 = info1 + ", " + strDownloadedSpeed

        status = ""
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 70, 3, width-70, 40, 2, RT_HALIGN_LEFT|RT_VALIGN_CENTER, item.fileName))
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 70, 45, width-70, 20, 0, RT_HALIGN_LEFT|RT_VALIGN_CENTER, item.url))
        
        info = ""
        if DMHelper.STS.WAITING == item.status:
            res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, 1, 64, 64, self.waitingPIX))
            status += _("PENDING")
        elif DMHelper.STS.DOWNLOADING == item.status:
            res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, 1, 64, 64, self.downloadingPIX))
            status += _("DOWNLOADING")
            info = info2
        elif DMHelper.STS.DOWNLOADED == item.status:
            res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, 1, 64, 64, self.downloadedPIX))
            status += _("DOWNLOADED")
            info = info1
        elif DMHelper.STS.INTERRUPTED == item.status:
            res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, 1, 64, 64, self.interruptedPIX))
            status += _("ABORTED")
            info = info1
        elif DMHelper.STS.ERROR == item.status:
            res.append((eListboxPythonMultiContent.TYPE_PIXMAP_ALPHABLEND, 3, 1, 64, 64, self.downloadedPIX))
            status += _("DOWNLOAD ERROR")
            
        res.append((eListboxPythonMultiContent.TYPE_TEXT, width - 240, 67, 240, 40, 1, RT_HALIGN_RIGHT|RT_VALIGN_CENTER, status))
        res.append((eListboxPythonMultiContent.TYPE_TEXT, 45, 67, width - 45 - 240, 40, 1, RT_HALIGN_LEFT|RT_VALIGN_CENTER, info))
         
        return res
 
