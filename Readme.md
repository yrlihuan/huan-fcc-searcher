#what this project is for and how it's done

# FCC #
FCC (Federal Communication Commission) is a US government agency. The goal of FCC is to place regulations on how communication media are used. It is required that communication products get FCC's approval before going to market or even before field testing. Some people are interested in FCC because they can get information of new products by searching FCC's database, legally or illegally.

Currently there are about 300,000 products' documents kept in FCC's database. Though some old products don't have any info kept in digital form, there are lots of stuff for products which come after 2000, including inside/outside pics and user manuals.

# Goal #
Some interesting facts can be extracted by looking at FCC's data. Because FCC certification is required for products sold in US, it can be found which companies are most active in electronics market of US. Or companies can find out how their competitors are performing by looking at how many new devices they are registering in FCC.

With FCC's data, there may be many possibilities. The scope of this project is to generate graphical reports for companies' annual filings. This will help people get a quick scan of the trend for each company, without having to deal with FCC's slowness.

# Crawl Data #
The FCC host a search entry at http://www.fcc.gov/oet/ea/fccid/, or a more advanced version at https://fjallfoss.fcc.gov/oetcf/eas/reports/GenericSearch.cfm. The search functionality is already powerful that user can search by company name, product id or even by date. The search used by this project is by grantee codes that FCC assigned to companies. The list of grantee codes is kept in a xml file which can be found at https://fjallfoss.fcc.gov/oetcf/eas/reports/GranteeSearch.cfm.

In the search result list of FCC, there are basic info for products, including the company's name and address, its FCC id and last modification date. Fortunately that's all that we are interested in. The search result sheet also contains links to detailed info pages, that contain files companies submitted to FCC. However, links for most old products seem not working. Besides, we don't really need that info, so it is ignored.

The FCC contains large amount of filings and even only summary is needed, it takes a considerable amount of time to grab them. In order to leverage GAE's distributed computation system, it's better to divide the whole problem into small tasks and run them concurrently. And there are dependencies between tasks, which means that one task may need output of another task as its input and can not start until the other task finishes. This is dependencies are described by the graph below.

![http://huan-fcc-searcher.googlecode.com/svn/wiki/CrawlerArch2.gif](http://huan-fcc-searcher.googlecode.com/svn/wiki/CrawlerArch2.gif)

And when a task's prerequisites are fulfilled, the task is added to a queue to wait for an executor to run it. When it's done, the result is saved as input for the next task, and the executor is free to run its next assignment.

**Note:** _Because of the restrictions GAE places on free apps, only about 1/10 data is extracted from FCC's site currently._

# Web UI #

In order to present the FCC filings data in a way easy to comprehend, a visual column chart is desired. There are numerous chart drawing libs for web applications, of which the Visualization API from Google wins the competition for its cleanness and ease to use.

The entry page displays data for several well-known companies. And user can find companies by using the built in search facilities.

The project is hosted at http://fccextract.appspot.com/.

**Note:** _Users in China need to set proxies to access web sites hosted on GAE._

# Thanks For #
Without these babies, the project can never be finished before deadline.
  * google app engine
  * mechanize
  * BeautifulSoup
  * google visualization
  * gviz\_api
  * jQuery