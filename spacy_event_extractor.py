import os
import pickle
from spacy.en import English
from spacy.tokens import Span
 
 
class SpacyEventExtractor:
    _nlp = English(entity=False)
    _keywords = list(map(lambda s : s.strip().lower(), open('keywords.txt', 'r').readlines()))
 
 
    @staticmethod
    def _get_chunk(token, doc):
        for chunk in doc.noun_chunks:
            if token in chunk:
                return chunk
        return token
 
 
    @staticmethod
    def get_prep_with_word(childs, doc):
        prep = None
        for child in childs:
            if child.dep_ == "prep":
                prep = child
                break
        if prep == None:
            return ("", None)
 
        for word in prep.children:
            if word.dep_ == "pobj":
                chunk = SpacyEventExtractor._get_chunk(word, doc)
                return (str(prep) + str(chunk), chunk)
 
        return ("", None)
 
 
    @staticmethod
    def extract(text):
        events = []
        text = text.strip()
        if len(text) == 0:
            return []
        text_doc = SpacyEventExtractor._nlp(text, tag=False, parse=True, entity=False)
        for sentence in text_doc.sents:
            doc = SpacyEventExtractor._nlp(str(sentence))
            if len(set([word.string.strip().lower() for word in doc]) & set(SpacyEventExtractor._keywords)) == 0:
                continue
            token = None
            for word in doc:
                if word.head is word:  # main verb
                    for child in word.children:
                        if child.dep_[:5] == "nsubj":
                            token = child
                            break
                    break
            if token is None:
                continue
            verb = token.head
            subj = None
            for child in verb.children:
                if child.dep_ == "dobj":
                    subj = child
                    break
            if subj is None:
                continue
 
            token = SpacyEventExtractor._get_chunk(token, doc)
            subj = SpacyEventExtractor._get_chunk(subj, doc)
 
            subj_string = str(subj) + " "
            subj = SpacyEventExtractor.get_prep_with_word(subj.rights, doc)
            while subj[1] is not None:
                subj_string += subj[0]
                subj = SpacyEventExtractor.get_prep_with_word(subj[1].rights, doc)
            if len(set([word.strip().lower() for word in str(token).split()]) & set(SpacyEventExtractor._keywords))  + len(set(word.strip().lower() for word in subj_string.split()) & set(SpacyEventExtractor._keywords)) == 0:
                    continue
            events += (str(token), str(verb), str(subj_string))
            #print(sentence)
            #print('Object: ', token)
            #print('Action: ', verb)
            #print('Subject: ', subj_string)

        return events

def main():
    TMP_DIR = './tmp'

    for filename in os.listdir(TMP_DIR):
        with open(os.path.join(TMP_DIR, filename), 'rb') as fin:
            events = SpacyEventExtractor.extract(pickle.load(fin).summary)
            fin.seek(0)
            events += SpacyEventExtractor.extract(pickle.load(fin).text)

if __name__ == '__main__':
    main()
