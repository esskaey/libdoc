{% block header %}
.. first line of object.rst template
{%- endblock %}
.. <% set key = "{{ key }}" %>
.. _`{{ key|replace(':', '.') }}`:
.. <% merge "object.Defines" %>
{% set particle = content.particles[key] %}
.. <% endmerge  %>

{% block context %}{% endblock %}
{% block index %}{% endblock %}
{% block title %}{% endblock %}
{% block declaration %}{% endblock %}
{% block doc %}
.. <% merge "object.Doc" %>
{% set doc = particle.doc %}

{% if doc %}
{{ doc }}
{% else %}
.. todo:: Please add documentation for {{ particle.type|lower }}: {{ particle.name }}
{% endif %}

.. <% endmerge  %>
{% endblock %}

{% block iotbl %}{% endblock %}

{% block toc %}
{% set toc = particle.toc %}
{% if toc %}

.. toctree::

{% for t in toc %}
   {{ t }}
{% endfor %}

{% endif %}
{% endblock %}
{% block footer %}
.. last line of object.rst template
{% endblock %}
