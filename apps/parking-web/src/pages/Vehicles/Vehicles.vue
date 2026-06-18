<template>
  <div class="space-y-6">
    <!-- Header Controls -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <p class="text-xs text-slate-500 font-medium">Danh sách xe ô tô, xe máy gửi vé tháng đăng ký trước</p>
      </div>
      <button 
        @click="openCreateModal"
        class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all duration-200 shadow-lg shadow-blue-500/10 shrink-0 self-start sm:self-auto"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Đăng ký xe tháng</span>
      </button>
    </div>

    <!-- Vehicles Data Table -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-950/40 border-b border-slate-800 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
              <th class="py-4 px-6">Biển số</th>
              <th class="py-4 px-6">Loại xe</th>
              <th class="py-4 px-6">Hiệu/Mẫu</th>
              <th class="py-4 px-6">Chủ sở hữu</th>
              <th class="py-4 px-6">Trạng thái</th>
              <th class="py-4 px-6">Ngày đăng ký</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60 text-sm">
            <tr 
              v-for="v in vehicles" 
              :key="v.id" 
              class="hover:bg-slate-950/20 text-slate-300 transition-colors"
            >
              <td class="py-4 px-6 font-mono font-bold text-slate-100">{{ v.plate_number }}</td>
              <td class="py-4 px-6">
                <span class="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-500/10 text-blue-400">
                  {{ v.vehicle_type?.name || 'Chưa phân loại' }}
                </span>
              </td>
              <td class="py-4 px-6 text-slate-400">{{ v.brand }} {{ v.model }} <span v-if="v.color">({{ v.color }})</span></td>
              <td class="py-4 px-6 text-xs text-slate-300">
                <div v-if="v.owner" class="flex flex-col">
                  <span>{{ v.owner.full_name }}</span>
                  <span class="text-[10px] text-slate-500">{{ v.owner.phone }}</span>
                </div>
                <span v-else class="text-slate-600">Vô chủ / Không gán</span>
              </td>
              <td class="py-4 px-6">
                <span 
                  class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                  :class="[v.is_active ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-500']"
                >
                  {{ v.is_active ? 'Kích hoạt' : 'Khóa' }}
                </span>
              </td>
              <td class="py-4 px-6 text-xs text-slate-500">{{ formatDate(v.created_at) }}</td>
              <td class="py-4 px-6 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button 
                    @click="openEditModal(v)"
                    class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-blue-400 transition-colors"
                    title="Sửa"
                  >
                    <EditIcon class="w-4 h-4" />
                  </button>
                  <button 
                    @click="handleDeleteVehicle(v)"
                    class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
                    title="Xóa"
                  >
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="vehicles.length === 0 && !loading">
              <td colspan="7" class="text-center py-12 text-slate-600 italic">Chưa có xe thành viên nào được đăng ký.</td>
            </tr>
            <tr v-if="loading">
              <td colspan="7" class="text-center py-12">
                <LoaderIcon class="w-6 h-6 animate-spin text-blue-500 mx-auto" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Vehicle Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <!-- Modal Header -->
        <div class="p-6 border-b border-slate-800 flex items-center justify-between">
          <h4 class="font-bold text-slate-200 text-base">Đăng ký Xe tháng mới</h4>
          <button @click="showModal = false" class="text-slate-500 hover:text-slate-300 text-sm font-semibold">✕</button>
        </div>
        
        <!-- Modal Form -->
        <form @submit.prevent="handleCreateVehicle" class="p-6 space-y-4">
          <!-- Plate Number -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Biển số xe</label>
            <input 
              v-model="newVehicle.plate_number" 
              type="text" 
              required
              placeholder="Ví dụ: 30F-12345"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Vehicle Type -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Loại xe</label>
            <select 
              v-model="newVehicle.vehicle_type_id"
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="''" disabled>-- Chọn loại xe --</option>
              <option v-for="t in vehicleTypes" :key="t.id" :value="t.id">
                {{ t.name }} ({{ t.code }})
              </option>
            </select>
          </div>

          <!-- Vehicle Owner -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Chủ sở hữu (Tùy chọn)</label>
            <select 
              v-model="newVehicle.owner_id"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="null">Không gán chủ sở hữu</option>
              <option v-for="o in owners" :key="o.id" :value="o.id">
                {{ o.full_name }} ({{ o.phone || 'Không số đt' }})
              </option>
            </select>
          </div>

          <!-- Brand & Model -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Hãng xe</label>
              <input 
                v-model="newVehicle.brand" 
                type="text" 
                placeholder="Ví dụ: Honda"
                class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Mẫu xe</label>
              <input 
                v-model="newVehicle.model" 
                type="text" 
                placeholder="Ví dụ: Civic"
                class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Color & Description -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Màu xe</label>
              <input 
                v-model="newVehicle.color" 
                type="text" 
                placeholder="Ví dụ: Trắng"
                class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Mô tả</label>
              <input 
                v-model="newVehicle.description" 
                type="text" 
                placeholder="Ví dụ: Xe VIP"
                class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Error Feedback -->
          <div v-if="modalError" class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
            {{ modalError }}
          </div>

          <!-- Modal Actions -->
          <div class="pt-4 border-t border-slate-800 flex gap-3">
            <button 
              type="button" 
              @click="showModal = false" 
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
              <span>Đăng ký</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Vehicle Modal -->
    <div v-if="showEditModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <!-- Modal Header -->
        <div class="p-6 border-b border-slate-800 flex items-center justify-between">
          <h4 class="font-bold text-slate-200 text-base">Chỉnh sửa Xe tháng</h4>
          <button @click="showEditModal = false" class="text-slate-500 hover:text-slate-300 text-sm font-semibold">✕</button>
        </div>
        
        <!-- Modal Form -->
        <form @submit.prevent="handleUpdateVehicle" class="p-6 space-y-4">
          <!-- Plate Number -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Biển số xe</label>
            <input 
              v-model="editingVehicle.plate_number" 
              type="text" 
              required
              placeholder="Ví dụ: 30F-12345"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Vehicle Type -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Loại xe</label>
            <select 
              v-model="editingVehicle.vehicle_type_id"
              required
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="''" disabled>-- Chọn loại xe --</option>
              <option v-for="t in vehicleTypes" :key="t.id" :value="t.id">
                {{ t.name }} ({{ t.code }})
              </option>
            </select>
          </div>

          <!-- Vehicle Owner -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Chủ sở hữu (Tùy chọn)</label>
            <select 
              v-model="editingVehicle.owner_id"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="null">Không gán chủ sở hữu</option>
              <option v-for="o in owners" :key="o.id" :value="o.id">
                {{ o.full_name }} ({{ o.phone || 'Không số đt' }})
              </option>
            </select>
          </div>

          <!-- Brand & Model -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Hãng xe</label>
              <input 
                v-model="editingVehicle.brand" 
                type="text" 
                placeholder="Ví dụ: Honda"
                class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Mẫu xe</label>
              <input 
                v-model="editingVehicle.model" 
                type="text" 
                placeholder="Ví dụ: Civic"
                class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Color & Description -->
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Màu xe</label>
              <input 
                v-model="editingVehicle.color" 
                type="text" 
                placeholder="Ví dụ: Trắng"
                class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Mô tả</label>
              <input 
                v-model="editingVehicle.description" 
                type="text" 
                placeholder="Ví dụ: Xe VIP"
                class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          <!-- Status / Active -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Trạng thái hoạt động</label>
            <select 
              v-model="editingVehicle.is_active"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="true">Kích hoạt</option>
              <option :value="false">Khóa</option>
            </select>
          </div>

          <!-- Error Feedback -->
          <div v-if="modalError" class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl">
            {{ modalError }}
          </div>

          <!-- Modal Actions -->
          <div class="pt-4 border-t border-slate-800 flex gap-3">
            <button 
              type="button" 
              @click="showEditModal = false" 
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
import { PlusIcon, LoaderIcon, EditIcon, TrashIcon } from 'lucide-vue-next'

