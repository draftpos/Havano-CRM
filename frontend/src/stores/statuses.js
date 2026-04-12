import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { parseColor, isTranslatable } from '@/utils'
import { defineStore } from 'pinia'
import { useTelemetry } from 'frappe-ui/frappe'
import { createResource } from 'frappe-ui'
import { reactive, h } from 'vue'

export const statusesStore = defineStore('crm-statuses', () => {
  let leadStatusesByName = reactive({})
  let dealStatusesByName = reactive({})
  let communicationStatusesByName = reactive({})

  const { capture } = useTelemetry()

  const leadStatuses = createResource({
    url: 'havano_crm.api.meta_ext.get_lead_status_options',
    cache: 'lead-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        status.color = parseColor(status.color)
        leadStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  const dealStatuses = createResource({
    url: 'havano_crm.api.meta_ext.get_deal_status_options',
    cache: 'deal-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        status.color = parseColor(status.color)
        dealStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  const communicationStatuses = createResource({
    url: 'havano_crm.api.meta_ext.get_communication_status_options',
    cache: 'communication-statuses',
    initialData: [],
    auto: true,
    transform(statuses) {
      for (let status of statuses) {
        communicationStatusesByName[status.name] = status
      }
      return statuses
    },
  })

  function getLeadStatus(name) {
    if (!name && leadStatuses.data?.length) {
      name = leadStatuses.data[0].name
    }
    return leadStatusesByName[name]
  }

  function getDealStatus(name) {
    if (!name && dealStatuses.data?.length) {
      name = dealStatuses.data[0].name
    }
    return dealStatusesByName[name]
  }

  function getCommunicationStatus(name) {
    if (!name && communicationStatuses.data?.length) {
      name = communicationStatuses.data[0].name
    }
    return communicationStatusesByName[name]
  }

  function statusOptions(doctype, statuses = [], triggerStatusChange = null) {
    let statusesByName =
      doctype == 'deal' ? dealStatusesByName : leadStatusesByName

    if (statuses?.length) {
      statusesByName = statuses.reduce((acc, status) => {
        acc[status] = statusesByName[status]
        return acc
      }, {})
    }

    let translatable = isTranslatable(doctype == 'deal' ? 'Opportunity' : 'Lead')

    let options = []
    for (const status in statusesByName) {
      options.push({
        label: translatable
          ? __(statusesByName[status]?.name)
          : statusesByName[status]?.name,
        value: statusesByName[status]?.name,
        icon: () => h(IndicatorIcon, { class: statusesByName[status]?.color }),
        onClick: async () => {
          await triggerStatusChange?.(statusesByName[status]?.name)
          capture('status_changed', { doctype, status })
        },
      })
    }
    return options
  }

  return {
    leadStatuses,
    dealStatuses,
    communicationStatuses,
    getLeadStatus,
    getDealStatus,
    getCommunicationStatus,
    statusOptions,
  }
})
