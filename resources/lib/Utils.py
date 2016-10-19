#!/usr/bin/python
# -*- coding: utf-8 -*-

import xbmcplugin, xbmcgui, xbmc, xbmcaddon, xbmcvfs
import os,sys
import urllib
from traceback import format_exc
from datetime import datetime, timedelta
import _strptime
import time
import unicodedata
import xml.etree.ElementTree as xmltree
from xml.dom.minidom import parse

try:
    from multiprocessing.pool import ThreadPool as Pool
    supportsPool = True
except Exception: supportsPool = False

try:
    import simplejson as json
except Exception:
    import json

ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id').decode("utf-8")
ADDON_ICON = ADDON.getAddonInfo('icon').decode("utf-8")
ADDON_NAME = ADDON.getAddonInfo('name').decode("utf-8")
ADDON_PATH = ADDON.getAddonInfo('path').decode("utf-8")
ADDON_VERSION = ADDON.getAddonInfo('version').decode("utf-8")
ADDON_DATA_PATH = xbmc.translatePath("special://profile/addon_data/%s" % ADDON_ID).decode("utf-8")
KODI_VERSION  = int(xbmc.getInfoLabel( "System.BuildVersion" ).split(".")[0])
WINDOW = xbmcgui.Window(10000)
SETTING = ADDON.getSetting
KODILANGUAGE = xbmc.getLanguage(xbmc.ISO_639_1)
sys.path.append(xbmc.translatePath(os.path.join(ADDON_PATH, 'resources', 'lib')).decode('utf-8'))

fields_base = '"dateadded", "file", "lastplayed","plot", "title", "art", "playcount",'
fields_file = fields_base + '"streamdetails", "director", "resume", "runtime",'
fields_movies = fields_file + '"plotoutline", "sorttitle", "cast", "votes", "showlink", "top250", "trailer", "year", "country", "studio", "set", "genre", "mpaa", "setid", "rating", "tag", "tagline", "writer", "originaltitle", "imdbnumber"'
fields_tvshows = fields_base + '"sorttitle", "mpaa", "premiered", "year", "episode", "watchedepisodes", "votes", "rating", "studio", "season", "genre", "cast", "episodeguide", "tag", "originaltitle", "imdbnumber"'
fields_episodes = fields_file + '"cast", "productioncode", "rating", "votes", "episode", "showtitle", "tvshowid", "season", "firstaired", "writer", "originaltitle"'
fields_musicvideos = fields_file + '"genre", "artist", "tag", "album", "track", "studio", "year"'
fields_files = fields_file + '"plotoutline", "sorttitle", "cast", "votes", "trailer", "year", "country", "studio", "genre", "mpaa", "rating", "tagline", "writer", "originaltitle", "imdbnumber", "premiered","episode", "showtitle","firstaired","watchedepisodes","duration" '
fields_songs = '"artist","displayartist", "title", "rating", "fanart", "thumbnail", "duration", "playcount", "comment", "file", "album", "lastplayed", "genre", "musicbrainzartistid", "track"'
fields_albums = '"title", "fanart", "thumbnail", "genre", "displayartist", "artist", "genreid", "musicbrainzalbumartistid", "year", "rating", "artistid", "musicbrainzalbumid", "theme", "description", "type", "style", "playcount", "albumlabel", "mood"'
fields_pvrrecordings = '"art", "channel", "directory", "endtime", "file", "genre", "icon", "playcount", "plot", "plotoutline", "resume", "runtime", "starttime", "streamurl", "title"'
KodiArtTypes = [ ("thumb","thumb.jpg"),("poster","poster.jpg"),("fanart","fanart.jpg"),("banner","banner.jpg"),("landscape","landscape.jpg"),("clearlogo","logo.png"),("clearart","clearart.png"),("channellogo","channellogo.png"),("discart","disc.png"),("discart","cdart.png"),("extrafanart","extrafanart/"),("characterart","characterart.png"),("folder","folder.jpg") ]

def log_msg(msg, loglevel = xbmc.LOGDEBUG):
    if isinstance(msg, unicode):
        msg = msg.encode('utf-8')
    xbmc.log("Skin Helper Service --> %s" %msg, level=loglevel)
    
def log_exception(modulename, exceptiondetails):
    log_msg(format_exc(sys.exc_info()),xbmc.LOGWARNING)
    log_msg("ERROR in %s ! --> %s" %(modulename,exceptiondetails), xbmc.LOGERROR)

def getContentPath(libPath):
    if "$INFO" in libPath and not "reload=" in libPath:
        libPath = libPath.replace("$INFO[Window(Home).Property(", "")
        libPath = libPath.replace(")]", "")
        libPath = WINDOW.getProperty(libPath)
    if "activate" in libPath.lower():
        if "activatewindow(musiclibrary," in libPath.lower():
            libPath = libPath.lower().replace("activatewindow(musiclibrary," ,"musicdb://")
            libPath = libPath.replace(",return","/")
            libPath = libPath.replace(", return","/")
        else:
            libPath = libPath.lower().replace(",return","")
            libPath = libPath.lower().replace(", return","")
            if ", " in libPath:
                libPath = libPath.split(", ",1)[1]
            elif " , " in libPath:
                libPath = libPath.split(" , ",1)[1]
            elif " ," in libPath:
                libPath = libPath.split(", ",1)[1]
            elif "," in libPath:
                libPath = libPath.split(",",1)[1]

        libPath = libPath.replace(")","")
        libPath = libPath.replace("\"","")
        libPath = libPath.replace("musicdb://special://","special://")
        libPath = libPath.replace("videodb://special://","special://")
    if "&reload=" in libPath:
        libPath = libPath.split("&reload=")[0]
    return libPath

