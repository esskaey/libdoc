{% extends "object.rst" %}
{% block header %}
{{ super() }}
.. first line of dut-object.rst template
{%- endblock %}
{% block iotbl %}
.. <% merge "object.iotbl" %>

{% from 'iotbl.inc' import render_table %}
{% set iotable = particle.iotbl %}
{% set header = particle.iotbl['header'] %}
{% set links = particle.iotbl['links'] %}
{% set pou_attributes = iotable['attributes'] %}
{% set t_pou_attributes, ml_pou_attributes = header[0] if header[0][1] else '' %}
{% if pou_attributes %}
{{ t_pou_attributes }}:
    {% for pou_attribute in pou_attributes %}
    {{ '| ' ~ pou_attribute }}
    {% endfor %}
{% endif %}

{% if iotable['body'] %}
InOut:
{{ render_table(iotable)|indent(4, true) }}
{% endif %}
{% if links %}

{% for link in links %}
{{ link }}
{% endfor %}

{% endif %}

.. <% endmerge  %>
{% endblock %}
{% block footer %}
.. last line of dut-object.rst template
{{ super() }}
{% endblock %}
