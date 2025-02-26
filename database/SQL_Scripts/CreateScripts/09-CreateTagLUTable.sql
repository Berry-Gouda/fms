USE fms;

CREATE TABLE IF NOT EXISTS tag_lu(
	tag_id INT PRIMARY KEY,
    tag VARCHAR(300),
    href TEXT
);