const vehicles = ref<any[]>([])
const vehicleTypes = ref<any[]>([])
const owners = ref<any[]>([])
const loading = ref(false)
const showModal = ref(false)
const showEditModal = ref(false)
const submitting = ref(false)
const modalError = ref<string | null>(null)

const newVehicle = ref({
  vehicle_type_id: '',
  owner_id: null as string | null,
  plate_number: '',
  brand: '',
  model: '',
  color: '',
  description: ''
})

const editingVehicle = ref<any>({
  id: '',
  vehicle_type_id: '',
  owner_id: null,
  plate_number: '',
  brand: '',
  model: '',
  color: '',
  description: '',
  is_active: true
})

const fetchVehicles = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/v1/vehicles/')
    vehicles.value = response.data
  } catch (err) {
    console.error('Failed to fetch vehicles list:', err)
  } finally {
    loading.value = false
  }
}

const fetchVehicleTypes = async () => {
  try {
    const response = await api.get('/api/v1/vehicles/types')
    vehicleTypes.value = response.data
  } catch (err) {
    console.error('Failed to fetch vehicle types:', err)
  }
}

const fetchOwners = async () => {
  try {
    const response = await api.get('/api/v1/vehicles/owners')
    owners.value = response.data
  } catch (err) {
    console.error('Failed to fetch owners:', err)
  }
}