def set_kodi_json(method,params):
    json_response = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method" : "%s", "params": %s, "id":1 }' %(method, try_encode(params)))
    jsonobject = json.loads(json_response.decode('utf-8','replace'))
    return jsonobject

def get_kodi_json(method,params):
    json_response = xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method" : "%s", "params": %s, "id":1 }' %(method, try_encode(params)))
    jsonobject = json.loads(json_response.decode('utf-8','replace'))
    if(jsonobject.has_key('result')):
        jsonobject = jsonobject['result']
        if isinstance(jsonobject, list):
            return jsonobject
        if jsonobject.has_key('files'):
            return jsonobject['files']
        elif jsonobject.has_key('movies'):
            return jsonobject['movies']
        elif jsonobject.has_key('tvshows'):
            return jsonobject['tvshows']
        elif jsonobject.has_key('episodes'):
            return jsonobject['episodes']
        elif jsonobject.has_key('seasons'):
            return jsonobject['seasons']
        elif jsonobject.has_key('musicvideos'):
            return jsonobject['musicvideos']
        elif jsonobject.has_key('channels'):
            return jsonobject['channels']
        elif jsonobject.has_key('recordings'):
            return jsonobject['recordings']
        elif jsonobject.has_key('timers'):
            return jsonobject['timers']
        elif jsonobject.has_key('channeldetails'):
            return jsonobject['channeldetails']
        elif jsonobject.has_key('recordingdetails'):
            return jsonobject['recordingdetails']
        elif jsonobject.has_key('songs'):
            return jsonobject['songs']
        elif jsonobject.has_key('albums'):
            return jsonobject['albums']
        elif jsonobject.has_key('songdetails'):
            return jsonobject['songdetails']
        elif jsonobject.has_key('albumdetails'):
            return jsonobject['albumdetails']
        elif jsonobject.has_key('artistdetails'):
            return jsonobject['artistdetails']
        elif jsonobject.get('favourites'):
            return jsonobject['favourites']
        elif jsonobject.has_key('tvshowdetails'):
            return jsonobject['tvshowdetails']
        elif jsonobject.has_key('episodedetails'):
            return jsonobject['episodedetails']
        elif jsonobject.has_key('moviedetails'):
            return jsonobject['moviedetails']
        elif jsonobject.has_key('setdetails'):
            return jsonobject['setdetails']
        elif jsonobject.has_key('musicvideodetails'):
            return jsonobject['musicvideodetails']
        elif jsonobject.has_key('sets'):
            return jsonobject['sets']
        elif jsonobject.has_key('video'):
            return jsonobject['video']
        elif jsonobject.has_key('artists'):
            return jsonobject['artists']
        elif jsonobject.has_key('channelgroups'):
            return jsonobject['channelgroups']
        elif jsonobject.get('sources'):
            return jsonobject['sources']
        elif jsonobject.has_key('addons'):
            return jsonobject['addons']
        elif jsonobject.has_key('item'):
            return jsonobject['item']
        elif jsonobject.has_key('genres'):
            return jsonobject['genres']
        elif jsonobject.has_key('value'):
            return jsonobject['value']
        else:
            return {}
    else:
        log_msg("getJson - invalid result for Method %s - params: %s - response: %s" %(method,params, str(jsonobject)))
        return {}

def checkFolders():
    if not xbmcvfs.exists(SETTING("pvrthumbspath")):
        xbmcvfs.mkdirs(SETTING("pvrthumbspath"))
    if not xbmcvfs.exists("special://profile/addon_data/script.skin.helper.service/musicartcache/"):
        xbmcvfs.mkdirs("special://profile/addon_data/script.skin.helper.service/musicartcache/")
    #Remove legacy musicart cache
    if xbmcvfs.exists("special://profile/addon_data/script.skin.helper.service/musicart/"):
        recursiveDelete("special://profile/addon_data/script.skin.helper.service/musicart/")

