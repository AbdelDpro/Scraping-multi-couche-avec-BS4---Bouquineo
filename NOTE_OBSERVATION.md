# Note d'observation — champs de prix et de taxe

## Constat

Chaque fiche produit expose trois montants dans le tableau
« Product Information » :

| Champ | Exemple |
|---|---|
| `Price (excl. tax)` | £51.77 |
| `Price (incl. tax)` | £51.77 |
| `Tax` | £0.00 |

Vérification menée d'abord manuellement sur 5 fiches, puis sur l'ensemble des
1 000 livres après chargement en base :

```sql
SELECT count(*) FROM books WHERE price_excl <> price_incl;   -- attendu : 0
SELECT count(*) FROM books WHERE tax <> 0;                   -- attendu : 0
```

## Conclusion

Les deux prix sont systématiquement égaux et la taxe vaut toujours zéro. Les
trois champs ne portent donc qu'une seule information réelle. Le site l'annonce
d'ailleurs lui-même : un bandeau précise que les prix et les notes sont attribués
aléatoirement et n'ont aucune signification.

Ces champs sont néanmoins collectés et stockés tels quels, pour trois raisons :
le coût est nul puisqu'ils sont déjà présents dans la page ; une fiabilité
constatée aujourd'hui n'est pas garantie demain ; et écarter une donnée à la
collecte est irréversible, alors que l'ignorer en aval ne l'est pas.

## Autres constats sur la fiabilité des données

- **Aucun avis sur les 1 000 titres.** Le champ `Number of reviews` est présent
  mais vaut systématiquement 0. La question métier « quels titres sont réellement
  commentés » n'a donc pas de réponse exploitable sur ce catalogue.
- **Deux catégories ne sont pas des catégories.** `Default` (152 titres) et
  `Add a comment` (67 titres) représentent 22 % du catalogue et sont des
  artefacts du site de démonstration. Toute analyse par catégorie doit les
  écarter ou les traiter à part.