import nltk.data
import shutil
import data_mining.infoworld as infoworld
import data_mining.developerandeconomics as developerandeconomics
import data_mining.slashdot as slashdot
import pickle
import os
import re


def split_into_sentences(text):
    return nltk.data.load('tokenizers/punkt/english.pickle').tokenize(text)

keywords = list(map(lambda s: s.strip().lower(), open('keywords.csv', 'r').readlines()))


def has_word(s, word):  # todo: parse different forms of words. For example, Apple's
    return re.search(r'\b' + re.escape(word) + r'\b', s, flags=re.IGNORECASE) is not None


def has_keywords(s):
    return len(list(filter(lambda w: has_word(s, w), keywords))) >= 2


TMP_DIR = './tmp'

#nltk.download('punkt')

if os.path.exists(TMP_DIR):
    shutil.rmtree(TMP_DIR)
os.makedirs(TMP_DIR)


for downloader in [developerandeconomics, infoworld, slashdot]:
    try:
        downloader.get_articles(300, TMP_DIR)
    except:
        pass

out = open('test.out', 'w')
sentences = []
for filename in os.listdir(TMP_DIR):
    with open(os.path.join(TMP_DIR, filename), 'rb') as fin:
        sentences += list(filter(has_keywords,
                                 map(lambda s: s.strip(), split_into_sentences(pickle.load(fin).summary))))
        fin.seek(0)
        sentences += list(filter(has_keywords,
                                 map(lambda s: s.strip(), split_into_sentences(pickle.load(fin).text))))
shutil.rmtree(TMP_DIR)

for s in sentences:
    print(s, file=out)
    #parser.parse(s).draw()
