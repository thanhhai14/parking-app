<template>
  <div class="space-y-8">
    
    <!-- Section: Physical Devices (Barriers, Readers) -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-bold text-slate-200 text-base flex items-center gap-2">
            <CpuIcon class="w-4 h-4 text-blue-500" />
            <span>Thiết bị phần cứng (Readers / Barriers)</span>
          </h3>
          <p class="text-xs text-slate-500 mt-1">Các barrier và đầu đọc RFID liên kết với cổng kiểm soát</p>
        </div>
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-950/40 border-b border-slate-800 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                <th class="py-4 px-6">Mã thiết bị</th>
                <th class="py-4 px-6">Tên gọi</th>
                <th class="py-4 px-6">Loại</th>
                <th class="py-4 px-6">Kiểu kết nối</th>
                <th class="py-4 px-6">Trạng thái kết nối</th>
                <th class="py-4 px-6">Cổng (Gate) gán</th>
                <th class="py-4 px-6 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 text-sm">
              <tr 
                v-for="d in devicesStore.devices" 
                :key="d.id" 
                class="hover:bg-slate-950/20 text-slate-300 transition-colors"
              >
                <td class="py-4 px-6 font-mono text-slate-400 text-xs">{{ d.code }}</td>
                <td class="py-4 px-6 font-semibold text-slate-200">{{ d.name }}</td>
                <td class="py-4 px-6">
                  <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400 capitalize">
                    {{ d.device_type }}
                  </span>
                </td>
                <td class="py-4 px-6 text-xs text-slate-500 font-mono capitalize">{{ d.connection_type }}</td>
                <td class="py-4 px-6">
                  <span 
                    class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase"
                    :class="[
                      d.status === 'online' 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : 'bg-slate-800 text-slate-500 border border-slate-700/30'
                    ]"
                  >
                    {{ d.status }}
                  </span>
                </td>
                <td class="py-4 px-6 text-xs text-slate-400">
                  <span class="font-mono">{{ getGateName(d.gate_id) }}</span>
                </td>
                <td class="py-4 px-6 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button 
                      @click="openEditDeviceModal(d)"
                      class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-blue-400 transition-colors"
                      title="Sửa"
                    >
                      <EditIcon class="w-4 h-4" />
                    </button>
                    <button 
                      @click="handleDeleteDevice(d)"
                      class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
                      title="Xóa"
                    >
                      <TrashIcon class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="devicesStore.devices.length === 0 && !devicesStore.loading">
                <td colspan="7" class="text-center py-8 text-slate-600 italic">Chưa có thiết bị nào được cấu hình.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Section: Cameras -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="font-bold text-slate-200 text-base flex items-center gap-2">
            <CameraIcon class="w-4 h-4 text-blue-500" />
            <span>Camera giám sát làn xe</span>
          </h3>
          <p class="text-xs text-slate-500 mt-1">Danh sách camera nhận diện biển số hoặc chụp ảnh toàn cảnh</p>
        </div>
      </div>

      <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div class="overflow-x-auto">
          <table class="w-full text-left border-collapse">
            <thead>
              <tr class="bg-slate-950/40 border-b border-slate-800 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                <th class="py-4 px-6">Mã Camera</th>
                <th class="py-4 px-6">Tên camera</th>
                <th class="py-4 px-6">Vai trò</th>
                <th class="py-4 px-6">Địa chỉ Luồng</th>
                <th class="py-4 px-6">Kết nối</th>
                <th class="py-4 px-6">Cổng (Gate) gán</th>
                <th class="py-4 px-6 text-right">Thao tác</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 text-sm">
              <tr 
                v-for="c in devicesStore.cameras" 
                :key="c.id" 
                class="hover:bg-slate-950/20 text-slate-300 transition-colors"
              >
                <td class="py-4 px-6 font-mono text-slate-400 text-xs">{{ c.code }}</td>
                <td class="py-4 px-6 font-semibold text-slate-200">{{ c.name }}</td>
                <td class="py-4 px-6">
                  <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 uppercase">
                    {{ c.role }}
                  </span>
                </td>
                <td class="py-4 px-6 text-xs text-slate-500 font-mono truncate max-w-[200px]" :title="c.stream_url || '---'">
                  {{ c.stream_url || 'Mock Stream' }}
                </td>
                <td class="py-4 px-6">
                  <span 
                    class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase"
                    :class="[
                      c.status === 'online' 
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                        : 'bg-slate-800 text-slate-500 border border-slate-700/30'
                    ]"
                  >
                    {{ c.status }}
                  </span>
                </td>
                <td class="py-4 px-6 text-xs text-slate-400">
                  <span class="font-mono">{{ getGateName(c.gate_id) }}</span>
                </td>
                <td class="py-4 px-6 text-right">
                  <div class="flex items-center justify-end gap-2">
                    <button 
                      @click="openEditCameraModal(c)"
                      class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-blue-400 transition-colors"
                      title="Sửa"
                    >
                      <EditIcon class="w-4 h-4" />
                    </button>
                    <button 
                      @click="handleDeleteCamera(c)"
                      class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
                      title="Xóa"
                    >
                      <TrashIcon class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="devicesStore.cameras.length === 0 && !devicesStore.loading">
                <td colspan="7" class="text-center py-8 text-slate-600 italic">Chưa có camera nào được cấu hình.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Edit Device Modal -->
    <div v-if="showEditDeviceModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <!-- Modal Header -->
        <div class="p-6 border-b border-slate-800 flex items-center justify-between">
          <h4 class="font-bold text-slate-200 text-base">Chỉnh sửa Thiết bị</h4>
          <button @click="showEditDeviceModal = false" class="text-slate-500 hover:text-slate-300 text-sm font-semibold">✕</button>
        </div>
        
        <!-- Modal Form -->
        <form @submit.prevent="handleUpdateDevice" class="p-6 space-y-4">
          <!-- Code -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Mã thiết bị</label>
            <input 
              v-model="editingDevice.code" 
              type="text" 
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Name -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Tên thiết bị</label>
            <input 
              v-model="editingDevice.name" 
              type="text" 
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Device Type -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Loại thiết bị</label>
            <select 
              v-model="editingDevice.device_type"
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="reader">Đầu đọc RFID (Reader)</option>
              <option value="barrier">Cổng đóng mở (Barrier)</option>
              <option value="controller">Bộ điều khiển trung tâm</option>
            </select>
          </div>

          <!-- Connection Type -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Kiểu kết nối</label>
            <select 
              v-model="editingDevice.connection_type"
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="tcp">TCP/IP</option>
              <option value="serial">Serial Port (RS485/RS232)</option>
              <option value="mqtt">MQTT Broker</option>
            </select>
          </div>

          <!-- Gate (Gate ID) -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Cổng gán</label>
            <select 
              v-model="editingDevice.gate_id"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="null">Chưa gán cổng</option>
              <option v-for="g in devicesStore.gates" :key="g.id" :value="g.id">
                {{ g.name }} ({{ g.code }})
              </option>
            </select>
          </div>

          <!-- Agent ID -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Agent ID</label>
            <input 
              v-model="editingDevice.agent_id" 
              type="text" 
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Error Feedback -->
          <div v-if="modalError" class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
            {{ modalError }}
          </div>

          <!-- Modal Actions -->
          <div class="pt-4 border-t border-slate-800 flex gap-3">
            <button 
              type="button" 
              @click="showEditDeviceModal = false" 
              class="flex-1 py-2.5 border border-slate-800 hover:bg-slate-950 text-slate-400 text-xs font-semibold rounded-xl"
            >
              Hủy
            </button>
            <button 
              type="submit" 
              :disabled="submitting"
              class="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/10 flex items-center justify-center gap-1.5"
            >
              <LoaderIcon v-if="submitting" class="w-3.5 h-3.5 animate-spin" />
              <span>Cập nhật</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Camera Modal -->
    <div v-if="showEditCameraModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <!-- Modal Header -->
        <div class="p-6 border-b border-slate-800 flex items-center justify-between">
          <h4 class="font-bold text-slate-200 text-base">Chỉnh sửa Camera</h4>
          <button @click="showEditCameraModal = false" class="text-slate-500 hover:text-slate-300 text-sm font-semibold">✕</button>
        </div>
        
        <!-- Modal Form -->
        <form @submit.prevent="handleUpdateCamera" class="p-6 space-y-4">
          <!-- Code -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Mã Camera</label>
            <input 
              v-model="editingCamera.code" 
              type="text" 
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Name -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Tên Camera</label>
            <input 
              v-model="editingCamera.name" 
              type="text" 
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Role -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Vai trò</label>
            <select 
              v-model="editingCamera.role"
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="plate">Nhận diện biển số (plate)</option>
              <option value="overview">Toàn cảnh (overview)</option>
              <option value="plate_front">Biển số trước (plate_front)</option>
              <option value="plate_back">Biển số sau (plate_back)</option>
            </select>
          </div>

          <!-- Stream URL -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Địa chỉ Luồng Stream</label>
            <input 
              v-model="editingCamera.stream_url" 
              type="text" 
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Snapshot URL -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Địa chỉ Chụp ảnh (Snapshot URL)</label>
            <input 
              v-model="editingCamera.snapshot_url" 
              type="text" 
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Gate (Gate ID) -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Cổng gán</label>
            <select 
              v-model="editingCamera.gate_id"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="null">Chưa gán cổng</option>
              <option v-for="g in devicesStore.gates" :key="g.id" :value="g.id">
                {{ g.name }} ({{ g.code }})
              </option>
            </select>
          </div>

          <!-- Agent ID -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Agent ID</label>
            <input 
              v-model="editingCamera.agent_id" 
              type="text" 
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Error Feedback -->
          <div v-if="modalError" class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
            {{ modalError }}
          </div>

          <!-- Modal Actions -->
          <div class="pt-4 border-t border-slate-800 flex gap-3">
            <button 
              type="button" 
              @click="showEditCameraModal = false" 
              class="flex-1 py-2.5 border border-slate-800 hover:bg-slate-950 text-slate-400 text-xs font-semibold rounded-xl"
            >
              Hủy
            </button>
            <button 
              type="submit" 
              :disabled="submitting"
              class="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/10 flex items-center justify-center gap-1.5"
            >
              <LoaderIcon v-if="submitting" class="w-3.5 h-3.5 animate-spin" />
              <span>Cập nhật</span>
            </button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import { useDevicesStore } from '@/stores/devices'
