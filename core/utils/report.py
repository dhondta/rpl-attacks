# -*- coding: utf8 -*-
import logging
import codecs
from markdown import markdown
from os.path import abspath, exists, join
from weasyprint import HTML


__all__ = [
    'generate_report',
]


# turn off noisy warnings
logging.getLogger('weasyprint').setLevel(100)


def generate_report(path, theme=None, intype='md'):
    """
    This function generates a "report.pdf" from a "report.[md|html]" template using weasyprint.

    :param path: path of report.[md|html]
    :param theme: full or relative (to "[path]/themes/") path to the CSS theme
    :param intype: input format
    """
    assert intype in ['html', 'md']
    if intype == 'md':
        input_file = codecs.open(join(path, 'report.md'), mode="r", encoding="utf-8")
        text = input_file.read()
        html = markdown(text)
    else:
        html = open(join(path, 'report.html')).read()
    html = HTML(string=html, base_url='file://{}/'.format(abspath(path)))
    output = join(path, 'report.pdf')
    kwargs = {}
    if theme is not None:
        theme = join(path, "themes", theme)
        if exists(theme):
            kwargs['stylesheets'] = [theme]
    html.write_pdf(output, **kwargs)
