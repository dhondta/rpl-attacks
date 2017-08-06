# -*- coding: utf8 -*-
import logging
import markdown2pdf
from os.path import join


__all__ = [
    'generate_report',
]


# turn off noisy warnings
logging.getLogger('weasyprint').setLevel(100)


def generate_report(path, theme=None):
    """
    This function generates a "report.pdf" from a "report.md" template using markdown2pdf.

    :param path: path where report.md is
    """
    markdown2pdf.convert_md_2_pdf(join(path, 'report.md'), join(path, 'report.pdf'), theme)
