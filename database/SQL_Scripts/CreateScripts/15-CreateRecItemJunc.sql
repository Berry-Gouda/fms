USE fms;

CREATE TABLE IF NOT EXISTS recipe_item_junc(
    recipe_item_junc INT UNSIGNED PRIMARY KEY,
    item_id INT NOT NULL,
    recipe_id INT UNSIGNED NOT NULL,
    unit_id INT NOT NULL,
    unit_amt float,
    item_grouping VARCHAR(50),
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id),
    FOREIGN KEY (unit_id) REFERENCES unit_lu(unit_id)
)