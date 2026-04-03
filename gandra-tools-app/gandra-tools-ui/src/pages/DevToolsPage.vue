<script setup lang="ts">
import { ref } from "vue";
import { api } from "../lib/api";

const method = ref("GET");
const url = ref("");
const expectedStatus = ref<number | null>(null);
const repeat = ref(1);
const loading = ref(false);
const result = ref<Record<string, unknown> | null>(null);
const error = ref<string | null>(null);

async function testApi() {
  if (!url.value) return;
  loading.value = true;
  error.value = null;
  try {
    const { data } = await api.post("/api/v1/devtools/api-test", {
      method: method.value,
      url: url.value,
      expected_status: expectedStatus.value,
      repeat: repeat.value,
    });
    result.value = data;
  } catch { error.value = "API test failed."; }
  finally { loading.value = false; }
}
</script>

<template>
  <div class="max-w-3xl">
    <h2 class="text-xl font-semibold mb-4">API Tester</h2>
    <div class="space-y-4">
      <div class="flex gap-2">
        <select v-model="method" class="px-3 py-2 border rounded-lg font-mono">
          <option v-for="m in ['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS']" :key="m" :value="m">{{ m }}</option>
        </select>
        <input v-model="url" placeholder="https://api.example.com/health" class="flex-1 px-3 py-2 border rounded-lg font-mono" />
      </div>
      <div class="flex gap-4">
        <div>
          <label class="block text-sm text-gray-700 mb-1">Expected status</label>
          <input v-model.number="expectedStatus" type="number" placeholder="200" class="w-24 px-3 py-2 border rounded-lg" />
        </div>
        <div>
          <label class="block text-sm text-gray-700 mb-1">Repeat</label>
          <input v-model.number="repeat" type="number" min="1" max="100" class="w-20 px-3 py-2 border rounded-lg" />
        </div>
      </div>
      <button @click="testApi" :disabled="loading || !url" class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
        {{ loading ? "Testing..." : "Test" }}
      </button>
    </div>
    <div v-if="error" class="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">{{ error }}</div>
    <div v-if="result" class="mt-6 space-y-2">
      <div class="flex items-center gap-3">
        <span class="text-lg font-bold" :class="(result as Record<string, unknown>).all_passed ? 'text-green-600' : 'text-red-600'">
          {{ (result as Record<string, unknown>).all_passed ? 'PASS' : 'FAIL' }}
        </span>
        <span class="text-sm text-gray-500">Avg: {{ (result as Record<string, unknown>).avg_response_time_ms }}ms</span>
      </div>
      <div v-for="(r, i) in ((result as Record<string, unknown>).results as Record<string, unknown>[])" :key="i" class="text-sm bg-white border rounded p-2 font-mono">
        #{{ i + 1 }}: {{ (r as Record<string, unknown>).status_code }} ({{ (r as Record<string, unknown>).response_time_ms }}ms, {{ (r as Record<string, unknown>).body_size_bytes }}B)
      </div>
    </div>
  </div>
</template>
