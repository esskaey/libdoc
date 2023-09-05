{% extends "dut-object.rst" %}
{% block header %}
{{ super() }}
.. first line of struct-object.rst template
{% endblock %}
{% block title %}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set prefix = particle.prefix %}
{% if prefix %}
{% set title = name + " (STRUCT; Prefix " + prefix + ")" %}
{% else %}
{% set title = name + " (STRUCT)" %}
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
.. last line of struct-object.rst template
{{ super() }}
{% endblock %}
