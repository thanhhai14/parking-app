<template>
  <div class="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative overflow-hidden">
    <!-- Background glow decorative effects -->
    <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl -z-10 animate-pulse"></div>
    <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -z-10 animate-pulse"></div>

    <div class="sm:mx-auto sm:w-full sm:max-w-md">
      <!-- Portal Brand Logo -->
      <div class="mx-auto w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center font-bold text-white shadow-xl shadow-blue-500/20 text-xl">
        P
      </div>
      <h2 class="mt-6 text-center text-3xl font-extrabold bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
        Đăng nhập hệ thống
      </h2>
      <p class="mt-2 text-center text-sm text-slate-500">
        Cổng điều khiển & Giám sát bãi đỗ xe thông minh
      </p>
    </div>

    <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
      <!-- Form card container -->
      <div class="bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 py-8 px-6 shadow-2xl rounded-2xl sm:px-10">
        <form class="space-y-6" @submit.prevent="handleSubmit">
          <!-- Username input field -->
          <div>
            <label for="username" class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Tài khoản
            </label>
            <div class="mt-2.5 relative">
              <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                <UserIcon class="w-4 h-4" />
              </span>
              <input
                id="username"
                type="text"
                required
                v-model="username"
                class="block w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                placeholder="Nhập tên đăng nhập..."
              />
            </div>
          </div>

          <!-- Password input field -->
          <div>
            <label for="password" class="block text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Mật khẩu
            </label>
            <div class="mt-2.5 relative">
              <span class="absolute inset-y-0 left-0 pl-3.5 flex items-center text-slate-500">
                <LockIcon class="w-4 h-4" />
              </span>
              <input
                id="password"
                type="password"
                required
                v-model="password"
                class="block w-full pl-10 pr-4 py-3 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-600 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
                placeholder="Nhập mật khẩu..."
              />
            </div>
          </div>

          <!-- Error Alert Banner -->
          <div v-if="authStore.error" class="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded-xl flex items-center gap-2">
            <AlertCircleIcon class="w-4 h-4 shrink-0" />
            <span>{{ authStore.error }}</span>
          </div>

          <!-- Submit Action Button -->
          <div>
            <button
              type="submit"
              :disabled="authStore.loading"
              class="w-full flex justify-center py-3 px-4 border border-transparent rounded-xl shadow-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-blue-500/15"
            >
              <LoaderIcon v-if="authStore.loading" class="w-5 h-5 animate-spin mr-2" />
              <span>{{ authStore.loading ? 'Đang xác thực...' : 'Đăng nhập' }}</span>
            </button>
          </div>
        </form>

        <!-- Dummy account suggestions -->
        <div class="mt-6 border-t border-slate-800/80 pt-4 flex flex-col gap-1.5 text-center text-xs text-slate-500">
          <span>Tài khoản thử nghiệm:</span>
          <span class="font-mono text-slate-400">Tài khoản: admin / Mật khẩu: admin123</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { UserIcon, LockIcon, AlertCircleIcon, LoaderIcon } from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')

const handleSubmit = async () => {
  if (!username.value || !password.value) return
  const success = await authStore.login(username.value, password.value)
  if (success) {
    router.push('/dashboard')
  }
}
</script>
