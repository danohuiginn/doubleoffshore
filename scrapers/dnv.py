import scrapekit
import copy
import dataset
import datetime
import base
import logging


search_terms = (
    # match vessel type
    "tanker for oil",
    "oil products",
    "tanker for chemicals",
    "production",
    "storage",
    "lng",
    
    #flags
    "nigeria",
    "guinea",
    "ivoire",
    "ivory",
    "senegal",
    "guinea",
    "sierra leone",
    "liberia",
    "togo",
 
    "benin",
    "cameroon",
    "gabon",
)


scraper = scrapekit.Scraper('dnv')



table = base.db['rigs']





def get_labelled(html, label):
        span = html.cssselect('#' + label)
        if not span:
            return ''
        return span[0].text_content().strip()
        

@scraper.task
def vessel_details(vesselid, vesseldetails):
    logging.info('getting details of %s' % vesselid)
    url = "https://exchange.dnv.com/Exchange/Main.aspx?EXTool=Vessel&VesselID=%s" % vesselid
    html = scraper.get(url).html()

    span_labels = {

        'docholder': 'ucMainControl_ToolContainer__ctl1_tabControl__ctl1_mDocHolderLink',
        'yard': 'ucMainControl_ToolContainer__ctl1_tabControl__ctl1_mYard',
        'shape': 'ucMainControl_ToolContainer__ctl1_tabControl__ctl1_mShape',
    }
    # span_labels omits data we already get from the js feed, namely:
    # callsign, capacity, classification, competitive_rig, country, current_water_depth, delivery year, derrick, detail_uri, drawworks, drilling_depth, field_operator, flag, flagcode, hasdnvservices, historicalnames, hitfields, hitfieldsdescription, homeport, id, imono, indnvclass, inglclass, location_field, mainclass, manager, managerid, managername, mud pumps, name, nonclassservices, nonclassservicevesselid, officialno, operating_status, operator, owner, ownerid, ownername, rated_water_depth, region, register, registercode, rig design, rig_design, rig_id, rig_type, rotary table, ruleset, ship_type, shipyard, site, source_uri, top drive, vesseltype


    for (k,v) in span_labels.items():
        if not vesseldetails.get(k, None):
            vesseldetails[k] = get_labelled(html, v)
    table.upsert(vesseldetails, ['id'])
    return vesseldetails

@scraper.task
def scrape_index(search_term):
    basic_data = {
        # copypasta for base.Scraper.setup()

        'site': 'DNV',
        'scrape_id': base.nonce(),
        'scrape_date': datetime.datetime.now(),
        }
    # fill in form
    url = 'http://vesselregister.dnvgl.com/vesselregister/api/vessel?term=%s&includeHistoricalNames=true&includeNonClass=true&chunkSize=20' % search_term

    # this is returned in the browser as xml, but to the scraper as json (?)
    # unpack the json
    js = scraper.get(url).json()
    for vessel in js['Vessels']:
        entry = copy.copy(basic_data)
        # The search method means we will get lots of duplicates
        # so use (Site,Name, ImoNo)
        for (k,v) in vessel.items():
            entry[k.lower()] = str(v)
        print('adding one item')
        table.upsert(entry, ['site', 'name', 'imono'])
        vessel_details.queue(entry['id'], entry)
    return

    
@scraper.task
def scrape_all_indexes():
    for term in search_terms:
        logging.info('scraping js for %s' % term)
        scrape_index(term)


if __name__ == '__main__':
    scrape_all_indexes()
