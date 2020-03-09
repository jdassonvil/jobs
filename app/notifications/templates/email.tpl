<html>
  <body>
      <p>Hi Mathilde,<br>
             How are you?<br>

      You should check this new job offers I've found: <br >

      {% for company, jobs in companies.items() %}
      <b>{{ company }}</b>
      <ul>
      {% for job in jobs %}
      <li><a href="{{ job.href }}">{{ job.title }}</a> {{ job.timetext }}</li>
      {% endfor %}
      </ul>
      {% endfor %}
      Sincerely,<br>
      Pascal
   </body>
</html>
