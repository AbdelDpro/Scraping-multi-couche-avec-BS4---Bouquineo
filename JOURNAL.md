## J1
- erreur GH007 au push (email privé) → rebase avec --reset-author
- ModuleNotFoundError: No module named 'scraper' → structure src/, [build-system], uv sync
- le terminal muet sur urljoin → différence REPL / script
- les cinq <i class="icon-star"> qui ne portent aucune information

## J2
- Bloqué : import scraper échoue (ModuleNotFoundError) alors que le fichier existe.
  Essayé : vérifier __init__.py. Débloqué par : déclarer le projet comme paquet
  installable dans pyproject.toml + uv sync.