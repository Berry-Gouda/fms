package db

import (
	"database/sql"
	"fmt"
	"log"
	"reflect"
	"strings"

	_ "github.com/go-sql-driver/mysql"
)

// GetTableRowCount returns the number of entrys in a table.
func GetTableRowCount(tName string, db *sql.DB) (int, error) {

	var count int

	query := fmt.Sprintf("SELECT COUNT(*) FROM %s", tName)
	err := db.QueryRow(query).Scan(&count)

	if err != nil {
		return count, err
	}

	return count, err
}

// GetTableOVerviewInfo Returns various information form the table to be displayed in the table overview page.
func GetTableOverviewInfo(tName string, db *sql.DB) ([]TableSchemaInfo, error) {

	var tableInfo []TableSchemaInfo

	query := fmt.Sprintf(
		`SELECT c.COLUMN_NAME, c.COLUMN_TYPE, c.IS_NULLABLE, c.COLUMN_DEFAULT, 
		IF(k.CONSTRAINT_NAME = 'PRIMARY', 'PRI', IF(k.REFERENCED_TABLE_NAME IS NOT NULL, 'FK', NULL)) AS KEY_TYPE
		FROM INFORMATION_SCHEMA.COLUMNS c
		LEFT JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
		ON c.TABLE_NAME = k.TABLE_NAME AND c.COLUMN_NAME = k.COLUMN_NAME AND c.TABLE_SCHEMA = k.TABLE_SCHEMA
		WHERE c.TABLE_NAME = '%s' AND c.TABLE_SCHEMA = DATABASE()
		ORDER BY c.ORDINAL_POSITION`, tName)

	results, err := db.Query(query)
	if err != nil {
		log.Fatal("Error getting Table SchemaInfo:")
	}
	defer results.Close()

	for results.Next() {
		var col TableSchemaInfo
		var colDefault, kType sql.NullString

		if err := results.Scan(&col.ColName, &col.DType, &col.IsNull, &colDefault, &kType); err != nil {
			println(err)
			return tableInfo, err
		}

		if colDefault.Valid {
			col.ColDefault = colDefault.String
		} else {
			col.ColDefault = "N/A"
		}

		if kType.Valid {
			col.KeyType = kType.String
		} else {
			col.KeyType = "N/A"
		}

		tableInfo = append(tableInfo, col)

	}

	return tableInfo, nil
}

