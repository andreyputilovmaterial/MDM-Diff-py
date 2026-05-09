
"""
Utilities for efficient text diffing.

This module provides text-oriented diff helpers built on top of
difflib.SequenceMatcher.

Unlike raw character-based SequenceMatcher usage, TextSequenceMatcher
performs matching hierarchically:

1. Text is first compared at line level.
2. Changed regions are refined using word-level matching.
3. Original whitespace and formatting are preserved in the resulting
   opcodes.

This approach is significantly faster and produces more readable diffs
for large text inputs.
"""


import re
from itertools import groupby

from difflib import SequenceMatcher




def as_text(input):
    return ''.join([s[1] for s in input])

def text_split_words(s):
    """Splits continuous text into pieces, separated with "word boundaries" """
    class Splitter:
        def __init__(self,data):
            self.data = data
            self.delimiter = r"(?:\w*?_|\w+|\s+|.)"
            
        def __iter__(self):
            delimiters = re.finditer(self.delimiter,self.data,flags=re.M|re.DOTALL|re.I)
            delimiters = [ delim.start(0) for delim in delimiters ]
            parts = []
            start = 0
            for delim in delimiters:
                pos = delim
                parts.append(self.data[start:pos])
                start = pos
            parts.append(self.data[start:])
            return iter(parts)
    return [a for a in Splitter(s)]

def textwithroles_split_words(input):
    """Splits continuous text into pieces, separated with "word boundaries" """
    text = as_text(input)
    chunks = text_split_words(text)
    cursor = 0
    for chunk in chunks:
        chunk_len = len(chunk)
        yield input[cursor:cursor+chunk_len]
        cursor += chunk_len
    assert cursor == len(text), 'textwithroles_split_lines: last piece is missed'

def textwithroles_split_lines(input):
    """Splits continuous text into pieces, separated with newline characters"""
    text = as_text(input)
    chunks = text.splitlines(keepends=True)
    cursor = 0
    for chunk in chunks:
        chunk_len = len(chunk)
        yield input[cursor:cursor+chunk_len]
        cursor += chunk_len
    assert cursor == len(text), 'textwithroles_split_lines: last piece is missed'


class TextWithRolesSequenceMatcher:
    """
    A text-oriented sequence matcher optimized for large multi-line inputs.

    The matcher performs an initial diff on normalized lines and then
    refines modified regions using word-level matching.

    The public interface intentionally mirrors the small subset of
    difflib.SequenceMatcher used by the application.
    """

    def __init__(self, skip, input_left: list[tuple[str,str]], input_right: list[tuple[str,str]]):
        """
        Initialize a matcher for two text inputs.
        """
        assert skip is None, f'TextWithRolesSequenceMatcher: skip=None is the only supported'
        self.skip = skip
        self.input_left = input_left
        self.input_right = input_right
        self.input_lines_left = [ line for line in textwithroles_split_lines(input_left) ]
        self.input_lines_right = [ line for line in textwithroles_split_lines(input_right) ]
        self.input_lines_norm_left = [ as_text(line).strip() for line in self.input_lines_left ]
        self.input_lines_norm_right = [ as_text(line).strip() for line in self.input_lines_right ]
        self.sm_as_lines = SequenceMatcher(self.skip,self.input_lines_norm_left,self.input_lines_norm_right)

    def get_opcodes(self):
        """
        Return diff opcodes describing the transformation from left to right.

        The returned opcodes follow the same structure as
        difflib.SequenceMatcher.get_opcodes():

            (tag, i1, i2, j1, j2)

        Unlike plain SequenceMatcher, matching is performed hierarchically
        using line-level and word-level comparison to improve performance
        and diff readability for large texts.
        """
        cursor_left = 0
        cursor_right = 0
        for line_tag, line_i1, line_i2, line_j1, line_j2 in self.sm_as_lines.get_opcodes():
            compared_left = [ char for line in self.input_lines_left[line_i1:line_i2] for char in line ]
            compared_right = [ char for line in self.input_lines_right[line_j1:line_j2] for char in line ]
            sm = SequenceMatcher(self.skip,compared_left,compared_right)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                yield (tag, cursor_left+i1, cursor_left+i2, cursor_right+j1, cursor_right+j2)
            cursor_left += len(compared_left)
            cursor_right += len(compared_right)
        
    @property
    def left_as_text(self):
        return ''.join([char for (role,char) in self.input_left])

    @property
    def right_as_text(self):
        return ''.join([char for (role,char) in self.input_right])

    @property
    def left_as_textwithroles(self):
        return [
            (role, ''.join(payload for _, payload in group))
            for role, group in groupby(self.input_left, key=lambda x: x[0])
        ]

    @property
    def right_as_textwithroles(self):
        return [
            (role, ''.join(payload for _, payload in group))
            for role, group in groupby(self.input_right, key=lambda x: x[0])
        ]

