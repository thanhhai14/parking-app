<template>
  <div class="space-y-6">
    <!-- Stat Cards Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      <!-- Card: Vehicles in lot -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden group">
        <div class="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-2xl group-hover:bg-blue-500/10 transition-colors"></div>
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Xe đang trong bãi</span>
          <span class="p-2.5 rounded-xl bg-blue-500/10 text-blue-400">
            <CarIcon class="w-5 h-5" />
          </span>
        </div>
        <div class="mt-4 flex items-baseline gap-2">
          <span class="text-3xl font-extrabold text-slate-100">{{ stats.currentInLot }}</span>
          <span class="text-xs text-slate-500 font-medium">phương tiện</span>
        </div>
      </div>

      <!-- Card: Entry Today -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden group">
        <div class="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl group-hover:bg-emerald-500/10 transition-colors"></div>
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Lượt vào hôm nay</span>
          <span class="p-2.5 rounded-xl bg-emerald-500/10 text-emerald-400">
            <ArrowDownLeftIcon class="w-5 h-5" />
          </span>
        </div>
        <div class="mt-4 flex items-baseline gap-2">
          <span class="text-3xl font-extrabold text-slate-100">{{ stats.entryToday }}</span>
          <span class="text-xs text-emerald-500 font-medium">↑ {{ stats.entryRate }}%</span>
        </div>
      </div>

      <!-- Card: Exit Today -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden group">
        <div class="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-2xl group-hover:bg-amber-500/10 transition-colors"></div>
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Lượt ra hôm nay</span>
          <span class="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
            <ArrowUpRightIcon class="w-5 h-5" />
          </span>
        </div>
        <div class="mt-4 flex items-baseline gap-2">
          <span class="text-3xl font-extrabold text-slate-100">{{ stats.exitToday }}</span>
          <span class="text-xs text-slate-500 font-medium">lượt xe</span>
        </div>
      </div>

      <!-- Card: Revenue Today -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 relative overflow-hidden group">
        <div class="absolute top-0 right-0 w-32 h-32 bg-purple-500/5 rounded-full blur-2xl group-hover:bg-purple-500/10 transition-colors"></div>
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-500 uppercase tracking-wider">Doanh thu hôm nay</span>
          <span class="p-2.5 rounded-xl bg-purple-500/10 text-purple-400">
            <DollarSignIcon class="w-5 h-5" />
          </span>
        </div>
        <div class="mt-4 flex items-baseline gap-2">
          <span class="text-2xl font-extrabold text-slate-100">{{ stats.revenueToday.toLocaleString() }}đ</span>
          <span class="text-xs text-purple-400 font-semibold">đã thanh toán</span>
        </div>
      </div>
    </div>

    <!-- Main Section Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Traffic Chart (SVG Custom Implementation) -->
      <div class="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h3 class="text-sm font-semibold text-slate-300 mb-6 flex items-center gap-2">
          <BarChart3Icon class="w-4 h-4 text-blue-500" />
          <span>Biểu đồ lưu lượng xe (hôm nay)</span>
        </h3>

        <!-- Custom SVG Chart -->
        <div class="h-64 flex items-end justify-between gap-2 border-b border-slate-800 pb-2 relative">
          <!-- Grid Background lines -->
          <div class="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-20">
            <div class="border-t border-slate-700 w-full"></div>
            <div class="border-t border-slate-700 w-full"></div>
            <div class="border-t border-slate-700 w-full"></div>
            <div class="border-t border-slate-700 w-full"></div>
          </div>
          
          <div 
            v-for="(val, label) in hourlyTraffic" 
            :key="label" 
            class="flex-1 flex flex-col items-center justify-end h-full group relative"
          >
            <!-- Hover Tooltip -->
            <span class="absolute bottom-full mb-2 bg-slate-950 text-white text-xs px-2 py-1 rounded border border-slate-800 opacity-0 group-hover:opacity-100 transition-opacity z-10 font-mono">
              {{ val }} xe
            </span>
            <!-- Bar -->
            <div 
              class="w-full bg-gradient-to-t from-blue-600 to-indigo-400 hover:from-blue-500 hover:to-indigo-300 rounded-t transition-all duration-300"
              :style="{ height: `${(val / maxTrafficValue) * 80 || 5}%` }"
            ></div>
            <!-- Axis Label -->
            <span class="text-xs text-slate-500 font-mono mt-2 shrink-0">{{ label }}</span>
          </div>
        </div>
      </div>

      <!-- Edge Agents Connectivity -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6">
        <h3 class="text-sm font-semibold text-slate-300 mb-6 flex items-center gap-2">
          <CpuIcon class="w-4 h-4 text-blue-500" />
          <span>Trạng thái kết nối Edge Agent</span>
        </h3>
        
        <div class="space-y-4">
          <!-- Device Agent Status Row -->
          <div class="p-4 bg-slate-950 border border-slate-800/80 rounded-xl flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                <TerminalIcon class="w-5 h-5" />
              </div>
              <div>
                <p class="text-sm font-semibold text-slate-200">Device Agent</p>
                <p class="text-xs text-slate-500">ID: device-agent-gate-01</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="h-2 w-2 rounded-full" :class="[agentConnection.device ? 'bg-emerald-500' : 'bg-slate-600']"></span>
              <span class="text-xs font-semibold uppercase tracking-wider" :class="[agentConnection.device ? 'text-emerald-400' : 'text-slate-500']">
                {{ agentConnection.device ? 'Online' : 'Offline' }}
              </span>
            </div>
          </div>

          <!-- Camera Agent Status Row -->
          <div class="p-4 bg-slate-950 border border-slate-800/80 rounded-xl flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                <CameraIcon class="w-5 h-5" />
              </div>
              <div>
                <p class="text-sm font-semibold text-slate-200">Camera Agent</p>
                <p class="text-xs text-slate-500">ID: camera-agent-gate-01</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <span class="h-2 w-2 rounded-full" :class="[agentConnection.camera ? 'bg-emerald-500' : 'bg-slate-600']"></span>
              <span class="text-xs font-semibold uppercase tracking-wider" :class="[agentConnection.camera ? 'text-emerald-400' : 'text-slate-500']">
                {{ agentConnection.camera ? 'Online' : 'Offline' }}
              </span>
            </div>
          </div>
        </div>

        <div class="mt-6 text-center">
          <p class="text-xs text-slate-500 font-medium">Trạng thái được cập nhật trực tiếp từ Gateway.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useParkingStore } from '@/stores/parking'
