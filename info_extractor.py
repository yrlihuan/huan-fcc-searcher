# encoding=utf-8

from datetime import datetime as date
import traceback
import domutil
import storage
from BeautifulSoup import BeautifulSoup as Soup

def extract(pages):
    products = {}

    for page in pages:
        root = Soup(page)

        elem = root.find(name='table', attrs={'id':'rsTable'})
        if not elem:
            continue

        for tr in elem.findAll(name='tr'):
            tds = tr.findAll(name='td')
            if not tds or len(tds) == 0:
                continue

            company = tds[5].getText()
            fcc_id = tds[11].getText()
            lastupdate = extract_date(tds[13].getText())

            if fcc_id in products:
                entity = products[fcc_id]
                if entity.lastupdate < lastupdate:
                    entity.lastupdate = lastupdate
            else:
                entity = storage.create_instance(storage.FCCENTITY, \
                                                 company=company, \
                                                 fcc_id=fcc_id, \
                                                 lastupdate=lastupdate)

                products[fcc_id] = entity

    storage.db.put(products.values())

def extract_date(date_str):
    values = date_str.split('/')
    for ind in xrange(0, len(values)):
        values[ind] = int(values[ind])
    
    mon, day, year = values
    return date(year, mon, day)



