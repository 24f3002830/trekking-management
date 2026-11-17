<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-dark shadow-sm">
    <div class="container">
      <router-link class="navbar-brand fw-bold d-flex align-items-center" to="/">
        <i class="bi bi-compass me-2 text-success fs-4"></i>
        <span>Trekking TMA</span>
      </router-link>

      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link class="nav-link" to="/"><i class="bi bi-map me-1"></i>Explore Treks</router-link>
          </li>
          <li class="nav-item" v-if="auth.user && auth.user.role === 'staff'">
            <router-link class="nav-link text-warning" to="/staff"><i class="bi bi-person-badge me-1"></i>Staff Dashboard</router-link>
          </li>
          <li class="nav-item" v-if="auth.user && auth.user.role === 'admin'">
            <router-link class="nav-link text-info" to="/admin"><i class="bi bi-shield-lock me-1"></i>Admin Console</router-link>
          </li>
        </ul>

        <div class="d-flex align-items-center">
          <!-- When Logged In -->
          <div v-if="auth.isAuthenticated()" class="d-flex align-items-center">
            <span class="badge bg-secondary me-3 p-2">
              <i class="bi bi-person-circle me-1"></i>{{ auth.user.full_name }} ({{ auth.user.role }})
            </span>
            <router-link class="btn btn-outline-light btn-sm me-2" to="/profile">
              <i class="bi bi-gear"></i> Profile
            </router-link>
            <button class="btn btn-danger btn-sm" @click="handleLogout">
              <i class="bi bi-box-arrow-right"></i> Logout
            </button>
          </div>

          <!-- When Logged Out -->
          <div v-else>
            <router-link class="btn btn-outline-light btn-sm me-2" to="/login">
              <i class="bi bi-box-arrow-in-right"></i> Login
            </router-link>
            <router-link class="btn btn-success btn-sm" to="/register">
              <i class="bi bi-person-plus"></i> Register
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script>
export default {
  name: 'Navbar',
  inject: ['auth'],
  methods: {
    handleLogout() {
      if (confirm('Are you sure you want to log out?')) {
        this.auth.logout();
      }
    }
  }
}
</script>
