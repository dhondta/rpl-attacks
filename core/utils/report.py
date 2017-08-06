# -*- coding: utf8 -*-
import logging
from markdown2 import markdown_path
from os.path import exists, join
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
    """
    html = markdown_path(join(path, 'report.md'))
    assert exists(html)
    output = join(path, 'report.pdf')
    assert exists(output)
    html = HTML(string=html)
    if theme is None:
        html.write_pdf(output)
    else:
        theme = join(path, "themes", theme)
        assert exists(theme)
        html.write_pdf(output, stylesheets=[theme])
