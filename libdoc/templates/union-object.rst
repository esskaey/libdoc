{% extends "dut-object.rst" %}
{% block header %}
{{ super() }}
.. first line of union-object.rst template
{% endblock %}
{% block title %}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set prefix = particle.prefix %}
{% if prefix %}
{% set title = name + " (UNION; Prefix " + prefix + ")" %}
{% else %}
{% set title = name + " (UNION)" %}
{% endif %}

.. Index::
   single: {{ iname }}

{{ particle.target }}

{{ title }}
{{ '-' * title|count }}
{% endblock %}
{% block declaration %}

{{ particle.declaration }}
{% endblock %}
{% block footer %}
.. last line of union-object.rst template
{{ super() }}
{% endblock %}
