# encoding=utf-8

def node_text(node):
    return str(node.childNodes[0].data)

def node_text_pair(node):
    return node.nodeName, node.childNodes[0].data