def setAddonsettings():
    checkFolders()
    #get the addonsettings and store them in memory
    WINDOW.setProperty("SkinHelper.pvrthumbspath",SETTING("pvrthumbspath"))
    WINDOW.setProperty("SkinHelper.cacheRecordings",SETTING("cacheRecordings"))
    WINDOW.setProperty("SkinHelper.cacheGuideEntries",SETTING("cacheGuideEntries"))
    WINDOW.setProperty("SkinHelper.customRecordingsPath",SETTING("customRecordingsPath"))
    WINDOW.setProperty("SkinHelper.useTMDBLookups",SETTING("useTMDBLookups"))
    WINDOW.setProperty("SkinHelper.useGoogleLookups",SETTING("useGoogleLookups"))
    WINDOW.setProperty("SkinHelper.useYoutubeLookups",SETTING("useYoutubeLookups"))
    WINDOW.setProperty("SkinHelper.useLocalLibraryLookups",SETTING("useLocalLibraryLookups"))
    WINDOW.setProperty("SkinHelper.customlookuppath",SETTING("customlookuppath"))
    WINDOW.setProperty("SkinHelper.useFanArtTv",SETTING("useFanArtTv"))
    WINDOW.setProperty("SkinHelper.ignorechannels",SETTING("ignorechannels"))
    WINDOW.setProperty("SkinHelper.ignoretitles",SETTING("ignoretitles"))
    WINDOW.setProperty("SkinHelper.stripwords",SETTING("stripwords"))
    WINDOW.setProperty("SkinHelper.directory_structure",SETTING("directory_structure"))
    WINDOW.setProperty("SkinHelper.lastUpdate","%s" %datetime.now())
    WINDOW.setProperty("SkinHelper.enablewallbackgrounds",SETTING("enablewallbackgrounds"))
    WINDOW.setProperty("SkinHelper.enableMusicArtScraper",SETTING("enableMusicArtScraper"))
    WINDOW.setProperty("SkinHelper.downloadMusicArt",SETTING("downloadMusicArt"))
    WINDOW.setProperty("SkinHelper.enableLocalMusicArtLookup",SETTING("enableLocalMusicArtLookup"))
    WINDOW.setProperty("SkinHelper.maxNumFanArts",SETTING("maxNumFanArts"))
    WINDOW.setProperty("SkinHelper.splittitlechar",SETTING("splittitlechar"))
    WINDOW.setProperty("SkinHelper.enablePVRThumbsRecordingsOnly",SETTING("enablePVRThumbsRecordingsOnly"))
    WINDOW.setProperty("SkinHelper.preferOnlineMusicArt",SETTING("preferOnlineMusicArt"))
    WINDOW.setProperty("SkinHelper.enableWidgetsArtworkLookups",SETTING("enableWidgetsArtworkLookups"))
    WINDOW.setProperty("SkinHelper.enableSpecialsInWidgets",SETTING("enableSpecialsInWidgets"))
    WINDOW.setProperty("SkinHelper.enableWidgetsAlbumBrowse",SETTING("enableWidgetsAlbumBrowse"))
    WINDOW.setProperty("SkinHelper.skipOnlineMusicArtOnLocal",SETTING("skipOnlineMusicArtOnLocal"))
    WINDOW.setProperty("SkinHelper.musicbrainzmirror",SETTING("musicbrainzmirror"))
    if SETTING("enableCustomMusicArtLookup") == "true": WINDOW.setProperty("SkinHelper.custommusiclookuppath",SETTING("custommusiclookuppath"))
    else: WINDOW.clearProperty("SkinHelper.custommusiclookuppath")
    if SETTING("enablecontextmenu_music") == "true": WINDOW.setProperty("SkinHelper.enablecontextmenu_music","enable")
    else: WINDOW.clearProperty("SkinHelper.enablecontextmenu_music")
    if SETTING("enablecontextmenu_pvr") == "true": WINDOW.setProperty("SkinHelper.enablecontextmenu_pvr","enable")
    else: WINDOW.clearProperty("SkinHelper.enablecontextmenu_pvr")
    if SETTING("enablecontextmenu_animatedart") == "true": WINDOW.setProperty("SkinHelper.enablecontextmenu_animatedart","enable")
    else: WINDOW.clearProperty("SkinHelper.enablecontextmenu_animatedart")
    if SETTING("enablecontextmenu_series") == "true": WINDOW.setProperty("SkinHelper.enablecontextmenu_series","enable")
    else: WINDOW.clearProperty("SkinHelper.enablecontextmenu_series")

