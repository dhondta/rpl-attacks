# -*- coding: utf8 -*-
import logging
from markdown2 import markdown_path
from os.path import abspath, exists, join
from weasyprint import HTML


__all__ = [
    'generate_report',
]


# turn off noisy warnings
logging.getLogger('weasyprint').setLevel(100)


def generate_report(path, theme=None):
    """
    This function generates a "report.pdf" from a "report.md" template using markdown2 and weasyprint.

    :param path: path of report.md
    :param theme: full or relative (to "[path]/themes/") path to the CSS theme
    """
    html = HTML(string=markdown_path(join(path, 'report.md')), base_url='file://{}'.format(abspath(path)))
    output = join(path, 'report.pdf')
    theme = join(path, "themes", theme)
    kwargs = {}
    if theme is not None and exists(theme):
        kwargs['stylesheets'] = theme
    html.write_pdf(output, **kwargs)
