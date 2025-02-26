package db

import (
	"fmt"
	"reflect"
	"strings"

	"golang.org/x/text/cases"
	"golang.org/x/text/language"
)

// TableOverview represents the data needed on the intial loading of a table overview page.
type TableOverview struct {
	Name       string
	SchemaInfo []TableSchemaInfo
	RowCount   int
	RandRows   [][]string
}

// TableSchemaInfo represents the schema information for a table on the table overview page.
type TableSchemaInfo struct {
	ColName    string
	DType      string
	KeyType    string
	IsNull     string
	ColDefault string
}

// BulkInsertRequest represents the data passed from the front end to preform a bulk insert from csv.
type BulkInsertRequest struct {
	File  string `json:"file"`
	Table string `json:"table"`
}

// SearchRequest represents the data passed from the front end to preform a search
type CompColumnSearchRequest struct {
	Table       string `json:"table"`
	CompColumn  string `json:"compColumn"`
	SearchValue string `json:"searchValue"`
}

type CompColumnSearchResponse struct {
	Message string     `json:msg`
	Results [][]string `json:"results"`
	Count   int        `json:"count"`
}

// nutrient_lu_data represents the nutrient_lu table in the DB.
type nutrient_lu_data struct {
	nutrient_id int
	name        string
}

// nutrient_cat_lu_data represents the nutrient_cat_lu table in the DB.
type nutrient_cat_lu_data struct {
	cat_id int
	name   string
}

// unit_lu_data represents the unit_lu table in the DB.
type unit_lu_data struct {
	unit_id int
	name    string
}

// tag_lu_data represents the tag_lu table in the DB.
type tag_lu_data struct {
	tag_id int
	name   string
}

// timing_lu_data represents the timing_lu table in the DB.
type timing_lu_data struct {
	timing_id int
	name      string
}

// method_data represents the method table in the DB.
type method_data struct {
	method_id   int
	step        int
	instruction string
}

// nutrition_junc_data represents the nutrition_junc table in the DB.
type nutrition_junc_data struct {
	nut_junc_id     int
	item_id         int
	nutrient_id     int
	nutrient_cat_id int
	ammount         float32
	unit_id         int
}

// conversion_junc_data represents the conversion_junc table in the DB.
type conversion_junc_data struct {
	conversion_id int
	item_id       int
	unit_id       int
	unit_alt      int
	unit_measure  float32
	ammount       float32
}

// tag_junc_data represents the tag_junc table in the DB.
type tag_junc_data struct {
	tag_junc_id int
	tag_id      int
	item_id     int
	recipe_id   int
}

// recipe_item_junc_data represents the recipe_item_junc table in the DB.
type recipe_item_junc_data struct {
	recipe_item_junc_id int
	item_id             int
	recipe_id           int
	unit_id             int
	unit_amt            float32
	item_grouping       string
}

// timing_junc_data represents the timing_junc table in the DB.
type timing_junc_data struct {
	timing_junc_id int
	recipe_id      int
	timing_id      int
	value          float32
}

// method_junc_data represents the method_junc table in the DB.
type method_junc_data struct {
	method_junc_id int
	method_id      int
	recipe_id      int
}

// item_data represents the item table in the DB.
type item_data struct {
	item_id         int
	name            string
	brand           string
	NLEA_unit       int
	NLEA_val        float32
	ammount         float32
	ammount_unit    int
	upc             string
	ingredient_list string
}

// recipe_data represents the recipe table in the DB.
type recipe_data struct {
	recipe_id int
	name      string
	servings  int
	yield_amt float32
	yield_unt int
	source    string
}

// CreateDynamicStruct creates a struct based on a table's schema.
func CreateDynamicStruct(schema map[string]string) reflect.Type {
	var fields []reflect.StructField

	for col, dtype := range schema {
		var fieldType reflect.Type

		switch dtype {
		case "int", "bigint", "int unsigned":
			fieldType = reflect.TypeOf(int(0))
		case "float", "double", "decimal":
			fieldType = reflect.TypeOf(float64(0))
		case "varchar", "text":
			fieldType = reflect.TypeOf("")
		default:
			fieldType = reflect.TypeOf(interface{}(nil))
		}

		fields = append(fields, reflect.StructField{
			Name: ConvertToCamelCase(col),
			Type: fieldType,
			Tag:  reflect.StructTag(fmt.Sprintf(`json:"%s"`, col)),
		})
	}

	return reflect.StructOf(fields)

}

// ConvertToCamelCase Converts a table name into the correct format for a go struct.
func ConvertToCamelCase(input string) string {
	parts := strings.Split(input, "_")
	for i := range parts {
		parts[i] = cases.Title(language.Und).String(parts[i])
	}
	return strings.Join(parts, "")
}
