import { defineStore } from 'pinia'
import api from '@/services/api'

interface User {
  id: string
  username: string
  full_name: string
  role_code: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    user: JSON.parse(localStorage.getItem('user') || 'null') as User | null,
    loading: false,
    error: null as string | null,
  }),
  getters: {
    isAuthenticated(): boolean {
      return !!this.token
    },
    isAdmin(): boolean {
      return this.user?.role_code === 'admin'
    },
    isGuard(): boolean {
      return this.user?.role_code === 'guard'
    }
  },
  actions: {
    async login(username: string, password: string): Promise<boolean> {
      this.loading = true
      this.error = null
      try {
        // OAuth2PasswordRequestForm expects form data
        const formData = new URLSearchParams()
        formData.append('username', username)
        formData.append('password', password)

        const response = await api.post('/api/v1/auth/login', formData, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        })
        
        const { access_token } = response.data
        this.token = access_token
        localStorage.setItem('token', access_token)
        
        // Fetch current user details after successful login
        await this.fetchCurrentUser()
        
        return true
      } catch (err: any) {
        console.error('Login error:', err)
        this.error = err.response?.data?.detail || 'Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin.'
        this.logout()
        return false
      } finally {
        this.loading = false
      }
    },
    async fetchCurrentUser(): Promise<void> {
      try {
        const response = await api.get('/api/v1/auth/me')
        this.user = response.data
        localStorage.setItem('user', JSON.stringify(response.data))
      } catch (err) {
        console.error('Fetch user details failed:', err)
        this.logout()
      }
    },
    logout(): void {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
