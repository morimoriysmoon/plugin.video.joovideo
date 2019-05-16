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
import urllib2
import requests

reload(sys)
sys.setdefaultencoding('utf-8')


class JooVideoAddonPseudo(JVABase):

    def __init__(self):
        JVABase.__init__(self)
        self.faulty_items = list()
        self.entire_items_no = 0

    def __del__(self):
        JVABase.__del__(self)

    def translation(self, text_id):
        return ''  # ADDON.getLocalizedString(id).encode('utf-8')

    def showCategories(self):
        data = self.getResponse(self.JOOVIDEO_LANDING_URL)
        soup = BeautifulSoup(data, self.HTML_PARSER)

        categories = self.getCategoryTables(soup)

        for category in categories:
            # 주의 : DOM은 규격상 table내에 강제로 tbody를 포함시킨다. 따라서 서버가 보낸 실제 스트림을 확인해야 한다.
            cat_name = category.tr.td.string.strip(' \t\n\r')
            print cat_name

    def showCategoryListItems(self, cat_name):
        data = self.getResponse(self.JOOVIDEO_LANDING_URL)
        soup = BeautifulSoup(data, self.HTML_PARSER)

        categories = self.getCategoryTables(soup)

        error_count = 0
        for category in categories:
            # 주의 : DOM은 규격상 table내에 강제로 tbody를 포함시킨다. 따라서 서버가 보낸 실제 스트림을 확인해야 한다.
            if unicode(cat_name) != unicode(category.tr.td.string.strip(' \t\n\r')):
                continue

            row_items = category.find_all('a', attrs={'href': re.compile(self.VIEWMEDIA_URL_PATN, re.I)})
            for row_item in row_items:
                content_title = ''
                content_date = ''
                content_internal_url = row_item['href']  # with hostname or no hostname

                self.JOOVIDEO_INTERNAL_CONTENT_HOSTNAME = self.getContentHostname(content_internal_url)

                for sibling in row_item.next_siblings:
                    if sibling.name == 'span':
                        content_date = sibling.string
                    elif sibling.name == 'img':
                        if sibling['src'] == 'images/hot.gif':
                            content_title += '[Hot] '
                        elif sibling['src'] == 'images/new.gif':
                            content_title += '[New] '

                content_title += row_item.string

                self.printSeparation()
                _category_name_ = category.tr.td.string.strip(' \t\n\r')
                print u'Category : [{0}]'.format(_category_name_)
                _jv_url_ = u'JvUrl : {0} {1} --> {2}'.format(content_title, content_date, content_internal_url)
                print _jv_url_

                m = re.search('[Nn]um=\d+', row_item['href'])  # m.group() looks like 'Num=1234567890'

                dm_emb_urls = self.getEmbedVideoUrls(self.getJooVideoInternalUrl(m.group()))

                if len(dm_emb_urls) is 2:
                    if dm_emb_urls[0]['title'] is dm_emb_urls[1]['title']:
                        error_count += 1

                for item in dm_emb_urls:
                    try:
                        dm_stream_url = self.getStreamUrl(item)

                        file_info = item['file_info']['result'][item['dm_video_id']] if item['file_info'] else ""
                        file_size = self.toMegabytes(file_info['size']) if item['file_info'] else ""
                        video_resolution = self.getVideoResolutionFromVStreamFilename(file_info['name'])

                        _embed_url_ = u'{0} : {1} : {2}, {3}MBytes [{4}]'.format(
                            item['title'],
                            item['dm_emb_url'],
                            item['dm_video_id'],
                            file_size,
                            video_resolution
                        )
                        print u'EmbedUrl : {0}'.format(_embed_url_)
                        print u'streamUrl : {0}'.format(dm_stream_url)
                    except UnicodeEncodeError as e:
                        print 'UnicodeEncodeError: {0}'.format(e.message)
                        continue

                    self.entire_items_no += 1

                    if not self.checkValidUrl(dm_stream_url):
                        faulty_item = dict()
                        faulty_item['Category'] = _category_name_
                        faulty_item['EmbedUrl'] = _embed_url_
                        faulty_item['Reason'] = dm_stream_url  # error message
                        self.faulty_items.append(faulty_item)

        if error_count > 0:
            print '[NG] error(%d) found on getting partial clips'.format(error_count)
        else:
            print '[OK] no error found'

    def getDMStreamUrl(self, url_info):

        """
        
        :param url_info: list()
        {'title': title, 'dm_emb_url': dm_embed_url, 'stream_provider': provider, 'dm_video_id': dm_video_id}
        :return: 
        """
        try:
            headers = {'User-Agent': 'Android'}
            cookie = {'lang': 'en', 'ff': 'off'}
            r = requests.get(
                "https://www.dailymotion.com/player/metadata/video/" + url_info['dm_video_id'],
                headers=headers,
                cookies=cookie
            )

            context_json = r.json()

            if context_json.get('error') is not None:
                err_title = context_json['error']['title']
                err_message = context_json['error']['message']
                return '[{0}] {1}'.format(err_title, err_message)
            else:
                try:
                    cc = context_json['qualities']  # ['380'][1]['url']
                    if '480' in cc.keys():
                        return cc['480'][1]['url']
                    elif '720' in cc.keys():
                        return cc['720'][1]['url']
                    elif '380' in cc.keys():
                        return cc['380'][1]['url']
                    elif '1080' in cc.keys():
                        return cc['1080'][1]['url']
                    elif '240' in cc.keys():
                        return cc['240'][1]['url']
                    elif '144' in cc.keys():
                        return cc['140'][1]['url']
                    # elif 'auto' in cc.keys():
                    #    return cc['auto'][1]['url']
                    else:
                        return "[ResolutionNotFound] url_not_found"
                except Exception as e:
                    return "[Exception] url_not_found"

        except urllib2.HTTPError as e:
            return "[Exception] {0}".format(e.message)
        except urllib2.URLError as e:
            return "[Exception] {0}".format(e.message)
        except ValueError as e:
            return "[Exception] {0}".format(e.message)
        except IndexError as e:
            return "[Exception] {0}".format(e.message)
        except requests.ConnectionError as e:
            return "[Exception] {0}".format(e.message)
        except TypeError as e:
            return "[Exception] {0}".format(e.message)

    def getOloadStreamUrl(self, oload_embed_url):
        """

        :param dm_embed_url: url 
        :return: 
        """
        try:
            oload_prefix = unicode("https://openload.co/stream/")
            oload_postfix = unicode("?mime=true")
            content = self.getResponse2(oload_embed_url)
            print("""{0}""".format(content))
            item_soup = BeautifulSoup(content, self.HTML_PARSER)
            row_item = item_soup.find('span', attrs={'id': re.compile('streamurl', re.I)})
            if row_item is not None:
                oload_video_src_url = row_item.string
                return oload_prefix + oload_video_src_url + oload_postfix
            return ''

        except urllib2.HTTPError as e:
            return "[Exception] {0}".format(e.message)
        except urllib2.URLError as e:
            return "[Exception] {0}".format(e.message)
        except ValueError as e:
            return "[Exception] {0}".format(e.message)
        except IndexError as e:
            return "[Exception] {0}".format(e.message)
        except requests.ConnectionError as e:
            return "[Exception] {0}".format(e.message)

    def getVStreamStreamUrl(self, vstream_embed_url):
        """

        :param vstream_embed_url: url
        :return:
        """
        try:
            vstream_prefix = unicode("https://verystream.com/gettoken/")
            vstream_postfix = unicode("?mime=true")
            content = self.getResponse(vstream_embed_url)
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
            return "[Exception] {0}".format(e.message)
        except urllib2.URLError as e:
            return "[Exception] {0}".format(e.message)
        except ValueError as e:
            return "[Exception] {0}".format(e.message)
        except IndexError as e:
            return "[Exception] {0}".format(e.message)
        except requests.ConnectionError as e:
            return "[Exception] {0}".format(e.message)

    def getStreamUrl(self, url_info):
        """
        
        :param url_info:
            {
            'title':, 
            'dm_emb_url':, 
            'stream_provider':
            }
        :return: 
        """
        if url_info['stream_provider'] == unicode('델리모션'):
            return self.getDMStreamUrl(url_info)
        elif url_info['stream_provider'] == unicode('Oload'):
            return self.getOloadStreamUrl(url_info['dm_emb_url'])
        elif url_info['stream_provider'] == unicode('VStream'):
            return self.getVStreamStreamUrl(url_info['dm_emb_url'])
        else:
            return 'NOT IMPLEMENTED'

    def printFaultyItems(self):
        self.printSeparation()
        ratio = float(len(self.faulty_items)) / float(self.entire_items_no) * float(100)
        print 'Faulty items list'
        print 'Ratio [{0}] % = Faulty[{1}] / Total[{2}]'.format(ratio, len(self.faulty_items), self.entire_items_no)
        self.printSeparation()

        for item in self.faulty_items:
            print u'[{0}] {1}'.format(item['Category'], item['EmbedUrl'])
            print u'\t[Reason] {0}'.format(item['Reason'])

        self.printSeparation()

    def printSeparation(self):
        def getDivider():
            line = ''
            for i in range(1, 20):
                line += '==========='
            return line

        print getDivider()


if __name__ == '__main__':

    jvaPseudo = JooVideoAddonPseudo()
    jvaPseudo.showCategories()
    jvaPseudo.showCategoryListItems('드라마')
    jvaPseudo.showCategoryListItems('오락')
    jvaPseudo.showCategoryListItems('다큐')
    jvaPseudo.showCategoryListItems('시사')
    jvaPseudo.showCategoryListItems('뉴스,스포츠')
    jvaPseudo.printFaultyItems()

    del jvaPseudo
