###################################################
# LOCAL import
###################################################
from Plugins.Extensions.IPTVPlayer.tools.iptvtools import printDBG, printExc, GetSubtitlesDir, byteify

# INFO about subtitles format
# https://wiki.videolan.org/Subtitles#Subtitles_support_in_VLC

#def printDBG(data):
#    print "%s" % data

###################################################

###################################################
# FOREIGN import
###################################################
import re
import codecs
import time
try:    import json
except: import simplejson as json
from os import remove as os_remove
###################################################

class IPTVSubtitlesHandler:
    def __init__(self):
        printDBG("OpenSubOrg.__init__")
        self.subAtoms = [] 
        self.pailsOfAtoms = {}
        self.CAPACITY = 10 * 1000 # 10s
        
    def _srtClearText(self, text):
        return re.sub('<[^>]*>', '', text)
        #<b></b> : bold
        #<i></i> : italic
        #<u></u> : underline
        #<font color=”#rrggbb”></font>
        
    def _srtTc2ms2(self, tc):
        sign    = 1
        if tc[0] in "+-":
            sign    = -1 if tc[0] == "-" else 1
            tc  = tc[1:]

        match   = self.TIMECODE_RE.match(tc)
        hh,mm,ss,ms = map(lambda x: 0 if x==None else int(x), match.groups())
        return ((hh*3600 + mm*60 + ss) * 1000 + ms) * sign
            
    def _srtTc2ms(self, time):
        if ',' in time:
            split_time = time.split(',')
        else:
            split_time = time.split('.')
        minor = split_time[1]
        major = split_time[0].split(':')
        return (int(major[0])*3600 + int(major[1])*60 + int(major[2])) * 1000 + int(minor)

    def _srtToAtoms(self, srtText):
        subAtoms = []
        srtText = srtText.replace('\r\n', '\n').split('\n\n')
        
        line = 0
        for idx in range(len(srtText)):
            line += 1
            st = srtText[idx].split('\n')
            #printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            #printDBG(st)
            #printDBG("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            if len(st)>=2:
                try:
                    try:
                        tmp = int(st[0])
                        i = 1
                    except:
                        if '' == st[0]: i = 1
                        else: i = 0
                    split = st[i].split(' --> ')
                    subAtoms.append( { 'start':self._srtTc2ms(split[0].strip()), 'end':self._srtTc2ms(split[1].strip()), 'text':self._srtClearText('\n'.join(j for j in st[i+1:len(st)])) } )
                except:
                    printExc("Line number [%d]" % line)
        return subAtoms
        
    def _mplClearText(self, text):
        text = text.split('|')
        for idx in range( len(text) ):
            if text[idx].startswith('/'):
                text[idx] = text[idx][1:]
        return re.sub('\{[^}]*\}', '', '\n'.join(text))
        
    def _mplTc2ms(self, time):
        return int(time) * 100
        
    def _mplToAtoms(self, mplData):
        # Timings          : Sequential Time
        # Timing Precision : 100 Milliseconds (1/10th sec)
        subAtoms = []
        mplData = mplData.replace('\r\n', '\n').split('\n')
        reObj = re.compile('^\[([0-9]+?)\]\[([0-9]+?)\](.+?)$')
        
        for s in mplData:
            tmp = reObj.search(s)
            if None != tmp:
                subAtoms.append( { 'start':self._mplTc2ms(tmp.group(1)), 'end':self._mplTc2ms(tmp.group(2)), 'text':self._mplClearText( tmp.group(3) ) } )
        return subAtoms
    
    #def _preparPails(self, scope):
        
    '''                      
    def getSubtitles(self, currTimeMS):
        printDBG("OpenSubOrg.getSubtitles [%s]" % currTimeMS)
        time1 = time.time()
        subsText = []
        for item in self.subAtoms:
            if currTimeMS >= item['start'] and currTimeMS < item['end']:
                subsText.append(item['text'])
        ret = '\n'.join(subsText)
        time2 = time.time()
        printDBG('>>>>>>>>>>getSubtitles function took %0.3f ms' % ((time2-time1)*1000.0))
        return ret
    '''
    
    def getSubtitles(self, currTimeMS, prevMarker):
        #printDBG("OpenSubOrg.getSubtitles [%s]" % currTimeMS)
        #time1 = time.time()
        subsText = []
        tmp = currTimeMS / self.CAPACITY
        tmp = self.pailsOfAtoms.get(tmp, [])
        
        ret    = None
        validAtomsIdexes = []
        for idx in tmp:
            item = self.subAtoms[idx]
            if currTimeMS >= item['start'] and currTimeMS < item['end']:
                validAtomsIdexes.append(idx)
                
        marker = validAtomsIdexes
        #printDBG("OpenSubOrg.getSubtitles marker[%s] prevMarker[%s] %.1fs" % (marker, prevMarker, currTimeMS/1000.0))
        if prevMarker != marker:
            for idx in validAtomsIdexes:
                item = self.subAtoms[idx]
                subsText.append(item['text'])
            ret = '\n'.join(subsText)
        #time2 = time.time()
        #printDBG('>>>>>>>>>>getSubtitles function took %0.3f ms' % ((time2-time1)*1000.0))
        return marker, ret
        
    def removeCacheFile(self, filePath):
        cacheFile = self._getCacheFileName(filePath)
        try:
            os_remove(cacheFile)
        except:
            printExc()
            
    def _getCacheFileName(self, filePath):
        tmp = filePath.split('/')[-1]
        return GetSubtitlesDir(tmp+'.iptv')
        
    def _loadFromCache(self, orgFilePath, encoding='utf-8'):
        printDBG("OpenSubOrg._loadFromCache")
        sts = False
        try:
            filePath = self._getCacheFileName(orgFilePath)
            try:
                with codecs.open(filePath, 'r', encoding, 'replace') as fp:
                    self.subAtoms = byteify( json.loads(fp.read()) )
                if len(self.subAtoms):
                    sts = True
                    printDBG("IPTVSubtitlesHandler._loadFromCache orgFilePath[%s] --> cacheFile[%s]" % (orgFilePath, filePath))
            except:
                printExc()
        except:
            printExc()
        return sts
        
    def _saveToCache(self, orgFilePath, encoding='utf-8'):
        printDBG("OpenSubOrg._saveToCache")
        try:
            filePath = self._getCacheFileName(orgFilePath)
            with codecs.open(filePath, 'w', encoding) as fp:
                fp.write(json.dumps(self.subAtoms))
            printDBG("IPTVSubtitlesHandler._saveToCache orgFilePath[%s] --> cacheFile[%s]" % (orgFilePath, filePath))
        except: 
            printExc()
    
    def loadSubtitles(self, filePath, encoding='utf-8'):
        printDBG("OpenSubOrg.loadSubtitles filePath[%s]" % filePath)
        saveCache = True
        self.subAtoms = []
        #time1 = time.time()
        sts = self._loadFromCache(filePath)
        if not sts:
            try:
                with codecs.open(filePath, 'r', encoding, 'replace') as fp:
                    subText = fp.read().encode('utf-8')
                    if filePath.endswith('.srt'):
                        self.subAtoms = self._srtToAtoms(subText)
                        sts = True
                    elif filePath.endswith('.mpl'):
                        self.subAtoms = self._mplToAtoms(subText)
                        sts = True
            except:
                printExc()
        else:
            saveCache = False

        self.pailsOfAtoms = {}
        for idx in range(len(self.subAtoms)):
            tmp = self.subAtoms[idx]['start'] / self.CAPACITY
            if tmp not in self.pailsOfAtoms:
                self.pailsOfAtoms[tmp] = [idx]
            elif idx not in self.pailsOfAtoms[tmp]:
                self.pailsOfAtoms[tmp].append( idx )
            
            tmp = self.subAtoms[idx]['end'] / self.CAPACITY
            if tmp not in self.pailsOfAtoms:
                self.pailsOfAtoms[tmp] = [idx]
            elif idx not in self.pailsOfAtoms[tmp]:
                self.pailsOfAtoms[tmp].append( idx )
        
        if saveCache and len(self.subAtoms):
            self._saveToCache(filePath)
            
        #time2 = time.time()
        #printDBG('>>>>>>>>>>loadSubtitles function took %0.3f ms' % ((time2-time1)*1000.0))

        return sts
        
if __name__ == "__main__":
    obj = IPTVSubtitlesHandler()
    obj.loadSubtitles('/hdd/_Back.To.The.Future[1985]DvDrip-aXXo.pl.srt')
    obj.getSubtitles(10000)
