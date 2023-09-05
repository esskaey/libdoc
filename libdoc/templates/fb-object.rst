{% extends "pou-object.rst" %}
{% block header %}
{{ super() }}
.. first line of fb-object.rst template
{% endblock %}
{% block title%}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set prefix = particle.prefix %}
{% if prefix %}
{% set title = name + " (FB; Prefix " + prefix + ")" %}
{% else %}
{% set title = name + " (FB)" %}
{% endif %}

.. index::
   single: {{ iname }}

{{ particle.target }}

{{ title }}
{{ '-' * title|count }}
{% endblock %}
{% block footer %}
.. last line of fb-object.rst template
{{ super() }}
{% endblock %}
