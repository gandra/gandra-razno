<script setup lang="ts">
import AppLayout from "./components/layout/AppLayout.vue";
import { useAuthStore } from "./stores/auth";

const auth = useAuthStore();
</script>

<template>
  <div v-if="!auth.isAuthenticated" class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="bg-white p-8 rounded-lg shadow-md w-full max-w-md">
      <h1 class="text-2xl font-bold mb-6 text-center">Gandra Tools</h1>
      <form @submit.prevent="auth.login(email, password)" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input v-model="email" type="email" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input v-model="password" type="password" class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none" />
        </div>
        <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition">
          Login
        </button>
        <p v-if="auth.error" class="text-red-500 text-sm text-center">{{ auth.error }}</p>
      </form>
    </div>
  </div>
  <AppLayout v-else />
</template>

<script lang="ts">
export default {
  data: () => ({ email: "", password: "" }),
};
</script>
