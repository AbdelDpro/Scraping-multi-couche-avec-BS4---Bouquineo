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