// GetRandomRows Gathers a random slice from a table.
func GetRandomRows(db *sql.DB, count int, tName string, structType reflect.Type) ([][]string, error) {

	columnOrder, err := getColumnOrder(db, tName)
	if err != nil {
		return nil, err
	}

	query := fmt.Sprintf("SELECT %s FROM %s ORDER BY RAND() LIMIT %d",
		strings.Join(columnOrder, " ,"), tName, count)

	rows, err := db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results [][]string

	for rows.Next() {
		rowVals := make([]string, len(columnOrder))

		rawVals := make([]interface{}, len(columnOrder))
		for i := range rawVals {
			rawVals[i] = new([]byte)
		}

		if err := rows.Scan(rawVals...); err != nil {
			return nil, err
		}

		for i, v := range rawVals {
			bytesVal := *(v.(*[]byte))
			rowVals[i] = string(bytesVal)
		}

		results = append(results, rowVals)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return results, nil

}

// GetTableSchemaForDynamicStruct returns the table schema needed to create the dynamic struct used in bulk insertion
func GetTableSchemaForDynamicStruct(db *sql.DB, tName string) (map[string]string, error) {
	query := `
		SELECT COLUMN_NAME, DATA_TYPE
		FROM INFORMATION_SCHEMA.COLUMNS
		WHERE TABLE_NAME = ?
		ORDER BY ORDINAL_POSITION`

	rows, err := db.Query(query, tName)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	schema := make(map[string]string)
	for rows.Next() {
		var columnName, dataType string
		if err := rows.Scan(&columnName, &dataType); err != nil {
			return nil, err
		}
		schema[columnName] = dataType
	}

	return schema, nil
}

// BulkInsert preforms a bulk insert operation on a table.
func BulkInsert(db *sql.DB, tName string, data []interface{}, structType reflect.Type) error {

	batchSize := 1000

	if len(data) == 0 {
		return fmt.Errorf("no records to insert")
	}

	columnOrder, err := getColumnOrder(db, tName)
	if err != nil {
		return err
	}

	numCols := len(columnOrder)
	numRows := len(data)

	for start := 0; start < numRows; start += batchSize {
		end := start + batchSize
		if end > numRows {
			end = numRows
		}

		rowPlaceholders := make([]string, end-start)

		for i := range rowPlaceholders {
			rowPlaceholders[i] = "(" + strings.Repeat("?,", numCols)[:(numCols*2)-1] + ")"
		}

		placeholders := strings.Join(rowPlaceholders, ", ")

		query := fmt.Sprintf("INSERT INTO %s (%s) VALUES %s",
			tName, strings.Join(columnOrder, ", "), placeholders)

		var values []interface{}
		for _, record := range data[start:end] {
			recordValue := reflect.ValueOf(record)

			for _, column := range columnOrder {
				field := recordValue.FieldByName(ConvertToCamelCase(column))
				if field.IsValid() {
					values = append(values, field.Interface())
				} else {
					values = append(values, nil)
				}
			}
		}

		stmt, err := db.Prepare(query)
		if err != nil {
			return err
		}

		_, err = stmt.Exec(values...)
		if err != nil {
			stmt.Close()
			return err
		}
		stmt.Close()
	}

	return err

}

// getColumnOrder returns the column information in their correct order. Used by BulkInsert.
func getColumnOrder(db *sql.DB, tName string) ([]string, error) {

	query := fmt.Sprintf(`
		SELECT COLUMN_NAME
		FROM INFORMATION_SCHEMA.COLUMNS
		WHERE TABLE_NAME = '%s'
		ORDER BY ORDINAL_POSITION`, tName)

	rows, err := db.Query(query)
	if err != nil {
		return nil, err
	}

	var columns []string
	for rows.Next() {
		var columnName string
		if err := rows.Scan(&columnName); err != nil {
			return nil, err
		}
		columns = append(columns, columnName)
	}

	return columns, nil
}

// CompColumnSearch returns rows from the database based on the search value compared on the compColumn
func CompColumnSearch(db *sql.DB, data CompColumnSearchRequest) ([][]string, error) {

	var query string
	var searchValue string
	if data.Table == "" || data.CompColumn == "" {
		return nil, fmt.Errorf("no data for query")
	}

	columnOrder, err := getColumnOrder(db, data.Table)
	if err != nil {
		return nil, err
	}

	isKeyCol, err := checkIfColumnIsKeyRefrense(db, data.Table, data.CompColumn)
	fmt.Println("Key Col?\t", isKeyCol)
	if err != nil {
		isKeyCol = false
	}
	if isKeyCol {
		query = `SELECT * FROM ` + data.Table + ` WHERE ` + data.CompColumn + ` = ?`
		searchValue = data.SearchValue
	} else {
		query = `SELECT * FROM ` + data.Table + ` WHERE ` + data.CompColumn + ` LIKE ?`
		searchValue = "%" + data.SearchValue + "%"

	}

	rows, err := db.Query(query, searchValue)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results [][]string

	for rows.Next() {
		rowVals := make([]string, len(columnOrder))
		rawVals := make([]interface{}, len(columnOrder))

		for i := range rawVals {
			rawVals[i] = new([]byte)
		}

		if err := rows.Scan(rawVals...); err != nil {
			return nil, err
		}

		for i, v := range rawVals {
			bytesVal := *(v.(*[]byte))
			rowVals[i] = string(bytesVal)
		}
		results = append(results, rowVals)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return results, nil
}

func checkIfColumnIsKeyRefrense(db *sql.DB, tName string, colName string) (bool, error) {
	var count int

	query := `
		SELECT COUNT(*) FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
		WHERE TABLE_SCHEMA = DATABASE()
		AND TABLE_NAME = ?
		AND COLUMN_NAME = ?;
		`

	err := db.QueryRow(query, tName, colName).Scan(&count)
	if err != nil {
		return false, err
	}

	return count > 0, nil
}