const openCreateModal = () => {
  newVehicle.value = {
    vehicle_type_id: vehicleTypes.value[0]?.id || '',
    owner_id: null,
    plate_number: '',
    brand: '',
    model: '',
    color: '',
    description: ''
  }
  modalError.value = null
  showModal.value = true
}

const openEditModal = (v: any) => {
  editingVehicle.value = {
    id: v.id,
    vehicle_type_id: v.vehicle_type_id,
    owner_id: v.owner_id,
    plate_number: v.plate_number,
    brand: v.brand || '',
    model: v.model || '',
    color: v.color || '',
    description: v.description || '',
    is_active: v.is_active
  }
  modalError.value = null
  showEditModal.value = true
}

const handleCreateVehicle = async () => {
  submitting.value = true
  modalError.value = null
  try {
    await api.post('/api/v1/vehicles/', newVehicle.value)
    showModal.value = false
    fetchVehicles()
  } catch (err: any) {
    console.error('Create vehicle error:', err)
    modalError.value = err.response?.data?.detail || 'Lưu xe thành viên thất bại.'
  } finally {
    submitting.value = false
  }
}

const handleUpdateVehicle = async () => {
  submitting.value = true
  modalError.value = null
  try {
    await api.put(`/api/v1/vehicles/${editingVehicle.value.id}`, editingVehicle.value)
    showEditModal.value = false
    fetchVehicles()
  } catch (err: any) {
    console.error('Update vehicle error:', err)
    modalError.value = err.response?.data?.detail || 'Cập nhật xe thành viên thất bại.'
  } finally {
    submitting.value = false
  }
}

const handleDeleteVehicle = async (v: any) => {
  if (!confirm(`Bạn có chắc chắn muốn xóa xe tháng có biển số ${v.plate_number}?`)) {
    return
  }
  try {
    await api.delete(`/api/v1/vehicles/${v.id}`)
    fetchVehicles()
  } catch (err: any) {
    alert(`Xóa xe thất bại: ${err.response?.data?.detail || err.message}`)
  }
}

const formatDate = (isoString: string) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return date.toLocaleDateString('vi-VN')
}

onMounted(() => {
  fetchVehicles()
  fetchVehicleTypes()
  fetchOwners()
})
</script>
