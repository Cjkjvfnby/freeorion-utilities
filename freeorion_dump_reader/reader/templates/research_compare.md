<pre>
Tech id | Count | Turns of research
------- | ----- | -----------------{% for name, stat_list in stats %}
**{{name}}** | {{stat_list|length}} | {% for group in stat_list %}{{group.started}}-{{group.finished}} {% endfor %}{% endfor %}
</pre>
