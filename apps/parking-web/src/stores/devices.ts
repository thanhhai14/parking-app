import { defineStore } from 'pinia'
import api from '@/services/api'

export interface Device {
  id: string
  gate_id: string | null
  code: string
  name: string
  device_type: string
  connection_type: string
  status: string // online, offline
  is_active: boolean
}

export interface Camera {
  id: string
  gate_id: string | null
  code: string
  name: string
  camera_type: string
  role: string // entry, exit, overview
  status: string // online, offline
  stream_url: string | null
  is_active: boolean
}

export interface Gate {
  id: string
  zone_id: string
  code: string
  name: string
  gate_type: string
  direction: string
}

export const useDevicesStore = defineStore('devices', {
  state: () => ({
    devices: [] as Device[],
    cameras: [] as Camera[],
    gates: [] as Gate[],
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchDevices() {
      this.loading = true
      try {
        const response = await api.get('/api/v1/devices/')
        this.devices = response.data
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async fetchCameras() {
      this.loading = true
      try {
        const response = await api.get('/api/v1/devices/cameras')
        this.cameras = response.data
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async fetchGates() {
      this.loading = true
      try {
        const response = await api.get('/api/v1/devices/gates')
        this.gates = response.data
      } catch (err: any) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },
    async controlBarrier(deviceId: string) {
      try {
        const response = await api.post(`/api/v1/devices/${deviceId}/control`, {
          command: 'barrier.open'
        })
        return response.data
      } catch (err: any) {
        console.error('Failed to trigger manual barrier open:', err)
        throw err
      }
    },
    updateDeviceStatus(deviceCode: string, status: string) {
      const dev = this.devices.find(d => d.code === deviceCode)
      if (dev) {
        dev.status = status
      }
    },
    updateCameraStatus(cameraCode: string, status: string) {
      const cam = this.cameras.find(c => c.code === cameraCode)
      if (cam) {
        cam.status = status
      }
    }
  }
})
