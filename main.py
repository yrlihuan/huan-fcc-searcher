import sys
import os
import os.path
import cgi
import logging
import pickle
import task
import storage
import gviz_api
from datetime import datetime

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

            
COMPANIES_T = '<div class="result_item" ind="%s">%s</div>\n'
JSONS_T = 'jsons[%s] = %s;\ncompany_names[%s] = "%s";\n'

TEMPLATE = """
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=9; IE=8; IE=7" > 
    <style type="text/css">
      body {font-family: "Lucida Grande",Arial,helvetica,sans-serif;}
      div.result_item {color: #FFFFFF; font-weight:bold; padding: 12px; cursor: pointer;}
      div.result_item:hover {background-color: #AFD775;}
      div.search_box {height: 77px; width: 728px; overflow: hidden; background-image:url("search_box.png")}
      #search_button, #search_button:active {border:0 none; padding:0; cursor:pointer; height:46px; width:107px; margin-left:9px; background-position:0px 0px; background-image: url("search.png")}
      #search_button:hover{background-position:0px 47px;}
      td.chart {background-color: white;}
      td.sidebar {background-color: #95CBE9; width: 120px; padding: 5px;}
      #search_input {border: 0 none; font-size: 20px; height:28px; margin: 22px 0 0 22px; width: 570px;}
    </style>
    
    <script type="text/javascript" src="jquery.js"></script>
    <script type="text/javascript" src="http://www.google.com/jsapi"></script>
    <script type="text/javascript">
      google.load("visualization", "1", {packages:["corechart"]});
      var jsons = new Array();
      var company_names = new Array();
      %(js_data)s

      function drawChart(json_data, company_name) {
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
        var data = new google.visualization.DataTable(json_data, 0.5);
        chart.draw(data, {width: 640, height: 420, title: company_name});
      }

      function drawNthChart(id) {
        drawChart(jsons[id], company_names[id]);
      }

      $(document).ready(
        function() {
          if (company_names.length != 0) {
              drawNthChart(0);
          }
        
          $(".result_item").click(function(event) {
            var id = Number($(this).attr("ind"));
            drawNthChart(id);
            event.preventDefault();
          });
        }
      );
    </script>
  </head>

  <body>
    <table>
      <tr class="titlebar">
        <form>
          <td colspan="2">
            <div class="search_box">
              <input id="search_input" value="%(query_str)s" name="q" />
              <input id="search_button" value="" type="submit" />
            </div>
          </td>
        </form>
      </tr>
      <tr>
        <td valign="top" class="sidebar">
          <div>
            %(html_companies)s
          </div>
        </td>
        <td class="chart" width="640" height="420">
          <div id="chart_div"></div>
        </td>
      </tr>
      <tr>
        <td colspan="2">
            <div style="text-align: center; color: rgb(118, 118, 118); font-size: 9pt;">
                &copy; 2011 - Huan Li        
            </div>
        </td>
      </tr>
    </table>
  </body>
<html>"""

class Search(webapp.RequestHandler):
    def get(self):
        query = self.request.get('q')
        if query:
            query = query.split()[0]
            index = storage.query(storage.SEARCHINDEX, keyword=query).get()
            if index:
                companies = pickle.loads(index.companies)
            else:
                companies = []
        else:
            query = ''
            companies = ['Intel Corporation', \
                         'Dell Inc.', \
                         'Microsoft Corporation', \
                         'Cisco Systems Inc', \
                         'Huawei Technologies Co.,Ltd', \
                         'Sony Corporation', \
                         'Qualcomm Incorporated']

        html = self._get_html(companies, query)
        self.response.out.write(html)

    def post(self):
        self.get()

    def _get_html(self, companies, query_str=''):
        js_data_list = []
        html_companies_list = []

        ind = 0
        for company in companies:
            json = self.get_json_for_company(company)
            if not json:
                continue
            
            js_data_list.append(JSONS_T % (ind, json, ind, self._remove_quotes(company)))
            html_companies_list.append(COMPANIES_T % (ind, company))
            
            ind += 1
            if ind >= 10:
                break

        js_data = ''.join(js_data_list)
        html_companies = ''.join(html_companies_list)

        return TEMPLATE % vars()

    def get_json_for_company(self, company_name):
        company = storage.query(storage.COMPANY, name=company_name).get()
        if not company:
            return

        filing_in_year = pickle.loads(company.filing_in_year)
    
        descriptions = [('Year', 'string'), ('Filings', 'number')]
        data = []
        for y in xrange(1980, 2012):
            if y in filing_in_year:
                filings = filing_in_year[y]
            else:
                filings = 0
            
            data.append([str(y), filings])
    
        data_table = gviz_api.DataTable(descriptions)
        data_table.LoadData(data)
    
        return data_table.ToJSon(columns_order=("Year", "Filings"), order_by="Year")

    def _remove_quotes(self, s):
        return s.replace('"', '')

class JQueryTest(webapp.RequestHandler):

    template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <title>jQuery demo</title>
    </head>
    <body>
      <a href="http://jquery.com/">jQuery</a>
      <script src="/jquery.js"></script>
      <script>
        $(document).ready(function(){
          $("a").click(function(event){
            alert("As you can see, the link no longer took you to jquery.com");
            event.preventDefault();
          });
        });
      </script>
    </body>
    </html>
    """

    def get(self):
        self.response.out.write(self.template)

application = webapp.WSGIApplication(
                                     [('/jquery', JQueryTest),
                                     ('/search', Search),
                                     ('/', Search),],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

