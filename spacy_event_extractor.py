import os
import pickle
from db.db_handler import DatabaseHandler
from itertools import *
from data_mining import ArticleDownloader
from spacy.en import English

class SpacyEventExtractor:
    _nlp = English(entity=False, load_vectors=False)
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
        sentences = []
        for sentence in text_doc.sents:
            doc = SpacyEventExtractor._nlp(str(sentence))
            sentences += [str(s) for s in doc.sents]
        for sentence in sentences:
            sentence = sentence.strip()
            doc = SpacyEventExtractor._nlp(sentence)

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
            aux_verbs = ""
            for child in verb.children:
                if child.dep_ == "aux" or child.dep_ == "neg":
                    aux_verbs += str(child)
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
            events.append((str(token), str(aux_verbs) + str(verb), str(subj_string), str(sentence)))
            print(sentence)
            print('Object: ', token)
            print('Action: ', str(aux_verbs) + str(verb))
            print('Subject: ', subj_string)

        return events


def main():
    db_handler = DatabaseHandler()
    db_handler.clear_db()
    for downloader in ArticleDownloader.downloaders:
        try:
            for article in islice(downloader.get_articles(), 0, 200):
                events = SpacyEventExtractor.extract(article.summary)
                events += SpacyEventExtractor.extract(article.text)
                if db_handler.get_article_id(article) is not None:
                    break
                for event in events:
                    print(db_handler.add_event_or_get_id(event, article))
        except:
            import traceback
            print(traceback.format_exc())

if __name__ == '__main__':
    main()
