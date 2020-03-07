<html>
  <body>
      <p>Hi Mathilde,<br>
             How are you?<br>

      You should check this new job offers I've found:
      <ul>
      {% for job in jobs %}
      <li><a href="{{ job.href }}">{{ job.title }}</a></li>
      {% endfor %}
      </ul>

      Sincerely,<br>
      Pascal
   </body>
</html>
