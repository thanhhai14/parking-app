# Task list for Phase 5: Web Frontend

## 1. Setup & Project Initialization
- [x] Initialize Vue 3 + Vite + TypeScript project in `apps/parking-web`
- [x] Configure `package.json` dependencies (Axios, Vue Router, Pinia, TailwindCSS, PostCSS, Autoprefixer, Lucide icons)
- [x] Configure `vite.config.ts`, `tailwind.config.js`, `postcss.config.js`, and TypeScript aliases
- [x] Create `apps/parking-web/Dockerfile`

## 2. Implement Core Services & Pinia Stores
- [x] Create Axios client at `src/services/api.ts` with auto JWT header injection
- [x] Create Auth store at `src/stores/auth.ts`
- [x] Create WebSocket store at `src/stores/websocket.ts` (handle auto-reconnect, hearbeats, event router)
- [x] Create Parking store at `src/stores/parking.ts`
- [x] Create Devices store at `src/stores/devices.ts`

## 3. Create Views & Layouts
- [x] Create `DefaultLayout.vue` and `Login.vue`
- [x] Create `Dashboard.vue` with stats cards and device map (realtime connectivity)
- [x] Create `LaneMonitor.vue` with split lane view (entry/exit) and simulated live camera feeds, visual logs, and manual barrier triggers
- [x] Create `Cards.vue` (RFID card management CRUD)
- [x] Create `Vehicles.vue` (Monthly member vehicle CRUD)
- [x] Create `Devices.vue` (Physical device config CRUD)
- [x] Create `History.vue` (Parking sessions log table with filters)

## 4. Testing & Verification
- [x] Create integration test `test/05_web_frontend_integration_test.py`
- [x] Run test suite: `docker compose exec -T -e PYTHONPATH=. parking-api pytest test/05_web_frontend_integration_test.py`
- [x] Build and verify frontend functionality via local browser on `http://localhost:3000`