import { CpuIcon, CameraIcon, EditIcon, TrashIcon, LoaderIcon } from 'lucide-vue-next'

const devicesStore = useDevicesStore()

const showEditDeviceModal = ref(false)
const showEditCameraModal = ref(false)
const submitting = ref(false)
const modalError = ref<string | null>(null)

const editingDevice = ref<any>({
  id: '',
  code: '',
  name: '',
  device_type: 'reader',
  connection_type: 'tcp',
  gate_id: null,
  agent_id: ''
})

const editingCamera = ref<any>({
  id: '',
  code: '',
  name: '',
  camera_type: 'ip',
  role: 'plate',
  stream_url: '',
  snapshot_url: '',
  gate_id: null,
  agent_id: ''
})

const getGateName = (id: string | null) => {
  if (!id) return 'Chưa gán'
  const g = devicesStore.gates.find(item => item.id === id)
  return g ? g.name : 'Chưa gán'
}

const openEditDeviceModal = (d: any) => {
  editingDevice.value = {
    id: d.id,
    code: d.code,
    name: d.name,
    device_type: d.device_type,
    connection_type: d.connection_type,
    gate_id: d.gate_id,
    agent_id: d.agent_id || ''
  }
  modalError.value = null
  showEditDeviceModal.value = true
}

