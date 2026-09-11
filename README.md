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

- **Reprise sur interruption** :  Au démarrage, `collect_products` relit le fichier de destination et construit l'ensemble des URL déjà traitées. Seules les fiches absentes de cet ensemble sont demandées. La comparaison porte sur l'URL de fiche et non sur l'UPC : l'URL est connue avant la requête, l'UPC seulement après parsing. 
L'écriture se fait au fil de l'eau, une ligne JSON par fiche (format JSONL). Une interruption ne fait perdre au maximum que la fiche en cours, jamais le fichier entier — contrairement à un JSON classique, qui serait illisible sans son crochet fermant.

- **Gestion des erreurs** : Chaque fiche est traitée dans un bloc isolé : une erreur est journalisée avec son URL et la collecte continue. Un compteur d'échecs **consécutifs** arrête la collecte au-delà de 20. Le choix du consécutif plutôt que du cumul est délibéré : des échecs dispersés sont du bruit normal, des échecs enchaînés signalent un site tombé ou modifié. Le compteur est remis à zéro à chaque succès.

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
`In stock (22 available)`. Le nombre est extrait par expression régulière
(`extraire_nombre`), qui rend `0` lorsqu'aucun nombre n'est présent — cas
d'un livre en rupture.

### Trois champs de prix pour une seule information

Les fiches exposent `Price (excl. tax)`, `Price (incl. tax)` et `Tax`.
Vérification faite sur plusieurs livres : les deux prix sont toujours égaux
et la taxe vaut systématiquement £0.00. Ces trois champs sont donc collectés
tels quels, mais ne portent qu'une seule information réelle. Détail dans
`NOTE_OBSERVATION.md`.

### Le titre n'est pas une clé

Le code UPC est retenu car c'est un ID unique qui évite les confusions et les doublons.

---

## Installation et lancement

```bash
git clone https://github.com/AbdelDpro/Scraping-multi-couche-avec-BS4---Bouquineo
cd Scraping-multi-couche-avec-BS4---Bouquineo
uv sync                         # dépendances + projet installé comme paquet
docker compose up -d            # base PostgreSQL
scraper tout                    # collecte complète (~9 min)
```

---

## Utilisation

```bash
scraper --help                  # affiche les options
scraper listing                 # collecte les 50 pages de liste
scraper produits                # collecte les 1 000 fiches produit
scraper tout                    # enchaîne les deux étapes

scraper listing --limit 2       # mode échantillon : 2 pages
scraper produits --limit 10     # mode échantillon : 10 fiches
```

La commande `scraper` est déclarée dans `pyproject.toml` (`[project.scripts]`)
et installée par `uv sync`. Elle fonctionne depuis n'importe quel dossier.

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

### Stratégie de chargement

Le chargement écrase les lignes existantes sur conflit d'UPC (`ON CONFLICT
DO UPDATE`) : la base reflète l'état courant du catalogue concurrent, ce que
demande la question métier.

Limite assumée : l'historique est perdu. Un suivi de l'évolution du stock dans
le temps demanderait une table historisée (SCD de type 2, avec `valid_from` /
`valid_to`), hors du périmètre de ce mini-brief.

---

## Requêtes répondant à la question métier

...