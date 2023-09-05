.. first line of folder.rst template
.. <% set key = "{{ key }}" %>
.. _`{{ key|replace(':', '.') }}`:
.. <% merge "folder.Title" %>
{% set particle = content.particles[key] %}
{% set iname = particle.name %}
{% set title = iname|fe %}
{% set toc = particle.toc %}

{{ particle.target }}

{{ title }}
{{ '=' * title|count }}

.. <% endmerge %>
.. <% merge "folder.Doc" -%>

{% set doc = particle.doc %}
{% if doc %}
{{ doc }}
{% else %}
.. todo:: Please add documentation for folder: {{ particle.name }}
{% endif %}

.. <%- endmerge %>

{% if toc %}
.. toctree::

{% for t in toc %}
   {{ t }}
{% endfor %}
{% endif %}

.. last line of folder.rst template
