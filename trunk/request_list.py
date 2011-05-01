# encoding=utf-8

import mechanize

def query_first_page(url, form, **kargs):
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.open(url)

    br.select_form(form)

    for key, value in kargs.items():
        br.form[key] = value

    br.submit()

    return br

def query_remains(browser, form):
    br = browser
    result_htmls = []

    try:
        while True:
            result_htmls.append(br.response().read())
            br.select_form(form)
            br.submit()
    except mechanize.FormNotFoundError:
        # runs to here when we're at the last page
        pass

    return result_htmls

if __name__ == '__main__':
    url = 'https://fjallfoss.fcc.gov/oetcf/eas/reports/GenericSearch.cfm'
    form = 'generic_search_form'
    show_records = '50'
    grantee_code = 'QIS'
    br = query_first_page(url, form, show_records=show_records, grantee_code=grantee_code)

    htmls = query_remains(br, 'next_result')
