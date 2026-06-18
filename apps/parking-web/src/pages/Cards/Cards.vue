<template>
  <div class="space-y-6">
    <!-- Header Controls -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <p class="text-xs text-slate-500 font-medium">Danh mục quản lý và gán thẻ RFID cho phương tiện</p>
      </div>
      <button 
        @click="openCreateModal"
        class="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-2 transition-all duration-200 shadow-lg shadow-blue-500/10 shrink-0 self-start sm:self-auto"
      >
        <PlusIcon class="w-4 h-4" />
        <span>Thêm thẻ RFID</span>
      </button>
    </div>

    <!-- Cards Data Table -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-950/40 border-b border-slate-800 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
              <th class="py-4 px-6">Mã thẻ UID</th>
              <th class="py-4 px-6">Số thẻ</th>
              <th class="py-4 px-6">Loại thẻ</th>
              <th class="py-4 px-6">Trạng thái</th>
              <th class="py-4 px-6">Gán cho</th>
              <th class="py-4 px-6 text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60 text-sm">
            <tr 
              v-for="card in cards" 
              :key="card.id" 
              class="hover:bg-slate-950/20 text-slate-300 transition-colors"
            >
              <td class="py-4 px-6 font-mono font-bold text-blue-400">{{ card.card_uid }}</td>
              <td class="py-4 px-6 font-mono text-slate-400">{{ card.card_number || '---' }}</td>
              <td class="py-4 px-6">
                <span class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase bg-slate-800 text-slate-300">
                  {{ card.card_type }}
                </span>
              </td>
              <td class="py-4 px-6">
                <span 
                  class="px-2.5 py-1 rounded-md text-[10px] font-bold uppercase"
                  :class="[
                    card.status === 'active' 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  ]"
                >
                  {{ card.status === 'active' ? 'Hoạt động' : 'Đã khóa' }}
                </span>
              </td>
              <td class="py-4 px-6 text-xs text-slate-400">
                <div v-if="card.assigned_vehicle_id" class="flex items-center gap-1.5">
                  <CarIcon class="w-3.5 h-3.5 text-slate-500" />
                  <span class="font-mono text-slate-300">{{ getVehiclePlate(card.assigned_vehicle_id) }}</span>
                </div>
                <div v-else-if="card.assigned_owner_id" class="flex items-center gap-1.5">
                  <UserIcon class="w-3.5 h-3.5 text-slate-500" />
                  <span>{{ getOwnerName(card.assigned_owner_id) }}</span>
                </div>
                <span v-else class="text-slate-600 italic">Thẻ vãng lai</span>
              </td>
              <td class="py-4 px-6 text-right">
                <div class="flex items-center justify-end gap-2">
                  <button 
                    @click="openEditModal(card)"
                    class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-blue-400 transition-colors"
                    title="Sửa"
                  >
                    <EditIcon class="w-4 h-4" />
                  </button>
                  <button 
                    @click="handleDeleteCard(card)"
                    class="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-rose-400 transition-colors"
                    title="Xóa"
                  >
                    <TrashIcon class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="cards.length === 0 && !loading">
              <td colspan="6" class="text-center py-12 text-slate-600 italic">Chưa có thẻ RFID nào được đăng ký.</td>
            </tr>
            <tr v-if="loading">
              <td colspan="6" class="text-center py-12">
                <LoaderIcon class="w-6 h-6 animate-spin text-blue-500 mx-auto" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Card Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <!-- Modal Header -->
        <div class="p-6 border-b border-slate-800 flex items-center justify-between">
          <h4 class="font-bold text-slate-200 text-base">Đăng ký Thẻ RFID mới</h4>
          <button @click="showModal = false" class="text-slate-500 hover:text-slate-300 text-sm font-semibold">✕</button>
        </div>
        
        <!-- Modal Form -->
        <form @submit.prevent="handleCreateCard" class="p-6 space-y-4">
          <!-- Card UID -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Mã thẻ UID</label>
            <input 
              v-model="newCard.card_uid" 
              type="text" 
              required
              placeholder="Ví dụ: 04A12345"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Card Number -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Số thẻ</label>
            <input 
              v-model="newCard.card_number" 
              type="text" 
              placeholder="Ví dụ: 1001"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Assign Vehicle (Optional) -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Gán cho xe tháng (Tùy chọn)</label>
            <select 
              v-model="newCard.assigned_vehicle_id"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="null">Không gán (Thẻ vãng lai)</option>
              <option v-for="v in vehicles" :key="v.id" :value="v.id">
                {{ v.plate_number }} ({{ v.brand || 'Chưa rõ hãng' }})
              </option>
            </select>
          </div>

          <!-- Note -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Ghi chú</label>
            <textarea 
              v-model="newCard.note" 
              placeholder="Nhập ghi chú thêm..."
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none"
            ></textarea>
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
              Hủy bỏ
            </button>
            <button 
              type="submit" 
              :disabled="submitting"
              class="flex-1 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl shadow-lg shadow-blue-500/10 flex items-center justify-center gap-1.5"
            >
              <LoaderIcon v-if="submitting" class="w-3.5 h-3.5 animate-spin" />
              <span>Lưu lại</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Edit Card Modal -->
    <div v-if="showEditModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div class="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-200">
        <!-- Modal Header -->
        <div class="p-6 border-b border-slate-800 flex items-center justify-between">
          <h4 class="font-bold text-slate-200 text-base">Chỉnh sửa Thẻ RFID</h4>
          <button @click="showEditModal = false" class="text-slate-500 hover:text-slate-300 text-sm font-semibold">✕</button>
        </div>
        
        <!-- Modal Form -->
        <form @submit.prevent="handleUpdateCard" class="p-6 space-y-4">
          <!-- Card UID -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Mã thẻ UID</label>
            <input 
              v-model="editingCard.card_uid" 
              type="text" 
              required
              placeholder="Ví dụ: 04A12345"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Card Number -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Số thẻ</label>
            <input 
              v-model="editingCard.card_number" 
              type="text" 
              placeholder="Ví dụ: 1001"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
            />
          </div>

          <!-- Status -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Trạng thái</label>
            <select 
              v-model="editingCard.status"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option value="active">Hoạt động</option>
              <option value="blocked">Đã khóa</option>
            </select>
          </div>

          <!-- Assign Vehicle (Optional) -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Gán cho xe tháng (Tùy chọn)</label>
            <select 
              v-model="editingCard.assigned_vehicle_id"
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
            >
              <option :value="null">Không gán (Thẻ vãng lai)</option>
              <option v-for="v in vehicles" :key="v.id" :value="v.id">
                {{ v.plate_number }} ({{ v.brand || 'Chưa rõ hãng' }})
              </option>
            </select>
          </div>

          <!-- Note -->
          <div>
            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Ghi chú</label>
            <textarea 
              v-model="editingCard.note" 
              placeholder="Nhập ghi chú thêm..."
              class="mt-2 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500 h-20 resize-none"
            ></textarea>
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
              Hủy bỏ
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
import { PlusIcon, CarIcon, UserIcon, LoaderIcon, EditIcon, TrashIcon } from 'lucide-vue-next'

