<template>
  <Dialog v-model="show" :options="{ size: '3xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Create Deal') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              v-if="isManager() && !isMobileView"
              variant="ghost"
              class="w-7"
              :tooltip="__('Edit Fields Layout')"
              :icon="EditIcon"
              @click="openQuickEntryModal"
            />
            <Button
              variant="ghost"
              class="w-7"
              icon="x"
              @click="show = false"
            />
          </div>
        </div>
        <div>
          <div
            v-if="hasOrganizationSections || hasContactSections"
            class="mb-4 grid grid-cols-1 gap-4 sm:grid-cols-3"
          >
            <div
              v-if="hasOrganizationSections"
              class="flex items-center gap-3 text-sm text-ink-gray-5"
            >
              <div>{{ __('Choose Existing Organization') }}</div>
              <Switch v-model="chooseExistingOrganization" />
            </div>
            <div
              v-if="hasContactSections"
              class="flex items-center gap-3 text-sm text-ink-gray-5"
            >
              <div>{{ __('Choose Existing Contact') }}</div>
              <Switch v-model="chooseExistingContact" />
            </div>
          </div>
          <div
            v-if="hasOrganizationSections || hasContactSections"
            class="h-px w-full border-t my-5"
          />
          <FieldLayout
            v-if="tabs.data?.length"
            :tabs="tabs.data"
            :data="deal.doc"
            doctype="Opportunity"
          />
          <ErrorMessage v-if="error" class="mt-4" :message="__(error)" />
        </div>
      </div>
      <div class="px-4 pb-7 pt-4 sm:px-6">
        <div class="flex flex-row-reverse gap-2">
          <Button
            variant="solid"
            :label="__('Create')"
            :loading="isDealCreating"
            @click="createDeal"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import EditIcon from '@/components/Icons/EditIcon.vue'
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { usersStore } from '@/stores/users'
import { statusesStore } from '@/stores/statuses'
import { isMobileView } from '@/composables/settings'
import { showQuickEntryModal, quickEntryProps } from '@/composables/modals'
import { useDocument } from '@/data/document'
import { useTelemetry } from 'frappe-ui/frappe'
import { Switch, createResource, call } from 'frappe-ui'
import { computed, ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  defaults: { type: Object, default: () => ({}) },
})

const { getUser, isManager } = usersStore()
const { getDealStatus, statusOptions } = statusesStore()

const show = defineModel({ type: Boolean })
const router = useRouter()
const error = ref(null)

const { document: deal, triggerOnBeforeCreate } = useDocument('Opportunity')

const hasOrganizationSections = ref(true)
const hasContactSections = ref(true)

const isDealCreating = ref(false)
const chooseExistingContact = ref(false)
const chooseExistingOrganization = ref(false)
const { capture } = useTelemetry()

watch(
  [chooseExistingOrganization, chooseExistingContact],
  ([organization, contact]) => {
    tabs.data.forEach((tab) => {
      tab.sections.forEach((section) => {
        if (section.name === 'organization_section') {
          section.hidden = !organization
        } else if (section.name === 'organization_details_section') {
          section.hidden = organization
        } else if (section.name === 'contact_section') {
          section.hidden = !contact
        } else if (section.name === 'contact_details_section') {
          section.hidden = contact
        }
      })
    })
  },
)

const tabs = createResource({
  url: 'havano_crm.api.fields_layout.get_fields_layout',
  cache: ['QuickEntry', 'Opportunity'],
  params: { doctype: 'Opportunity', type: 'Quick Entry' },
  auto: true,
  transform: (_tabs) => {
    hasOrganizationSections.value = false
    return _tabs.forEach((tab) => {
      tab.sections.forEach((section) => {
        section.columns.forEach((column) => {
          if (
            ['organization_section', 'organization_details_section'].includes(
              section.name,
            )
          ) {
            hasOrganizationSections.value = true
          } else if (
            ['contact_section', 'contact_details_section'].includes(
              section.name,
            )
          ) {
            hasContactSections.value = true
          }
          column.fields.forEach((field) => {
            if (field.fieldname == 'status') {
              field.fieldtype = 'Select'
              field.options = dealStatuses.value
              field.prefix = getDealStatus(deal.doc.status).color
            }

            if (field.fieldtype === 'Table') {
              deal.doc[field.fieldname] = []
            }
          })
        })
      })
    })
  },
})

const dealStatuses = computed(() => statusOptions('deal'))

async function createDeal() {
  if (deal.doc.website && !deal.doc.website.startsWith('http')) {
    deal.doc.website = 'https://' + deal.doc.website
  }
  if (chooseExistingContact.value) {
    deal.doc['first_name'] = null
    deal.doc['last_name'] = null
    deal.doc['email'] = null
    deal.doc['mobile_no'] = null
  } else deal.doc['contact'] = null

  error.value = null
  if (deal.doc.annual_revenue) {
    if (typeof deal.doc.annual_revenue === 'string') {
      deal.doc.annual_revenue = deal.doc.annual_revenue.replace(/,/g, '')
    } else if (isNaN(deal.doc.annual_revenue)) {
      error.value = __('Annual Revenue should be a number')
      return
    }
  }
  if (
    deal.doc.mobile_no &&
    isNaN(deal.doc.mobile_no.replace(/[-+() ]/g, ''))
  ) {
    error.value = __('Mobile No. should be a number')
    return
  }
  if (deal.doc.email && !deal.doc.email.includes('@')) {
    error.value = __('Invalid email address')
    return
  }
  if (!deal.doc.status) {
    error.value = __('Status is required')
    return
  }

  await triggerOnBeforeCreate?.()

  isDealCreating.value = true
  try {
    const name = await call('havano_crm.api.opportunity.create_deal', {
      doc: JSON.parse(JSON.stringify(deal.doc)),
    })
    const dealId = typeof name === 'string' ? name : name?.message
    if (dealId) {
      capture('deal_created')
      show.value = false
      router.push({ name: 'Deal', params: { dealId } })
    }
  } catch (err) {
    if (err.messages?.length) {
      error.value = err.messages.join('\n')
    } else {
      error.value = err.message
    }
  } finally {
    isDealCreating.value = false
  }
}

function openQuickEntryModal() {
  showQuickEntryModal.value = true
  quickEntryProps.value = { doctype: 'Opportunity' }
  nextTick(() => (show.value = false))
}

onMounted(async () => {
  deal.doc.no_of_employees = '1-10'
  try {
    const defs = await call('havano_crm.api.opportunity.get_create_deal_defaults')
    if (defs && typeof defs === 'object') {
      if (defs.opportunity_from != null && !deal.doc.opportunity_from) {
        deal.doc.opportunity_from = defs.opportunity_from
      }
      if (defs.transaction_date != null && !deal.doc.transaction_date) {
        deal.doc.transaction_date = defs.transaction_date
      }
      if (defs.company != null && !deal.doc.company) {
        deal.doc.company = defs.company
      }
    }
  } catch {
    /* defaults are optional; server still applies on create */
  }
  Object.assign(deal.doc, props.defaults)

  if (!deal.doc.opportunity_owner) {
    deal.doc.opportunity_owner = getUser().name
  }
  if (!deal.doc.status && dealStatuses.value[0].value) {
    deal.doc.status = dealStatuses.value[0].value
  }
})
</script>