const handleUpdateDevice = async () => {
  submitting.value = true
  modalError.value = null
  try {
    await api.put(`/api/v1/devices/${editingDevice.value.id}`, editingDevice.value)
    showEditDeviceModal.value = false
    devicesStore.fetchDevices()
  } catch (err: any) {
    console.error('Update device error:', err)
    modalError.value = err.response?.data?.detail || 'Cập nhật thiết bị thất bại.'
  } finally {
    submitting.value = false
  }
}

const handleDeleteDevice = async (d: any) => {
  if (!confirm(`Bạn có chắc chắn muốn xóa thiết bị ${d.name}?`)) {
    return
  }
  try {
    await api.delete(`/api/v1/devices/${d.id}`)
    devicesStore.fetchDevices()
  } catch (err: any) {
    alert(`Xóa thiết bị thất bại: ${err.response?.data?.detail || err.message}`)
  }
}

const openEditCameraModal = (c: any) => {
  editingCamera.value = {
    id: c.id,
    code: c.code,
    name: c.name,
    camera_type: c.camera_type || 'ip',
    role: c.role,
    stream_url: c.stream_url || '',
    snapshot_url: c.snapshot_url || '',
    gate_id: c.gate_id,
    agent_id: c.agent_id || ''
  }
  modalError.value = null
  showEditCameraModal.value = true
}

const handleUpdateCamera = async () => {
  submitting.value = true
  modalError.value = null
  try {
    await api.put(`/api/v1/devices/cameras/${editingCamera.value.id}`, editingCamera.value)
    showEditCameraModal.value = false
    devicesStore.fetchCameras()
  } catch (err: any) {
    console.error('Update camera error:', err)
    modalError.value = err.response?.data?.detail || 'Cập nhật camera thất bại.'
  } finally {
    submitting.value = false
  }
}

const handleDeleteCamera = async (c: any) => {
  if (!confirm(`Bạn có chắc chắn muốn xóa camera ${c.name}?`)) {
    return
  }
  try {
    await api.delete(`/api/v1/devices/cameras/${c.id}`)
    devicesStore.fetchCameras()
  } catch (err: any) {
    alert(`Xóa camera thất bại: ${err.response?.data?.detail || err.message}`)
  }
}

onMounted(() => {
  devicesStore.fetchDevices()
  devicesStore.fetchCameras()
  devicesStore.fetchGates()
})
</script>
