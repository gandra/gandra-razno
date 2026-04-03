<script setup lang="ts">
import { useRoute } from "vue-router";
import { useAuthStore } from "../../stores/auth";
import SidebarNav from "./SidebarNav.vue";
import EnvSelector from "./EnvSelector.vue";

const route = useRoute();
const auth = useAuthStore();
</script>

<template>
  <div class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <SidebarNav />

    <!-- Main content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <header class="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <h1 class="text-lg font-semibold text-gray-800">
          {{ (route.meta.title as string) || "Gandra Tools" }}
        </h1>
        <div class="flex items-center gap-4">
          <EnvSelector />
          <span class="text-sm text-gray-500">{{ auth.userEmail }}</span>
          <button @click="auth.logout()" class="text-sm text-gray-400 hover:text-red-500 transition">
            Logout
          </button>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>
