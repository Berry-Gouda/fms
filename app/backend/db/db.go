// Package db provides utilities for calling queries and returning the data gathered back to the front end.
package db

import (
	"database/sql"
	"encoding/csv"
	"fmt"
	"log"
	"os"
	"reflect"
	"strconv"

	"github.com/go-sql-driver/mysql"
	_ "github.com/go-sql-driver/mysql"
)

var DB *sql.DB

// InitDB opens a connection to the database without ever calling for it to close.
func InitDB() {
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s",
		os.Getenv("DBUSER"),
		os.Getenv("DBPASS"),
		"127.0.0.1",
		"3306",
		os.Getenv("DBNAME"),
	)

	var err error

	DB, err = sql.Open("mysql", dsn)
	if err != nil {
		log.Fatal("Error opening Database:", err)
	}

	if err = DB.Ping(); err != nil {
		log.Fatal("Error Connecting to Database:", err)
	}
}

// CloseDB will close the DB connection opened by InitDB
func CloseDB() {
	DB.Close()
}

// getDBConfig returns the configueration values gathered from the enviornment
func getDBConfig() mysql.Config {

	return mysql.Config{
		User:   os.Getenv("DBUSER"),
		Passwd: os.Getenv("DBPASS"),
		Net:    "tcp",
		Addr:   "127.0.0.1:3306",
		DBName: os.Getenv("DBNAME"),
	}
}

// CreateDBConnection creates and returns a sql.DB connection, this connection must be closed when called.
func CreateDBConnection() (*sql.DB, error) {
	dbConfig := getDBConfig()
	dsn := dbConfig.FormatDSN()

	db, err := sql.Open("mysql", dsn)

	if err != nil {
		return nil, err
	}
	err = db.Ping()
	if err != nil {
		return nil, err
	}
	return db, nil
}

// GatherTableOverviewPageData returns the data for to be displayed on the table overview page.
func GatherTableOverviewPageData(tName string) (TableOverview, error) {

	var data TableOverview
	var schema []TableSchemaInfo

	db, err := CreateDBConnection()
	if err != nil {
		return data, err
	}
	defer db.Close()

	count, err := GetTableRowCount(tName, db)
	if err != nil {
		return data, err
	}

	schema, err = GetTableOverviewInfo(tName, db)
	if err != nil {
		return data, err
	}

	var rRows [][]string

	if count > 0 {
		tSchema, err := GetTableSchemaForDynamicStruct(db, tName)
		if err != nil {
			return data, err
		}

		structType := CreateDynamicStruct(tSchema)

		rRows, err = GetRandomRows(db, 20, tName, structType)
		if err != nil {
			return data, err
		}
	} else {
		rRows = nil
	}

	data.RowCount = count
	data.Name = tName
	data.SchemaInfo = schema
	data.RandRows = rRows

	return data, err
}

// DBPrepareBulkInsert Calls all the functions to create the Struct and load the bulk data from a csv file.
func DBPrepareBulkInsert(file string, tName string) (string, error) {

	db, err := CreateDBConnection()
	if err != nil {
		return "Error", err
	}
	defer db.Close()

	schema, err := GetTableSchemaForDynamicStruct(db, tName)
	if err != nil {
		return "Error", err
	}

	dynamicStruct := CreateDynamicStruct(schema)

	loadedInsertData, err := openCSV(dynamicStruct, file)
	if err != nil {
		fmt.Println("Error:", err)
		return "Error", err
	}

	counter := 0

	for _, record := range loadedInsertData {
		if counter == 20 {
			break
		}
		fmt.Printf("%v\n", record)
		counter += 1
	}

	err = BulkInsert(db, tName, loadedInsertData, dynamicStruct)
	if err != nil {
		fmt.Println("Insert error:", err)
		return "Failed", err
	} else {
		fmt.Println("Bulk insert successful!")
	}

	return "Success", nil
}

// openCSV loads a CSV file of any format into a dynamically created struct. Returns a slice of an interface
func openCSV(structType reflect.Type, path string) ([]interface{}, error) {

	file, err := os.Open(path)

	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	rows, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}

	if len(rows) < 2 {
		return nil, fmt.Errorf("CSV file is empty or missing headers")
	}

	headers := rows[0]

	var result []interface{}

	for _, row := range rows[1:] {
		instance := reflect.New(structType).Elem()

		for i, colName := range headers {
			field := instance.FieldByName(ConvertToCamelCase(colName))
			if !field.IsValid() {
				fmt.Println("invalid Field name:", field)
				continue

			}

			switch field.Kind() {
			case reflect.Int, reflect.Int64:
				val, err := strconv.Atoi(row[i])
				if err == nil {
					field.SetInt(int64(val))

				}
			case reflect.Float64:
				val, err := strconv.ParseFloat(row[i], 64)
				if err == nil {
					field.SetFloat(val)
				}
			case reflect.String:
				field.SetString(row[i])
			}
		}
		result = append(result, instance.Interface())
	}

	return result, nil
}
