<script setup lang="ts">
import { ref } from "vue";
import { api } from "../lib/api";

const activeTab = ref<"search" | "rename">("search");

// Search
const searchPath = ref("");
const searchPattern = ref("*");
const searchContent = ref("");
const searchResults = ref<Record<string, unknown>[]>([]);
const searchTotal = ref(0);

// Rename
const renamePath = ref("");
const strategy = ref("slugify");
const prefix = ref("");
const suffix = ref("");
const dryRun = ref(true);
const renameResults = ref<Record<string, unknown>[]>([]);
const renameCount = ref(0);

const loading = ref(false);
const error = ref<string | null>(null);

async function search() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await api.post("/api/v1/fileops/search", {
      path: searchPath.value,
      pattern: searchPattern.value,
      content: searchContent.value || null,
    });
    searchResults.value = data.results;
    searchTotal.value = data.total_found;
  } catch { error.value = "Search failed."; }
  finally { loading.value = false; }
}

async function rename() {
  loading.value = true;
  error.value = null;
  try {
    const { data } = await api.post("/api/v1/fileops/rename", {
      path: renamePath.value,
      strategy: strategy.value,
      prefix: prefix.value || null,
      suffix: suffix.value || null,
      dry_run: dryRun.value,
    });
    renameResults.value = data.previews;
    renameCount.value = data.renamed_count;
  } catch { error.value = "Rename failed."; }
  finally { loading.value = false; }
}
</script>

<template>
  <div class="max-w-3xl">
    <div class="flex gap-4 mb-6">
      <button @click="activeTab = 'search'" :class="activeTab === 'search' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'" class="pb-2 font-medium">Search</button>
      <button @click="activeTab = 'rename'" :class="activeTab === 'rename' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'" class="pb-2 font-medium">Rename</button>
    </div>

    <!-- Search tab -->
    <div v-if="activeTab === 'search'" class="space-y-4">
      <input v-model="searchPath" placeholder="Directory path" class="w-full px-3 py-2 border rounded-lg" />
      <div class="flex gap-4">
        <input v-model="searchPattern" placeholder="*.py" class="flex-1 px-3 py-2 border rounded-lg" />
        <input v-model="searchContent" placeholder="Content regex (optional)" class="flex-1 px-3 py-2 border rounded-lg" />
      </div>
      <button @click="search" :disabled="loading" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">Search</button>
      <div v-if="searchTotal" class="text-sm text-gray-500">Found {{ searchTotal }} file(s)</div>
      <div v-for="r in searchResults" :key="(r as Record<string, unknown>).path as string" class="text-sm bg-white border rounded p-2">
        <span class="font-mono">{{ (r as Record<string, unknown>).name }}</span>
        <span class="text-gray-400 ml-2">{{ (r as Record<string, unknown>).size_bytes }}B</span>
      </div>
    </div>

    <!-- Rename tab -->
    <div v-if="activeTab === 'rename'" class="space-y-4">
      <input v-model="renamePath" placeholder="Directory path" class="w-full px-3 py-2 border rounded-lg" />
      <div class="flex gap-4">
        <select v-model="strategy" class="px-3 py-2 border rounded-lg">
          <option v-for="s in ['slugify','uppercase','lowercase','snake_case','kebab-case','camelCase','prefix','suffix','date_prefix','regex']" :key="s" :value="s">{{ s }}</option>
        </select>
        <input v-model="prefix" placeholder="Prefix" class="flex-1 px-3 py-2 border rounded-lg" />
        <input v-model="suffix" placeholder="Suffix" class="flex-1 px-3 py-2 border rounded-lg" />
      </div>
      <label class="flex items-center gap-2 text-sm"><input type="checkbox" v-model="dryRun" /> Dry run (preview only)</label>
      <button @click="rename" :disabled="loading" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">{{ dryRun ? 'Preview' : 'Rename' }}</button>
      <div v-if="renameCount !== null" class="text-sm text-gray-500">{{ renameCount }} file(s) {{ dryRun ? 'would be' : '' }} renamed</div>
      <div v-for="r in renameResults" :key="(r as Record<string, unknown>).original as string" class="text-sm bg-white border rounded p-2">
        <span class="font-mono">{{ (r as Record<string, unknown>).original }}</span>
        <span class="text-gray-400 mx-2">→</span>
        <span class="font-mono text-blue-600">{{ (r as Record<string, unknown>).renamed }}</span>
      </div>
    </div>

    <div v-if="error" class="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{{ error }}</div>
  </div>
</template>
