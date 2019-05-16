# -*- coding: utf-8 -*-
#
#      Copyright (C) 2016 Yong Sik Moon
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

from jva_base import *
import sys
import os
import urllib2
import urllib
import requests

import buggalo
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

reload(sys)
sys.setdefaultencoding('utf-8')


class JooVideoAddon(JVABase):

    def __init__(self):
        JVABase.__init__(self)

    def __del__(self):
        JVABase.__del__(self)

    def translation(self, text_id):
        return ADDON.getLocalizedString(text_id).encode('utf-8')

    def showCategories(self):
        data = self.getResponse(self.JOOVIDEO_LANDING_URL)
        soup = BeautifulSoup(data, self.HTML_PARSER)

        categories = self.getCategoryTables(soup)

        for category in categories:
            # 주의 : DOM은 규격상 table내에 강제로 tbody를 포함시킨다. 따라서 서버가 보낸 실제 스트림을 확인해야 한다.
            cat_name = category.tr.td.string.strip(' \t\n\r')

            # Create ListItems
            item_title = cat_name
            item = xbmcgui.ListItem(item_title, iconImage=ICON)
            item.setInfo(
                type='video',
                infoLabels={
                    'title': item_title,
                    'studio': ADDON.getAddonInfo('name')
                }
            )
            item.setProperty('Fanart_Image', FANART)
            item.setProperty('IsPlayable', 'false')  # IMPORTANT : mandatory, if not, HANDLE not to be valid

            # plugin://plugin.video.joovideo/?para1=val1&para2=val2...
            _url = PLUGIN_PATH + '?' + 'mode=category' + ('&url=%s' % self.cat_kor_to_eng[cat_name])

            xbmcplugin.addDirectoryItem(HANDLE, _url, item, True)  # Folder

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategoryListItems(self, cat_name):
        data = self.getResponse(self.JOOVIDEO_LANDING_URL)
        soup = BeautifulSoup(data, self.HTML_PARSER)

        categories = self.getCategoryTables(soup)

        for category in categories:
            # 주의 : DOM은 규격상 table내에 강제로 tbody를 포함시킨다. 따라서 서버가 보낸 실제 스트림을 확인해야 한다.
            if self.cat_eng_to_kor[cat_name] != unicode(category.tr.td.string.strip(' \t\n\r')):
                continue

            row_items = category.find_all('a', attrs={'href': re.compile(self.VIEWMEDIA_URL_PATN, re.I)})
            for row_item in row_items:
                content_title = ''
                content_date = ''
                content_internal_url = row_item['href']  # with hostname or no hostname

                for sibling in row_item.next_siblings:
                    if sibling.name == 'span':
                        content_date = sibling.string
                    elif sibling.name == 'img':
                        if sibling['src'] == 'images/hot.gif':
                            content_title += '[Hot] '
                        elif sibling['src'] == 'images/new.gif':
                            content_title += '[New] '

                content_title += row_item.string

                # Create ListItems
                item_title = content_title + ' - ' + content_date

                item = xbmcgui.ListItem(item_title, iconImage=ICON)
                item.setInfo(
                    type='video',
                    infoLabels={
                        'title': content_title,
                        'studio': ADDON.getAddonInfo('name')
                    }
                )
                item.setProperty('Fanart_Image', FANART)
                item.setProperty('IsPlayable', 'false')  # IMPORTANT : mandatory, if not, HANDLE not to be valid

                content_hostname = self.getContentHostname(content_internal_url)

                # plugin://plugin.video.joovideo/?Num=xxxxxxxxx&play=1
                m = re.search('[Nn]um=\d+', content_internal_url)  # m.group() looks like 'Num=1234567890'
                _url = PLUGIN_PATH + '?' + m.group() + '&mode=partialclips' + '&content_hostname=' + content_hostname

                xbmcplugin.addDirectoryItem(HANDLE, _url, item, True)  # Folder

        xbmcplugin.endOfDirectory(HANDLE)

    def showPartialClips(self, jv_media_no):
        dm_embed_urls = self.getEmbedVideoUrls(self.getJooVideoInternalUrl('Num=' + jv_media_no))

        # xbmc.log('JOOVIDEO::showPartialClips - dm_embed_urls is %s' % dm_embed_urls, xbmc.LOGDEBUG)

        for dm_embed_url in dm_embed_urls:
            # Create ListItems
            item_title = dm_embed_url['title']
            file_info = dm_embed_url['file_info']['result'][dm_embed_url['dm_video_id']] if dm_embed_url['file_info'] else ""
            file_size = self.toMegabytes(file_info['size']) if dm_embed_url['file_info'] else ""
            video_resolution = self.getVideoResolutionFromVStreamFilename(file_info['name'] if dm_embed_url['file_info'] else None)

            title_template = "{0}, {1}MBytes [{2}]"
            title = title_template.format(item_title, file_size, video_resolution)

            item = xbmcgui.ListItem(title, iconImage=ICON)
            item.setInfo(
                type='video',
                infoLabels={
                    'title': title,
                    'studio': ADDON.getAddonInfo('name')
                }
            )
            item.setProperty('Fanart_Image', FANART)
            item.setProperty('IsPlayable', 'true')  # IMPORTANT : mandatory, if not, HANDLE not to be valid

            _url = PLUGIN_PATH + '?' + ('url=%s' % urllib.quote_plus(dm_embed_url['dm_video_id'])) + '&mode=play'

            xbmcplugin.addDirectoryItem(HANDLE, _url, item, False)  # File

        xbmcplugin.endOfDirectory(HANDLE)

    def getVStreamStreamUrl(self, vid):
        """

        :param vid: verystream video id
        :return:
        """
        try:
            vstream_prefix = unicode("https://verystream.com/gettoken/")
            vstream_postfix = unicode("?mime=true")
            content = self.getResponse(self.VSTREAM_EMBED_URL_TEMPLATE.format(vid))
            # print("""{0}""".format(content))
            item_soup = BeautifulSoup(content, self.HTML_PARSER)
            row_item = item_soup.find('p', attrs={'id': re.compile('videolink', re.I)})
            if row_item is not None:
                vstream_video_src_url = row_item.string
                stream_url = vstream_prefix + vstream_video_src_url + vstream_postfix
                r = requests.get(stream_url, stream=True)
                return r.url

            return ''

        except urllib2.HTTPError as e:
            xbmc.executebuiltin('XBMC.Notification(Info:, [Exception] {0}!,10000)'.format(e.message))
        except urllib2.URLError as e:
            xbmc.executebuiltin('XBMC.Notification(Info:, [Exception] {0}!,10000)'.format(e.message))
        except ValueError as e:
            xbmc.executebuiltin('XBMC.Notification(Info:, [Exception] {0}!,10000)'.format(e.message))
        except IndexError as e:
            xbmc.executebuiltin('XBMC.Notification(Info:, [Exception] {0}!,10000)'.format(e.message))
        except requests.ConnectionError as e:
            xbmc.executebuiltin('XBMC.Notification(Info:, [Exception] {0}!,10000)'.format(e.message))

    def getStreamUrl(self, vid):
        return self.getVStreamStreamUrl(vid)

    def playVideo(self, vid):
        dm_stream_url = self.getStreamUrl(vid)
        item = xbmcgui.ListItem(path=dm_stream_url)
        item.setContentLookup(False)
        xbmcplugin.setResolvedUrl(HANDLE, True, item)


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


if __name__ == '__main__':
    ADDON = xbmcaddon.Addon()
    PLUGIN_PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    FANART = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    # dialog = xbmcgui.Dialog()
    # dialog.ok(ADDON.getAddonInfo('name'), sys.argv[0], sys.argv[1], sys.argv[2])

    params = parameters_string_to_dict(sys.argv[2])
    jv_media_num = urllib.unquote_plus(params.get('Num', ''))
    mode = urllib.unquote_plus(params.get('mode', ''))
    url_ = urllib.unquote_plus(params.get('url', ''))

    try:
        jva = JooVideoAddon()
        if mode == 'play':
            jva.playVideo(url_)  # 4
        elif mode == 'partialclips':
            jva.setContentHostname(urllib.unquote_plus(params.get('content_hostname', '')))
            jva.showPartialClips(jv_media_num)  # 3
        elif mode == 'category':
            jva.showCategoryListItems(cat_name=url_)  # 2
        else:
            jva.showCategories()  # 1
    except Exception as e:
        xbmc.log('JOOVIDEO - Exception is %s' % e.message, xbmc.LOGDEBUG)
        buggalo.onExceptionRaised()
