USE fms;

DROP USER IF EXISTS 'fmsUser'@'localhost';
CREATE USER 'fmsUser'@'localhost' IDENTIFIED BY 'FMSForLife1!';
GRANT ALL PRIVILEGES ON fms.* TO 'fmsUser'@'localhost';
FLUSH PRIVILEGES;