def indentXML( elem, level=0 ):
    i = "\n" + level*"\t"
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "\t"
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indentXML(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def try_encode(text, encoding="utf-8"):
    try:
        return text.encode(encoding,"ignore")
    except Exception:
        return text

def try_decode(text, encoding="utf-8"):
    try:
        return text.decode(encoding,"ignore")
    except Exception:
        return text

def createListItem(item,asTuple=True):

    try:
        liz = xbmcgui.ListItem(label=item.get("label",""),label2=item.get("label2",""))
        liz.setProperty('IsPlayable', item.get('IsPlayable','true'))
        liz.setPath(item.get('file'))

        nodetype = "Video"
        if item["type"] in ["song","album","artist"]:
            nodetype = "Music"

        #extra properties
        for key, value in item["extraproperties"].iteritems():
            liz.setProperty(key, value)

        #video infolabels
        if nodetype == "Video":
            infolabels = {
                "title": item.get("title"),
                "size": item.get("size"),
                "genre": item.get("genre"),
                "year": item.get("year"),
                "top250": item.get("top250"),
                "tracknumber": item.get("tracknumber"),
                "rating": item.get("rating"),
                "playcount": item.get("playcount"),
                "overlay": item.get("overlay"),
                "cast": item.get("cast"),
                "castandrole": item.get("castandrole"),
                "director": item.get("director"),
                "mpaa": item.get("mpaa"),
                "plot": item.get("plot"),
                "plotoutline": item.get("plotoutline"),
                "originaltitle": item.get("originaltitle"),
                "sorttitle": item.get("sorttitle"),
                "duration": item.get("duration"),
                "studio": item.get("studio"),
                "tagline": item.get("tagline"),
                "writer": item.get("writer"),
                "tvshowtitle": item.get("tvshowtitle"),
                "premiered": item.get("premiered"),
                "status": item.get("status"),
                "code": item.get("imdbnumber"),
                "aired": item.get("aired"),
                "credits": item.get("credits"),
                "album": item.get("album"),
                "artist": item.get("artist"),
                "votes": item.get("votes"),
                "trailer": item.get("trailer"),
                "progress": item.get('progresspercentage')
            }
            if "DBID" in item["extraproperties"] and item["type"] not in ["tvrecording","tvchannel","favourite"]:
                infolabels["mediatype"] = item["type"]
                infolabels["dbid"] = item["extraproperties"]["DBID"]
            if "date" in item: infolabels["date"] = item["date"]
            if "lastplayed" in item: infolabels["lastplayed"] = item["lastplayed"]
            if "dateadded" in item: infolabels["dateadded"] = item["dateadded"]
            if item["type"] == "episode":
                infolabels["season"] = item["season"]
                infolabels["episode"] = item["episode"]

            liz.setInfo( type="Video", infoLabels=infolabels)

            #streamdetails
            if item.get("streamdetails"):
                liz.addStreamInfo("video", item["streamdetails"].get("video",{}))
                liz.addStreamInfo("audio", item["streamdetails"].get("audio",{}))
                liz.addStreamInfo("subtitle", item["streamdetails"].get("subtitle",{}))

        #music infolabels
        if nodetype == "Music":
            infolabels = {
                "title": item.get("title"),
                "size": item.get("size"),
                "genre": item.get("genre"),
                "year": item.get("year"),
                "tracknumber": item.get("track"),
                "album": item.get("album"),
                "artist": " / ".join(item.get('artist')),
                "rating": str(item.get("rating",0)),
                "lyrics": item.get("lyrics"),
                "playcount": item.get("playcount")
            }
            if "date" in item: infolabels["date"] = item["date"]
            if "duration" in item: infolabels["duration"] = item["duration"]
            if "lastplayed" in item: infolabels["lastplayed"] = item["lastplayed"]
            liz.setInfo( type="Music", infoLabels=infolabels)

        #artwork
        liz.setArt( item.get("art", {}))
        if "icon" in item:
            liz.setIconImage(item['icon'])
        if "thumbnail" in item:
            liz.setThumbnailImage(item['thumbnail'])

        if asTuple:
            return (item["file"], liz, item.get("isFolder",False))
        else:
            return liz
    except Exception as e:
        log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
        log_msg("ERROR Preparing ListItem --> %s" %e, xbmc.LOGERROR)
        return None

def prepareListItem(item):
    try:
        #fix values returned from json to be used as listitem values
        properties = item.get("extraproperties",{})

        #set type
        for idvar in [ ('episode','DefaultTVShows.png'),('tvshow','DefaultTVShows.png'),('movie','DefaultMovies.png'),('song','DefaultAudio.png'),('musicvideo','DefaultMusicVideos.png'),('recording','DefaultTVShows.png'),('album','DefaultAudio.png') ]:
            if item.get(idvar[0] + "id"):
                properties["DBID"] = str(item.get(idvar[0] + "id"))
                if not item.get("type"): item["type"] = idvar[0]
                if not item.get("icon"): item["icon"] = idvar[1]
                break

        #general properties
        if item.get('genre') and isinstance(item.get('genre'), list): item["genre"] = " / ".join(item.get('genre'))
        if item.get('studio') and isinstance(item.get('studio'), list): item["studio"] = " / ".join(item.get('studio'))
        if item.get('writer') and isinstance(item.get('writer'), list): item["writer"] = " / ".join(item.get('writer'))
        if item.get('director') and isinstance(item.get('director'), list): item["director"] = " / ".join(item.get('director'))
        if not isinstance(item.get('artist'), list) and item.get('artist'): item["artist"] = [item.get('artist')]
        if not item.get('artist'): item["artist"] = []
        if item.get('type') == "album" and not item.get('album'): item['album'] = item.get('label')
        if not item.get("duration") and item.get("runtime"): item["duration"] = item.get("runtime")
        if not item.get("plot") and item.get("comment"): item["plot"] = item.get("comment")
        if not item.get("tvshowtitle") and item.get("showtitle"): item["tvshowtitle"] = item.get("showtitle")
        if not item.get("premiered") and item.get("firstaired"): item["premiered"] = item.get("firstaired")
        if not properties.get("imdbnumber") and item.get("imdbnumber"): properties["imdbnumber"] = item.get("imdbnumber")
        properties["dbtype"] = item.get("type")
        properties["type"] = item.get("type")
        properties["path"] = item.get("file")

        #cast
        listCast = []
        listCastAndRole = []
        if item.get("cast") and isinstance(item["cast"],list):
            for castmember in item["cast"]:
                if isinstance(castmember,dict):
                    listCast.append( castmember.get("name","") )
                    listCastAndRole.append( (castmember["name"], castmember["role"]) )
                else:
                    listCast.append( castmember )
                    listCastAndRole.append( (castmember, "") )

        item["cast"] = listCast
        item["castandrole"] = listCastAndRole

        if item.get("season") and item.get("episode"):
            properties["episodeno"] = "s%se%s" %(item.get("season"),item.get("episode"))
        if item.get("resume"):
            properties["resumetime"] = str(item['resume']['position'])
            properties["totaltime"] = str(item['resume']['total'])
            properties['StartOffset'] = str(item['resume']['position'])

        #streamdetails
        if item.get("streamdetails"):
            streamdetails = item["streamdetails"]
            audiostreams = streamdetails.get('audio',[])
            videostreams = streamdetails.get('video',[])
            subtitles = streamdetails.get('subtitle',[])
            if len(videostreams) > 0:
                stream = videostreams[0]
                height = stream.get("height","")
                width = stream.get("width","")
                if height and width:
                    resolution = ""
                    if width <= 720 and height <= 480: resolution = "480"
                    elif width <= 768 and height <= 576: resolution = "576"
                    elif width <= 960 and height <= 544: resolution = "540"
                    elif width <= 1280 and height <= 720: resolution = "720"
                    elif width <= 1920 and height <= 1080: resolution = "1080"
                    elif width * height >= 6000000: resolution = "4K"
                    properties["VideoResolution"] = resolution
                if stream.get("codec",""):
                    properties["VideoCodec"] = str(stream["codec"])
                if stream.get("aspect",""):
                    properties["VideoAspect"] = str(round(stream["aspect"], 2))
                item["streamdetails"]["video"] = stream

            #grab details of first audio stream
            if len(audiostreams) > 0:
                stream = audiostreams[0]
                properties["AudioCodec"] = stream.get('codec','')
                properties["AudioChannels"] = str(stream.get('channels',''))
                properties["AudioLanguage"] = stream.get('language','')
                item["streamdetails"]["audio"] = stream

            #grab details of first subtitle
            if len(subtitles) > 0:
                properties["SubtitleLanguage"] = subtitles[0].get('language','')
                item["streamdetails"]["subtitle"] = subtitles[0]
        else:
            item["streamdetails"] = {}
            item["streamdetails"]["video"] =  {'duration': item.get('duration',0)}

        #additional music properties
        if item.get('album_description'):
            properties["Album_Description"] = item.get('album_description')

        #pvr properties
        if item.get("starttime"):
            starttime = getLocalDateTimeFromUtc(item['starttime'])
            endtime = getLocalDateTimeFromUtc(item['endtime'])
            properties["StartTime"] = starttime[1]
            properties["StartDate"] = starttime[0]
            properties["EndTime"] = endtime[1]
            properties["EndDate"] = endtime[0]
            fulldate = starttime[0] + " " + starttime[1] + "-" + endtime[1]
            properties["Date"] = fulldate
            properties["StartDateTime"] = starttime[0] + " " + starttime[1]
            item["date"] = starttime[0]
            item["premiered"] = starttime[0]
        if item.get("channellogo"):
            properties["channellogo"] = item["channellogo"]
            properties["channelicon"] = item["channellogo"]
        if item.get("episodename"): properties["episodename"] = item.get("episodename","")
        if item.get("channel"): properties["channel"] = item.get("channel","")
        if item.get("channel"): properties["channelname"] = item.get("channel","")
        if item.get("channel"): item["label2"] = item.get("channel","")

        #artwork
        art = item.get("art",{})
        if item.get("type") == "episode":
            if not art.get("fanart") and art.get("season.fanart"):
                art["fanart"] = art["season.fanart"]
            if not art.get("poster") and art.get("season.poster"):
                art["poster"] = art["season.poster"]
            if not art.get("landscape") and art.get("season.landscape"):
                art["poster"] = art["season.landscape"]
            if not art.get("fanart") and art.get("tvshow.fanart"):
                art["fanart"] = art.get("tvshow.fanart")
            if not art.get("poster") and art.get("tvshow.poster"):
                art["poster"] = art.get("tvshow.poster")
            if not art.get("clearlogo") and art.get("tvshow.clearlogo"):
                art["clearlogo"] = art.get("tvshow.clearlogo")
            if not art.get("landscape") and art.get("tvshow.landscape"):
                art["landscape"] = art.get("tvshow.landscape")
        if not art.get("fanart") and item.get('fanart'): art["fanart"] = item.get('fanart')
        if not art.get("thumb") and item.get('thumbnail'): art["thumb"] = getCleanImage(item.get('thumbnail'))
        if not art.get("thumb") and art.get('poster'): art["thumb"] = getCleanImage(item.get('poster'))
        if not art.get("thumb") and item.get('icon'): art["thumb"] = getCleanImage(item.get('icon'))
        if not item.get("thumbnail") and art.get('thumb'): item["thumbnail"] = art["thumb"]

        item["extraproperties"] = properties
        
        if not "file" in item:
            log_msg("Item is missing file path ! --> %s" %item["label"], xbmc.LOGWARNING)
            item["file"] = ""
        
        #return the result
        return item

    except Exception as e:
        log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
        log_msg("ERROR Preparing ListItem --> %s" %e, xbmc.LOGERROR)
        return None

def detectPluginContent(plugin):
    #based on the properties in the listitem we try to detect the content

    #load from cache first
    cacheStr = try_encode("skinhelper-widgetcontenttype-%s" %plugin)
    contentType = WINDOW.getProperty(cacheStr).decode("utf-8")

    #no cache, we need to detect the contenttype
    if not contentType:
        #detect content based on the path
        if ("movie" in plugin.lower() or
            "box" in plugin.lower() or
            "dvd" in plugin.lower() or
            "rentals" in plugin.lower() or
            "incinemas" in plugin.lower() or
            "comingsoon" in plugin.lower() or
            "upcoming" in plugin.lower() or
            "opening" in plugin.lower() or
            "intheaters" in plugin.lower()):
                contentType = "movies"
        elif "album" in plugin.lower():
            contentType = "albums"
        elif "show" in plugin.lower():
            contentType = "tvshows"
        elif "episode" in plugin.lower():
            contentType = "episodes"
        elif "media" in plugin.lower():
            contentType = "movies"
        elif "favourites" in plugin.lower():
            contentType = "movies"
        elif "song" in plugin.lower():
            contentType = "songs"
        elif "musicvideo" in plugin.lower():
            contentType = "musicvideos"
        elif "type=dynamic" in plugin.lower():
            contentType = "movies"
        elif "videos" in plugin.lower():
            contentType = "movies"
        elif "type=both" in plugin.lower():
            contentType = "movies"

        #if we didn't get the content based on the path, we need to probe the addon...
        if not contentType and not xbmc.getCondVisibility("Window.IsMedia"): #safety check: check if no library windows are active to prevent any addons setting the view
            log_msg("detectPluginContent probing contenttype for: " + plugin)
            media_array = get_kodi_json('Files.GetDirectory','{ "directory": "%s", "media": "files", "properties": ["title", "file", "thumbnail", "episode", "showtitle", "season", "album", "artist", "imdbnumber", "firstaired", "mpaa", "trailer", "studio", "art"], "limits": {"end":1} }' %plugin)
            for item in media_array:
                if item.get("filetype","") == "directory":
                    contentType = "folder"
                    break
                elif not item.has_key("showtitle") and not item.has_key("artist"):
                    #these properties are only returned in the json response if we're looking at actual file content...
                    # if it's missing it means this is a main directory listing and no need to scan the underlying listitems.
                    contentType = "files"
                    break
                if not item.has_key("showtitle") and item.has_key("artist"):
                    ##### AUDIO ITEMS ####
                    if item["type"] == "artist":
                        contentType = "artists"
                        break
                    elif isinstance(item["artist"], list) and len(item["artist"]) > 0 and item["artist"][0] == item["title"]:
                        contentType = "artists"
                        break
                    elif item["type"] == "album" or item["album"] == item["title"]:
                        contentType = "albums"
                        break
                    elif (item["type"] == "song" and not "play_album" in item["file"]) or (item["artist"] and item["album"]):
                        contentType = "songs"
                        break
                else:
                    ##### VIDEO ITEMS ####
                    if (item["showtitle"] and not item["artist"]):
                        #this is a tvshow, episode or season...
                        if item["type"] == "season" or (item["season"] > -1 and item["episode"] == -1):
                            contentType = "seasons"
                            break
                        elif item["type"] == "episode" or item["season"] > -1 and item["episode"] > -1:
                            contentType = "episodes"
                            break
                        else:
                            contentType = "tvshows"
                            break
                    elif (item["artist"]):
                        #this is a musicvideo!
                        contentType = "musicvideos"
                        break
                    elif item["type"] == "movie" or item["imdbnumber"] or item["mpaa"] or item["trailer"] or item["studio"]:
                        contentType = "movies"
                        break

        #save to cache
        WINDOW.setProperty(cacheStr,contentType)

    #return the value
    return contentType

def getLocalDateTimeFromUtc(timestring):
    try:
        systemtime = xbmc.getInfoLabel("System.Time")
        utc = datetime.fromtimestamp(time.mktime(time.strptime(timestring, '%Y-%m-%d %H:%M:%S')))
        epoch = time.mktime(utc.timetuple())
        offset = datetime.fromtimestamp (epoch) - datetime.utcfromtimestamp(epoch)
        correcttime = utc + offset
        if "AM" in systemtime or "PM" in systemtime:
            return (correcttime.strftime("%Y-%m-%d"),correcttime.strftime("%I:%M %p"))
        else:
            return (correcttime.strftime("%d-%m-%Y"),correcttime.strftime("%H:%M"))
    except Exception as e:
        log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
        log_msg("ERROR in utils.getLocalDateTimeFromUtc ! --> %s" %e, xbmc.LOGERROR)

        return (timestring,timestring)

def double_urlencode(text):
   text = single_urlencode(text)
   text = single_urlencode(text)
   return text

def single_urlencode(text):
   blah = urllib.urlencode({'blahblahblah':try_encode(text)})
   blah = blah[13:]
   return blah

def createSmartShortcutSubmenu(windowProp,iconimage):
    try:
        if xbmcvfs.exists("special://skin/shortcuts/"):
            shortcutFile = xbmc.translatePath("special://home/addons/script.skinshortcuts/resources/shortcuts/info-window-home-property-%s-title.DATA.xml" %windowProp.replace(".","-")).decode("utf-8")
            templatefile = os.path.join(ADDON_PATH,"resources","smartshortcuts","smartshortcuts-submenu-template.xml")
            if not xbmcvfs.exists(shortcutFile):
                with open(templatefile, 'r') as f:
                    data = f.read()
                data = data.replace("WINDOWPROP",windowProp)
                data = data.replace("ICONIMAGE",iconimage)
                with open(shortcutFile, 'w') as f:
                    f.write(data)
    except Exception as e:
        log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
        log_msg("ERROR in utils.createSmartShortcutSubmenu ! --> %s" %e, xbmc.LOGERROR)

def get_current_content_type(containerprefix=""):
    contenttype = ""
    if not containerprefix:
        if xbmc.getCondVisibility("Container.Content(episodes)"):
            contenttype = "episodes"
        elif xbmc.getCondVisibility("Container.Content(movies) + !substring(Container.FolderPath,setid=)"):
            contenttype = "movies"
        elif xbmc.getCondVisibility("[Container.Content(sets) | StringCompare(Container.Folderpath,videodb://movies/sets/)] + !substring(Container.FolderPath,setid=)"):
            contenttype = "sets"
        elif xbmc.getCondVisibility("substring(Container.FolderPath,setid=)"):
            contenttype = "setmovies"
        elif xbmc.getCondVisibility("!IsEmpty(Container.Content)"):
            contenttype = xbmc.getInfoLabel("Container.Content")
        elif xbmc.getCondVisibility("Container.Content(tvshows)"):
            contenttype = "tvshows"
        elif xbmc.getCondVisibility("Container.Content(seasons)"):
            contenttype = "seasons"
        elif xbmc.getCondVisibility("Container.Content(musicvideos)"):
            contenttype = "musicvideos"
        elif xbmc.getCondVisibility("Container.Content(songs) | StringCompare(Container.FolderPath,musicdb://singles/)"):
            contenttype = "songs"
        elif xbmc.getCondVisibility("Container.Content(artists)"):
            contenttype = "artists"
        elif xbmc.getCondVisibility("Container.Content(albums)"):
            contenttype = "albums"
        elif xbmc.getCondVisibility("Window.IsActive(MyPVRChannels.xml) | Window.IsActive(MyPVRGuide.xml) | Window.IsActive(MyPVRSearch.xml) | Window.IsActive(pvrguideinfo)"):
            contenttype = "tvchannels"
        elif xbmc.getCondVisibility("Window.IsActive(MyPVRRecordings.xml) | Window.IsActive(MyPVRTimers.xml) | Window.IsActive(pvrrecordinginfo)"):
            contenttype = "tvrecordings"
        elif xbmc.getCondVisibility("Window.IsActive(programs) | Window.IsActive(addonbrowser)"):
            contenttype = "addons"
        elif xbmc.getCondVisibility("Window.IsActive(pictures)"):
            contenttype = "pictures"
        elif xbmc.getCondVisibility("Container.Content(genres)"):
            contenttype = "genres"
        elif xbmc.getCondVisibility("Container.Content(files)"):
            contenttype = "files"
    #last resort: try to determine type by the listitem properties
    if not contenttype and (containerprefix or xbmc.getCondVisibility("Window.IsActive(movieinformation)")):
        if xbmc.getCondVisibility("!IsEmpty(%sListItem.DBTYPE)" %containerprefix):
            contenttype = xbmc.getInfoLabel("%sListItem.DBTYPE" %containerprefix) + "s"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Property(DBTYPE))" %containerprefix):
            contenttype = xbmc.getInfoLabel("%sListItem.Property(DBTYPE)" %containerprefix) + "s"
        elif xbmc.getCondVisibility("SubString(%sListItem.FileNameAndPath,playrecording) | SubString(%sListItem.FileNameAndPath,tvtimer)" %(containerprefix,containerprefix)):
            contenttype = "tvrecordings"
        elif xbmc.getCondVisibility("SubString(%sListItem.FileNameAndPath,launchpvr)" %(containerprefix)):
            contenttype = "tvchannels"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,pvr://channels)" %containerprefix):
            contenttype = "tvchannels"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,flix2kodi) + SubString(%sListItem.Genre,Series)" %(containerprefix,containerprefix)):
            contenttype = "tvshows"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,flix2kodi)" %(containerprefix)):
            contenttype = "movies"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Artist) + StringCompare(%sListItem.Label,%sListItem.Artist)" %(containerprefix,containerprefix,containerprefix)):
            contenttype = "artists"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Album) + StringCompare(%sListItem.Label,%sListItem.Album)" %(containerprefix,containerprefix,containerprefix)):
            contenttype = "albums"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Artist) + !IsEmpty(%sListItem.Album)" %(containerprefix,containerprefix)):
            contenttype = "songs"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.TvShowTitle) + StringCompare(%sListItem.Title,%sListItem.TvShowTitle)" %(containerprefix,containerprefix,containerprefix)):
            contenttype = "tvshows"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Property(TotalEpisodes))" %(containerprefix)):
            contenttype = "tvshows"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.TvshowTitle) + !IsEmpty(%sListItem.Season)" %(containerprefix,containerprefix)):
            contenttype = "episodes"
        elif xbmc.getCondVisibility("IsEmpty(%sListItem.TvshowTitle) + !IsEmpty(%sListItem.Year)" %(containerprefix,containerprefix)):
            contenttype = "movies"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,movies)" %containerprefix):
            contenttype = "movies"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,shows)" %containerprefix):
            contenttype = "tvshows"
        elif xbmc.getCondVisibility("SubString(%sListItem.FolderPath,episodes)" %containerprefix):
            contenttype = "episodes"
        elif xbmc.getCondVisibility("!IsEmpty(%sListItem.Property(ChannelLogo))" %(containerprefix)):
            contenttype = "tvchannels"

    return contenttype

