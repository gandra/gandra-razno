<script setup lang="ts">
import { ref } from "vue";

const activeEnv = ref<string | null>(null);
const envs = ref([
  { slug: "office-dt", name: "Kancelarija DT" },
  { slug: "office-sistemi", name: "Kancelarija Sistemi" },
  { slug: "home-milesevska", name: "Kuća Mileševska" },
  { slug: "mobile", name: "Mobilni" },
]);
const showDropdown = ref(false);

function selectEnv(slug: string) {
  activeEnv.value = slug;
  showDropdown.value = false;
}
</script>

<template>
  <div class="relative">
    <button
      @click="showDropdown = !showDropdown"
      class="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm border border-gray-200 hover:bg-gray-50 transition"
    >
      <span class="w-2 h-2 rounded-full" :class="activeEnv ? 'bg-green-500' : 'bg-gray-300'"></span>
      <span>{{ activeEnv ? envs.find(e => e.slug === activeEnv)?.name : 'No env' }}</span>
      <span class="text-xs text-gray-400">▾</span>
    </button>

    <div
      v-if="showDropdown"
      class="absolute right-0 top-full mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-50"
    >
      <button
        v-for="env in envs"
        :key="env.slug"
        @click="selectEnv(env.slug)"
        class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center gap-2"
        :class="activeEnv === env.slug ? 'text-blue-600 font-medium' : 'text-gray-700'"
      >
        <span class="w-2 h-2 rounded-full" :class="activeEnv === env.slug ? 'bg-green-500' : 'bg-transparent'"></span>
        {{ env.name }}
      </button>
    </div>
  </div>
</template>
