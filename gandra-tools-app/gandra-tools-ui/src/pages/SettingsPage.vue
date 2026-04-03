<script setup lang="ts">
import { ref, onMounted } from "vue";
import { api } from "../lib/api";

const settings = ref<Record<string, { value: unknown; source: string }>>({});
const formats = ref<string[]>([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const [settingsRes, formatsRes] = await Promise.all([
      api.get("/api/v1/publish/formats"),
      api.get("/api/v1/publish/formats"),
    ]);
    formats.value = formatsRes.data.formats;
  } catch { /* Settings endpoint not implemented yet */ }
  loading.value = false;
});

const categories = ["llm", "embeddings", "output", "env", "system"];
</script>

<template>
  <div class="max-w-3xl">
    <h2 class="text-xl font-semibold mb-6">Settings</h2>

    <div class="space-y-6">
      <!-- LLM Provider -->
      <div class="bg-white border rounded-lg p-4">
        <h3 class="font-medium text-gray-800 mb-3">LLM Provider</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1">Provider</label>
            <select class="w-full px-3 py-2 border rounded-lg">
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="ollama">Ollama</option>
            </select>
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Model</label>
            <input value="gpt-4o" class="w-full px-3 py-2 border rounded-lg" />
          </div>
        </div>
      </div>

      <!-- API Keys -->
      <div class="bg-white border rounded-lg p-4">
        <h3 class="font-medium text-gray-800 mb-3">API Keys (BYOK)</h3>
        <div class="space-y-3">
          <div>
            <label class="block text-sm text-gray-600 mb-1">OpenAI</label>
            <input type="password" placeholder="sk-..." class="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Anthropic</label>
            <input type="password" placeholder="sk-ant-..." class="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Ollama URL</label>
            <input value="http://localhost:11434" class="w-full px-3 py-2 border rounded-lg" />
          </div>
        </div>
      </div>

      <!-- Output -->
      <div class="bg-white border rounded-lg p-4">
        <h3 class="font-medium text-gray-800 mb-3">Output</h3>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm text-gray-600 mb-1">Default directory</label>
            <input value="gandra-output/" class="w-full px-3 py-2 border rounded-lg" />
          </div>
          <div>
            <label class="block text-sm text-gray-600 mb-1">Default format</label>
            <select class="w-full px-3 py-2 border rounded-lg">
              <option v-for="f in formats" :key="f" :value="f">{{ f }}</option>
            </select>
          </div>
        </div>
      </div>

      <button class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">Save</button>
    </div>
  </div>
</template>
