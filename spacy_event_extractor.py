import os
import pickle
from db.db_handler import DatabaseHandler

from spacy.en import English


class SpacyEventExtractor:
    _nlp = English(entity=False)
    _keywords = list(map(lambda s: s.strip().lower(), open('keywords.txt', 'r').readlines()))

    def __init__(self):
        pass

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
        if prep is None:
            return "", None

        for word in prep.children:
            if word.dep_ == "pobj":
                chunk = SpacyEventExtractor._get_chunk(word, doc)
                return str(prep) + str(chunk), chunk

        return "", None

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

            keywords_set = set(SpacyEventExtractor._keywords)
            if len(set([word.strip().lower() for word in str(token).split()]) & keywords_set) + \
                    len(set(word.strip().lower() for word in subj_string.split()) & keywords_set) == 0:
                continue  # there is no keywords in token and subj_string
            events.append((str(token), str(verb), str(subj_string), str(sentence)))
            print(sentence)
            print('Object: ', token)
            print('Action: ', verb)
            print('Subject: ', subj_string)

        return events


def main():
    import data_mining.infoworld as infoworld
    import data_mining.developerandeconomics as developerandeconomics
    import data_mining.slashdot as slashdot
    import os

    tmp_dir = './tmp'

    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

        for downloader in [developerandeconomics, infoworld, slashdot]:
            for i in range(3):
                try:
                    downloader.get_articles(100, tmp_dir, 100 * i)
                except:
                    import traceback
                    print(traceback.format_exc())
                print('')
    db_handler = DatabaseHandler()
    for filename in os.listdir(tmp_dir):
        with open(os.path.join(tmp_dir, filename), 'rb') as fin:
            article = pickle.load(fin)
            events = SpacyEventExtractor.extract(article.summary)
            events += SpacyEventExtractor.extract(article.text)
            for event in events:
                print(db_handler.add_event_or_get_id(event, article))

if __name__ == '__main__':
    main()