const cards = ref<any[]>([])
const vehicles = ref<any[]>([])
const owners = ref<any[]>([])
const loading = ref(false)
const showModal = ref(false)
const showEditModal = ref(false)
const submitting = ref(false)
const modalError = ref<string | null>(null)

const newCard = ref({
  card_uid: '',
  card_number: '',
  card_type: 'rfid',
  assigned_vehicle_id: null as string | null,
  assigned_owner_id: null as string | null,
  status: 'active',
  note: ''
})

const editingCard = ref<any>({
  id: '',
  card_uid: '',
  card_number: '',
  card_type: 'rfid',
  assigned_vehicle_id: null,
  assigned_owner_id: null,
  status: 'active',
  note: ''
})

const fetchCards = async () => {
  loading.value = true
  try {
    const response = await api.get('/api/v1/cards/')
    cards.value = response.data
  } catch (err) {
    console.error('Failed to fetch cards list:', err)
  } finally {
    loading.value = false
  }
}

const fetchVehicles = async () => {
  try {
    const response = await api.get('/api/v1/vehicles/')
    vehicles.value = response.data
  } catch (err) {
    console.error('Failed to fetch vehicles list:', err)
  }
}

const fetchOwners = async () => {
  try {
    const response = await api.get('/api/v1/vehicles/owners')
    owners.value = response.data
  } catch (err) {
    console.error('Failed to fetch owners list:', err)
  }
}

