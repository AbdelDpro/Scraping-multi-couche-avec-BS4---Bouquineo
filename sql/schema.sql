CREATE TABLE IF NOT EXISTS books (
    upc           TEXT PRIMARY KEY,     -- Clé naturelle du site

    title         TEXT NOT NULL,        -- Pas FLOAT car risque d'erreur d'arrondi

    category      TEXT,

    price_excl    NUMERIC(10, 2),

    price_incl    NUMERIC(10, 2),

    tax           NUMERIC(10, 2),

    rating        SMALLINT,             -- Note inconnue ≠ note de zéro

    stock         INTEGER,

    reviews_count INTEGER,

    description   TEXT,

    url           TEXT NOT NULL,

    collected_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_books_category ON books (category);
CREATE INDEX IF NOT EXISTS idx_books_stock    ON books (stock);