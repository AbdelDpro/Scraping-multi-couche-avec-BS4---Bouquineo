# Scraper Bouquineo — catalogue concurrent

Collecte du catalogue de [books.toscrape.com](https://books.toscrape.com) (1 000 livres),
enrichissement depuis les fiches produit et chargement dans PostgreSQL.

**Auteur :** Abdel DAADI

---

## Objectif

Répondre à la question métier : *sur quels titres le concurrent est-il en rupture
ou en stock faible, et lesquels sont les mieux notés de son catalogue ?*

Les trois informations manquantes (stock réel, UPC, nombre d'avis) n'existent
que sur les fiches produit, pas sur les pages de liste.

---

## Technologies

| Outil | Rôle | Justification |
|---|---|---|
| Python + `uv` | Langage et gestion d'environnement | Gestion d'environnement et de dépendances, uv.lock garantit des versions identiques d'une machine à l'autre. |
| `requests` | Requêtes HTTP | Requêtes HTTP, avec Session pour réutiliser la connexion sur 1 000 requêtes. |
| `BeautifulSoup4` + `lxml` | Parsing HTML | Parsing HTML, `lxml` comme parseur rapide. |
| PostgreSQL | Stockage final | Stockage relationnel, contrainte d'unicité sur l'UPC pour l'idempotence. |
| Docker | Exécution de PostgreSQL | PostgreSQL reproductible sans installation locale. |
| `structlog` | Journalisation structurée | Logs en paires clé-valeur exportables en JSON, filtrables et agrégeables — contrairement aux lignes de texte du module `logging` standard, qui exigent des expressions régulières pour être exploitées. |

---

## Reconnaissance du site

### Pagination

- 50 pages de liste, 20 livres par page = 1 000 livres.
- URL prévisible : `https://books.toscrape.com/catalogue/page-{n}.html`, de 1 à 50.
- `page-1.html` existe : la page d'accueil (`index.html`) n'a donc pas besoin
  d'être traitée comme un cas particulier.
- Le site annonce lui-même « Page 1 of 50 » et son nombre total de résultats,
  ce qui permet de vérifier en fin de collecte qu'aucune page n'a été manquée.

### URL des fiches produit

Les liens vers les fiches sont **relatifs**, et relatifs à des bases différentes
selon la page d'origine :

| Page d'origine | Valeur du `href` |
|---|---|
| `index.html` | `catalogue/a-light-in-the-attic_1000/index.html` |
| `catalogue/page-2.html` | `in-her-wake_980/index.html` |

Une concaténation naïve (`base + href`) produit une URL invalide depuis les
pages de catalogue : le segment `/catalogue/` disparaît. Le serveur répond
alors **404 sans lever d'exception**, et le scraper enregistre silencieusement
des fiches vides.

**Solution retenue :** `urllib.parse.urljoin(url_page_courante, href)`.

### robots.txt

`https://books.toscrape.com/robots.txt` renvoie **404** : le site ne publie
aucune directive.

Absence de robot.txt ce qui signifie que le site s'en remet à la législation en vigueur dans le pays, sans apporter de précisions propres. Aussi par rapport à ce que supporte le serveur, et ce que serait le comportement normal d'un navigateur humain.

### Nombre de pages

Le nombre total de pages est lu sur la page elle-même (« Page 1 of 50 ») plutôt
que codé en dur. Si le catalogue s'agrandit, la collecte suit sans modification
du code. `MAX_PAGES = 60` sert uniquement de garde-fou contre une boucle infinie.

---

## Comportement du collecteur

- **User-Agent explicite :** Dictionnaire de 5 entrées + WARNING
- **Temporisation :** 0.5s secondes entre deux requêtes.

  Justification :  
  Concernant la réflexion sur le choix du délai entre 2 requêtes, mon choix s'oriente vers 0.5s entre 2 requêtes. Cela équivaudrait à : 1050 requêtes espacées de 0.5 donc 0.5s x 1050 = 9min. Ce délai correspond à peu près au comportement humain de navigation. En phase de développement je relance la collecte plusieurs fois par jour; à 6 s de délai chaque cycle durerait 1 h 45, ce qui rendrait tout test impraticable et serait un obstacle au développement et à la maintenance du code. Un délai trop rapide serait adopter un comportement de robot agressif, visible comme un pic anormal côté serveur.
  Par ailleurs, aucun 'crawl-delay' n'est imposé ce qui me laisse la responsabilité de fixer un rythme raisonnable.


- **Mode échantillon :** paramètre limitant le nombre de fiches collectées.
  Nécessaire pour détecter tôt les bugs silencieux, pour ne pas saturer le site
  pendant les dizaines de tests de développement, et pour la démonstration
  en soutenance (10 minutes).

---

## Pièges rencontrés

### La note n'est pas un texte

Elle est encodée dans l'attribut `class` : `<p class="star-rating Three">`.
Les cinq balises `<i class="icon-star">` sont présentes quel que soit le
nombre d'étoiles affichées et ne portent aucune information.

La conversion se fait via un dictionnaire de correspondance (`MAPPING_NOTES`)
défini dans `config.py`, qui associe chaque mot anglais à un entier. Si aucune
classe ne correspond, la fonction journalise un WARNING et rend `None` plutôt
que `0` : une note absente n'est pas une note de zéro, et `None` devient `NULL`
en base, ce que les fonctions d'agrégation SQL ignorent au lieu de le compter.

### La page de liste ment par omission

Elle affiche `In stock` sans quantité. La fiche produit indique
`In stock (22 available)`.

### Trois champs de prix pour une seule information

Ne garder que le TTC car information la plus utile et aussi car j'ai testé pour 5 livres qui ont tous HT = TTC, ainsi que Tax = 0.

### Le titre n'est pas une clé

Le code UPC est retenu car c'est un ID unique qui évite les confusions et les doublons.

---

## Installation et lancement

...

```bash
git clone <url>
cd Scraping
uv sync          # Pour le coup, installe les dépendances ET le projet comme paquet. Le projet est déclaré comme paquet installable ([build-system] + packages = ["src/scraper"]), pour que les imports fonctionnent quel que soit le dossier courant. Plus de stabilité dans les tests.
docker compose up -d
...
```

---

## Structure du projet

```text
bouquineo-scraper/
├── pyproject.toml          # versionné
├── uv.lock                 # versionné
├── .gitignore
├── docker-compose.yml      # PostgreSQL
├── README.md
├── JOURNAL.md
├── NOTE_OBSERVATION.md
│
├── src/
│   └── scraper/
│       ├── __init__.py
│       ├── config.py            # réglages : URL, délai, User-Agent, chemins
│       ├── http_client.py       # EXTRACT : session, requête, temporisation
│       ├── parsing.py           # TRANSFORM : HTML → dicts
│       ├── collect_listing.py   # collecteur 1 : boucle sur les 50 pages
│       ├── collect_products.py  # collecteur 2 : 1000 fiches + reprise
│       ├── storage.py           # LOAD (1) : écriture fichier + reprise
│       ├── db.py                # LOAD (2) : PostgreSQL
│       └── cli.py               # point d'entrée, arguments
│
├── sql/
│   └── schema.sql
│
└── data/
    ├── work/               # ignoré — fichiers de travail, reprise
    └── export/             # versionné — livrable CSV/JSON
```
---

## Schéma de la base

...

---

## Requêtes répondant à la question métier

...