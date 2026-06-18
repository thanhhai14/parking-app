<template>
  <div class="space-y-6 flex flex-col h-[calc(100vh-10rem)]">
    <!-- Top Lane Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 flex-1 min-h-0">
      
      <!-- Làn Vào (Entry Lane) -->
      <div class="bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col justify-between">
        <div>
          <!-- Title & Controls Header -->
          <div class="flex items-center justify-between pb-4 border-b border-slate-800">
            <div class="flex items-center gap-2.5">
              <span class="w-3 h-3 rounded-full bg-blue-500 animate-pulse"></span>
              <h3 class="font-bold text-slate-200">LÀN VÀO (Entry Gate)</h3>
            </div>
            <span class="text-xs font-mono text-slate-500">GATE-IN-EDGE-01</span>
          </div>

          <!-- Video Snapshot Mock/Container - 2 Cameras -->
          <div class="mt-4 grid grid-cols-2 gap-3">
            <!-- Camera Biển Số (Plate Camera) -->
            <div class="aspect-video rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden relative group">
              <img 
                v-if="parkingStore.activeEntrySession?.plate_image_url || parkingStore.activeEntrySession?.image_url" 
                :src="parkingStore.activeEntrySession.plate_image_url || parkingStore.activeEntrySession.image_url" 
                class="w-full h-full object-cover" 
                alt="Entry plate camera snap"
              />
              <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-slate-700 select-none bg-slate-950/90">
                <div class="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-0.5 bg-rose-500/10 border border-rose-500/20 rounded text-[9px] text-rose-400 font-bold uppercase tracking-wider">
                  <span class="h-1.5 w-1.5 rounded-full bg-rose-500 animate-ping"></span>
                  <span>Live Feed</span>
                </div>
                <CameraIcon class="w-8 h-8 stroke-[1.2] text-slate-800 mb-1" />
                <span class="text-[9px] uppercase tracking-wider font-semibold">CAM BIỂN SỐ VÀO</span>
              </div>
              <span v-if="parkingStore.activeEntrySession?.plate_image_url || parkingStore.activeEntrySession?.image_url" class="absolute bottom-2 left-2 px-1.5 py-0.5 rounded bg-slate-900/90 text-[9px] text-slate-400 font-mono">CAM BIỂN SỐ</span>
            </div>

            <!-- Camera Toàn Cảnh (Overview Camera) -->
            <div class="aspect-video rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden relative group">
              <img 
                v-if="parkingStore.activeEntrySession?.overview_image_url" 
                :src="parkingStore.activeEntrySession.overview_image_url" 
                class="w-full h-full object-cover" 
                alt="Entry overview camera snap"
              />
              <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-slate-700 select-none bg-slate-950/90">
                <div class="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-0.5 bg-rose-500/10 border border-rose-500/20 rounded text-[9px] text-rose-400 font-bold uppercase tracking-wider">
                  <span class="h-1.5 w-1.5 rounded-full bg-rose-500 animate-ping"></span>
                  <span>Live Feed</span>
                </div>
                <CameraIcon class="w-8 h-8 stroke-[1.2] text-slate-800 mb-1" />
                <span class="text-[9px] uppercase tracking-wider font-semibold">CAM TOÀN CẢNH VÀO</span>
              </div>
              <span v-if="parkingStore.activeEntrySession?.overview_image_url" class="absolute bottom-2 left-2 px-1.5 py-0.5 rounded bg-slate-900/90 text-[9px] text-slate-400 font-mono">CAM TOÀN CẢNH</span>
            </div>
          </div>

          <!-- Details -->
          <div class="mt-4 grid grid-cols-2 gap-4">
            <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800/40">
              <span class="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Mã thẻ RFID</span>
              <p class="text-md font-mono font-bold text-slate-200 mt-0.5">
                {{ parkingStore.activeEntrySession?.card_uid || '---' }}
              </p>
            </div>
            <div class="bg-slate-950/60 p-3 rounded-xl border border-slate-800/40">
              <span class="text-[10px] text-slate-500 font-semibold uppercase tracking-wider">Biển số nhận diện</span>
              <p class="text-md font-mono font-bold text-blue-400 mt-0.5">
                {{ parkingStore.activeEntrySession?.entry_plate_number || '---' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Barrier trigger buttons -->
        <div class="mt-6 flex gap-3">
          <button
            @click="triggerBarrier('in')"
            :disabled="loadingIn"
            class="flex-1 py-3 px-4 rounded-xl font-semibold text-xs border border-blue-500/30 hover:border-blue-500 bg-blue-600/10 hover:bg-blue-600 text-blue-400 hover:text-white transition-all duration-200 flex items-center justify-center gap-2"
          >
            <LoaderIcon v-if="loadingIn" class="w-4 h-4 animate-spin" />
            <UnlockIcon v-else class="w-4 h-4" />
            <span>Mở Barrier Vào</span>
          </button>
        </div>
      </div>

      <!-- Làn Ra (Exit Lane) -->
      <div 
        class="bg-slate-900 border rounded-2xl p-5 flex flex-col justify-between transition-colors duration-300"
        :class="[plateMismatch ? 'border-rose-500/40 bg-rose-950/5' : 'border-slate-800']"
      >
        <div>
          <!-- Title Header -->
          <div class="flex items-center justify-between pb-4 border-b border-slate-800">
            <div class="flex items-center gap-2.5">
              <span class="w-3 h-3 rounded-full bg-emerald-500 animate-pulse"></span>
              <h3 class="font-bold text-slate-200">LÀN RA (Exit Gate)</h3>
            </div>
            <span class="text-xs font-mono text-slate-500">GATE-OUT-EDGE-01</span>
          </div>

          <!-- Mismatch Warning Banner -->
          <div v-if="plateMismatch" class="mt-3 p-2.5 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl flex items-center gap-2 animate-bounce">
            <AlertTriangleIcon class="w-4 h-4 shrink-0" />
            <span class="font-semibold">Cảnh báo: Biển số xe vào và xe ra không khớp!</span>
          </div>

          <!-- Split Entry vs Exit 4-Image Comparison Grid -->
          <div class="mt-4 grid grid-cols-2 gap-3">
            <!-- Entry plate photo -->
            <div class="aspect-video bg-slate-950 border border-slate-800 rounded-lg overflow-hidden relative">
              <img 
                v-if="parkingStore.activeExitSession?.entry_plate_image_url || parkingStore.activeExitSession?.image_entry_url" 
                :src="parkingStore.activeExitSession.entry_plate_image_url || parkingStore.activeExitSession.image_entry_url" 
                class="w-full h-full object-cover"
                alt="Entry plate snap comparison"
              />
              <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-slate-700 bg-slate-950/80 text-[10px]">
                <span>ẢNH BIỂN SỐ VÀO</span>
              </div>
              <span class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 rounded bg-slate-900/90 text-[8px] text-slate-400 font-mono">Vào - Biển số</span>
            </div>

            <!-- Entry overview photo -->
            <div class="aspect-video bg-slate-950 border border-slate-800 rounded-lg overflow-hidden relative">
              <img 
                v-if="parkingStore.activeExitSession?.entry_overview_image_url" 
                :src="parkingStore.activeExitSession.entry_overview_image_url" 
                class="w-full h-full object-cover"
                alt="Entry overview snap comparison"
              />
              <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-slate-700 bg-slate-950/80 text-[10px]">
                <span>ẢNH TOÀN CẢNH VÀO</span>
              </div>
              <span class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 rounded bg-slate-900/90 text-[8px] text-slate-400 font-mono">Vào - Toàn cảnh</span>
            </div>
            
            <!-- Exit plate photo -->
            <div class="aspect-video bg-slate-950 border border-slate-800 rounded-lg overflow-hidden relative">
              <img 
                v-if="parkingStore.activeExitSession?.exit_plate_image_url || parkingStore.activeExitSession?.image_exit_url" 
                :src="parkingStore.activeExitSession.exit_plate_image_url || parkingStore.activeExitSession.image_exit_url" 
                class="w-full h-full object-cover"
                alt="Exit plate snap comparison"
              />
              <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-slate-700 bg-slate-950/80 text-[10px]">
                <span>ẢNH BIỂN SỐ RA</span>
              </div>
              <span class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 rounded bg-slate-900/90 text-[8px] text-slate-400 font-mono">Ra - Biển số</span>
            </div>

            <!-- Exit overview photo -->
            <div class="aspect-video bg-slate-950 border border-slate-800 rounded-lg overflow-hidden relative">
              <img 
                v-if="parkingStore.activeExitSession?.exit_overview_image_url" 
                :src="parkingStore.activeExitSession.exit_overview_image_url" 
                class="w-full h-full object-cover"
                alt="Exit overview snap comparison"
              />
              <div v-else class="absolute inset-0 flex flex-col items-center justify-center text-slate-700 bg-slate-950/80 text-[10px]">
                <span>ẢNH TOÀN CẢNH RA</span>
              </div>
              <span class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 rounded bg-slate-900/90 text-[8px] text-slate-400 font-mono">Ra - Toàn cảnh</span>
            </div>
          </div>

          <!-- Details comparing exit to entry -->
          <div class="mt-4 grid grid-cols-3 gap-3">
            <div class="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/40 text-center">
              <span class="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">Mã thẻ</span>
              <p class="text-sm font-mono font-bold text-slate-200 truncate mt-0.5">
                {{ parkingStore.activeExitSession?.card_uid || '---' }}
              </p>
            </div>
            <div class="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/40 text-center">
              <span class="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">Bản vào</span>
              <p class="text-sm font-mono font-bold text-slate-400 truncate mt-0.5">
                {{ parkingStore.activeExitSession?.entry_plate_number || '---' }}
              </p>
            </div>
            <div class="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800/40 text-center" :class="{'border-rose-500/20 bg-rose-500/5': plateMismatch}">
              <span class="text-[9px] text-slate-500 font-semibold uppercase tracking-wider">Bản ra</span>
              <p class="text-sm font-mono font-bold truncate mt-0.5" :class="[plateMismatch ? 'text-rose-400' : 'text-emerald-400']">
                {{ parkingStore.activeExitSession?.exit_plate_number || '---' }}
              </p>
            </div>
          </div>

          <!-- Price calculations -->
          <div class="mt-4 p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex items-center justify-between">
            <div class="text-xs">
              <span class="text-slate-500 font-medium">Thời gian gửi:</span>
              <span class="text-slate-300 font-semibold ml-1.5">{{ simulatedDuration }}</span>
            </div>
            <div class="text-right">
              <span class="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">Phí gửi xe</span>
              <span class="text-lg font-extrabold text-amber-500">
                {{ parkingStore.activeExitSession?.calculated_fee?.toLocaleString() || '0' }}đ
              </span>
            </div>
          </div>
        </div>

        <!-- Exit controllers -->
        <div class="mt-6 flex gap-3">
          <!-- Manual exit override -->
          <button
            @click="handleManualCheckout"
            :disabled="!parkingStore.activeExitSession || loadingCheckout"
            class="flex-1 py-3 px-4 rounded-xl font-semibold text-xs bg-emerald-600 hover:bg-emerald-500 text-white transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/10"
          >
            <LoaderIcon v-if="loadingCheckout" class="w-4 h-4 animate-spin" />
            <CheckCircleIcon v-else class="w-4 h-4" />
            <span>Xác nhận xe ra</span>
          </button>
          
          <button
            @click="triggerBarrier('out')"
            :disabled="loadingOut"
            class="py-3 px-4 rounded-xl font-semibold text-xs border border-slate-800 hover:border-slate-700 bg-slate-950/60 hover:bg-slate-900 text-slate-400 hover:text-white transition-all duration-200 flex items-center justify-center gap-2"
          >
            <LoaderIcon v-if="loadingOut" class="w-4 h-4 animate-spin" />
            <UnlockIcon v-else class="w-4 h-4" />
            <span>Mở Barrier Ra</span>
          </button>
        </div>
      </div>

    </div>

    <!-- Live Event Logs Panel -->
    <div class="h-48 bg-slate-900 border border-slate-800 rounded-2xl p-5 flex flex-col shrink-0">
      <h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider pb-3 border-b border-slate-800 shrink-0">
        Nhật ký hệ thống thời gian thực (Live Logs)
      </h3>
      <div ref="logContainer" class="flex-1 overflow-y-auto mt-3 font-mono text-xs space-y-1.5 pr-2">
        <div 
          v-for="log in parkingStore.realtimeLogs" 
          :key="log.id" 
          class="flex items-start gap-2.5 leading-relaxed"
          :class="[
            log.type === 'success' ? 'text-emerald-400' :
            log.type === 'error' ? 'text-rose-400' :
            log.type === 'warning' ? 'text-amber-400' : 'text-blue-400'
          ]"
        >
          <span class="text-slate-600 shrink-0 select-none">[{{ log.time }}]</span>
          <span class="font-medium shrink-0">[{{ log.type.toUpperCase() }}]</span>
          <span class="text-slate-300">{{ log.message }}</span>
        </div>
        
        <div v-if="parkingStore.realtimeLogs.length === 0" class="text-slate-600 text-center py-6">
          Chưa có sự kiện nào được ghi nhận. Quẹt thẻ để bắt đầu...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useParkingStore } from '@/stores/parking'
