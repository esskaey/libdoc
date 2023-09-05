{% macro render_table(iotbl) %}
    {% set header = iotbl['header'] %}
    {% set body = iotbl['body'] -%}
    {% if body %}
        {% set t_scope, ml_scope = header[1] if header[1][1] else ('', 0) %}
        {% set t_name, ml_name = header[2] if header[2][1] else ('', 0) %}
        {% set t_type, ml_type  = header[3] if header[3][1] else ('', 0) %}
        {% set t_address, ml_address = header[4] if header[4][1] else ('', 0) %}
        {% set t_initial, ml_initial = header[5] if header[5][1] else ('', 0) %}
        {% set t_comment, ml_comment = header[6] if header[6][1] else ('', 0) %}
        {% set t_attribute, ml_attribute = header[7] if header[7][1] else ('', 0) %}
        {% set t_inherited_from, ml_inherited_from = header[8] if header[8][1] else ('', 0) %}
        {% set t_scope = ('| ' ~ t_scope ~ ' ').ljust(ml_scope+3) if ml_scope>0 else '' %}
        {% set t_name = ('| ' ~ t_name ~ ' ').ljust(ml_name+3) if ml_name>0 else '' %}
        {% set t_type = ('| ' ~ t_type ~ ' ').ljust(ml_type+3) if ml_type>0 else '' %}
        {% set t_address = ('| ' ~ t_address ~ ' ').ljust(ml_address+3) if ml_address>0 else '' %}
        {% set t_initial = ('| ' ~ t_initial ~ ' ').ljust(ml_initial+3) if ml_initial>0 else '' %}
        {% set t_comment = ('| ' ~ t_comment ~ ' ').ljust(ml_comment+3) if ml_comment>0 else '' %}
        {% set t_attribute = ('| ' ~ t_attribute ~ ' ').ljust(ml_attribute+3) if ml_attribute>0 else '' %}
        {% set t_inherited_from = ('| ' ~ t_inherited_from ~ ' ').ljust(ml_inherited_from+3) if ml_inherited_from>0 else '' %}
        {% set l_scope = ('+' ~ '-' * (ml_scope+2)) if ml_scope>0 else '' %}
        {% set l_name = ('+' ~ '-' * (ml_name+2)) if ml_name>0 else '' %}
        {% set l_type = ('+' ~ '-' * (ml_type+2)) if ml_type>0 else '' %}
        {% set l_address = ('+' ~ '-' * (ml_address+2)) if ml_address>0 else '' %}
        {% set l_initial = ('+' ~ '-' * (ml_initial+2)) if ml_initial>0 else '' %}
        {% set l_comment = ('+' ~ '-' * (ml_comment+2)) if ml_comment>0 else '' %}
        {% set l_attribute = ('+' ~ '-' * (ml_attribute+2)) if ml_attribute>0 else '' %}
        {% set l_inherited_from = ('+' ~ '-' * (ml_inherited_from+2)) if ml_inherited_from>0 else '' -%}
        {{ l_scope ~ l_name ~ l_type ~ l_address ~ l_initial ~ l_comment ~ l_attribute ~ l_inherited_from ~ '+\n' ~
           t_scope ~ t_name ~ t_type ~ t_address ~ t_initial ~ t_comment ~ t_attribute ~ t_inherited_from ~ '|\n' ~
          (l_scope ~ l_name ~ l_type ~ l_address ~ l_initial ~ l_comment ~ l_attribute ~ l_inherited_from ~ '+')|replace('-', '=')
        }}
        {% set last_scope = body[0][0][0] %}
        {% for row in body -%}
            {% set m_scope = row[0][0] %}
            {% if not loop.first -%}
                {% if m_scope != last_scope %}
                    {% set l_scope = ('+' ~ '-' * (ml_scope+2)) if ml_scope>0 else '' %}
                {% else %}
                    {% set l_scope = ('+' ~ ' ' * (ml_scope+2)) if ml_scope>0 else '' %}
                {% endif -%}
                {{ l_scope ~ l_name ~ l_type ~ l_address ~ l_initial ~ l_comment ~ l_attribute ~ l_inherited_from ~ '+' }}
            {% endif %}
            {% set p_scope = (m_scope != last_scope or loop.first) %}
            {% set last_scope = m_scope %}
            {% for c_scope, c_name, c_type, c_address, c_initial, c_comment, c_attribute, c_inherited_from in row %}
                {% set c_scope = c_scope.ljust(ml_scope) if c_scope and p_scope else ' ' * ml_scope %}
                {% set c_name = (c_name).ljust(ml_name) if c_name else ' ' * ml_name %}
                {% set c_type = (c_type).ljust(ml_type) if c_type else ' ' * ml_type %}
                {% set c_address = (c_address).ljust(ml_address) if c_address else ' ' * ml_address %}
                {% set c_initial = (c_initial).ljust(ml_initial) if c_initial else ' ' * ml_initial %}
                {% set c_comment = c_comment.ljust(ml_comment) if c_comment else ' ' * ml_comment %}
                {% set c_attribute = (c_attribute).ljust(ml_attribute) if c_attribute else ' ' * ml_attribute %}
                {% set c_inherited_from = (c_inherited_from).ljust(ml_inherited_from) if c_inherited_from else ' ' * ml_inherited_from %}
                {% set scope = ('| ' ~ c_scope ~ ' ') if ml_scope>0 else '' %}
                {% set name = ('| ' ~ c_name ~ ' ') if ml_name>0 else '' %}
                {% set type = ('| ' ~ c_type ~ ' ') if ml_type>0 else '' %}
                {% set address = ('| ' ~ c_address ~ ' ') if ml_address>0 else '' %}
                {% set initial = ('| ' ~ c_initial ~ ' ') if ml_initial>0 else '' %}
                {% set comment = ('| ' ~ c_comment ~ ' ') if ml_comment>0 else '' %}
                {% set attribute = ('| ' ~ c_attribute ~ ' ') if ml_attribute>0 else '' %}
                {% set inherited_from = ('| ' ~ c_inherited_from ~ ' ') if ml_inherited_from>0 else '' -%}
                {{ scope ~ name ~ type ~ address ~ initial ~ comment ~ attribute ~ inherited_from ~ '|' }}
            {% endfor %}
        {% endfor %}
        {% set l_scope = ('+' ~ '-' * (ml_scope+2)) if ml_scope>0 else '' -%}
        {{ l_scope ~ l_name ~ l_type ~ l_address ~ l_initial ~ l_comment ~ l_attribute ~ l_inherited_from ~ '+' }}
    {% endif %}
{% endmacro %}
