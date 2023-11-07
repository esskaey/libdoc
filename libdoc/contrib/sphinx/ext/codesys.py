# -*- coding: utf-8 -*-
"""
    sphinx.ext.codesys
    ~~~~~~~~~~~~~~~~~~

    Allow CoDeSys specific directives and roles to be inserted into your documentation.
    Inclusion of ranges can be switched of by a configuration variable.
    The rangeslist directive collects all ranges of your project and lists
    them along with a backlink to the original location.

    :copyright: Copyright 2012 by the Sphinx Team and 3S-Smart Software Solutions GmbH.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx.locale import _
from sphinx.errors import NoUri
from sphinx.util.nodes import set_source_info
from docutils.parsers.rst import Directive
# from sphinx.util.nodes import make_admonition
from sphinx.domains import Domain
from docutils.parsers.rst import directives
from sphinx import addnodes

class ranges_node(nodes.Admonition, nodes.Element): pass
class rangeslist(nodes.General, nodes.Element): pass

from sphinx.directives import ObjectDescription

class CoDeSysDirective(ObjectDescription):

    def handle_signature(self, sig, signode):
        if sig.find(':') != -1:
            name, returnType = sig.split(' : ', 1)
        else:
            name = sig
        signode.clear()
        signode += addnodes.desc_name(sig, sig)
        return name

    def add_target_and_index(self, name, sig, signode):
            targetname = self.objtype + '-' + name
            if targetname not in self.state.document.ids:
                signode['names'].append(targetname)
                signode['ids'].append(targetname)
                signode['first'] = (not self.names)
                self.state.document.note_explicit_target(signode)
    
                objects = self.env.domaindata['cds']['objects']
                key = (self.objtype, name)
                if key in objects:
                    self.state_machine.reporter.warning(
                        'duplicate description of %s %s, ' % (self.objtype, name) +
                        'other instance in ' + self.env.doc2path(objects[key]),
                        line=self.lineno)
                objects[key] = self.env.docname
            indextext = self.get_index_text(self.objtype, name)
            if indextext:
                self.indexnode['entries'].append(('single', indextext,
                                                  targetname, ''))
    def get_index_text(self, objectname, name):
        if self.objtype == 'fun':
            return _('%s (function)') % name
        elif self.objtype == 'fb':
            return _('%s (function block)') % name
        elif self.objtype == 'enum':
            return _('%s (enum)') % name
        elif self.objtype == 'struct':
            return _('%s (struct)') % name
        elif self.objtype == 'union':
            return _('%s (union)') % name
        elif self.objtype == 'alias':
            return _('%s (alias)') % name
        elif self.objtype == 'gvl':
            return _('%s (global variable list)') % name
        elif self.objtype == 'itf':
            return _('%s (interface)') % name
        elif self.objtype == 'action':
            return _('%s (action)') % name
        elif self.objtype == 'trans':
            return _('%s (transition)') % name
        elif self.objtype == 'meth':
            return _('%s (method)') % name
        elif self.objtype == 'prop':
            return _('%s (property)') % name
        return ''

class PropertyDirective(CoDeSysDirective):
    option_spec = {
        'noindex': directives.flag,
        'readonly': directives.flag,
        'writeonly': directives.flag,
    }

class FunctionDirective(CoDeSysDirective):
    pass

class RangesDirective(Directive):
    """
    A ranges entry, displayed (if configured) in the form of an admonition.
    """

    has_content = True
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        env = self.state.document.settings.env
        targetid = 'index-%s' % env.new_serialno('index')
        targetnode = nodes.target('', '', ids=[targetid])

        # ad = make_admonition(ranges_node, self.name, [_('Ranges')], self.options,
        #                      self.content, self.lineno, self.content_offset,
        #                      self.block_text, self.state, self.state_machine)
        # set_source_info(self, ad[0])
        return [targetnode] # + ad


def process_ranges(app, doctree):
    # collect all ranges in the environment
    # this is not done in the directive itself because some transformations
    # must have already been run, e.g. substitutions
    env = app.builder.env
    if not hasattr(env, 'codesys_all_ranges'):
        env.codesys_all_ranges = []
    for node in doctree.traverse(ranges_node):
        try:
            targetnode = node.parent[node.parent.index(node) - 1]
            if not isinstance(targetnode, nodes.target):
                raise IndexError
        except IndexError:
            targetnode = None
        env.codesys_all_ranges.append({
            'docname': env.docname,
            'source': node.source or env.doc2path(env.docname),
            'lineno': node.line,
            'ranges': node.deepcopy(),
            'target': targetnode,
        })


class RangesListDirective(Directive):
    """
    A list of all ranges entries.
    """

    has_content = False
    required_arguments = 0
    optional_arguments = 0
    final_argument_whitespace = False
    option_spec = {}

    def run(self):
        # Simply insert an empty rangeslist node which will be replaced later
        # when process_ranges_nodes is called
        return [rangeslist('')]


def process_ranges_nodes(app, doctree, fromdocname):
    if not app.config['codesys_include_ranges']:
        for node in doctree.traverse(ranges_node):
            node.parent.remove(node)

    # Replace all rangeslist nodes with a list of the collected ranges.
    # Augment each ranges with a backlink to the original location.
    env = app.builder.env

    if not hasattr(env, 'codesys_all_ranges'):
        env.codesys_all_ranges = []

    for node in doctree.traverse(rangeslist):
        if not app.config['codesys_include_ranges']:
            node.replace_self([])
            continue

        content = []

        for ranges_info in env.codesys_all_ranges:
            para = nodes.paragraph(classes=['ranges-source'])
            description = _('(The <<original entry>> is located in '
                            ' %s, line %d.)') % \
                          (ranges_info['source'], ranges_info['lineno'])
            desc1 = description[:description.find('<<')]
            desc2 = description[description.find('>>')+2:]
            para += nodes.Text(desc1, desc1)

            # Create a reference
            newnode = nodes.reference('', '', internal=True)
            innernode = nodes.emphasis(_('original entry'), _('original entry'))
            try:
                newnode['refuri'] = app.builder.get_relative_uri(
                    fromdocname, ranges_info['docname'])
                newnode['refuri'] += '#' + ranges_info['target']['refid']
            except NoUri:
                # ignore if no URI can be determined, e.g. for LaTeX output
                pass
            newnode.append(innernode)
            para += newnode
            para += nodes.Text(desc2, desc2)

            # (Recursively) resolve references in the ranges content
            ranges_entry = ranges_info['ranges']
            env.resolve_references(ranges_entry, ranges_info['docname'], app.builder)

            # Insert into the rangeslist
            content.append(ranges_entry)
            content.append(para)

        node.replace_self(content)


def purge_ranges(app, env, docname):
    if not hasattr(env, 'codesys_all_ranges'):
        return
    env.codesys_all_ranges = [ranges for ranges in env.codesys_all_ranges
                          if ranges['docname'] != docname]


def visit_ranges_node(self, node):
    self.visit_admonition(node)

def depart_ranges_node(self, node):
    self.depart_admonition(node)

class CoDeSysDomain(Domain):
    """CoDeSys domain."""
    name = 'cds'
    label = 'CoDeSys'

    object_types = {
    }
    
    directives = {
        'ranges': RangesDirective,
        'rangeslist': RangesListDirective,
        'gvl' : CoDeSysDirective,
        'fun' : FunctionDirective,
        'fb' : CoDeSysDirective,
        'itf' : CoDeSysDirective,
        'meth' : CoDeSysDirective,
        'prop' : PropertyDirective,
        'enum' : CoDeSysDirective,
        'struct' : CoDeSysDirective,
        'union' : CoDeSysDirective,
        'alias' : CoDeSysDirective,
        'trans' : CoDeSysDirective,
        'action' : CoDeSysDirective,
    }
    
    roles = {
    }
    
    initial_data = {
        'objects': {},  # fullname -> docname, objtype
    }

def setup(app):
    app.add_config_value('codesys_include_ranges', False, 'env')
    app.add_domain(CoDeSysDomain)

    app.add_node(rangeslist)
    app.add_node(ranges_node,
                 html=(visit_ranges_node, depart_ranges_node),
                 latex=(visit_ranges_node, depart_ranges_node),
                 text=(visit_ranges_node, depart_ranges_node),
                 man=(visit_ranges_node, depart_ranges_node),
                 texinfo=(visit_ranges_node, depart_ranges_node))

    app.add_directive('ranges', RangesDirective)
    app.add_directive('rangeslist', RangesListDirective)
    app.connect('doctree-read', process_ranges)
    app.connect('doctree-resolved', process_ranges_nodes)
    app.connect('env-purge-doc', purge_ranges)
