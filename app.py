{% extends "base.html" %}
{% block title %}Comptabilité{% endblock %}
{% block content %}
<h1>Comptabilité</h1>
<section class="panel">
<h2>Ajouter une opération</h2>
<form method="post" class="form-grid">
<input type="date" name="date" required>
<select name="type"><option value="recette">Recette</option><option value="depense">Dépense</option></select>
<input name="category" placeholder="Catégorie" required>
<input name="description" placeholder="Description" required>
<input type="number" step="0.01" name="amount" placeholder="Montant $" required>
<input name="responsible" placeholder="Responsable">
<button>Ajouter</button>
</form>
</section>
<section class="panel">
<table>
<tr><th>Date</th><th>Type</th><th>Catégorie</th><th>Description</th><th>Montant</th><th>Responsable</th><th></th></tr>
{% for r in rows %}
<tr>
<td>{{ r.date }}</td><td>{{ r.type }}</td><td>{{ r.category }}</td><td>{{ r.description }}</td>
<td class="{{ r.type }}">{{ "%.2f"|format(r.amount) }} $</td><td>{{ r.responsible }}</td>
<td><form method="post" action="{{ url_for('delete_transaction', item_id=r.id) }}"><button class="danger-btn">Supprimer</button></form></td>
</tr>
{% endfor %}
</table>
</section>
{% endblock %}