def getCleanImage(image):
    if image and "image://" in image:
        image = image.replace("image://","").replace("music@","")
        image=urllib.unquote(image.encode("utf-8"))
        if image.endswith("/"):
            image = image[:-1]
    return try_decode(image)

def normalize_string(text):
    text = text.replace(":", "")
    text = text.replace("/", "-")
    text = text.replace("\\", "-")
    text = text.replace("<", "")
    text = text.replace(">", "")
    text = text.replace("*", "")
    text = text.replace("?", "")
    text = text.replace('|', "")
    text = text.replace('(', "")
    text = text.replace(')', "")
    text = text.replace("\"","")
    text = text.strip()
    text = text.rstrip('.')
    text = unicodedata.normalize('NFKD', try_decode(text))
    return text

def recursiveDelete(path):
    success = True
    path = try_encode(path)
    dirs, files = xbmcvfs.listdir(path)
    for file in files:
        success = xbmcvfs.delete(os.path.join(path,file))
    for dir in dirs:
        success = recursiveDelete(os.path.join(path,dir))
    success = xbmcvfs.rmdir(path)
    return success

def addToZip(src, zf, abs_src):
    dirs, files = xbmcvfs.listdir(src)
    for file in files:
        file = file.decode("utf-8")
        log_msg("zipping " + file)
        file = xbmc.translatePath( os.path.join(src, file) ).decode("utf-8")
        absname = os.path.abspath(file)
        arcname = absname[len(abs_src) + 1:]
        try:
            #newer python can use unicode for the files in the zip
            zf.write(absname, arcname)
        except Exception:
            #older python version uses utf-8 for filenames in the zip
            zf.write(absname.encode("utf-8"), arcname.encode("utf-8"))
    for dir in dirs:
        addToZip(os.path.join(src,dir),zf,abs_src)
    return zf