import { useDevicesStore } from '@/stores/devices'
import { 
  CameraIcon, 
  UnlockIcon, 
  CheckCircleIcon, 
  AlertTriangleIcon, 
  LoaderIcon 
} from 'lucide-vue-next'

const parkingStore = useParkingStore()
const devicesStore = useDevicesStore()

const loadingIn = ref(false)
const loadingOut = ref(false)
const loadingCheckout = ref(false)
const logContainer = ref<HTMLElement | null>(null)

// Compute plate discrepancy warning
const plateMismatch = computed(() => {
  const s = parkingStore.activeExitSession
  if (!s || !s.entry_plate_number || !s.exit_plate_number) return false
  return s.entry_plate_number.replace(/\s|-/g, '').toLowerCase() !== 
         s.exit_plate_number.replace(/\s|-/g, '').toLowerCase()
})

const simulatedDuration = computed(() => {
  const s = parkingStore.activeExitSession
  if (!s || !s.entry_time) return '---'
  const entry = new Date(s.entry_time).getTime()
  const exit = s.exit_time ? new Date(s.exit_time).getTime() : Date.now()
  const diffMs = exit - entry
  
  const diffMins = Math.floor(diffMs / (1000 * 60))
  if (diffMins < 60) return `${diffMins} phút`
  const diffHours = Math.floor(diffMins / 60)
  return `${diffHours} giờ ${diffMins % 60} phút`
})

