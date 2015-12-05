{% extends "base.html" %}

{% block title %}Research progress{% endblock %}
{% block content %}
{{ block.super }}
<p>Markdown:</p>
<pre>
{% for turn, finished, started in progress %} - Turn {{ turn }}
{% if started %}    - started
{% for ri in started %}        - {{ ri.name }}
{% endfor %}{% endif %}{% if finished %}    - finished
{% for ri in finished %}        - {{ ri.name }}
{% endfor %}{% endif %}
{% endfor %}
</pre>
{% endblock %}
