{% extends "pou-object.rst" %}
{% block header %}
{{ super() }}
.. first line of act-object.rst template
{% endblock %}
{% block title %}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set ilast_name = iname.split('.')[-1] %}
{% set title = name + " (ACT)" %}

{{ particle.target }}

{{ title }}
{{ '-' * title|count }}
{% endblock %}
{% block footer %}
.. last line of act-object.rst template
{{ super() }}
{% endblock %}
