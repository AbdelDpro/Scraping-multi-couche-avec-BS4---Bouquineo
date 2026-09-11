-- Titres en rupture de stock
SELECT title, category, price_incl
FROM books
WHERE stock = 0
ORDER BY title;

-- Titres en stock faible (moins de 5 exemplaires)
SELECT title, category, stock, price_incl
FROM books
WHERE stock > 0 AND stock < 5
ORDER BY stock, title;

-- Les mieux notés du catalogue
SELECT title, category, rating, stock, price_incl
FROM books
WHERE rating = 5
ORDER BY title
LIMIT 20;

-- Croisement : les mieux notés qui sont aussi en stock faible
-- (pour la question : ou le concurrent est-il vulnerable ?)
SELECT title, category, rating, stock
FROM books
WHERE rating >= 4 AND stock < 5
ORDER BY rating DESC, stock;

-- Repartition du stock par categorie
SELECT category,
       count(*)      AS nb_titres,
       sum(stock)    AS stock_total,
       round(avg(rating), 2) AS note_moyenne
FROM books
GROUP BY category
ORDER BY stock_total;

-- Combien de titres ont des avis ?
SELECT count(*) FILTER (WHERE reviews_count > 0) AS avec_avis,
       count(*)                                   AS total
FROM books;