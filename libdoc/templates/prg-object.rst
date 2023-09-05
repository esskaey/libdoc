{% extends "pou-object.rst" %}
{% block header %}
{{ super() }}
.. first line of prg-object.rst template
{% endblock %}
{% block title %}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set title = name + " (PRG)" %}

{{ particle.target }}

{{ title }}
{{ '-' * title|count }}
{% endblock %}
{% block footer %}
.. last line of prg-object.rst template
{{ super() }}
{% endblock %}
