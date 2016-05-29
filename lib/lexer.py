# -*- coding: utf-8 -*-
from pygments.lexer import RegexLexer, bygroups, using
from pygments.token import Error, Keyword, Name, Number, Operator, String, Whitespace


class ValueLexer(RegexLexer):
    tokens = {
        'root': [
            ('"', String, 'string'),
            (r'([0-9]+)', Number),
            (r'(false|true)', Keyword),
            (r'([a-zA-Z0-9-_=\/\\\<\>\.]+)', String),
        ],
        'string': [
            (r'[^"\\]+', String),
            (r'\\.', String.Escape),
            ('"', String, '#pop'),
        ],
    }


class ArgumentsLexer(RegexLexer):
    tokens = {
        'root': [
            (r'\s+', Whitespace),
            (r'([a-zA-Z]|[a-zA-Z][a-zA-Z0-9-_]*[a-zA-Z0-9])(=)(.+?)(\s+)', bygroups(Name, Operator, using(ValueLexer), Whitespace), 'kwargs'),
            (r'(.+?)(\s+)', bygroups(using(ValueLexer), Whitespace), '#push'),
        ],
        'kwargs': [
            (r'\s+', Whitespace),
            (r'([a-zA-Z]|[a-zA-Z][a-zA-Z0-9-_]*[a-zA-Z0-9])(=)(.+?)(\s+)', bygroups(Name, Operator, using(ValueLexer), Whitespace)),
        ],
    }

    def analyze(self, text):
        if any([token is Error for token, value in self.get_tokens(text)]):
            return 2 * (None, )
        tokens, args, kwargs = self.get_tokens(text), [], {}
        for token, value in tokens:
            if token in (Keyword, Number, String):
                args.append(value)
            if token is Name:
                next(tokens)  # pass the Operator '='
                kwargs.update({value: next(tokens)[1]})
        return args, kwargs
