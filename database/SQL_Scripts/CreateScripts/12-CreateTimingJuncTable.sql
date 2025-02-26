USE fms;

CREATE TABLE IF NOT EXISTS timing_junc(
    timing_junc_id INT UNSIGNED PRIMARY KEY,
    recipe_id INT UNSIGNED NOT NULL,
    timing_id INT NOT NULL,
    value float NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id),
    FOREIGN KEY (timing_id) REFERENCES timing_lu(timing_id)
)