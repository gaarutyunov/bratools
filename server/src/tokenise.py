#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Tokenisation using external software.

Author:     Pontus Stenetorp <pontus stenetorp se>
Version:    2011-05-23
'''

from os.path import join as path_join
from os.path import dirname
from subprocess import Popen, PIPE
from shlex import split as shlex_split

### Constants
GTB_TOKENIZE_PL_PATH = path_join(dirname(__file__), '../../external/',
        'GTB-tokenize.pl')
###

def _token_boundaries_by_alignment(tokens, original_text):
    curr_pos = 0
    for tok in tokens:
        start_pos = original_text.index(tok, curr_pos)
        # TODO: Check if we fail to find the token!
        end_pos = start_pos + len(tok)
        yield (start_pos, end_pos)
        curr_pos = end_pos

def jp_token_boundary_gen(text):
    from mecab import token_offsets_gen
    for o in token_offsets_gen(text):
        yield o
       
def en_token_boundary_gen(text):
    # Call the external script
    tok_p = Popen(shlex_split(GTB_TOKENIZE_PL_PATH), stdin=PIPE,
            stdout=PIPE, stderr=PIPE)

    tok_p.stdin.write(text.encode('utf-8'))
    tok_p.stdin.close()
    tok_p.wait()
    output, errors = (tok_p.stdout.read().decode('utf-8'),
            tok_p.stderr.read().decode('utf-8'))
    #output, errors = tok_p.communicate(text)

    # TODO: Check errors!

    # Decode our output, we assume utf-8 as this is our internal format
    #output = output.decode('utf-8')

    # Then align the now tokenised data to get the offsets
    tokens = output.split()
    for o in _token_boundaries_by_alignment(tokens, text):
        yield o

if __name__ == '__main__':
    from sys import argv

    from annotation import open_textfile

    def _text_by_offsets_gen(text, offsets):
        for start, end in offsets:
            yield text[start:end]

    try:
        for txt_file_path in argv[1:]:
            print
            print '### Tokenising:', txt_file_path
            with open_textfile(txt_file_path, 'r') as txt_file:
                text = txt_file.read()
            print '# Original text:'
            print text.replace('\n', '\\n')
            offsets = [o for o in jp_token_boundary_gen(text)]
            print '# Offsets:'
            print offsets
            print '# Tokens:'
            for tok in _text_by_offsets_gen(text, offsets):
                assert tok, 'blank tokens disallowed'
                assert not tok[0].isspace() and not tok[-1].isspace(), (
                        'tokens may not start or end with white-space "%s"' % tok)
                print '"%s"' % tok
    except IOError:
        pass # Most likely a broken pipe