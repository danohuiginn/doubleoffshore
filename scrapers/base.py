
u"""
data structure

site
scrape_id # unique id for the scrape [Q: over multiple sources?]
scrape_date

source_uri # may end up being not-entirely-realistic

cached downloaded pages:
 BASEDIR/site/YYYYMMDD/scrape_nonce/escaped_uri.html

"""

import copy
import dataset
import datetime
import logging
import lxml.html
import random
import string
import urllib2, urllib

from lxml.cssselect import CSSSelector

import settings

if settings.USE_TOR:
    import socks
    import socket
    socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, u"127.0.0.1", 9050)
    socket.socket = socks.socksocket


db = dataset.connect(settings.DBURI)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def nonce(chars=8):
    return u''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase) for x in xrange(chars))

class Scraper(object):
    table = db[u'rigs']

    def run(self):
        self.setup()
        for (rigID, data) in self.crawl_indices():
            self.add_item(rigID, data)
            

    def crawl_indices(self):
        # should 
        # yield a tuple (_id, data), where:
        # _id uniquely identifies the item within this site (e.g. ship name)
        #   this allows skipping when we only want to pick up new items
        # data contains everything else that we found and don't want to repeat
        # XXX: need to deal with the possibility of duplicates here, at least in warning
        # unique should be (site, scrape_id, rig_id)
        logger.debug(u'reading indices')

        for item in []:
            yield (u'NA', {})
    
    def add_item(self, rigID, data):
        logger.debug(u'adding item')
        item = copy.copy(self.basedata)
        item[u'rig_id'] = rigID
        item.update(data)
        self.table.insert(item)

    def setup(self):
        self.basedata = {
            u'site': self.site,
            u'scrape_id': nonce(),
            u'scrape_date': datetime.datetime.now(),
            }

class FPSO(Scraper):

    site = u'FPSO'
    site_url = u'http://fpso.com'
        
    def unpack_rigrow(self, row, data):
        u"""Get the data from one row of a FPSO table"""
        cells = row.findall(u'td')
        for cellno, label in enumerate((
                u'name', u'owner', u'operator', u'field_operator',
                u'location_field', u'country', u'capacity')):
            data[label] = cells[cellno].text_content()
        data[u'detail_uri'] = self.site_url + cells[0].find(u'a').attrib[u'href']
        logger.debug(data)
        return (data[u'name'], data)
        
    def crawl_indices(self):
        page_num = 1
        while True:
            url = u'http://fpso.com/fpso/?page=%s' % page_num
            page = urllib2.urlopen(url)
            tree = lxml.html.parse(page)
            rigrows = CSSSelector(u'tr.odd,tr.even')(tree)
            if len(rigrows) == 0:
                raise StopIteration
                
            basedata = copy.copy(self.basedata)
            basedata[u'source_uri'] = url
            
            for row in rigrows:
                yield self.unpack_rigrow(row, basedata)

            page_num += 1             
            if page_num > 30:
                logger.warn(u"""
                   many more pages than expected on FPSO
                   aborting from fear of infinite loop""")
                raise StopIteration


class RigzoneBasic(Scraper):
    u"""
    Rigzone -- just getting the rig names, but not going into the detail pages
    """

    site = u'Rigzone -- basic'
    site_url = u'http://www.rigzone.com'

    def unpack_rigrow(self, row, data):
        u"""Get the data from one row of a FPSO table"""
        cells = row.findall(u'td')
        for cellno, label in enumerate((
                u'name', u'manager', u'rig_type', u'rated_water_depth', u'drilling_depth')):
            data[label] = cells[cellno].text_content().strip()
        data[u'detail_uri'] = self.site_url + cells[0].find(u'a').attrib[u'href']
        logger.debug(data)
        return (data[u'name'], data)

    
    def crawl_indices(self):
        page_num = 1
        while True:
            url = u'http://www.rigzone.com/data/results.asp?P=%s&Region_ID=10' % page_num
            page = urllib2.urlopen(url)
            tree = lxml.html.parse(page)
            sel = CSSSelector(u'tr[style*="height:20px;"]')
            rigrows = sel(tree)
            if len(rigrows) == 0:
                raise StopIteration

            basedata = copy.copy(self.basedata)
            basedata[u'source_uri'] = url
            
            for row in rigrows:
                yield self.unpack_rigrow(row, basedata)


            page_num += 1
            if page_num > 8:
                logger.warn(u"""
                   many more pages than expected on Rigdata
                   aborting from fear of infinite loop""")
                raise StopIteration
           
class RigzoneFull(RigzoneBasic):
    
    def find_value(self, tree, label):
        path = u'.//strong[contains(text(), "%s")]' % label
        label_node = tree.xpath(path)[0]
        value = label_node.getparent().getnext().text_content().strip()
        return value
    
    def scrape_detail_page(self, data):
        logger.debug(u'making request for %s' % data[u'detail_uri'])
        page = urllib2.urlopen(data[u'detail_uri'])
        logger.debug(u'opened page')
        tree = lxml.html.parse(page)
        
        # ignore labels we know from the index page:
        # name, manager, rig type, rated water depth, drilling depth
        labels = {
            # overview
            u'Rig Owner:': u'owner',
            u'Competitive Rig:': u'competitive_rig',            
            u' Type:': u'ship_type', # may be rig type, drillship type,...
            u'Rig Design': u'rig_design',
            
            # contract
            u'Operating Status:': u'operating_status',
            u'Operator:': u'operator',
            
            # location
            u'Region:': u'region',
            u'Country:': u'country',
            u'Current Water Depth:': u'current_water_depth',
        }
        for l in (
                u'Classification:', u'Rig Design:', u'Shipyard:', u'Delivery Year:',
                u'Flag:', u'Derrick:', u'Drawworks:', u'Mud Pumps:', u'Top Drive:',
                u'Rotary Table:'
                ):
            labels[l] = l.strip(u':').lower()
        for (searchterm, dbname) in labels.items():
            data[dbname] = self.find_value(tree, searchterm)
        
        logger.debug(data)
        return data

    def add_item(self, rigID, data):
        logger.debug(u'adding item')
        item = copy.copy(self.basedata)
        item[u'rig_id'] = rigID
        item.update(data)
        data = self.scrape_detail_page(data)
        self.table.insert(item)

def run_all_scrapers():
    scrapers = [FPSO,RigzoneFull]
    for scraper_cl in scrapers:
        instance = scraper_cl()
        instance.run()
        
if __name__ == u'__main__':
    run_all_scrapers()
