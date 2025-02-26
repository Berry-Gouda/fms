USE fms;

CREATE TABLE IF NOT EXISTS nutrition_junc(
    nut_junc_id INT UNSIGNED PRIMARY KEY,
    item_id INT NOT NULL,
    nutrient_id INT NOT NULL,
    alt_id INT NOT NULL,
    cat_id INT NOT NULL,
    ammount FLOAT,
    unit_id INT NOT NULL,
    dv VARCHAR(10),
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (nutrient_id) REFERENCES nutrient_lu(nutrient_id),
    FOREIGN KEY (alt_id) REFERENCES nutrient_lu(nutrient_id),
    FOREIGN KEY (cat_id) REFERENCES nutrient_cat_lu(cat_id),
    FOREIGN KEY (unit_id) REFERENCES unit_lu(unit_id)
);