// Scroll logs console to bottom on append
watch(() => parkingStore.realtimeLogs.length, () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = 0 // Scroll to top because logs are unshifted
    }
  })
})

const triggerBarrier = async (lane: 'in' | 'out') => {
  if (lane === 'in') loadingIn.value = true
  else loadingOut.value = true
  
  try {
    // Sealed Device UUIDs in migration seed:
    // Entry barrier: a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6
    // Exit barrier: b2c3d4e5-f6a7-8b9c-0d1e-f2a3b4c5d6e7
    const devId = lane === 'in' 
      ? 'a1b2c3d4-e5f6-7a8b-9c0d-e1f2a3b4c5d6' 
      : 'b2c3d4e5-f6a7-8b9c-0d1e-f2a3b4c5d6e7'
      
    await devicesStore.controlBarrier(devId)
    parkingStore.addLog({
      message: `Đã gửi yêu cầu kích hoạt Mở Barrier (${lane === 'in' ? 'Cổng Vào' : 'Cổng Ra'})`,
      type: 'info'
    })
  } catch (err: any) {
    parkingStore.addLog({
      message: `Mở Barrier thất bại: ${err.message}`,
      type: 'error'
    })
  } finally {
    if (lane === 'in') loadingIn.value = false
    else loadingOut.value = false
  }
}

const handleManualCheckout = async () => {
  const s = parkingStore.activeExitSession
  if (!s) return
  
  loadingCheckout.value = true
  try {
    await parkingStore.checkoutSession(s.card_uid, 'GATE-OUT-EDGE-01', s.exit_plate_number)
    // Clear display exit card
    parkingStore.activeExitSession = null
  } catch (err) {
    // Handled in store logs
  } finally {
    loadingCheckout.value = false
  }
}

onMounted(() => {
  devicesStore.fetchDevices()
})
</script>
