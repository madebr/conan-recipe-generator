# Jinja2 extensions
# Copyright (C) 2020 Anonymous Maarten
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import re

from jinja2 import nodes
from jinja2.ext import Extension


class ConditionalIndentationExtension(Extension):
    # a set of names that trigger the extension.
    tags = {"cond_indent"}

    def __init__(self, environment):
        super().__init__(environment)

    def parse(self, parser):
        # the first token is the conditionaltoken that started the tag.  In our case
        # we only listen to ``'cache'`` so this will be a name token with
        # `cache` as value.  We get the line number so that we can give
        # that line number to the nodes we create by hand.
        lineno = next(parser.stream).lineno

        args = [
            # 1st argument is the conditional:
            parser.parse_expression(),
            # 2nd argument is the line before the indentation.
            parser.parse_expression(),
        ]

        # now we parse the body of the cache block up to `end_cond_indent` and
        # drop the needle (which would always be `end_cond_indent` in that case)
        body = parser.parse_statements(["name:end_cond_indent"], drop_needle=True)

        # now return a `CallBlock` node that calls our _cache_support
        # helper method on this extension.
        return nodes.CallBlock(
            self.call_method("_increase_indentation", args), [], [], body
        ).set_lineno(lineno)

    def _increase_indentation(self, cond, line, caller):
        """Helper callback."""
        rv = caller()
        if cond:
            m = re.match("^\n?([ \t]*).*", rv)
            if not m:
                raise RuntimeError("Cannot find initial whitespace")
            rv = "\n" + m.group(1) + line + rv.replace("\n", "\n    ")
        return rv
