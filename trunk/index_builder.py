import storage
import pickle
from datetime import datetime as date

SKIPPED_KEYWORDS = set(['co.,ltd', 'ltd', 'co', 'inc', 'limited', 'of', 'corporation'])

def build():
    companies = {}
    search_index = {}

    for entity in storage.query(storage.FCCENTITY):
        company = entity.company
        update = entity.lastupdate

        try:
            products_cnt = companies[company]
            new_company = False
        except KeyError:
            products_cnt = {}
            companies[company] = products_cnt
            new_company = True

        year = update.year
        try:
            products_cnt[year] += 1
        except KeyError:
            products_cnt[year] = 1

        if not new_company:
            continue

        for keyword in company.split():
            if not keyword:
                continue

            keyword = keyword.lower()
            if keyword in SKIPPED_KEYWORDS:
                continue

            try:
                company_list = search_index[keyword]
            except KeyError:
                company_list = []
                search_index[keyword] = company_list

            company_list.append(company)
            
    for company in companies:
        products_cnt = companies[company]
        total_products = sum(products_cnt.values())
        db_obj = storage.create_instance(storage.COMPANY, \
                                         name=company, \
                                         total_filings=total_products, \
                                         filing_in_year=pickle.dumps(products_cnt))

        companies[company] = db_obj

    for keyword in search_index:
        company_list = search_index[keyword]
        db_obj = storage.create_instance(storage.SEARCHINDEX, \
                                         keyword=keyword, \
                                         companies=pickle.dumps(company_list))

        search_index[keyword] = db_obj

    storage.db.put(companies.values())
    storage.db.put(search_index.values())

if __name__ == '__main__':
    build()

