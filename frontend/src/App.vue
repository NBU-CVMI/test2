<template>
  <div class="container">
    <h1>会议室智能预约系统</h1>

    <section v-if="!auth.token" class="card">
      <h2>登录</h2>
      <div class="row">
        <input v-model="loginForm.username" placeholder="用户名" />
        <input v-model="loginForm.password" type="password" placeholder="密码" />
        <button @click="login">登录</button>
      </div>
    </section>

    <template v-else>
      <section class="card">
        <div class="space-between">
          <h2>欢迎，{{ auth.user.username }}（{{ auth.user.role === 'ADMIN' ? '管理员' : '普通用户' }}）</h2>
          <button @click="logout">退出登录</button>
        </div>
      </section>

      <section class="card">
        <h2>会议室信息</h2>
        <div class="room-grid">
          <article v-for="room in rooms" :key="room.id" class="room-item">
            <h3>{{ room.name }}</h3>
            <p>容量：{{ room.capacity }}</p>
            <p>地点：{{ room.location || '未设置' }}</p>
            <p>设备：{{ room.equipment?.join('、') || '无' }}</p>
            <button @click="selectRoom(room)">查看可用时间</button>
          </article>
        </div>
      </section>

      <section class="card" v-if="selectedRoom">
        <h2>{{ selectedRoom.name }} 可用时间段</h2>
        <div class="row">
          <input type="date" v-model="selectedDate" />
          <button @click="loadAvailability">查询</button>
        </div>
        <ul>
          <li v-for="slot in availableSlots" :key="slot.start_time">
            {{ formatTime(slot.start_time) }} - {{ formatTime(slot.end_time) }}
          </li>
        </ul>
      </section>

      <section class="card" v-if="selectedRoom">
        <h2>发起预约</h2>
        <div class="booking-form">
          <input v-model="bookingForm.title" placeholder="会议主题" />
          <input type="datetime-local" v-model="bookingForm.start_time" />
          <input type="datetime-local" v-model="bookingForm.end_time" />
          <input type="number" min="1" v-model.number="bookingForm.attendees" placeholder="参会人数" />
          <button @click="createBooking">提交预约</button>
        </div>
      </section>

      <section class="card">
        <h2>{{ auth.user.role === 'ADMIN' ? '全部预约' : '我的预约' }}</h2>
        <ul>
          <li v-for="item in bookings" :key="item.id" class="space-between">
            <span>{{ item.title }} | {{ item.room_detail.name }} | {{ formatTime(item.start_time) }} - {{ formatTime(item.end_time) }} | {{ item.status }}</span>
            <button v-if="item.status === 'BOOKED'" @click="cancelBooking(item.id)">取消预约</button>
          </li>
        </ul>
      </section>

      <section class="card">
        <h2>通知中心</h2>
        <ul>
          <li v-for="note in notifications" :key="note.id">
            [{{ note.channel }}] {{ note.subject }} - {{ note.content }}
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import api, { setToken } from './api'

const auth = reactive({ token: localStorage.getItem('token'), user: JSON.parse(localStorage.getItem('user') || 'null') || {} })
const loginForm = reactive({ username: '', password: '' })
const rooms = ref([])
const selectedRoom = ref(null)
const selectedDate = ref(new Date().toISOString().slice(0, 10))
const availableSlots = ref([])
const bookings = ref([])
const notifications = ref([])
const bookingForm = reactive({ title: '', start_time: '', end_time: '', attendees: 1 })

async function login() {
  const { data } = await api.post('/auth/login/', loginForm)
  auth.token = data.token
  auth.user = data.user
  localStorage.setItem('user', JSON.stringify(data.user))
  setToken(data.token)
  await bootstrap()
}

function logout() {
  setToken(null)
  localStorage.removeItem('user')
  location.reload()
}

async function bootstrap() {
  await Promise.all([loadRooms(), loadBookings(), loadNotifications()])
}

async function loadRooms() {
  const { data } = await api.get('/rooms/')
  rooms.value = data
}

function selectRoom(room) {
  selectedRoom.value = room
  loadAvailability()
}

async function loadAvailability() {
  if (!selectedRoom.value) return
  const { data } = await api.get(`/rooms/${selectedRoom.value.id}/availability/`, { params: { date: selectedDate.value } })
  availableSlots.value = data.available_slots
}

async function createBooking() {
  await api.post('/bookings/', {
    room: selectedRoom.value.id,
    title: bookingForm.title,
    start_time: new Date(bookingForm.start_time).toISOString(),
    end_time: new Date(bookingForm.end_time).toISOString(),
    attendees: bookingForm.attendees
  })
  await Promise.all([loadBookings(), loadNotifications(), loadAvailability()])
}

async function loadBookings() {
  const { data } = await api.get('/bookings/')
  bookings.value = data
}

async function cancelBooking(id) {
  await api.delete(`/bookings/${id}/`)
  await Promise.all([loadBookings(), loadNotifications(), loadAvailability()])
}

async function loadNotifications() {
  const { data } = await api.get('/notifications/')
  notifications.value = data
}

function formatTime(val) {
  return new Date(val).toLocaleString('zh-CN', { hour12: false })
}

if (auth.token) {
  bootstrap()
}
</script>
