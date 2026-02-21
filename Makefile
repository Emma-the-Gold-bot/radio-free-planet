.PHONY: help run-backend validate-streams sync-bad refresh-schedules refresh-schedules-dry run-schedule-worker

help:
	@echo "Available targets:"
	@echo "  make run-backend      - Start backend API server"
	@echo "  make validate-streams - Run playback matrix + bad-list + health sync"
	@echo "  make sync-bad         - Sync health_status from bad_stations.json only"
	@echo "  make refresh-schedules - Run tiered schedule + now-playing refresh once"
	@echo "  make refresh-schedules-dry - Dry-run refresh without writing files"
	@echo "  make run-schedule-worker - Refresh schedules every 5 minutes"

run-backend:
	@bash -lc 'cd backend && source venv/bin/activate && python main.py'

validate-streams:
	@bash -lc 'cd backend && source venv/bin/activate && python playback_matrix.py'

sync-bad:
	@bash -lc 'cd backend && source venv/bin/activate && python sync_bad_stations.py'

refresh-schedules:
	@bash -lc 'cd backend && source venv/bin/activate && python schedule_refresh.py'

refresh-schedules-dry:
	@bash -lc 'cd backend && source venv/bin/activate && python schedule_refresh.py --dry-run'

run-schedule-worker:
	@bash -lc 'cd backend && source venv/bin/activate && python schedule_refresh.py --worker --interval-seconds 300'
