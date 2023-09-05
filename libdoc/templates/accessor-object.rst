{% extends "pou-object.rst" %}
{% block header %}
{{ super() }}
.. first line of accessor-object.rst template
{% endblock %}
{% block title %}
{% set iname = particle.name %}
{% set name = iname|se %}
{% set last_name = name.split('.')[-1] %}
{% set title = name + " (ACC)" %}
{% set at = 'Getter; ' if last_name == 'Get' else 'Setter; ' %}

{{ particle.target }}

{{ title }}
{{ '-' * title|count }}

{% endblock %}
{% block footer %}
.. last line of accessor-object.rst template
{{ super() }}
{% endblock %}
