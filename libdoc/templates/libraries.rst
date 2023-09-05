.. first line of libraries.rst template
.. <% merge "properties.Shortcuts" %>
{% set libraries = content.libraries %}
.. <% endmerge %>

.. _libraries:

Library Reference
=================

This is a dictionary of all referenced libraries and their name spaces.

{% for key in libraries if libraries[key]['TopLevelNode'] %}
{% set lib = libraries[key] %}
{% set iname = lib["Name"] %}
{% set name = iname|se %}
{% set icompany = lib["Company"] %}
{{ name }}
{{ '-' * name|count }}

Library Identification
~~~~~~~~~~~~~~~~~~~~~~

{% set placeholder = lib["Placeholder"] %}
{% if placeholder %}
| Placeholder: {{ placeholder }}
| Default Resolution: {{ lib["DefaultResolution"]|se }}
{% else %}
| Name: {{ name }}
{% set version = lib["Version"]|se %}
{% set version = version if version != '*' else '**newest**' %}
| Version: {{ version }}
| Company: {{ icompany|se }}
{% endif %}
{% set namespace = lib["Namespace"] %}
| Namespace: {{ namespace }}

{% set exclude = ('Parameters', 'Namespace', 'Name', 'Placeholder', 'Version', 'Company', 'DefaultResolution', 'ResolverGuid' , 'TopLevelNode')%}
Library Properties
~~~~~~~~~~~~~~~~~~

.. hlist::
    :columns: 3

    {% for info in lib if info not in exclude -%}
        {{ ('* ' ~ info ~ ': ' ~ lib[info])|indent(4, true) }}
    {% endfor %}

{% set parameters = lib["Parameters"] %}
{% if parameters %}
Library Parameter
~~~~~~~~~~~~~~~~~

{% for par in parameters %}
| Parameter: {{ par }} = {{ parameters[par]["Value"] }}

{% endfor %}
{% endif %}
{% endfor %}
.. last line of libraries.rst template
