USE fms;

CREATE TABLE IF NOT EXISTS method_junc(
    method_junc_id INT UNSIGNED PRIMARY KEY,
    method_id INT UNSIGNED NOT NULL,
    recipe_id INT UNSIGNED NOT NULL,
    FOREIGN KEY (method_id) REFERENCES method(method_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id)
)