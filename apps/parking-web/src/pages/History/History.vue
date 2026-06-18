<template>
  <div class="space-y-6">
    <!-- Filters Row -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row gap-4 items-end">
      <!-- Search plate number -->
      <div class="flex-1 w-full">
        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Tìm theo biển số</label>
        <input 
          v-model="filters.plate_number" 
          @input="handleFilterChange"
          type="text" 
          placeholder="Nhập biển số xe (ví dụ: 30F)..."
          class="mt-2.5 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500"
        />
      </div>

      <!-- Filter status -->
      <div class="w-full md:w-48 shrink-0">
        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">Trạng thái xe</label>
        <select 
          v-model="filters.status"
          @change="handleFilterChange"
          class="mt-2.5 block w-full px-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-300 text-sm focus:outline-none focus:border-blue-500"
        >
          <option :value="''">Tất cả xe</option>
          <option :value="'active'">Đang gửi trong bãi</option>
          <option :value="'completed'">Đã ra (Hoàn tất)</option>
        </select>
      </div>

      <!-- Reset button -->
      <button
        @click="resetFilters"
        class="w-full md:w-auto px-5 py-2.5 bg-slate-950 border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-white rounded-xl text-xs font-semibold shrink-0 transition-all duration-200"
      >
        Làm mới bộ lọc
      </button>
    </div>

    <!-- History Data Table -->
    <div class="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-950/40 border-b border-slate-800 text-[10px] text-slate-500 font-bold uppercase tracking-wider">
              <th class="py-4 px-6">Mã phiên</th>
              <th class="py-4 px-6">Mã thẻ UID</th>
              <th class="py-4 px-6">Biển vào</th>
              <th class="py-4 px-6">Biển ra</th>
              <th class="py-4 px-6">Giờ vào</th>
              <th class="py-4 px-6">Giờ ra</th>
              <th class="py-4 px-6">Trạng thái</th>
              <th class="py-4 px-6 text-right">Phí thu</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60 text-sm">
            <tr 
              v-for="s in parkingStore.sessions" 
              :key="s.id" 
              class="hover:bg-slate-950/20 text-slate-300 transition-colors"
            >
              <td class="py-4 px-6 font-mono text-slate-500 text-xs truncate max-w-[120px]" :title="s.session_code">
                {{ s.session_code }}
              </td>
              <td class="py-4 px-6 font-mono font-bold text-blue-400">{{ s.card_uid }}</td>
              <td class="py-4 px-6 font-mono text-slate-300">{{ s.entry_plate_number || '---' }}</td>
              <td class="py-4 px-6 font-mono text-slate-300">{{ s.exit_plate_number || '---' }}</td>
              <td class="py-4 px-6 text-xs text-slate-400">{{ formatDateTime(s.entry_time) }}</td>
              <td class="py-4 px-6 text-xs text-slate-400">{{ formatDateTime(s.exit_time) }}</td>
              <td class="py-4 px-6">
                <span 
                  class="px-2 py-0.5 rounded-full text-[10px] font-semibold"
                  :class="[
                    s.status === 'active' 
                      ? 'bg-blue-500/10 text-blue-400' 
                      : 'bg-emerald-500/10 text-emerald-400'
                  ]"
                >
                  {{ s.status === 'active' ? 'Đang gửi' : 'Đã ra' }}
                </span>
              </td>
              <td class="py-4 px-6 text-right font-semibold" :class="[s.calculated_fee > 0 ? 'text-amber-500' : 'text-slate-500']">
                {{ s.calculated_fee > 0 ? `${s.calculated_fee.toLocaleString()}đ` : 'Miễn phí' }}
              </td>
            </tr>
            <tr v-if="parkingStore.sessions.length === 0 && !parkingStore.loading">
              <td colspan="8" class="text-center py-12 text-slate-600 italic">Không tìm thấy lịch sử ra vào nào phù hợp.</td>
            </tr>
            <tr v-if="parkingStore.loading">
              <td colspan="8" class="text-center py-12">
                <LoaderIcon class="w-6 h-6 animate-spin text-blue-500 mx-auto" />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useParkingStore } from '@/stores/parking'
import { LoaderIcon } from 'lucide-vue-next'

const parkingStore = useParkingStore()

const filters = ref({
  plate_number: '',
  status: ''
})

let debounceTimer: any = null

const handleFilterChange = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    parkingStore.fetchSessions(filters.value)
  }, 300)
}

const resetFilters = () => {
  filters.value = {
    plate_number: '',
    status: ''
  }
  parkingStore.fetchSessions()
}

const formatDateTime = (isoString: string | null) => {
  if (!isoString) return '---'
  const date = new Date(isoString)
  return `${date.toLocaleDateString('vi-VN')} ${date.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })}`
}

onMounted(() => {
  parkingStore.fetchSessions()
})
</script>
