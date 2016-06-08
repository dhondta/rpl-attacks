# -*- coding: utf-8 -*-
"""
Source: https://bugs.python.org/issue17337
Other reference: http://stackoverflow.com/questions/9468435/look-how-to-fix-column-calculation-in
                          -python-readline-if-use-color-prompt
"""


def surround_ansi_escapes(prompt, start="\x01", end="\x02"):
    """
    This function allows to preprocess console's colored prompt in order to avoid incorrect prompt length
     calculation by raw_input|input.
    """
    escaped = False
    result = ""
    for c in prompt:
        if c == "\x1b" and not escaped:
            result += start + c
            escaped = True
        elif c.isalpha() and escaped:
            result += c + end
            escaped = False
        else:
            result += c
    return result