import { 
  CarIcon, 
  ArrowDownLeftIcon, 
  ArrowUpRightIcon, 
  DollarSignIcon, 
  BarChart3Icon, 
  CpuIcon, 
  TerminalIcon, 
  CameraIcon 
} from 'lucide-vue-next'

const parkingStore = useParkingStore()

const stats = ref({
  currentInLot: 0,
  entryToday: 0,
  entryRate: 12,
  exitToday: 0,
  revenueToday: 0
})

const hourlyTraffic = ref<Record<string, number>>({
  '08h': 12,
  '09h': 24,
  '10h': 18,
  '11h': 8,
  '12h': 5,
  '13h': 11,
  '14h': 15,
  '15h': 19,
  '16h': 28,
  '17h': 32,
  '18h': 21
})

const maxTrafficValue = ref(35)

const agentConnection = ref({
  device: false,
  camera: false
})

let intervalId: any = null

const fetchStatsData = async () => {
  try {
    await parkingStore.fetchSessions()
    const allSessions = parkingStore.sessions
    
    // 1. Calculate stats based on retrieved sessions
    const active = allSessions.filter(s => s.status === 'active')
    stats.value.currentInLot = active.length
    
    // Filter sessions belonging to today
    const todayStr = new Date().toISOString().split('T')[0]
    const todaySessions = allSessions.filter(s => s.entry_time.startsWith(todayStr))
    stats.value.entryToday = todaySessions.length
    
    const exitedToday = todaySessions.filter(s => s.status === 'completed')
    stats.value.exitToday = exitedToday.length
    
    const revenue = exitedToday.reduce((sum, s) => sum + (s.calculated_fee || 0), 0)
    stats.value.revenueToday = revenue
    
    // Populate hourly charts based on actual entry logs (mock fallback if empty)
    if (todaySessions.length > 0) {
      const hoursCount: Record<string, number> = {}
      // Initialize hours
      for (let i = 8; i <= 18; i++) {
        hoursCount[`${String(i).padStart(2, '0')}h`] = 0
      }
      
      todaySessions.forEach(s => {
        const hour = new Date(s.entry_time).getHours()
        const key = `${String(hour).padStart(2, '0')}h`
        if (key in hoursCount) {
          hoursCount[key]++
        }
      })
      hourlyTraffic.value = hoursCount
      maxTrafficValue.value = Math.max(...Object.values(hoursCount), 10)
    }
  } catch (err) {
    console.error('Failed to aggregate dashboard metrics:', err)
  }
}

const checkGatewayConnections = async () => {
  try {
    // Call gateway internal connections endpoint
    const gatewayUrl = import.meta.env.VITE_GATEWAY_WS_URL 
      ? import.meta.env.VITE_GATEWAY_WS_URL.replace('ws://', 'http://').split('/ws')[0]
      : 'http://localhost:8300'
      
    const response = await axios.get(`${gatewayUrl}/internal/connections`)
    const { device_agents, camera_agents } = response.data
    
    agentConnection.value.device = device_agents.includes('device-agent-gate-01')
    agentConnection.value.camera = camera_agents.includes('camera-agent-gate-01')
  } catch (err) {
    console.warn('Unable to reach gateway internal connections endpoint:', err)
    // Fallback based on mock
    agentConnection.value.device = false
    agentConnection.value.camera = false
  }
}

onMounted(() => {
  fetchStatsData()
  checkGatewayConnections()
  
  // Refresh stats and agent online states every 5 seconds
  intervalId = setInterval(() => {
    fetchStatsData()
    checkGatewayConnections()
  }, 5000)
})

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId)
  }
})
</script>
