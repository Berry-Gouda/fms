USE fms;

CREATE TABLE IF NOT EXISTS tag_junc(
    tag_junc_id INT UNSIGNED PRIMARY KEY,
    tag_id INT NOT NULL,
    item_id INT NULL,
    recipe_id INT UNSIGNED NULL,
    FOREIGN KEY (tag_id) REFERENCES tag_lu(tag_id),
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (recipe_id) REFERENCES recipe(recipe_id)
);