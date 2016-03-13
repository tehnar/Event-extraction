from stat_parser import Parser
from nltk.tree import Tree
from functools import reduce

def modify_tree(node, parent):
    node.parent = parent

    #map(lambda x : modify_tree(x, node), get_childs(node))

    for child in node:
        if isinstance(child, Tree):
            modify_tree(child, node)

def print_tree(node):
    for child in node:
        if isinstance(child, Tree):
            print_tree(child)
        else:
            print(child, end=' ')

def get_words(node):
    if not isinstance(node, Tree):
        return [node]
    return reduce(lambda x, y: x + get_words(y), node, [])

def find_node_by_word(node, word):
    if len(list(filter(lambda x : x == word, node))) > 0:
        return node

    data = map(lambda x : find_node_by_word(x, word), get_childs(node))
    return next((item for item in data if item is not None), None)

def get_childs(node):
    return list(filter(lambda x : isinstance(x, Tree), node))

def find_first_node(node, p, after = None):
    if not isinstance(node, Tree):
        return None

    if p(node._label) == True:
        return node

    found = after is None
    childs = []
    for child in get_childs(node):
        if found == True:
            childs.append(child)
        if child == after:
            found = True

    results = map(lambda x : find_first_node(x, p), childs)
    result = next((item for item in results if item is not None), None)

    if result is None:
        if node.parent is not None:
            return find_first_node(node.parent, p, node)

    return result