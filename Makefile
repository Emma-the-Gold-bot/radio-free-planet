.PHONY: help run-backend validate-streams sync-bad

help:
	@echo "Available targets:"
	@echo "  make run-backend      - Start backend API server"
	@echo "  make validate-streams - Run playback matrix + bad-list + health sync"
	@echo "  make sync-bad         - Sync health_status from bad_stations.json only"

run-backend:
	@bash -lc 'cd backend && source venv/bin/activate && python main.py'

validate-streams:
	@bash -lc 'cd backend && source venv/bin/activate && python playback_matrix.py'

sync-bad:
	@bash -lc 'cd backend && source venv/bin/activate && python sync_bad_stations.py'
