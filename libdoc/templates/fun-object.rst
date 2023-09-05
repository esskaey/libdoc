{% extends "pou-object.rst" %}
{% block header %}
{{ super() }}
.. first line of fun-object.rst template
{% endblock %}
{% block title %}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set title = name + " (FUN)" %}

.. index::
   single: {{ iname }}

{{ particle.target }}

{{ title }}
{{ '-' * title|count }}
{% endblock %}
{% block footer %}
.. last line of fun-object.rst template
{{ super() }}
{% endblock %}
