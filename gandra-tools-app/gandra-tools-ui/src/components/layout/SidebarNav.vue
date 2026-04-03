<script setup lang="ts">
import { useRoute } from "vue-router";

const route = useRoute();

const navItems = [
  { path: "/chat", label: "Chat", icon: "💬" },
  { path: "/youtube", label: "YouTube", icon: "🎬" },
  { path: "/research", label: "Research", icon: "🔍" },
  { path: "/imageops", label: "Image Ops", icon: "🖼️" },
  { path: "/fileops", label: "File Ops", icon: "📁" },
  { path: "/devtools", label: "DevTools", icon: "🔧" },
  { path: "/settings", label: "Settings", icon: "⚙️" },
];
</script>

<template>
  <nav class="w-56 bg-gray-900 text-gray-300 flex flex-col">
    <div class="px-4 py-5">
      <h2 class="text-white text-lg font-bold">Gandra Tools</h2>
      <p class="text-xs text-gray-500 mt-1">v0.1.0</p>
    </div>
    <ul class="flex-1 space-y-1 px-2">
      <li v-for="item in navItems" :key="item.path">
        <router-link
          :to="item.path"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition"
          :class="route.path === item.path
            ? 'bg-gray-700 text-white'
            : 'hover:bg-gray-800 hover:text-white'"
        >
          <span>{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </li>
    </ul>
  </nav>
</template>
