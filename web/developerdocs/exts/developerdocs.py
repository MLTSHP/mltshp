import shutil

import docutils.nodes
from sphinx import addnodes
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.util import ws_re
from sphinx.util.console import bold
from sphinx.util.docfields import GroupedField


class JustHTMLBuilder(StandaloneHTMLBuilder):

    """
    Builds only the pages of a set of HTML docs.
    """

    name = 'justhtml'
    copysource = False

    def finish(self):
        pass


def remove_doctreedir(app, exception):
    shutil.rmtree(app.doctreedir)


def setup(app):
    app.add_builder(JustHTMLBuilder)
    app.connect('build-finished', remove_doctreedir)

    def entity_parse_node(env, sig, signode):
        signode += docutils.nodes.strong(sig, sig)
        return ws_re.sub('', sig)
    entity_doc_field_types = [
        GroupedField('contents', label='Contents', names=('contents', 'key')),
    ]
    app.add_object_type('entity', 'entity', ref_nodeclass=docutils.nodes.emphasis,
        parse_node=entity_parse_node, doc_field_types=entity_doc_field_types)
