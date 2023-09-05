.. first line of info.rst template
.. <% merge "properties.Shortcuts" %>
{% set info_table = content.info.info_table %}
.. <% endmerge %>

.. _info:

File and Project Information
============================

{% set header = info_table['header'] %}
{% set body = info_table['body'] -%}
{% if body %}
    {% set t_scope, ml_scope = header[0] if header[0][1] else ('', 0) %}
    {% set t_name, ml_name = header[1] if header[1][1] else ('', 0) %}
    {% set t_type, ml_type  = header[2] if header[2][1] else ('', 0) %}
    {% set t_content, ml_content = header[3] if header[3][1] else ('', 0) %}
    {% set t_scope = ('| ' ~ t_scope ~ ' ').ljust(ml_scope+3) if ml_scope>0 else '' %}
    {% set t_name = ('| ' ~ t_name ~ ' ').ljust(ml_name+3) if ml_name>0 else '' %}
    {% set t_type = ('| ' ~ t_type ~ ' ').ljust(ml_type+3) if ml_type>0 else '' %}
    {% set t_content = ('| ' ~ t_content ~ ' ').ljust(ml_content+3) if ml_content>0 else '' %}
    {% set l_scope = ('+' ~ '-' * (ml_scope+2)) if ml_scope>0 else '' %}
    {% set l_name = ('+' ~ '-' * (ml_name+2)) if ml_name>0 else '' %}
    {% set l_type = ('+' ~ '-' * (ml_type+2)) if ml_type>0 else '' %}
    {% set l_content = ('+' ~ '-' * (ml_content+2)) if ml_content>0 else '' -%}
    {{ l_scope ~ l_name ~ l_type ~ l_content ~ '+\n' ~
       t_scope ~ t_name ~ t_type ~ t_content ~ '|\n' ~
      (l_scope ~ l_name ~ l_type ~ l_content ~ '+')|replace('-', '=')
    }}
    {% set last_scope = body[0][0][0] %}
    {% set last_type = body[0][0][2] %}
    {% for row in body -%}
        {% set m_scope = row[0][0] %}
        {% set m_type = row[0][2] %}
        {% if not loop.first -%}
            {% if m_scope != last_scope %}
                {% set l_scope = ('+' ~ '-' * (ml_scope+2)) if ml_scope>0 else '' %}
            {% else %}
                {% set l_scope = ('+' ~ ' ' * (ml_scope+2)) if ml_scope>0 else '' %}
            {% endif -%}
            {% if m_type != last_type %}
                {% set l_type = ('+' ~ '-' * (ml_type+2)) if ml_type>0 else '' %}
            {% else %}
                {% set l_type = ('+' ~ ' ' * (ml_type+2)) if ml_type>0 else '' %}
            {% endif -%}
            {{ l_scope ~ l_name ~ l_type ~ l_content ~ '+' }}
        {% endif %}
        {% set p_scope = (m_scope != last_scope or loop.first) %}
        {% set p_type = (m_type != last_type or loop.first) %}
        {% set last_scope = m_scope %}
        {% set last_type = m_type %}
        {% for c_scope, c_name, c_type, c_content in row %}
            {% set c_scope = c_scope.ljust(ml_scope) if c_scope and p_scope else ' ' * ml_scope %}
            {% set c_name = (c_name).ljust(ml_name) if c_name else ' ' * ml_name %}
            {% set c_type = c_type.ljust(ml_type) if c_type and p_type else ' ' * ml_type %}
            {% set c_content = c_content.ljust(ml_content) if c_content else ' ' * ml_content %}
            {% set scope = ('| ' ~ c_scope ~ ' ') if ml_scope>0 else '' %}
            {% set name = ('| ' ~ c_name ~ ' ') if ml_name>0 else '' %}
            {% set type = ('| ' ~ c_type ~ ' ') if ml_type>0 else '' %}
            {% set content = ('| ' ~ c_content ~ ' ') if ml_content>0 else '' -%}
            {{ scope ~ name ~ type~ content ~ '|' }}
        {% endfor %}
    {% endfor %}
    {% set l_scope = ('+' ~ '-' * (ml_scope+2)) if ml_scope>0 else '' -%}
    {{ l_scope ~ l_name ~ l_type ~ l_content ~ '+' }}
{% endif %}

.. last line of info.rst template
