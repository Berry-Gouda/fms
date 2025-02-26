USE fms;

CREATE TABLE IF NOT EXISTS conversion_junc(
    conversion_id INT UNSIGNED PRIMARY KEY,
    item_id INT NOT NULL,
    unit_id INT NOT NULL,
    unit_amt FLOAT,
    ammount FLOAT,
    amt_unit INT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (unit_id) REFERENCES unit_lu(unit_id),
    FOREIGN KEY (amt_unit) REFERENCES unit_lu(unit_id)
);