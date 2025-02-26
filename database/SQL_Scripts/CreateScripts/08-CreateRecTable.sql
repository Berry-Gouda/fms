USE fms;

CREATE TABLE IF NOT EXISTS recipe(
    recipe_id INT UNSIGNED PRIMARY KEY,
    name VARCHAR(300),
    servings INT,
    yield_amt float,
    yield_unt INT NOT NULL,
    source TEXT,
    FOREIGN KEY (yield_unt) REFERENCES unit_lu(unit_id)
);