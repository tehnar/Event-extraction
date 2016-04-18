class Event:
    def __init__(self, entity1, entity2, action, sentence, date=None, location=None, id=None):
        self.entity1 = entity1
        self.entity2 = entity2
        self.action = action
        self.sentence = sentence
        self.date = date
        self.location = location
        self.id = id