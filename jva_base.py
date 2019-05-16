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

import sys
import re
import urlparse
from bs4 import BeautifulSoup
import requests

reload(sys)
sys.setdefaultencoding('utf-8')


class JVABase:
    # need a proper header information to make web-server recognize
    # user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:47.0) Gecko/20100101 Firefox/47.0'  # Firefox
    user_agent = 'Android'
    headers = {
        'Host': 'joovideo.net',
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }

    headers2 = [
        ('Host', 'joovideo.net'),
        ('User-Agent', user_agent),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Accept-Language', 'ko-kr,ko;q=0.8,en-us;q=0.5,en;q=0.3'),
        ('Accept-Encoding', 'gzip, deflate'),
        ('Connection', 'keep-alive')
    ]

    header3 = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Connection': 'keep-alive'
    }

    cat_kor_to_eng = {
        unicode('드라마'): 'drama',
        unicode('오락'): 'entertainment',
        unicode('다큐'): 'docu',
        unicode('시사'): 'sisa',
        unicode('뉴스,스포츠'): 'news_sports'
    }

    cat_eng_to_kor = {
        'drama': unicode('드라마'),
        'entertainment': unicode('오락'),
        'docu': unicode('다큐'),
        'sisa': unicode('시사'),
        'news_sports': unicode('뉴스,스포츠')
    }

    JOOVIDEO_LANDING_URL = "http://joovideo.net"
    # JOOVIDEO_LANDING_URL = "http://krtune.net"

    ENTRY_FILENAME = "ViewLink"

    VIEWMEDIA_URL_PATN = "{0}\.aspx\?num=".format(ENTRY_FILENAME)
    DAILYMOTION_URL_PATN = "http://www\.dailymotion\.com/embed/video/*\?*"

    JOOVIDEO_EPISODENUM_PATN = "ctl00_ContentPlaceHolder1_{0}1_lblEpisodeNum".format(ENTRY_FILENAME)
    JOOVIDEO_SEQUEL_PATN = "ctl00_ContentPlaceHolder1_{0}1_GridView1_ctl[0-9]+_linkBtnHost".format(ENTRY_FILENAME)
    EVT_TARGET_PATN = 'ctl00\$ContentPlaceHolder1\${0}1\$GridView1\$ctl[0-9]+\$linkBtnHost'.format(ENTRY_FILENAME)

    JOOVIDEO_TXT_TITLE_PATN = 'ctl00_ContentPlaceHolder1_{0}1_txtTitle'.format(ENTRY_FILENAME)
    JOOVIDEO_TXT_URL_PATN = 'ctl00_ContentPlaceHolder1_{0}1_txtUrl'.format(ENTRY_FILENAME)

    EVT_TARGET_PATN2 = "('HostLink','.+')"

    DM_STREAM_CONTEXT_PATN = r'dmp\.create\(document\.getElementById\(\'player\'\),\s*(.+)\n'
    DM_STREAM_CONFIG_PATN = r'var\s+config\s*\=\s*(.+)\n'
    HOSTNAME_PATN = 'http[s]*://.+/'
    JOOVIDEO_INTERNAL_CONTENT_HOSTNAME = None
    HTTPS_FETCH_TIMEOUT = 256

    category_tblnames = ["tblDrama", "tblEnt", "tblDoc", "tblEven", "tblNews"]

    # stream_providers = [unicode('델리모션'), unicode('Oload')]  # converts 'str' to 'unicode'
    # stream_providers = [unicode('델리모션')]  # converts 'str' to 'unicode'
    stream_providers = [unicode('VStream')]  # converts 'str' to 'unicode'

    VSTREAM_EMBED_URL_TEMPLATE = 'https://verystream.com/e/{0}'

    def __init__(self):
        self.HTML_PARSER = "html.parser"  # default: "html.parser", "lxml", "html5lib"

    def __del__(self):
        pass

    def getJooVideoInternalUrl(self, media_no):
        url = self.JOOVIDEO_INTERNAL_CONTENT_HOSTNAME + '/{0}.aspx?'.format(self.ENTRY_FILENAME) + media_no
        return url

    def getResponse(self, url):
        headers = {'User-Agent': self.user_agent, 'Accept-Encoding': 'gzip, deflate'}
        response = requests.get(url, headers=headers)
        return response.text

    def getResponse_raw(self, url):
        headers = {'User-Agent': self.user_agent, 'Accept-Encoding': 'gzip, deflate'}
        response = requests.get(url, headers=headers)
        return response

    def getResponse2(self, url):
        headers = {'User-Agent': self.user_agent}
        cookies = {'lang': 'en', 'family_filter': 'off'}
        response = requests.get(url, headers=headers, cookies=cookies)
        return response.text

    def getResponse_ByPOST(self, url, post_values):
        response = requests.post(url, headers=self.header3, data=post_values)
        return response.text

    def getEpisodeNameFromHTML(self, jv_html):
        soup = BeautifulSoup(jv_html, self.HTML_PARSER)
        episode_name = self.getEpisodeNameFromBS(soup)
        return episode_name

    def getEpisodeNameFromBS(self, bs):
        # 중간에 <br>이 있으면 episode_name.string이 None이다. 따라서 strings를 이용해야 한다.
        episode_name = bs.find('span', attrs={'id': re.compile(self.JOOVIDEO_EPISODENUM_PATN, re.I)})
        retVal = ''
        if episode_name:
            for _str in episode_name.stripped_strings:
                retVal += (_str + ' ')
        return retVal

    def getDMEmbedVideoUrlFromHTML(self, jv_html):
        soup = BeautifulSoup(jv_html, self.HTML_PARSER)
        return self.getDMEmbedVideoUrlFromBS(soup)

    def getDMEmbedVideoIDFromBS(self, bs):
        row_item = bs.find('iframe', attrs={'id': re.compile('frameFlashId', re.I)})
        if row_item is not None:
            dm_video_key = row_item['src'].split("=")[1]
            return dm_video_key
        return None

    def getDMEmbedVideoUrlFromBS(self, bs):
        video_id = self.getDMEmbedVideoIDFromBS(bs)
        if video_id is not None:
            return "www.dailymotion.com/embed/video/{0}?syndication=110300&autoPlay=0".format(video_id)
        return ''

    def getOloadEmbedVideoUrlFromBS(self, bs):
        row_item = bs.find('iframe', attrs={'id': re.compile('frameFlashId', re.I)})
        if row_item is not None:
            oload_video_src_url = row_item['src']
            return oload_video_src_url
        return ''

    def getVStreamEmbedVideoIDFromBS(self, bs):
        row_item = bs.find('iframe', attrs={'id': re.compile('frameFlashId', re.I)})
        if row_item is not None:
            vs_video_id = row_item['src'].split("/")[4]
            return vs_video_id
        return None

    def getVStreamEmbedVideoUrlFromBS(self, bs):
        vs_video_id = self.getVStreamEmbedVideoIDFromBS(bs)
        if vs_video_id is not None:
            return self.VSTREAM_EMBED_URL_TEMPLATE.format(vs_video_id)
        return ''

    def getEmbedVideoUrlFromBS(self, bs, provider_name):
        if provider_name == unicode('델리모션'):
            return self.getDMEmbedVideoUrlFromBS(bs)
        elif provider_name == unicode('Oload'):
            return self.getOloadEmbedVideoUrlFromBS(bs)
        elif provider_name == unicode('VStream'):
            return self.getVStreamEmbedVideoUrlFromBS(bs)
        else:
            return 'NOT IMPLEMENTED'

    def getEmbedVideoUrls(self, joovideo_internal_url):
        """
        
        :param joovideo_internal_url: 
        :param provider_name: 
        :return: 
            {
            'title':, 
            'dm_emb_url':, 
            'stream_provider':
            }
        """

        urls = list()

        res = self.getResponse_raw(joovideo_internal_url)

        # xbmc.log('JOOVIDEO::getEmbedVideoUrls - res is %s' % res, xbmc.LOGDEBUG)

        soup = BeautifulSoup(res.text, self.HTML_PARSER)

        main_iframe = soup.find('iframe', attrs={'id': 'frameFlashId'})

        try:
            provider_list = main_iframe.parent
        except AttributeError as e:
            return urls

        row_items = provider_list.find_all('a', attrs={'id': 'btn'})

        # if False:  # stream_provider in unicode(row_items[0].string):
        #    # 현재 페이지에 이미 Daily Motion 첫번째 클립의 URL이 존재하므로 이것을 이용한다.
        #    first_clip_title = self.getEpisodeNameFromBS(soup)
        #    first_clip_dm_emb_url = self.getDMEmbedVideoUrlFromBS(soup)
        #    urls.append({'title': first_clip_title, 'dm_emb_url': first_clip_dm_emb_url})
        #    row_items = row_items[1:]

        for item in row_items:
            is_supported = False
            for provider in self.stream_providers:
                if unicode(item.string).startswith(provider):
                    is_supported = True
                    break

            if is_supported:
                # ex> javascript:__doPostBack('HostLink','414234|25|델리모션[1/2]|용문동-이필모, 온주완 |0|0')
                m = re.search(self.EVT_TARGET_PATN2, item['href'])

                if m is not None:
                    form_data = self.getPOSTFormDataFromBS(soup)

                    args = m.group().replace("'", "").split(",")

                    form_data['__EVENTTARGET'] = args[0]

                    # 중간의 "," 처리
                    if len(args) > 1:
                        for idx in range(1, len(args)):
                            if idx != 1:
                                form_data['__EVENTARGUMENT'] += (',' + args[idx])
                            else:
                                form_data['__EVENTARGUMENT'] += args[idx]

                    # xbmc.log('JOOVIDEO::getEmbedVideoUrls - form_data is %s' % form_data, xbmc.LOGDEBUG)

                    jv_html = self.getResponse_ByPOST(res.url, form_data)

                    # xbmc.log('JOOVIDEO::getEmbedVideoUrls - jv_html is %s' % jv_html, xbmc.LOGDEBUG)

                    item_soup = BeautifulSoup(jv_html, self.HTML_PARSER)

                    dm_video_id = self.getVStreamEmbedVideoIDFromBS(item_soup)
                    vstream_fileinfo = self.getVStreamFileinfo(dm_video_id)

                    # TODO : refactoring
                    dm_embed_url = self.getEmbedVideoUrlFromBS(item_soup, provider)

                    title = self.getEpisodeNameFromBS(item_soup)
                    urls.append({'title': title, 'dm_emb_url': dm_embed_url, 'stream_provider': provider,
                                 'dm_video_id': dm_video_id, 'file_info': vstream_fileinfo})
                else:
                    print 'm is None'

        return urls

    def getContentHostname(self, content_url):
        """
        :param content_url:
        :return:
        """
        hostname = ''
        m = re.search(self.HOSTNAME_PATN, content_url)
        if m is None:
            hostname = self.JOOVIDEO_LANDING_URL
        else:
            hostname = m.group()
            hostname = hostname[:(len(hostname) - 1)]

        return hostname

    def setContentHostname(self, hostname):
        self.JOOVIDEO_INTERNAL_CONTENT_HOSTNAME = hostname

    def isHTTPS(self, url):
        if re.search('https://.+[/]*', url) is not None:
            return True

        return False

    def getPOSTFormDataFromBS(self, bs):

        """
          POST method에 필요한 모든 form data를 획득한 후,
          그대로 다시 전달해 주어야 한다.

          - __EVENTTARGET
          - __EVENTARGUMENT
          - __VIEWSTATE
          - __EVENTVALIDATION
          - ctl00$ContentPlaceHolder1$ViewMedia1$txtTitle
          - ctl00$ContentPlaceHolder1$ViewMedia1$txtUrl

        """

        post_data = dict()

        # __EVENTARGUMENT
        __eventargument = ''
        post_data['__EVENTARGUMENT'] = __eventargument

        # __VIEWSTATE
        __viewstate_tag = bs.find('input', attrs={'type': 'hidden', 'id': '__VIEWSTATE'})
        __viewstate = __viewstate_tag['value']
        post_data['__VIEWSTATE'] = __viewstate

        # __EVENTVALIDATION
        __eventvalidation_tag = bs.find('input', attrs={'type': 'hidden', 'id': '__EVENTVALIDATION'})
        __eventvalidation = __eventvalidation_tag['value']
        post_data['__EVENTVALIDATION'] = __eventvalidation

        # ctl00$ContentPlaceHolder1${0}1$txtTitle.format(self.ENTRY_FILENAME)
        __txtTitle_tag = bs.find('input',
                                 attrs={'type': 'hidden', 'id': re.compile(self.JOOVIDEO_TXT_TITLE_PATN, re.I)})
        __txtTitle = __txtTitle_tag['value']
        post_data['ctl00$ContentPlaceHolder1${0}1$txtTitle'.format(self.ENTRY_FILENAME)] = __txtTitle

        # ctl00$ContentPlaceHolder1${0}1$txtUrl.format(self.ENTRY_FILENAME)
        __txtUrl_tag = bs.find('input', attrs={'type': 'hidden', 'id': re.compile(self.JOOVIDEO_TXT_URL_PATN, re.I)})
        __txtUrl = __txtUrl_tag['value']
        post_data['ctl00$ContentPlaceHolder1${0}1$txtUrl'.format(self.ENTRY_FILENAME)] = __txtUrl

        return post_data

    def checkValidUrl(self, _url):
        o = urlparse.urlparse(_url)
        if len(o[1]) > 0:
            return True

        return False

    def quarantineUrl(self, _url):
        """
        url에 scheme이 없으면 urllib2/3에서 에러를 반환한다. 이를 막고자 임의의 scheme을 삽입해 준다.
        :param _url:
        :return:
        """
        pr = urlparse.urlparse(_url)
        _new_url = ''
        if len(pr[0]) > 0:
            _new_url += pr[0] + '://'
        else:
            _new_url += 'http://'  # TODO : workaround

        if len(pr[1]) > 0:
            _new_url += pr[1]
        if len(pr[2]) > 0:
            _new_url += pr[2]
        if len(pr[3]) > 0:
            pass
        if len(pr[4]) > 0:
            _new_url += '?' + pr[4]

        return _new_url

    def getDMEmbedUrl_v1_From(self, jv_link):

        """
            기존에는 페이지내에 DM embedded url이 그대로 노출되었는데,
            최근에는 바뀌어서 특정 링크(<a/>)를 누르면 다른 페이지로 redirect되고 redirect된 페이지에서
            아래처럼 javascript로 링크를 생성하여 영상을 재생한다.
            광고가 없어지기 때문에 불이익일거 같은데...

            src url : http://www.jvlink.net/xlink.htm?q=k1mVZ8e5tqBlwwkkdPe

            function fxlink(){
                var a = window.location.toString();
                var name = a.substring(a.indexOf("=") + 1);

                if (name.length > 0 && name.indexOf("http:") < 0)
                    window.location = "http://www.dailymotion.com/embed/video/" + name + "?syndication=110300&logo=0&info=0&autoPlay=0";
            }
        """
        para_q = jv_link[jv_link.rfind("=") + 1:]
        new_dm_embed_url = "http://www.dailymotion.com/embed/video/" + para_q + "?syndication=110300&logo=0&info=0&autoPlay=0"
        return new_dm_embed_url

    def getDMEmbedUrl_v2_From(self, jv_link):
        return jv_link

    def getCategoryTables(self, soup):

        categories = list()

        for tblname in self.category_tblnames:
            categ_table = soup.find('table', attrs={'id': tblname})
            if categ_table:
                categories.append(categ_table)

        # WORKAROUND
        if len(categories) < 5:
            categories = soup.find_all('table', attrs={'id': self.category_tblnames[0]})
        # WORKAROUND

        return categories

    def getVStreamFileinfo(self, vid):
        try:
            url_template = 'https://api.verystream.com/file/info?file={0}'
            url = url_template.format(vid)
            r = requests.get(url)
            if r.json()['status'] == 200:
                return r.json()
        except requests.ConnectionError as e:
            return None

    def toMegabytes(self, bytes):
        return int(bytes) / (1024 * 1024)

    def getVideoResolutionFromVStreamFilename(self, vs_stream_url):
        if vs_stream_url:
            re_pat = '[\d]{3}p\.mp4'
            m = re.search(re_pat, vs_stream_url)
            if m is not None:
                resolution = m.group()
                return resolution.split('.')[0]
            else:
                return ""
        return ""


if __name__ == '__main__':
    pass
