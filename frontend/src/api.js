import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api'
})

export function setToken(token) {
  if (token) {
    api.defaults.headers.common.Authorization = `Token ${token}`
    localStorage.setItem('token', token)
  } else {
    delete api.defaults.headers.common.Authorization
    localStorage.removeItem('token')
  }
}

const token = localStorage.getItem('token')
if (token) {
  setToken(token)
}

export default api
