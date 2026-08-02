{% extends "base.html" %}
{% block title %}Événements{% endblock %}
{% block content %}
<h1>Événements</h1>
<section class="panel">
<form method="post" class="form-grid">
<input name="name" placeholder="Nom de l'événement" required>
<input type="date" name="event_date" required>
<input type="number" step="0.01" name="entry_price" placeholder="Prix d'entrée" required>
<input type="number" name="participants" placeholder="Participants" required>
<input type="number" step="0.01" name="expenses" placeholder="Dépenses prévues" required>
<select name="status"><option>Prévu</option><option>En cours</option><option>Terminé</option><option>Annulé</option></select>
<button>Ajouter</button>
</form>
</section>
<section class="panel">
<table>
<tr><th>Date</th><th>Nom</th><th>Entrée</th><th>Participants</th><th>Dépenses</th><th>Bénéfice estimé</th><th>Statut</th><th></th></tr>
{% for r in rows %}
<tr><td>{{ r.event_date }}</td><td>{{ r.name }}</td><td>{{ "%.0f"|format(r.entry_price) }} $</td><td>{{ r.participants }}</td><td>{{ "%.0f"|format(r.expenses) }} $</td><td>{{ "%.0f"|format(r.estimated_profit) }} $</td><td>{{ r.status }}</td>
<td><form method="post" action="{{ url_for('delete_event', item_id=r.id) }}"><button class="danger-btn">Supprimer</button></form></td></tr>
{% endfor %}
</table>
</section>
{% endblock %}
