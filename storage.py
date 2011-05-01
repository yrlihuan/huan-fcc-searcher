"""
Provides a way to store data persistently. The real method for data
storage differs across platforms. On development machine, python's
standard module sqlite3 is used; while on google app engine, the data
storage api from GAE is used.

This module provides a unified way to access data storage submodule.
"""
import sys
import os.path
import logging
import traceback
import time

db = None
try:
    from google.appengine.ext import db
except Exception, ex:
    logging.error(ex)

if not db:
    import sqlitedb as db

MODULE = None

WORKITEM = 'WorkItem'
FCCENTITY = 'FccEntity'
COMPANY = 'Company'
SEARCHINDEX = 'SearchIndex'
TABLES = [WORKITEM, FCCENTITY, COMPANY, SEARCHINDEX]

class WorkItem(db.Model):
    keyprop = 'item_id'
    item_id = db.StringProperty(required=True)
    item_type = db.StringProperty(required=True)
    status = db.StringProperty(required=True) # queued, assigned, completed
    config = db.StringProperty(required=True)
    param = db.BlobProperty()

class FccEntity(db.Model):
    keyprop = 'fcc_id'
    fcc_id = db.StringProperty(required=True)
    company = db.StringProperty()
    lastupdate = db.DateTimeProperty()

class Company(db.Model):
    keyprop = 'name'
    name = db.StringProperty(required=True)
    total_filings = db.IntegerProperty()
    filing_in_year = db.BlobProperty() # a pickled dict. key->year, value->count of products

class SearchIndex(db.Model):
    keyprop = 'keyword'
    keyword = db.StringProperty(required=True)
    companies = db.BlobProperty() # pickled list. stored companis with the keyword in their name

def text_type_converter(datatype, properties):
    for prop in properties:
        dbProperty = getattr(datatype, prop)
        if isinstance(dbProperty, db.TextProperty):
            properties[prop] = db.Text(properties[prop])
        elif isinstance(dbProperty, db.BlobProperty):
            properties[prop] = db.Blob(properties[prop])

def linebreak_remover(datatype, properties):
    for prop in properties:
        dbProperty = getattr(datatype, prop)
        if isinstance(dbProperty, db.StringProperty) and '\n' in properties[prop]:
            properties[prop] = properties[prop].replace('\n', '')

def create_instance(table, **properties):
    datatype = get_type_for_table(table)
    text_type_converter(datatype, properties)
    linebreak_remover(datatype, properties)

    primarykey = datatype.keyprop
    key = properties[primarykey]

    return datatype(key_name=key, **properties)

def add_or_update(table, **properties):
    datatype = get_type_for_table(table)
    text_type_converter(datatype, properties)
    linebreak_remover(datatype, properties)

    primarykey = datatype.keyprop
    key = properties[primarykey]
    entity = datatype.get_by_key_name(key)

    if not entity:
        updated = True
        entity = datatype(key_name=key, **properties)
    else:
        updated = False
        for prop in properties:
            oldvalue = getattr(entity, prop)
            newvalue = properties[prop]
            if oldvalue != newvalue:
                updated = True
                setattr(entity, prop, newvalue)

    if updated:
        entity.put()

    return entity

def query(table, **restrictions):
    t = get_type_for_table(table)
    text_type_converter(t, restrictions)
    linebreak_remover(t, restrictions)

    if restrictions == {}:
        return t.all()
    else:
        query_str = generate_selection(**restrictions)
        return t.gql(query_str, **restrictions)

def delete(table, **restrictions):
    for entity in query(table, **restrictions):
        entity.delete()

def generate_selection(**restrictions):
    if restrictions == {}:
        return ''
    else:
        s = 'WHERE '
        for r in restrictions:
            s += '%s = :%s AND ' % (r, r)

        return s[:-5]

def get_type_for_table(table):
    global MODULE
    if not MODULE:
        MODULE = sys.modules[__name__]

    if table in TABLES and hasattr(MODULE, table):
        return getattr(MODULE, table)
    else:
        raise TypeError('Can not determine appropriate type for table: %s' % table)


