# Project Tree

parking-system/

├── README.md

├── LICENSE

├── docker-compose.yml

├── .env.example

│

├── apps/

│ ├── parking-web/

│ ├── parking-api/

│ ├── parking-gateway/

│ ├── parking-device-agent/

│ ├── parking-camera-agent/

│ └── parking-worker/

│

├── deploy/

│ ├── nginx/

│ ├── postgres/

│ ├── redis/

│ └── minio/

│

├── docs/

│ ├── ARCHITECTURE.md

│ ├── DATABASE.md

│ ├── API_REFERENCE.md

│ ├── PLUGIN_SYSTEM.md

│ ├── DEPLOYMENT.md

│ ├── CONTRIBUTING.md

│

│ └── services/

│ ├── api.md

│ ├── web.md

│ ├── gateway.md

│ ├── device-agent.md

│ ├── camera-agent.md

│ └── worker.md

│

├── plugins/

│ ├── rfid/

│ ├── barrier/

│ ├── camera/

│ └── alpr/

│

└── scripts/

├── start.sh

├── stop.sh

└── backup.sh
