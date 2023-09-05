.. first line of index.rst template
.. <% set key = "{{ key }}" %>
.. <% merge "index.Shortcuts" %>
{% set contentInfo = content.info %}
{% set particle = content.particles[key] %}
{% set toc = particle.toc %}
{% set title = contentInfo.Title ~ " Library Documentation" %}
{% set title_len = title|count %}
.. <% endmerge %>

.. <% merge "index.Title" -%>
.. _index:

{{ '=' * title_len }}
{{ title }}
{{ '=' * title_len }}

.. <%- endmerge %>

.. <% merge "index.ProjectInfo" -%>

:Company: {{  contentInfo.Company }}
:Title: {{ contentInfo.Title }}
:Version: {{ contentInfo.Version }}
{% if contentInfo.LibraryCategories %}
:Categories: {{ contentInfo.LibraryCategories }}
{% endif %}
{% if contentInfo.DefaultNamespace %}
:Namespace: {{ contentInfo.DefaultNamespace }}
{% endif %}
:Author: {{ contentInfo.Author }}
{% if contentInfo.Placeholder %}
:Placeholder: {{ contentInfo.Placeholder }}
{% endif %}

.. <%- endmerge %>

.. _index_description:

Description [1]_
----------------

.. <% merge "index.Description" -%>

{% set doc = particle.doc %}
{% if doc %}
{{ doc }}
{% endif %}

.. <%- endmerge %>

{% if toc %}
Contents:
---------

.. toctree::
   :maxdepth: 2

{% for t in toc %}
   {{ t }}
{% endfor %}
{% endif %}

Indices and tables
------------------

{% set todo = content.config["todo_include_todos"] %}
.. toctree::
   :hidden:

{% if todo %}
   todo
{% endif %}
   info
   libraries

.. only:: libdoc_html

    * :ref:`genindex`
    * :ref:`search`
    {% if todo %}
    * :ref:`todo`
    {% endif %}
    * :ref:`info`
    * :ref:`libraries`

.. only:: libdoc_chm

    {% if todo %}
    * :ref:`todo`
    {% endif %}
    * :ref:`info`
    * :ref:`libraries`

.. only:: libdoc_lmd

    {% if todo %}
    * :ref:`todo`
    {% endif %}
    * :ref:`info`
    * :ref:`libraries`

.. <% merge "index.SourceRelation" %>
.. [1] | Based on {{ contentInfo.libraryFile }}, last modified {{ contentInfo.LastModificationDateTime }}.
       | The content file {{ contentInfo.contentFile }} was generated with {{ contentInfo.productProfile }} on {{ contentInfo.creationDateTime }}
.. <% endmerge %>
.. last line of index.rst template
