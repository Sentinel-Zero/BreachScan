package main

import (
	"encoding/json"
	"html/template"
	"log"
	"net/http"
)

// Adjust if your backend runs somewhere other than 8000
const backendBaseURL = "http://127.0.0.1:8000"

// Asset matches one asset object from your backend
type Asset struct {
	ID          string   `json:"id"`
	Hostname    string   `json:"hostname"`
	IPv4s       []string `json:"ipv4s"`
	RiskScore   float64  `json:"risk_score"`
	Critical    int      `json:"critical_vulns"`
	High        int      `json:"high_vulns"`
	OperatingOS []string `json:"operating_system"`
}

// Response shape from /tenable/assets: { "assets": [ ... ] }
type AssetsResponse struct {
	Assets []Asset `json:"assets"`
}

// --- Scheduled scan types ---

type Schedule struct {
	Type string  `json:"type"` // once, daily, weekly
	Day  *string `json:"day"`  // e.g. "Sunday" or null
	Time string  `json:"time"` // "02:00"
}

type ScheduledScan struct {
	ID                  string   `json:"id"`
	Name                string   `json:"name"`
	Targets             []string `json:"targets"`
	ExpandedTargetCount int      `json:"expanded_target_count"`
	Schedule            Schedule `json:"schedule"`
	NextRunAt           *string  `json:"next_run_at"`
	CreatedAt           string   `json:"created_at"`
	Enabled             bool     `json:"enabled"`
	Status              string   `json:"status"`
}

// Backend returns: { "scans": [ ... ] }
type ScheduledScansResponse struct {
	Scans []ScheduledScan `json:"scans"`
}

// Parse disk-based templates
var templates = template.Must(template.ParseFiles(
	"templates/index.html",
	"templates/scheduler.html",
))

func main() {
	http.HandleFunc("/", handleIndex)
	http.HandleFunc("/scheduler", handleScheduler)

	log.Println("Go frontend running on http://localhost:8080 ...")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatal(err)
	}
}

func handleIndex(w http.ResponseWriter, r *http.Request) {
	// --- Assets ---
	resp, err := http.Get(backendBaseURL + "/tenable/assets")
	if err != nil {
		http.Error(w, "Error calling backend for assets: "+err.Error(), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		http.Error(w, "Backend returned status for assets: "+resp.Status, http.StatusBadGateway)
		return
	}

	var assetsResp AssetsResponse
	if err := json.NewDecoder(resp.Body).Decode(&assetsResp); err != nil {
		http.Error(w, "Error decoding assets response: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// --- Scheduled scans ---
	var scheduledScans []ScheduledScan
	schedResp, err := http.Get(backendBaseURL + "/tenable/scheduled-scans")
	if err == nil {
		defer schedResp.Body.Close()
		if schedResp.StatusCode == http.StatusOK {
			var scansResp ScheduledScansResponse
			if err := json.NewDecoder(schedResp.Body).Decode(&scansResp); err == nil {
				scheduledScans = scansResp.Scans
			}
		}
		// if it fails, we just leave scheduledScans empty; assets still show
	}

	data := struct {
		BackendURL     string
		Assets         []Asset
		ScheduledScans []ScheduledScan
	}{
		BackendURL:     backendBaseURL,
		Assets:         assetsResp.Assets,
		ScheduledScans: scheduledScans,
	}

	if err := templates.ExecuteTemplate(w, "index.html", data); err != nil {
		http.Error(w, "Template error: "+err.Error(), http.StatusInternalServerError)
		return
	}
}

func handleScheduler(w http.ResponseWriter, r *http.Request) {
	data := struct {
		BackendURL string
	}{
		BackendURL: backendBaseURL,
	}

	if err := templates.ExecuteTemplate(w, "scheduler.html", data); err != nil {
		http.Error(w, "Template error: "+err.Error(), http.StatusInternalServerError)
		return
	}
}