def zipToFile(src, dst):
    import zipfile
    src = try_decode(src)
    dst = try_decode(dst)
    zf = zipfile.ZipFile("%s.zip" % (dst), "w", zipfile.ZIP_DEFLATED)
    abs_src = os.path.abspath(xbmc.translatePath(src).decode("utf-8"))
    zf = addToZip(src,zf,abs_src)
    zf.close()

def unzipFromFile(zip_file,path):
    import shutil
    import zipfile
    zip_file = try_decode(zip_file)
    path = try_decode(path)
    log_msg("START UNZIP of file %s  to path %s " %(zipfile,path))
    f = zipfile.ZipFile(zip_file, 'r')
    for fileinfo in f.infolist():
        filename = fileinfo.filename
        filename = try_decode(filename)
        log_msg("unzipping " + filename)
        if "\\" in filename: xbmcvfs.mkdirs(os.path.join(path,filename.rsplit("\\", 1)[0]))
        elif "/" in filename: xbmcvfs.mkdirs(os.path.join(path,filename.rsplit("/", 1)[0]))
        filename = os.path.join(path,filename)
        log_msg("unzipping " + filename, xbmc.LOGDEBUG)
        try:
            #newer python uses unicode
            outputfile = open(filename, "wb")
        except Exception:
            #older python uses utf-8
            outputfile = open(filename.encode("utf-8"), "wb")
        #use shutil to support non-ascii formatted files in the zip
        shutil.copyfileobj(f.open(fileinfo.filename), outputfile)
        outputfile.close()
    f.close()
    log_msg("UNZIP DONE of file %s  to path %s " %(zipfile,path))

