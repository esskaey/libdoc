{% extends "dut-object.rst" %}
{% block header %}
{{ super() }}
.. first line of enum-object.rst template
{% endblock %}
{% block title %}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set title = name + " (ENUM)" %}

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
.. last line of enum-object.rst template
{{ super() }}
{% endblock %}
