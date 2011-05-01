import sys
import os
import os.path
import cgi
import logging
import task
import storage
import index_builder
from datetime import datetime

from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

CONFIGS = {'fcc':'fcc.xml'}

class InitiateTask(webapp.RequestHandler):
    def get(self):
        site_id = self.request.get('id').lower()
        if site_id not in CONFIGS:
            logging.warning('ID not in list')
            self.response.out.write('ID not in list.')
            return

        config = CONFIGS[site_id]
        task.TaskDispatcher(config).initiate()
        self.response.out.write('Site %s successfully initiated!' % site_id)

class CreateExecutor(webapp.RequestHandler):
    def get(self):
        site_id = self.request.get('id').lower()
        if site_id not in CONFIGS:
            logging.warning('ID not in list')
            self.response.out.write('ID not in list.')
            return

        logging.info('Enqueue executor')
        taskqueue.add(queue_name='taskexecutor', url='/admin/execute_task', params={'id':site_id})
        self.response.out.write('Executor added for site %s' % site_id)

class ExecuteTask(webapp.RequestHandler):
    def post(self):
        logging.info('Start Executor!')

        site_id = self.request.get('id').lower()
        if site_id not in CONFIGS:
            logging.warning('ID not in list')
            self.response.out.write('ID not in list.')
            return
                
        config = CONFIGS[site_id]
        executor = task.TaskExecutor(config)

        if executor.execute():
            # enqueue another executor
            logging.info('Enqueue a new executor')
            taskqueue.add(queue_name='taskexecutor', url='/admin/execute_task', params={'id':site_id})
        else:
            # there is no tasks right now.
            logging.info('No tasks in queue. Quitting...')

class DisplayStatistics(webapp.RequestHandler):
    def get(self):
        query = storage.query(storage.WORKITEM)
        self.response.out.write('Count of work items: %s\n' % query.count(limit=None))

        query = storage.query(storage.WORKITEM, status='queued')
        self.response.out.write('Queued work items: %s\n' % query.count(limit=None))

        query = storage.query(storage.FCCENTITY)
        self.response.out.write('Count of FCC entities: %s\n' % query.count(limit=None))

class BuildIndex(webapp.RequestHandler):
    def get(self):
        taskqueue.add(queue_name='taskexecutor', url='/admin/build_index')
        self.response.out.write('Enqueue index builder')

    def post(self):
        index_builder.build()
        logging.info('Index successfully built!')

application = webapp.WSGIApplication(
                                     [('/admin/initiate_task', InitiateTask),
                                      ('/admin/create_executor', CreateExecutor),
                                      ('/admin/execute_task', ExecuteTask),
                                      ('/admin/build_index', BuildIndex),
                                      ('/admin/display_status', DisplayStatistics),],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()

