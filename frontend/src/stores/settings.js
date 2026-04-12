import { createResource } from 'frappe-ui'
import { reactive, ref } from 'vue'

const settings = ref({})
const brand = reactive({})

const _settings = createResource({
  url: 'havano_crm.api.settings_havano.get_ui_settings',
  auto: true,
  onSuccess(data) {
    settings.value = data || {}
    getSettings().setupBrand()
    return data
  },
})

export function getSettings() {
  function setupBrand() {
    brand.name = settings.value?.brand_name
    brand.logo = settings.value?.brand_logo
    brand.favicon = settings.value?.favicon
  }

  return {
    _settings,
    settings,
    brand,
    setupBrand,
  }
}
