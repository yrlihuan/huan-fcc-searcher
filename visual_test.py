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

def get_json_for_company(company_name):
    company = storage.query(storage.COMPANY, name=company_name).get()
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

class GvizExample(webapp.RequestHandler):
    page_template = """
    <html>
      <head>
      <title>Static example</title>
        <script src="http://www.google.com/jsapi" type="text/javascript"></script>
        <script>
          google.load("visualization", "1", {packages:["%(package)s"]});
    
          google.setOnLoadCallback(drawTable);
          function drawTable() {
            %(jscode)s
            var jscode_table = new google.visualization.%(table_type)s(document.getElementById('table_div_jscode'));
            jscode_table.draw(jscode_data, {showRowNumber: true});
    
            var json_table = new google.visualization.%(table_type)s(document.getElementById('table_div_json'));
            var json_data = new google.visualization.DataTable(%(json)s, 0.5);
            json_table.draw(json_data, {showRowNumber: true});
          }
        </script>
      </head>
      <body>
        <H1>Table created using ToJSCode</H1>
        <div id="table_div_jscode"></div>
        <H1>Table created using ToJSon</H1>
        <div id="table_div_json"></div>
      </body>
    </html>
    """

    packages = {'Table':'table', 'ColumnChart':'corechart', 'AreaChart':'corechart'}

    def get(self):

        # Creating the data
        description = {"name": ("string", "Name"),
                       "salary": ("number", "Salary"),
                       "full_time": ("boolean", "Full Time Employee")}
        data = [{"name": "Mike", "salary": (10000, "$10,000"), "full_time": True},
                {"name": "Jim", "salary": (800, "$800"), "full_time": False},
                {"name": "Alice", "salary": (12500, "$12,500"), "full_time": True},
                {"name": "Bob", "salary": (7000, "$7,000"), "full_time": True}]

        # Loading it into gviz_api.DataTable
        data_table = gviz_api.DataTable(description)
        data_table.LoadData(data)

        # Creating a JavaScript code string
        jscode = data_table.ToJSCode("jscode_data",
                                     columns_order=("name", "salary", "full_time"),
                                     order_by="salary")
        # Creating a JSon string
        json = data_table.ToJSon(columns_order=("name", "salary", "full_time"),
                                 order_by="salary")

        table_type = self.request.get('type')
        if not table_type:
            table_type = 'Table'

        package = self.packages[table_type]

        # Putting the JS code and JSon string into the template
        self.response.out.write(self.page_template % vars())

class TwoChart(webapp.RequestHandler):
    template = """
    <html>
      <head>
        <script type="text/javascript" src="/jquery.js"></script>
        <script type="text/javascript" src="https://www.google.com/jsapi"></script>
        <script type="text/javascript">
          google.load("visualization", "1", {packages:["corechart"]});
          function drawChart(json_data) {
            var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
            var data = new google.visualization.DataTable(json_data, 0.5);
            chart.draw(data, {width: 800, height: 540, title: 'Company FCC Filings'});
          }

          $(document).ready(
            function() {
              $(".company").click(function(event) {
                var link = $(this).attr("href");
                var id = Number(link.substring(1, link.length));

                var jsons = new Array(2);
                jsons[0] = %(json_ms)s
                jsons[1] = %(json_intel)s

                drawChart(jsons[id]);
                event.preventDefault();
              });
            }
          );
        </script>
      </head>

      <body>
        <a href="#0" class="company">Microsoft Corporation</a> <br/>
        <a href="#1" class="company">Intel Corporation</a> <br/>
        <div id="chart_div"></div>
      </body>
    <html>
    """

    def get(self):
        json_ms = get_json_for_company('Microsoft Corporation')
        json_intel = get_json_for_company('Intel Corporation')

        self.response.out.write(self.template % vars())


class MSChart(webapp.RequestHandler):
    template = """
    <html>
      <head>
        <script type="text/javascript" src="https://www.google.com/jsapi"></script>
        <script type="text/javascript">
          google.load("visualization", "1", {packages:["corechart"]});
          google.setOnLoadCallback(drawChart);
          function drawChart() {
            var chart = new google.visualization.ColumnChart(document.getElementById('chart_div'));
            var data = new google.visualization.DataTable(%(json)s, 0.5);
            chart.draw(data, {width: 800, height: 540, title: 'Company FCC Filings'});
          }
        </script>
      </head>
    
      <body>
        <div id="chart_div"></div>
      </body>
    </html>
    
    """

    def get(self):
        name = self.request.get('company')
        if not name:
            name = 'Microsoft Corporation'

        json = get_json_for_company(name)
        self.response.out.write(self.template % vars())


application = webapp.WSGIApplication(
                                     [('/visual_test/gviz_api', GvizExample),
                                     ('/visual_test/ms_chart', MSChart),
                                     ('/visual_test/two_chart', TwoChart)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

