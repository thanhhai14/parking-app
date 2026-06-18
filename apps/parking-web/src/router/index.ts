import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login/Login.vue'),
    meta: { guestOnly: true }
  },
  {
    path: '/',
    component: () => import('@/layouts/DefaultLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: () => {
          const authStore = useAuthStore()
          return authStore.user?.role_code === 'admin' ? '/dashboard' : '/lane-monitor'
        }
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard/Dashboard.vue'),
        meta: { role: 'admin' }
      },
      {
        path: 'lane-monitor',
        name: 'LaneMonitor',
        component: () => import('@/pages/LaneMonitor/LaneMonitor.vue')
      },
      {
        path: 'cards',
        name: 'Cards',
        component: () => import('@/pages/Cards/Cards.vue'),
        meta: { role: 'admin' }
      },
      {
        path: 'vehicles',
        name: 'Vehicles',
        component: () => import('@/pages/Vehicles/Vehicles.vue'),
        meta: { role: 'admin' }
      },
      {
        path: 'devices',
        name: 'Devices',
        component: () => import('@/pages/Devices/Devices.vue'),
        meta: { role: 'admin' }
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/pages/History/History.vue'),
        meta: { role: 'admin' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  const isAuthenticated = authStore.isAuthenticated

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'Login' })
  } else if (to.meta.guestOnly && isAuthenticated) {
    // Redirect authenticated users trying to access login
    const target = authStore.user?.role_code === 'admin' ? { name: 'Dashboard' } : { name: 'LaneMonitor' }
    next(target)
  } else if (to.matched.some(record => record.meta.role === 'admin') && authStore.user?.role_code !== 'admin') {
    // Restrict admin routes for guards
    next({ name: 'LaneMonitor' })
  } else {
    next()
  }
})

export default router
