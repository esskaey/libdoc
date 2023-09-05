:orphan:

..
    :Name: {{ particle.name }}
    :Type: {{ particle.type }}

{% for image in images %}
.. figure:: {{ image }}

{% endfor %}
