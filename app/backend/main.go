package main

import (
	"fms/handlers"
	"fmt"
	"log"
	"net/http"
	"path/filepath"
)

func main() {
	staticDir, _ := filepath.Abs(filepath.Join("../", "frontend"))
	http.Handle("/static/", http.StripPrefix("/static", http.FileServer(http.Dir(staticDir))))
	http.HandleFunc("/connect-db", handlers.HandleConnectDB)
	http.HandleFunc("/table-page", handlers.HandleTableOverview)
	http.HandleFunc("/bulk-insert", handlers.HandleBulkInsert)
	http.HandleFunc("/comp-column-search", handlers.HandleCompColumnSearch)
	fmt.Println("Go Server Running on http://localhost:8080")
	log.Fatal(http.ListenAndServe(":8080", nil))
}