const getVehiclePlate = (id: string) => {
  const v = vehicles.value.find(item => item.id === id)
  return v ? v.plate_number : '---'
}

const getOwnerName = (id: string) => {
  const o = owners.value.find(item => item.id === id)
  return o ? o.full_name : '---'
}

const openCreateModal = () => {
  newCard.value = {
    card_uid: '',
    card_number: '',
    card_type: 'rfid',
    assigned_vehicle_id: null,
    assigned_owner_id: null,
    status: 'active',
    note: ''
  }
  modalError.value = null
  showModal.value = true
}

const openEditModal = (card: any) => {
  editingCard.value = {
    id: card.id,
    card_uid: card.card_uid,
    card_number: card.card_number || '',
    card_type: card.card_type,
    assigned_vehicle_id: card.assigned_vehicle_id,
    assigned_owner_id: card.assigned_owner_id,
    status: card.status,
    note: card.note || ''
  }
  modalError.value = null
  showEditModal.value = true
}

const handleCreateCard = async () => {
  submitting.value = true
  modalError.value = null
  try {
    // Find assigned owner of the vehicle if vehicle is selected
    if (newCard.value.assigned_vehicle_id) {
      const selectedVehicle = vehicles.value.find(v => v.id === newCard.value.assigned_vehicle_id)
      if (selectedVehicle && selectedVehicle.owner_id) {
        newCard.value.assigned_owner_id = selectedVehicle.owner_id
      }
    }

    await api.post('/api/v1/cards/', newCard.value)
    showModal.value = false
    fetchCards()
  } catch (err: any) {
    console.error('Create card error:', err)
    modalError.value = err.response?.data?.detail || 'Lưu thẻ không thành công'
  } finally {
    submitting.value = false
  }
}

const handleUpdateCard = async () => {
  submitting.value = true
  modalError.value = null
  try {
    if (editingCard.value.assigned_vehicle_id) {
      const selectedVehicle = vehicles.value.find(v => v.id === editingCard.value.assigned_vehicle_id)
      if (selectedVehicle && selectedVehicle.owner_id) {
        editingCard.value.assigned_owner_id = selectedVehicle.owner_id
      }
    } else {
      editingCard.value.assigned_owner_id = null
    }

    await api.put(`/api/v1/cards/${editingCard.value.id}`, editingCard.value)
    showEditModal.value = false
    fetchCards()
  } catch (err: any) {
    console.error('Update card error:', err)
    modalError.value = err.response?.data?.detail || 'Cập nhật thẻ không thành công'
  } finally {
    submitting.value = false
  }
}

const handleDeleteCard = async (card: any) => {
  if (!confirm(`Bạn có chắc chắn muốn xóa thẻ RFID có UID ${card.card_uid}?`)) {
    return
  }
  try {
    await api.delete(`/api/v1/cards/${card.id}`)
    fetchCards()
  } catch (err: any) {
    alert(`Xóa thẻ thất bại: ${err.response?.data?.detail || err.message}`)
  }
}

onMounted(() => {
  fetchCards()
  fetchVehicles()
  fetchOwners()
})
</script>
