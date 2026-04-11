<template>
  <Dialog v-model="show" :options="{ size: '2xl' }">
    <template #body>
      <div class="bg-surface-modal px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-4">
          <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
            {{ __('Open Todo') }}
          </h3>
          <p v-if="referenceLabel" class="mt-1 text-sm text-ink-gray-5">
            {{ referenceLabel }}
          </p>
        </div>
        <div v-if="loading" class="flex items-center gap-2 py-8 text-ink-gray-5">
          <LoadingIndicator class="h-5 w-5" />
          {{ __('Loading...') }}
        </div>
        <div v-else-if="!tasks.length" class="py-8 text-center text-ink-gray-5">
          {{ emptyMessage }}
        </div>
        <ul v-else class="max-h-[min(420px,60vh)] space-y-3 overflow-y-auto pr-1">
          <li
            v-for="t in tasks"
            :key="t.name"
            class="flex flex-col gap-3 rounded-lg border border-outline-gray-modals bg-surface-gray-2 p-3 sm:flex-row sm:items-center"
          >
            <div class="min-w-0 flex-1">
              <div class="font-medium text-ink-gray-9">
                {{ plainTitle(t.description) }}
              </div>
              <div class="mt-1 text-xs leading-snug text-ink-gray-6">
                <span class="font-medium text-ink-gray-8">{{
                  assigneeLabel(t)
                }}</span>
                <template v-if="openTodoDueSegment(t)">
                  <span>. {{ openTodoDueSegment(t) }}</span>
                </template>
                <template v-if="t.creation">
                  <span>. {{ __(timeAgo(t.creation)) }}</span>
                </template>
                <template v-if="t.priority">
                  <span>. {{ __(t.priority) }}</span>
                </template>
              </div>
            </div>
            <div class="flex shrink-0 flex-wrap gap-2">
              <Button
                size="sm"
                variant="subtle"
                :label="__('Edit')"
                @click="emit('edit', t)"
              />
              <Button
                size="sm"
                variant="solid"
                theme="green"
                :label="__('Done')"
                @click="setStatus(t, 'Closed')"
              />
              <Button
                size="sm"
                variant="subtle"
                :label="__('Cancel')"
                @click="setStatus(t, 'Cancelled')"
              />
            </div>
          </li>
        </ul>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { htmlToText, timeAgo } from '@/utils'
import { usersStore } from '@/stores/users'
import { Dialog, Button, call, dayjs } from 'frappe-ui'
import { ref, watch, computed } from 'vue'

const { getUser } = usersStore()

const props = defineProps({
  /** Reference document name (Lead or Opportunity). */
  leadName: { type: String, default: '' },
  referenceDoctype: { type: String, default: 'Lead' },
})

const show = defineModel({ type: Boolean, default: false })
const emit = defineEmits(['edit', 'updated'])

const loading = ref(false)
const tasks = ref([])

const referenceLabel = computed(() => props.leadName)

const emptyMessage = computed(() =>
  props.referenceDoctype === 'Opportunity'
    ? __('No open todo for this deal.')
    : __('No open todo for this lead.'),
)

function plainTitle(html) {
  const s = htmlToText(html || '')
  return s || __('(no title)')
}

function assigneeLabel(t) {
  const u = t.allocated_to
  if (!u) return __('Unassigned')
  return getUser(u).full_name || u
}

function openTodoDueSegment(t) {
  if (!t.date) return ''
  const formatted = dayjs(t.date).format('DD/MM/YYYY')
  const due = dayjs(t.date).format('YYYY-MM-DD')
  const today = dayjs().format('YYYY-MM-DD')
  if (due < today) {
    return `${formatted}(${__('overdue')})`
  }
  return formatted
}

async function load() {
  if (!props.leadName) {
    tasks.value = []
    return
  }
  loading.value = true
  try {
    tasks.value =
      (await call('havano_crm.api.activities.get_open_todos_for_reference', {
        reference_doctype: props.referenceDoctype,
        reference_name: props.leadName,
      })) || []
  } catch {
    tasks.value = []
  } finally {
    loading.value = false
  }
}

watch(
  () => [show.value, props.leadName, props.referenceDoctype],
  ([open]) => {
    if (open) load()
  },
)

async function setStatus(t, value) {
  await call('frappe.client.set_value', {
    doctype: 'ToDo',
    name: t.name,
    fieldname: 'status',
    value,
  })
  emit('updated')
  await load()
}
</script>
