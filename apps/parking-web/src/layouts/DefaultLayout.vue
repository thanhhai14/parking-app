<template>
  <div class="min-h-screen bg-slate-900 text-slate-100 flex flex-col md:flex-row">
    <!-- Sidebar -->
    <aside class="w-full md:w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between shrink-0">
      <div>
        <!-- Brand Logo -->
        <div class="p-6 border-b border-slate-800 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-lg shadow-blue-500/20">
            P
          </div>
          <div>
            <h1 class="font-bold text-lg leading-tight bg-gradient-to-r from-blue-400 to-indigo-300 bg-clip-text text-transparent">Parking Portal</h1>
            <span class="text-xs text-slate-500 font-medium">Hệ thống Quản trị Biên</span>
          </div>
        </div>

        <!-- Navigation Links -->
        <nav class="p-4 space-y-1.5">
          <router-link
            v-for="item in filteredNavItems"
            :key="item.path"
            :to="item.path"
            class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group text-sm font-medium"
            :class="[
              $route.path === item.path
                ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-md shadow-blue-500/10'
                : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200'
            ]"
          >
            <component :is="item.icon" class="w-5 h-5 transition-transform duration-200 group-hover:scale-105" />
            <span>{{ item.name }}</span>
          </router-link>
        </nav>
      </div>

      <!-- User Profile & Logout -->
      <div class="p-4 border-t border-slate-800 space-y-3">
        <div class="flex items-center gap-3 px-2">
          <div class="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700 text-blue-400 font-semibold uppercase">
            {{ authStore.user?.username?.substring(0, 2) || 'AD' }}
          </div>
          <div class="overflow-hidden">
            <p class="text-sm font-semibold text-slate-200 truncate">{{ authStore.user?.full_name || 'System Admin' }}</p>
            <p class="text-xs text-slate-500 capitalize truncate">{{ authStore.user?.role_code || 'admin' }}</p>
          </div>
        </div>
        
        <button
          @click="handleLogout"
          class="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-slate-800 hover:bg-slate-900 text-slate-400 hover:text-red-400 hover:border-red-500/30 text-xs font-semibold transition-all duration-200"
        >
          <LogOutIcon class="w-4 h-4" />
          <span>Đăng xuất</span>
        </button>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Topbar Header -->
      <header class="h-16 bg-slate-950/50 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between shrink-0">
        <div class="flex items-center gap-4">
          <h2 class="text-md font-semibold text-slate-200 capitalize">
            {{ activePageName }}
          </h2>
        </div>
        
        <!-- Live Connection Indicator -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs">
            <span class="relative flex h-2 w-2">
              <span 
                class="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                :class="[websocketStore.connected ? 'bg-emerald-400' : 'bg-rose-400']"
              ></span>
              <span 
                class="relative inline-flex rounded-full h-2 w-2"
                :class="[websocketStore.connected ? 'bg-emerald-500' : 'bg-rose-500']"
              ></span>
            </span>
            <span class="font-medium text-slate-400">
              Gateway: {{ websocketStore.connected ? 'Đã kết nối' : 'Mất kết nối' }}
            </span>
          </div>
        </div>
      </header>

      <!-- View Wrapper -->
      <main class="flex-1 p-6 overflow-y-auto">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useWebsocketStore } from '@/stores/websocket'
import { 
  LayoutDashboardIcon, 
  TvIcon, 
  CreditCardIcon, 
  CarIcon, 
  CpuIcon, 
  HistoryIcon, 
  LogOutIcon 
} from 'lucide-vue-next'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const websocketStore = useWebsocketStore()

const navItems = [
  { name: 'Bảng điều khiển', path: '/dashboard', icon: LayoutDashboardIcon },
  { name: 'Giám sát làn xe', path: '/lane-monitor', icon: TvIcon },
  { name: 'Thẻ RFID', path: '/cards', icon: CreditCardIcon },
  { name: 'Xe thành viên', path: '/vehicles', icon: CarIcon },
  { name: 'Thiết bị & Cổng', path: '/devices', icon: CpuIcon },
  { name: 'Lịch sử ra vào', path: '/history', icon: HistoryIcon }
]

const activePageName = computed(() => {
  const matched = navItems.find(item => item.path === route.path)
  return matched ? matched.name : ''
})

const filteredNavItems = computed(() => {
  return navItems.filter(item => {
    // Hide administrative routes for non-admin users
    if (item.path !== '/lane-monitor' && authStore.user?.role_code !== 'admin') {
      return false
    }
    return true
  })
})

const handleLogout = () => {
  websocketStore.disconnect()
  authStore.logout()
  router.push('/login')
}

// Establish Web Socket Connection on mount
onMounted(() => {
  websocketStore.connect()
})

// Clean up socket connections on app layouts swap
onUnmounted(() => {
  websocketStore.disconnect()
})
</script>
