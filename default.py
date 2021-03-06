# https://docs.python.org/2.7/
import os
#import logging
import sys
import urllib
import urlparse
# http://mirrors.kodi.tv/docs/python-docs/
import xbmcaddon
import xbmcgui
import xbmcplugin
# http://docs.python-requests.org/en/latest/
import requests
# http://www.crummy.com/software/BeautifulSoup/bs4/doc/
from bs4 import BeautifulSoup
#from urllib.request import urlopen
import re
import HTMLParser


radicale_url='https://www.radioradicale.it/'
actual_page=0

def get_page(url):
    #response = urlopen(url)
    #html = response.read().decode("utf-8")
    html = requests.get(url).text
    return html

def get_chunks_file(url):
    html = get_page(url)
    #https://video.radioradicale.it/aac-1/_definst_/2016/10/18/MP857128.m4a/playlist.m3u8
    #chunklist_w448231132.m3u8
    p=re.findall('(https://video\.radioradicale\.it/aac\-1/_definst_/[0-9]{4}/[0-9]{2}/[0-9]{2}/.+\.m4a/)playlist\.m3u8',html)
    tracker_base_url=p[0]
    tracker_file_txt = get_page(tracker_base_url + 'playlist.m3u8')
    tracker=re.findall('chunklist.*\.m3u8',tracker_file_txt)
    chunks_url=tracker_base_url + tracker[0]
    return chunks_url


def parse_udienze_list_page(page_num):
    udienze_list={}
    index=1
    #page to parse
    html=get_page('https://www.radioradicale.it/archivio?raggruppamenti_radio=6&field_data_1&field_data_2&page='+str(page_num))
    #find content in page
    udienze=re.findall('<span class="date-display-single" property="dc:date" datatype="xsd:dateTime" content=".+?">(.+?)</span>    \n          <h3><a href="(/scheda/[0-9]+?/processo.+?)">(.+?)</a>',html)
    for udienza in udienze:
        url=radicale_url+udienza[1]
        udienze_list.update({index: {'title': udienza[0] + ' - ' +HTMLParser.HTMLParser().unescape(udienza[2]), 'url': url}})
        index += 1
        #date_index+=1

    return udienze_list

def build_url(query):
    base_url = sys.argv[0]
    #logging.debug('url: ' + str(query))
    return base_url + '?' + urllib.urlencode(query)
    
    
def build_udienze_list(udienze):
    udienze_list = []
    #subtitle = os.path.join(subtitle, 'subtitle.srt')
    # iterate over the contents of the dictionary udienze to build the list
    for udienza in udienze:
        # create a list item using the udienza filename for the label
        #li = xbmcgui.ListItem(label=udienze[udienza]['title'], thumbnailImage=udienze[udienza]['album_cover'])
        li = xbmcgui.ListItem(label=udienze[udienza]['title'])
        # set the fanart to the albumc cover
        #li.setProperty('fanart_image', udienze[udienza]['album_cover'])
        # set the list item to playable
        li.setProperty('IsPlayable', 'true')
        #li.setSubtitles(['special://temp/subtitle.srt'])
        #li.setProperty('upnp:subtitle:1', 'https://www.radioradicale.it/trascrizioni/8/3/2/3/7/832372.vtt')
        #li.setSubtitles(('https://www.radioradicale.it/trascrizioni/8/3/2/3/7/832372.vtt',))
        url = build_url({'mode': 'stream', 'url': udienze[udienza]['url'], 'title': udienze[udienza]['title'].encode('utf-8').strip()})
        # add the current list item to a list
        udienze_list.append((url, li, False))

    #building next page link
    next_page=actual_page+1
    showing_page=next_page+1
    li = xbmcgui.ListItem(label='Next Page ('+str(showing_page)+')')
    #logging.debug('Next Page ('+str(showing_page)+')')
    # set the fanart to the albumc cover
    #li.setProperty('fanart_image', udienze[udienza]['album_cover'])
    # set the list item to playable
    li.setProperty('IsPlayable', 'false')
    #li.setProperty('IsPlayable', 'false')
    url = build_url({'mode':'next','page_number': next_page, 'title': 'Next Page ('+str(showing_page)+')'})

    xbmcplugin.addDirectoryItems(addon_handle, udienze_list, len(udienze_list))
    xbmcplugin.addDirectoryItem(handle = addon_handle, url = url, listitem = li, isFolder = True)
    # set the content of the directory
    #xbmcplugin.setContent(addon_handle, 'songs')
    xbmcplugin.endOfDirectory(addon_handle)
    
def play_song(url):
    chunks_url=get_chunks_file(url)
    # set the path of the song to a list item
    play_item = xbmcgui.ListItem(path=chunks_url)
    # the list item is ready to be played by Kodi
    xbmcplugin.setResolvedUrl(addon_handle, True, listitem=play_item)
    #xbmc.Player().play(play_item)
    #xbmc.Player().setSubtitles('https://www.radioradicale.it/trascrizioni/8/3/2/3/7/832372.vtt')
    
def main():
    args = urlparse.parse_qs(sys.argv[2][1:])
    mode = args.get('mode', None)

    if mode is None:
        udienze_arr = parse_udienze_list_page(0)
        # display the list of songs in Kodi
        build_udienze_list(udienze_arr) 
        # a song from the list has been selected
    elif mode[0] == 'stream':
        # pass the url of the song to play_song
        play_song(args['url'][0])
    elif mode[0] == 'next':
        global actual_page
        next_page=args.get('page_number', 0)
        actual_page=int(next_page[0])
        #xbmcplugin.setContent(addon_handle, 'songs')
        udienze_arr = parse_udienze_list_page(actual_page)
        # display the list of songs in Kodi
        build_udienze_list(udienze_arr) 
        # a song from the list has been selected

    
if __name__ == '__main__':
    addon_handle = int(sys.argv[1])
    #logging.debug('ADDON_HANDLER: '+sys.argv[1]) 
    main()