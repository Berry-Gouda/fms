USE fms;

CREATE TABLE IF NOT EXISTS method(
    method_id INT UNSIGNED PRIMARY KEY,
    step INT NOT NULL,
    instruction TEXT
)