USE fms;

CREATE TABLE IF NOT EXISTS item(
    item_id INT PRIMARY KEY,
    `name` TEXT,
    `brand` TEXT,
    NLEA_unit int NOT NULL,
    NLEA_val float,
    ammount float,
    ammount_unit int NOT NULL,
    upc VARCHAR(15),
    ingrdient_list TEXT,
    FOREIGN KEY (NLEA_unit) REFERENCES unit_lu(unit_id),
    FOREIGN KEY (ammount_unit) REFERENCES unit_lu(unit_id)
);