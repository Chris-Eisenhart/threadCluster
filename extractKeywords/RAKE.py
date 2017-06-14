#!/usr/bin/env python2.7
# Chris Eisenhart
# Implementation of RAKE - Rapid Automtic Keyword Exraction algorithm
# as described in:
# Rose, S., D. Engel, N. Cramer, and W. Cowley (2010). 
# Automatic keyword extraction from indi-vidual documents. 
# In M. W. Berry and J. Kogan (Eds.), Text Mining: Applications and Theory.unknown: John Wiley and Sons, Ltd.
# The majority of the code here came from; https://github.com/aneesha/RAKE/blob/master/rake.py
import sys
import re
import operator
import argparse

debug = False
test = True

def parseArgs(args):
    """
    Parse the command line arguments.
    """
    parser= argparse.ArgumentParser(description = __doc__)
    parser.add_argument ("inputFile",
    help = " The input file. ",
    type = argparse.FileType("r"))
    parser.add_argument ("outputFile",
    help = " The output file. ",
    type =argparse.FileType("w"))
    if (len(sys.argv) == 1):
        parser.print_help()
        exit(1)
    options = parser.parse_args()
    return options

def is_number(s):
    try:
        float(s) if '.' in s else int(s)
        return True
    except ValueError:
        return False

def split_sentences(text):
    """
    Utility function to return a list of sentences.
    @param text The text that must be split in to sentences.
    """
    sentence_delimiters = re.compile(u'[.!?,;:\t\\\\"\\(\\)\\\'\u2019\u2013]|\\s\\-\\s')
    sentences = sentence_delimiters.split(text)
    return sentences

def separate_words(text, min_word_return_size):
    """
    Utility function to return a list of all words that are have a length greater than a specified number of characters.
    @param text The text that must be split in to words.
    @param min_word_return_size The minimum no of characters a word must have to be included.
    """
    splitter = re.compile('[^a-zA-Z0-9_\\+\\-/]')
    words = []
    for single_word in splitter.split(text):
        current_word = single_word.strip().lower()
        #leave numbers in phrase, but don't count as words, since they tend to invalidate scores of their phrases
        if len(current_word) > min_word_return_size and current_word != '' and not is_number(current_word):
            words.append(current_word)
    return words


def build_stop_word_regex():
    engStopWords = "a about above after again against all am an and any are aren't as at be because " + \
            "been before being below between both but by can't cannot could couldn't did didn't do " + \
            "does doesn't doing don't down during each few for from further had hadn't has hasn't " + \
            "have haven't having he he'd he'll he's her here here's hers herself him himself his how " + \
            " how's i i'd i'll i'm i've if in into is isn't it it's its itself like let's me more " + \
            "most mustn't my myself no nor not of off on once only or other ought our ours ourselves " + \
            "out over own same shan't she she'd she'll she's should shouldn't so some such than that " + \
            "that's the their theirs them themselves then there there's these they they'd they'll " + \
            "they're they've this those through to too under until up very was wasn't we we'd we'll " + \
            "we're we've were weren't what what's when when's where where's which while who who's " + \
            "whom why why's with won't would wouldn't you you'd you'll you're you've your yours yourself " + \
            "yourselves"
    stop_word_list = engStopWords.split()
    stop_word_regex_list = []
    for word in stop_word_list:
        word_regex = r'\b' + word + r'(?![\w-])'  # added look ahead for hyphen
        stop_word_regex_list.append(word_regex)
    stop_word_pattern = re.compile('|'.join(stop_word_regex_list), re.IGNORECASE)
    return stop_word_pattern


def generate_candidate_keywords(sentence_list, stopword_pattern):
    phrase_list = []
    for s in sentence_list:
        tmp = re.sub(stopword_pattern, '|', s.strip())
        phrases = tmp.split("|")
        for phrase in phrases:
            phrase = phrase.strip().lower()
            if phrase != "":
                phrase_list.append(phrase)
    return phrase_list


def calculate_word_scores(phraseList):
    word_frequency = {}
    word_degree = {}
    for phrase in phraseList:
        word_list = separate_words(phrase, 0)
        word_list_length = len(word_list)
        word_list_degree = word_list_length - 1
        #if word_list_degree > 3: word_list_degree = 3 #exp.
        for word in word_list:
            word_frequency.setdefault(word, 0)
            word_frequency[word] += 1
            word_degree.setdefault(word, 0)
            word_degree[word] += word_list_degree  #orig.
            #word_degree[word] += 1/(word_list_length*1.0) #exp.
    for item in word_frequency:
        word_degree[item] = word_degree[item] + word_frequency[item]

    # Calculate Word scores = deg(w)/frew(w)
    word_score = {}
    for item in word_frequency:
        word_score.setdefault(item, 0)
        word_score[item] = word_degree[item] / (word_frequency[item] * 1.0)  #orig.
    #word_score[item] = word_frequency[item]/(word_degree[item] * 1.0) #exp.
    return word_score


def generate_candidate_keyword_scores(phrase_list, word_score):
    keyword_candidates = {}
    for phrase in phrase_list:
        keyword_candidates.setdefault(phrase, 0)
        word_list = separate_words(phrase, 0)
        candidate_score = 0
        for word in word_list:
            candidate_score += word_score[word]
        keyword_candidates[phrase] = candidate_score
    return keyword_candidates


class Rake():
    def __init__(self):
        self.__stop_words_pattern = build_stop_word_regex()

    def run(self, text):
        sentence_list = split_sentences(text)

        phrase_list = generate_candidate_keywords(sentence_list, self.__stop_words_pattern)

        word_scores = calculate_word_scores(phrase_list)

        keyword_candidates = generate_candidate_keyword_scores(phrase_list, word_scores)

        sorted_keywords = sorted(keyword_candidates.iteritems(), key=operator.itemgetter(1), reverse=True)
        return sorted_keywords


def main(args):
    """
    Initialized options and calls other functions.
    """
    options = parseArgs(args)
    text = " ".join(options.inputFile.readlines())

    # Split text into sentences
    #sentenceList = split_sentences(text)
    sentenceList = text.split(".")

    # Some jazz going on right here, make a regular expression pattern to be used
    # later to break apart the string into useful words
    stopwordpattern = build_stop_word_regex()

    # generate candidate keywords
    phraseList = generate_candidate_keywords(sentenceList, stopwordpattern)

    # calculate individual word scores
    wordscores = calculate_word_scores(phraseList)

    # generate candidate keyword scores
    keywordcandidates = generate_candidate_keyword_scores(phraseList, wordscores)

    rake = Rake()
    keywords = rake.run(text)
    for item in keywords:
        string = item[0]
        value = str(item[1])
        options.outputFile.write(string + "\t" + value + "\n")


if __name__ == "__main__" : 
    sys.exit(main(sys.argv))
