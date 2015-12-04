Compare
=======
Field | this | that | added | removed
:--- | ---: | ---: | ---: | ---:{% for name, group in compare %}
**{{name|title}}** | | {% for diff  in group %}
{{diff.name|title}} | {{diff.this}} | {{diff.that}} | {{diff.added}} | {{diff.removed}}{% endfor%}{% endfor%}