def getDataFromCacheFile(file):
    data = {}
    try:
        if xbmcvfs.exists(file):
            f = xbmcvfs.File(file, 'r')
            text =  f.read().decode("utf-8")
            f.close()
            if text: data = eval(text)
    except Exception as e:
        log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
        log_msg("ERROR in utils.getDataFromCacheFile ! --> %s" %e, xbmc.LOGERROR)
    return data

def saveDataToCacheFile(file,data):
    #safety check: does the config directory exist?
    if not xbmcvfs.exists(ADDON_DATA_PATH + os.sep):
        xbmcvfs.mkdirs(ADDON_DATA_PATH)
    try:
        str_data = repr(data).encode("utf-8")
        f = xbmcvfs.File(file, 'w')
        f.write(str_data)
        f.close()
    except Exception as e:
        log_msg(format_exc(sys.exc_info()),xbmc.LOGDEBUG)
        log_msg("ERROR in utils.saveDataToCacheFile ! --> %s" %e, xbmc.LOGERROR)


    
   
def process_method_on_list(method_to_run,items):
    '''helper method that processes a method on each listitem with pooling if the system supports it'''
    all_items = []
    if supportsPool:
        pool = Pool()
        try:
            all_items = pool.map(method_to_run, items)
        except Exception:
            #catch exception to prevent threadpool running forever
            log_msg(format_exc(sys.exc_info()))
            log_msg("Error in %s" %method_to_run)
        pool.close()
        pool.join()
    else:
        all_items = [method_to_run(item) for item in items]
    all_items = filter(None, all_items)
    return all_items
