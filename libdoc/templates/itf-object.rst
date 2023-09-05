{% extends "object.rst" %}
{% block header %}
{{ super() }}
.. first line of itf-object.rst template
{% endblock %}
{% block title %}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set title = name + " (ITF)" %}

.. Index::
   single: {{ iname }}

{{ particle.target }}

{{ title }}
{{ '-' * title|count }}
{% endblock %}
{% block declaration %}

{{ particle.declaration|se }}

{% endblock %}
{% block footer %}
.. last line of itf-object.rst template
{{ super() }}
{% endblock %}
