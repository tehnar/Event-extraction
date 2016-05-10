from itertools import *

from spacy.en import English

from data_mining import article_downloaders, Article
from db.db_handler import DatabaseHandler
from event import Event


class SpacyEventExtractor:
    _nlp = English()
    _keywords = list(map(lambda s: s.strip().lower(), open('keywords.txt', 'r').readlines()))

    def __init__(self):
        pass

    @staticmethod
    def _get_tree(root, depth, good_token):
        if depth == 0:
            return [root] if good_token(root) else []
        result = []
        for child in filter(good_token, root.lefts):
            result += SpacyEventExtractor._get_tree(child, depth - 1, good_token)
        result.append(root)
        for child in filter(good_token, root.rights):
            result += SpacyEventExtractor._get_tree(child, depth - 1, good_token)
        return result

    @staticmethod
    def _get_chunk(token):
        if token is None:
            return "", None
        return " ".join(map(str, SpacyEventExtractor._get_tree(token, 2,
            lambda tok: tok is token or tok.dep_.endswith("mod") or tok.dep_ == "compound"))), token

    @staticmethod
    def _have_pronouns(text):
        pronouns = ['i', 'you', 'he', 'she', 'they', 'be', 'him', 'her']
        return list(filter(lambda s: s.lower() in pronouns, str(text).split())) != []

    @staticmethod
    def _is_present_simple(verb):
        for child in verb.children:
            if child.orth_ == 'will':
                return False  # will have etc
        lemma = verb.lemma_.lower()
        if verb.orth_.lower() in [lemma, lemma + 's', lemma + 'es', 'have', 'has', 'do']:
            return True
        return False

    @staticmethod
    def _is_present_continuous(verb):
        for child in verb.children:
            if child.dep_ == 'aux' and child.lemma_ not in ['be', 'is', 'are', 'am']:
                return False  # will have etc
        return verb.orth_.endswith('ing')

    @staticmethod
    def _get_prep_with_word(token):
        prep = None
        for child in token.rights:
            if child.dep_ == "prep":
                prep = child
                break
        if prep is None:
            return "", None

        for word in prep.children:
            if word.dep_ in ["pobj", "pcomp"]:
                chunk_str, chunk_head = SpacyEventExtractor._get_chunk(word)
                return str(prep) + chunk_str, chunk_head

        return "", None

    @staticmethod
    def extract(text, replace_we=None):
        text = ' '.join(text.split())  # remove any extra whitespaces
        for aux, replace_with in zip(['ve', 're'], ['have', 'are']):
            text = text.replace("'" + aux, " " + replace_with).replace("’" + aux, " " + replace_with)
            # just because sometimes spaCy fails on sth like we've
        events = []
        text = text.strip()
        if len(text) == 0:
            return []
        text_doc = SpacyEventExtractor._nlp(text)
        sentences = []
        for sentence in text_doc.sents:  # actually we need to split on sentences twice because sometimes spaCy cannot
            #  split correctly a long sentence
            doc = SpacyEventExtractor._nlp(str(sentence))
            sentences += [str(s) for s in doc.sents]
        for sentence in sentences:
            sentence = sentence.strip()
            doc = SpacyEventExtractor._nlp(sentence)

            if len(set([word.string.strip().lower() for word in doc]) & set(SpacyEventExtractor._keywords)) == 0:
                continue

            entity1 = None
            for word in doc:
                if word.head is word:  # main verb
                    for child in word.children:
                        if child.dep_.endswith("nsubj"):
                            entity1 = child
                            break
                    break
            if entity1 is None:
                continue
            verb = entity1.head
            aux_verbs = ""
            for child in verb.children:
                if child.dep_ == "aux" or child.dep_ == "neg":
                    aux_verbs += str(child)

            entity2 = None
            for child in verb.children:
                if child.dep_ == "dobj":
                    entity2 = child
                    break

            if entity2 is None:
                continue

            entity1_string, entity1 = SpacyEventExtractor._get_chunk(entity1)
            entity2_string, entity2 = SpacyEventExtractor._get_chunk(entity2)
            entities = []
            for entity, entity_string in [(entity1, entity1_string), (entity2, entity2_string)]:
                entity = SpacyEventExtractor._get_prep_with_word(entity)
                while entity[1] is not None:
                    entity_string += entity[0]
                    entity = SpacyEventExtractor._get_prep_with_word(entity[1])
                entities.append(entity_string)
            entity1_string, entity2_string = entities
            keywords_set = set(SpacyEventExtractor._keywords)
            if len(set([word.strip().lower() for word in entity1_string.split()]) & keywords_set) + \
                    len(set(word.strip().lower() for word in entity2_string.split()) & keywords_set) == 0:
                continue  # there is no keywords in token and subj_string

            if SpacyEventExtractor._have_pronouns(entity1_string) or SpacyEventExtractor._have_pronouns(entity2_string):
                continue

            if SpacyEventExtractor._is_present_simple(verb) or SpacyEventExtractor._is_present_continuous(verb):
                continue


            entities_strings = []
            for string in [entity1_string, entity2_string]:
                new_string = ""
                for word in string.split():
                    if word == "we" and replace_we is not None:
                        new_string += replace_we + " "
                    elif word == "We" and replace_we is not None:
                        new_string += replace_we.capitalize() + " "
                    else:
                        new_string += str(word) + " "
                entities_strings.append(new_string)
            entity1_string, entity2_string = entities_strings

            events.append(Event(str(entity1_string), str(entity2_string), str(aux_verbs) + str(verb), str(sentence)))

            print(sentence)
            print('Object: ', entity1_string)
            print('Action: ', str(aux_verbs) + str(verb))
            print('Subject: ', entity2_string)
            print("=======")

        return events


def main():
    db_handler = DatabaseHandler()

    #for sent in open('samples.txt', 'r').read  lines():
    #    SpacyEventExtractor.extract(sent)
    #exit()

    #db_handler.clear_db()
    for downloader in article_downloaders:
        cnt = 1
        try:
            for article in islice(downloader.get_articles(), 0, 1600):
                events = SpacyEventExtractor.extract(article.summary, article.site_owner)
                events += SpacyEventExtractor.extract(article.text, article.site_owner)
                events += SpacyEventExtractor.extract(article.header, article.site_owner)

                if db_handler.get_article_id(article) is not None:
                    continue
                for event in events:
                    print(db_handler.add_event_or_get_id(event, article), article.url)
                print(cnt)
                cnt += 1
        except:
            import traceback
            print(traceback.format_exc())

if __name__ == '__main__':
    main()
