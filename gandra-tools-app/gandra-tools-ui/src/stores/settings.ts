import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../lib/api";

interface SettingEntry {
  value: unknown;
  source: string;
}

export const useSettingsStore = defineStore("settings", () => {
  const settings = ref<Record<string, SettingEntry>>({});
  const activeEnv = ref<string | null>(null);
  const formats = ref<string[]>([]);

  async function loadSettings() {
    const { data } = await api.get("/api/v1/settings");
    settings.value = data;
  }

  async function loadFormats() {
    const { data } = await api.get("/api/v1/publish/formats");
    formats.value = data.formats;
  }

  function get(key: string): unknown {
    return settings.value[key]?.value ?? null;
  }

  return { settings, activeEnv, formats, loadSettings, loadFormats, get };
});
