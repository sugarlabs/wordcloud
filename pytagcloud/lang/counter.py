# -*- coding: utf-8 -*-
import re
from pytagcloud.lang.stopwords import StopWords
from operator import itemgetter
import logging

def get_tag_counts(text):
    """
    Search tags in a given text. The language detection is based on stop lists.
    This implementation is inspired by https://github.com/jdf/cue.language. Thanks Jonathan Feinberg.
    """
    text = unicode(text, 'UTF-8')
    words = map(lambda x:x.lower(), re.findall(r'\w+', text, re.UNICODE))

    # Workaround because the regex mangled the unicode
    # _PUNCTUATION = u'.,<>;:/?\\\"\'-_+=!@\#$%^&*()'
    # words = text.split()
    # words = map(lambda x:x.lower(), words)
    # words = map(lambda x:unicode(x, 'UTF-8'), words)
    # words = map(lambda x: x.translate(dict.fromkeys(map(ord, _PUNCTUATION))),
    #             words)

    s = StopWords()
    s.load_language(s.guess(words))
    
    counted = {}
    
    for word in words:
        if not s.is_stop_word(word) and len(word) > 1:
            if counted.has_key(word):
                counted[word] += 1
            else: 
                counted[word] = 1
      
    if len(counted.keys()) == 0:
        return None
    else:
        return sorted(counted.iteritems(), key=itemgetter(1), reverse=True)
