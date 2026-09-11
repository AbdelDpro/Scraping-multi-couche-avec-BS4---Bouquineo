## J1
- erreur GH007 au push (email privé) → rebase avec --reset-author
- ModuleNotFoundError: No module named 'scraper' → structure src/, [build-system], uv sync
- le terminal muet sur urljoin → différence REPL / script
- les cinq <i class="icon-star"> qui ne portent aucune information

## J2
- Bloqué : import scraper échoue (ModuleNotFoundError) alors que le fichier existe.
  Essayé : vérifier __init__.py. Débloqué par : déclarer le projet comme paquet
  installable dans pyproject.toml + uv sync.

- **Bloqué :** `ModuleNotFoundError: No module named 'scraper'` alors que le
  fichier existait. Essayé : vérifier `__init__.py`. Débloqué par : déclarer
  le projet comme paquet installable dans `pyproject.toml` (`[build-system]`
  + `packages = ["src/scraper"]`) puis `uv sync`. La structure `src/` impose
  cette étape.

- **Bloqué :** `UnboundLocalError` sur `_dernier_appel`. Le mot-clé `global`
  désigne la variable du module mais ne la crée pas. Débloqué par :
  l'initialiser à `0.0` au niveau du module. Bug qui n'apparaît qu'au
  deuxième appel — le premier crée la variable.

- **Bloqué :** push refusé (`GH007`, email privé exposé). Débloqué par :
  adresse `noreply` GitHub + `git rebase --root --exec "git commit --amend
  --no-edit --reset-author"` pour réécrire les commits déjà faits.

- **Constat :** `convert_prix` repose sur une hypothèse de format (point décimal,
  pas de séparateur de milliers). Vraie sur ce site, fausse en format européen —
  et l'erreur serait silencieuse. Hypothèse documentée dans la docstring plutôt
  que corrigée : le cas ne se présente pas ici.

  - **Blocage :** modifications d'un fichier invisibles depuis le REPL, l'ImportError
  se répétait à l'identique après correction. Cause : Python met les modules en
  cache dans `sys.modules` et ne relit pas le fichier aux imports suivants.
  Débloqué par : redémarrer le REPL. Règle retenue — modification de fichier =
  redémarrage du REPL.

- **Blocage :** `ValueError: could not convert string to float: ''` sur
  `parser_fiche`. Deux causes empilées : clés de dictionnaire inventées
  (`"Price HT"`) au lieu des libellés réels du site (`"Price (excl. tax)"`),
  et `convert_price` qui plantait sur une chaîne sans chiffre. Débloqué par :
  lire les libellés réels via un sélecteur, et rendre `convert_price` tolérante
  (WARNING + `None`).

- **Bug silencieux :** description dupliquée dans le résultat de `parser_fiche`.
  Cause : le sélecteur `#product_description ~ p` prend tous les paragraphes
  frères suivants, dont BeautifulSoup concatène le texte. Corrigé avec `+`
  (frère immédiat). Aucune erreur levée — repéré uniquement en lisant le résultat.

- 1 000 livres collectés depuis les 50 pages de liste,
  avec l'URL de leur fiche produit.

- 1 000 fiches produit collectées, 0 échec, en ~9
  minutes (délai de 0,5 s entre requêtes, conforme à l'estimation initiale).

- **Reprise sur interruption testée :** collecte interrompue par Ctrl-C après
  35 fiches, relance de la même commande — les logs annoncent `deja_faites=35`
  et seules les fiches restantes sont demandées. Aucune requête inutile envoyée
  au site.

- **Limite identifiée :** `collect_listing` n'est pas idempotent — deux
  exécutions ajoutent les livres en double dans `livres.jsonl` (mode append).
  Choix assumé : la contrainte d'unicité sur l'UPC en base neutralise les
  doublons au chargement. Le fichier de travail est un intermédiaire, pas la
  source de vérité.