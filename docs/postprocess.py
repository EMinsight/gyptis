#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.0.2
# License: MIT
# See the documentation at gyptis.gitlab.io
"""
%prog MODE FILES...

Post-processes HTML and Latex files output by Sphinx.
MODE is either 'html' or 'tex'.

"""
from __future__ import absolute_import, division, print_function

import io
import optparse
import re

from bs4 import BeautifulSoup

import gyptis as package


def main():
    p = optparse.OptionParser(__doc__)
    options, args = p.parse_args()

    if len(args) < 1:
        p.error("no mode given")

    mode = args.pop(0)

    if mode not in ("html", "tex"):
        p.error(f"unknown mode {mode}")

    for fn in args:
        f = io.open(fn, "r", encoding="utf-8")
        try:
            if mode == "html":
                lines = process_html(fn, f.readlines())
            elif mode == "tex":
                lines = process_tex(f.readlines())
        finally:
            f.close()

        f = io.open(fn, "w", encoding="utf-8")
        f.write("".join(lines))
        f.close()

        # try:
        #     if mode == "html":
        #         postpro_download_links(fn)
        # finally:
        #     pass


def postpro_download_links(fn):
    sgfoot = None
    with open(fn, "r") as file:
        soup = BeautifulSoup(file, "html.parser")
    for item in soup.findAll(["div"]):
        if item.get("class") is not None and "sphx-glr-footer" in item.get("class"):
            sgfoot = item

    if sgfoot is not None:
        for item in soup.findAll(["div"]):
            if item.get("class") is not None and "d-none" in item.get("class"):
                item.insert(0, sgfoot)
    with open(fn, "w") as file:
        file.write(str(soup))


def process_html(fn, lines):
    new_lines = []
    for line in lines:
        # Remove escaped arguments from the html files.
        line = line.replace(r"\*args", "*args")
        line = line.replace(r"\*\*kwargs", "**kwargs")
        line = line.replace("col-md-3", "col-md-2")

        line = line.replace(
            "<title> &#8212; __WEBPAGE_TITLE_PLACEHOLDER__</title>",
            f"<title>Gyptis: {package.__description__}</title>",
        )

        line = line.replace(
            "__WEBPAGE_TITLE_PLACEHOLDER__",
            f"Gyptis",
        )

        line = line.replace(". URL: ", ".")
        if line.startswith("<dd><p>") and line.endswith("</a>.</p>\n"):
            line = line.replace("</a>.</p>", "</a></p>")

        line = line.replace(
            "<h3>This Page</h3>",
            "",
        )

        line = line.replace(
            "https://mybinder.org/v2/gh/gyptis/gyptis.gitlab.io",
            "https://mybinder.org/v2/gl/gyptis%2Fgyptis.gitlab.io",
        )

        line = line.replace(
            "https://mybinder.org/v2/gl/gyptis%2Fgyptis.gitlab.io/doc?filepath=notebooks/examples/",
            "https://mybinder.org/v2/gl/gyptis%2Fgyptis.gitlab.io/doc?filepath=notebooks/",
        )

        first_tag = "binder_badge_logo"
        second_tag = ".svg"
        reg = f"(?<={first_tag}).*?(?={second_tag})"
        line = re.sub(reg, "", line, flags=re.DOTALL)

        line = line.replace(
            'binder" src="../../_images/binder_badge_logo.svg" width="150px"',
            'binder" src="../../_images/binder_badge_logo.svg" width="200px"',
        )

        line = line.replace(
            '<span class="pre">notebooks:</span>',
            '<span class="pre">notebooks</span>',
        )

        line = line.replace(
            '<span class="pre">examples_jupyter.zip</span>',
            "",
        )

        new_binder_badge = "https://img.shields.io/badge/run-online-45957d.svg?style=for-the-badge&logo=data:image/png;base64,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"
        line = line.replace(
            "../../_images/binder_badge_logo.svg",
            new_binder_badge,
        )

        icon_python = '<i class="icondld icon-python"></i>'
        icon_jupyter = '<i class="icondld icon-jupyter"></i>'

        first_tag = '<span class="pre">Download</span> <span class="pre">Python</span> <span class="pre">source</span> <span class="pre">code'
        second_tag = "</span></code></a></p>"
        reg = f"(?<={first_tag}).*?(?={second_tag})"

        line = re.sub(reg, "", line, flags=re.DOTALL)
        if icon_python not in line:
            line = line.replace(
                first_tag,
                icon_python
                + '<span class="pre">Download</span> <span class="pre">Python</span> <span class="pre">script',
            )

        first_tag = '<span class="pre">Download</span> <span class="pre">Jupyter</span> <span class="pre">notebook'
        reg = f"(?<={first_tag}).*?(?={second_tag})"
        line = re.sub(reg, "", line, flags=re.DOTALL)
        # if icon_jupyter in line:
        if icon_jupyter not in line:
            line = line.replace(first_tag, icon_jupyter + first_tag)

        first_tag = '<span class="pre">Download</span> <span class="pre">all</span> <span class="pre">examples</span> <span class="pre">in</span> <span class="pre">Python</span> <span class="pre">source</span> <span class="pre">code'
        second_tag = "</span></code></a></p>"
        reg = f"(?<={first_tag}).*?(?={second_tag})"
        line = re.sub(reg, "", line, flags=re.DOTALL)
        if icon_python not in line:
            line = line.replace(first_tag, icon_python + first_tag)

        first_tag = '<span class="pre">Download</span> <span class="pre">all</span> <span class="pre">examples</span> <span class="pre">in</span> <span class="pre">Jupyter</span> <span class="pre">notebooks'
        reg = f"(?<={first_tag}).*?(?={second_tag})"
        line = re.sub(reg, "", line, flags=re.DOTALL)
        if icon_jupyter not in line:
            line = line.replace(first_tag, icon_jupyter + first_tag)

        new_lines.append(line)
    return new_lines


def process_tex(lines):
    """
    Remove unnecessary section titles from the LaTeX file.

    """
    return [
        line
        for line in lines
        if not line.startswith(r"\section{gyptis.")
        and not line.startswith(r"\subsection{gyptis.")
        and not line.startswith(r"\subsubsection{gyptis.")
        and not line.startswith(r"\paragraph{gyptis.")
        and not line.startswith(r"\subparagraph{gyptis.")
    ]


if __name__ == "__main__":
    main()
