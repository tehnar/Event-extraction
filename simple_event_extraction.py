import utils as Utils
from functools import reduce

#data = "Google has released Android Wear for iOS, allowing Android Wear users to pair their wearables with iPh."

data = "The Visual Studio Code lightweight editor now supports Apache Cordova, Microsoft has announced."
main_word = "Visual"

parser = Utils.Parser()
tree = parser.parse(data)
Utils.modify_tree(tree, None)

object = Utils.find_node_by_word(tree, main_word)
object = Utils.find_first_node(object, lambda x : x == "NP")

nodeVP = Utils.find_first_node(object, lambda x : x == "VP")
patterns = ["VB", "VBD", "VBG", "VBN", "VBZ"]

action = []
verbs = filter(lambda x : x._label in patterns, Utils.get_childs(nodeVP))
for word in verbs:
    action += Utils.get_words(word)

subjNode = Utils.find_first_node(nodeVP, lambda x : x == "NP")
subject = Utils.get_words(subjNode)

print ("Object:  " + ' '.join(Utils.get_words(object)))
print ("Action:  " + ' '.join(action))
print ("Subject: " + ' '.join(subject))

