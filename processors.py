import os
from HTMLParser import HTMLParser
from urllib import urlencode
import requests
import html5lib
import unicodecsv as csv
from pyquery import PyQuery
import re
import json

class ProcessorParam(object):
   
    hiring_authority = None
    date_range = None

    def __init__(self, position, keywords, country, hiring):
        self.position = position
        self.keywords = keywords
        self.country = country
        self.state = state

    def get_prefix(self):
        prefix = '-'.join((self.position, self.country, self.state, self.city, ''.join(map(str, self.date_range))))

        return prefix.replace(' ', '-')


class Processor(object):
    ROOT_URL = None
    ROOT_QUERY_URL = None
    CSV_OUTPUT = None
    html_parser = HTMLParser()
    RE_AGE_NUMBER = re.compile(r'\d+')
    SUPPORTS_COUNTRY = False

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/58.0.3029.110 Chrome/58.0.3029.110 Safari/537.36'
    }

    def __init__(self, params):
        self.params = params
        self.prefix = self.params.get_prefix()

    def get_query(self):
        return self.params.position


    def filter_age(self, age_date):
        if self.params.date_range:
            date_from, date_to = self.params.date_range
            return date_from <= age_date <= date_to

        return True

  
    def start(self):
        raise NotImplementedError()

    def fetch(self, url):
        return requests.get(url, headers=self.HEADERS).text

    def next(self):
        raise NotImplementedError()

    def get_full_next_url(self, link):
        return '{}{}'.format(self.ROOT_URL, link)

    def unescape(self, link):
        return self.html_parser.unescape(link)

    def get_keywords(self):
        if self.params.keywords:
            return self.params.keywords

        return None

    def get_text_content(self, data, css_select, child_num=None):
        py_rows = PyQuery(data)
        c = py_rows(css_select)

        if not c:
            return None

        if not child_num:
            child_num = 0

        if child_num > len(c):
            return None

        return c[child_num].text_content().strip()

    def parse_location(self, location):

        if not location:
            return '', '', 'USA'

        location_split = location.strip().split(',')

        city = location_split[0]
        state = ''

        if len(location_split) > 1:
            state_split = location_split[1].strip().split(' ')

            state = state_split[0]

        return city, state, 'USA'

    def get_text_attr(self, data, css_select, attribute):
        py_rows = PyQuery(data)

        e = py_rows(css_select)

        return e[0].get(attribute)

    def process(self):
        data = self.start()
        self.csv_open()
        
        while True:
            for row in self.get_rows(data):
                location = self.get_location(row)
                company_name = self.get_company(row)
                position_title = self.get_position_title(row)

             
                city, state, country = self.parse_location(location)

                if self.filter_age(age_date):
                    self.csv_write((position_title, company_name, position_url, city, state, country))

            next_url = self.next(data)

            if not next_url:
                break

            next_url = self.get_full_next_url(next_url)

            data = self.fetch(next_url)


class IndeedProcessor(Processor):
    ROOT_URL = 'https://www.indeed.com'
    ROOT_QUERY_URL = ''.join((ROOT_URL, '/jobs?{}'))
    CSV_OUTPUT = 'indeed.csv'

    def get_query(self):
        q = super(IndeedProcessor, self).get_query()

        return 'title:{}'.format(q)

    def next(self, data):
        pyq = PyQuery(data)

        pagination = pyq('.pagination')

        py = PyQuery(pagination)
        n = py('.pn')

        next_ele = n[-1]

        if 'Next' not in next_ele.text_content():
            return None

        href = next_ele.getparent().get('href')

        return href


class Processor(Processor):
    ROOT_URL = 'https://www.dice.com'
    ROOT_QUERY_URL = ''.join((ROOT_URL, '/jobs?{}'))
    CSV_OUTPUT = 'dice.csv'

    def get_full_position_url(self, link):
        return link

    def get_full_next_url(self, url):
        return url

    def start(self):
        data = {
            'for_jt': self.get_query(),
            'l': self.get_search_location() or '',
            'sort': 'date',
            'radius':'5',
            'for_one': self.get_keywords()
        }

        url = self.ROOT_QUERY_URL.format(urlencode(data))
        text = self.fetch(url)

        return text



class LnProcessor(Processor):
    ROOT_URL = 'https://www.linkedin.com'
    ROOT_QUERY_URL = ''.join((ROOT_URL, '/jobs/searchRefresh?{}'))
    CSV_OUTPUT = 'linkedin.csv'
    SUPPORTS_COUNTRY = True

    def get_query(self):
        q = super(LnProcessor, self).get_query()

        k = self.get_keywords()

        if not k:
            return q

        return '{} {}'.format(q,k)

    def start(self):

        data = {
            'refreshType': 'fullpage',
            'keywords': self.get_query(),
            'location': self.get_search_location() or '',
            'sortBy': 'DD',
            'radius':'5'
        }

        url = self.ROOT_QUERY_URL.format(urlencode(data))

        text = self.fetch(url)

        return json.loads(text)

    def get_rows(self, data):

        if isinstance(data, basestring):
            data = json.loads(data)

        return data['decoratedJobPostingsModule']['elements']

  
