#!/bin/bash

mysql -u root -p << EOF

SOURCE 00-CreateDB.sql;
SOURCE 01-CreateUser.sql;
SOURCE 02-CreateNutrientLU.sql;
SOURCE 03-CreateUnitLU.sql;
SOURCE 04-CreateItemTable.sql;
SOURCE 05-CreateNutCatLU.sql;
SOURCE 06-CreateNutrientJunc.sql;
SOURCE 07-CreateConversionJunc.sql;
SOURCE 08-CreateRecTable.sql;
SOURCE 09-CreateTagLUTable.sql;
SOURCE 10-CreateTagJuncTable.sql;
SOURCE 11-CreateTimingLUTable.sql;
SOURCE 12-CreateTimingJuncTable.sql;
SOURCE 13-CreateMethodTable.sql;
SOURCE 14-CreateMethodJuncTable.sql;
SOURCE 15-CreateRecItemJunc.sql;

EOF