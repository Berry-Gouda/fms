// Package handlers, handles and directs the calls from the frontend and main.go
package handlers

import (
	"encoding/json"
	"fms/db"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"path/filepath"
)

// HandleConnectDB checks the connection to the database from the frontend
func HandleConnectDB(w http.ResponseWriter, r *http.Request) {
	dataB, err := db.CreateDBConnection()
	if err != nil {
		log.Println("Database connection error:", err)
		http.Error(w, "Connection Failed: "+err.Error(), http.StatusInternalServerError)
		return
	}
	defer dataB.Close()

	response := map[string]interface{}{
		"message": "Connection Successful!",
		"success": true,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// HandleTableOverview gathers the data from the database needed to fill the tablepage html template
func HandleTableOverview(w http.ResponseWriter, r *http.Request) {
	tName := r.URL.Query().Get("table")
	if tName == "" {
		http.Error(w, "Table name required", http.StatusBadRequest)
		return
	}

	overviewData, err := db.GatherTableOverviewPageData(tName)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error Gathering Overview Data: %s", err), http.StatusFailedDependency)
	}

	templatePath, _ := filepath.Abs(filepath.Join("../", "../", "app", "frontend", "templates", "tablepage.html"))

	println(templatePath)

	tmpl, err := template.ParseFiles(templatePath)
	if err != nil {
		http.Error(w, "Error Loading Template", http.StatusInternalServerError)
		return
	}

	tmpl.Execute(w, overviewData)
}

// HandleBulkInsert recieves the information required to preform a bulk insert opperation, returning success or failur to the frontend.
func HandleBulkInsert(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		return
	}

	var req db.BulkInsertRequest
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		http.Error(w, "Invalid JSON data", http.StatusBadRequest)
		return
	}

	if req.File == "" {
		http.Error(w, "Missing 'file' parameter", http.StatusBadRequest)
		return
	}

	if filepath.Ext(req.File) != ".csv" {
		http.Error(w, "Must be a CSV file", http.StatusBadRequest)
		return
	}

	mssg, err := db.DBPrepareBulkInsert(req.File, req.Table)
	if err != nil {
		fmt.Println("Error:", err)
	}

	response := map[string]string{
		"message": mssg,
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// HandleSearch recieves and process the information required to search the database
func HandleCompColumnSearch(w http.ResponseWriter, r *http.Request) {

	var response db.CompColumnSearchResponse

	DB, err := db.CreateDBConnection()
	if err != nil {
		fmt.Println("Error on the connection")
	}

	if r.Method != http.MethodPost {
		fmt.Println("Error on the Request")
		http.Error(w, "Invalid request method", http.StatusMethodNotAllowed)
		response.Message = "Invalid request method"
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(response)
	}

	var search db.CompColumnSearchRequest
	err = json.NewDecoder(r.Body).Decode(&search)
	if err != nil {
		http.Error(w, "invalid JSON data", http.StatusBadRequest)
	}

	results, err := db.CompColumnSearch(DB, search)
	if err != nil {
		http.Error(w, "Could Not Exicute Query", http.StatusBadRequest)
	}

	response.Results = results
	response.Count = len(response.Results)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
