# encoding=utf-8

import sys
import xml.dom.minidom as dom
import domutil
import storage
import uuid
import pickle
import logging
import traceback

class TaskExecutor():
    def __init__(self, config):
        self._dispatcher = TaskDispatcher(config)

    def execute(self):
        dispatcher = self._dispatcher

        item = dispatcher.get_queued()
        if item:
            item_id = item.item_id
            dispatcher.assign(item_id)
            try:
                result = self._run_task(item)
                dispatcher.complete(item_id, result)
            except:
                err = traceback.print_exc()
                logging.error(err)
                dispatcher.fail(item_id)

            return True
        else:
            return False

    def _run_task(self, work_item):
        task = self._dispatcher._tasks[work_item.item_type]
        param = pickle.loads(work_item.param)

        return task.run(param)

class TaskDispatcher():
    def __init__(self, config):
        self._tasks = {}
        self._config = config
        domRoot = dom.parse(config)

        for node in domRoot.getElementsByTagName('Task'):
            task = Task.load_from_node(node)
            self._tasks[task._name] = task

    def initiate(self):
        self._create_new_work(prev_task="", param=None)

    def get_queued(self):
        items = storage.query(storage.WORKITEM, status='queued', config=self._config)

        return items and items.get() or None

    def assign(self, item_id):
        item = storage.WorkItem.get_by_key_name(item_id)
        item.status = 'assigned'
        item.put()

    def complete(self, item_id, result):
        item = storage.WorkItem.get_by_key_name(item_id)
        item.status = 'completed'
        item.put()

        prev_task = self._tasks[item.item_type]
        output = prev_task._output
        prev_name = prev_task._name

        if output == 'single':
            results = [result]
        elif output == 'multi':
            results = result

        for r in results:
            self._create_new_work(prev_task=prev_name, param=r)

    def fail(self, item_id):
        item = storage.WorkItem.get_by_key_name(item_id)
        item.status = 'queued'
        item.put()

    def _create_new_work(self, prev_task, param=None):
        for task in self._tasks.values():
            if task._follow == prev_task:
                self._enqueue_work_item(task, param)

    def _enqueue_work_item(self, task, param=None):
        item_id = str(uuid.uuid4())
        item_type = task._name
        status = 'queued'
        param = pickle.dumps(param)

        storage.add_or_update(storage.WORKITEM, item_id=item_id, config=self._config, item_type=item_type, status=status, param=param)

class Task():
    def __init__(self, name, output, follow, subs):
        self._name = name
        self._output = output
        self._follow = follow
        self._subs = subs

    def run(self, param):
        for subTask in self._subs:
            param = subTask.run(param)

        return param

    @classmethod
    def load_from_node(cls, node):
        attrs = node.attributes
        name = attrs['name'].value
        output = attrs['output'].value
        follow = attrs['follow'].value

        subTasks = []
        for n in node.childNodes:
            if n.nodeType != n.ELEMENT_NODE:
                continue

            task = SubTask.load_from_node(n)
            subTasks.append(task)

        return cls(name, output, follow, subTasks)

class SubTask():
    def __init__(self, module, method, param_name, kargs):
        self._method = getattr(self._load_module(module), method)
        self._param_name = param_name
        self._other_args = kargs

    def run(self, param=None):
        method = self._method
        args = self._other_args

        param_name = self._param_name
        if param_name:
            args[param_name] = param

        for key in args:
            if isinstance(key, unicode):
                value = args.pop(key)
                args[str(key)] = value

        return method(**args)

    def _load_module(self, module_name):
        __import__(module_name)
        return sys.modules[module_name]

    @classmethod
    def load_from_node(cls, node):
        attrs = node.attributes
        module = attrs['module'].value
        method = attrs['method'].value

        try:
            param_name = attrs['param_name'].value
        except KeyError:
            param_name = ''

        key_args = {}
        for n in node.childNodes:
            if n.nodeType != n.ELEMENT_NODE:
                continue

            key, value = domutil.node_text_pair(n)
            key_args[key] = value

        return cls(module, method, param_name, key_args)

def initiate():
    dispatcher = TaskDispatcher('fcc.xml')
    dispatcher.initiate()

def run_one_task():
    executor = TaskExecutor('fcc.xml')
    if executor.execute():
        logging.info('one task executed!')
    else:
        logging.info('no tasks in queue!')

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # initiate()
    run_one_task()
