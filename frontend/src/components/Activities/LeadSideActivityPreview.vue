<template>
  <div class="border-b border-slate-200/90 bg-slate-50/40 px-4 py-3">
    <div class="mb-2 flex items-center justify-between gap-2">
      <span class="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {{ __('Recent activity') }}
      </span>
      <Button variant="ghost" class="!h-7 !px-2 !text-xs" @click="emit('view-all')">
        {{ __('View all') }}
      </Button>
    </div>
    <div
      v-if="feed.loading && !feed.data"
      class="flex items-center gap-2 py-2 text-sm text-ink-gray-5"
    >
      <LoadingIndicator class="h-4 w-4" />
      {{ __('Loading...') }}
    </div>
    <ul
      v-else-if="previewItems.length"
      class="max-h-64 space-y-2 overflow-y-auto pr-0.5 text-sm"
    >
      <li
        v-for="item in previewItems"
        :key="itemKey(item)"
        class="flex items-start gap-2 rounded-md border border-transparent px-1 py-1 hover:border-slate-200/80 hover:bg-white"
      >
        <template v-if="item.kind === 'feed'">
          <div class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center text-ink-gray-6">
            <component :is="previewIcon(item.row)" class="h-3.5 w-3.5" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="truncate text-ink-gray-8">
              <span class="font-medium">{{ ownerName(item.row) }}</span>
              {{ ' ' }}
              <span class="text-ink-gray-6">{{ previewPhrase(item.row) }}</span>
            </div>
            <div class="text-xs text-ink-gray-5">
              {{ __(timeAgo(item.row.creation)) }}
            </div>
          </div>
        </template>
        <template v-else-if="item.kind === 'event'">
          <div class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center text-emerald-600">
            <CalendarIcon class="h-3.5 w-3.5" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-ink-gray-8">
              <span class="font-medium">{{ ownerName(item.event) }}</span>
              {{ ' ' }}
              <span class="text-ink-gray-6">{{ __('scheduled an event') }}</span>
            </div>
            <div
              class="line-clamp-3 break-words leading-snug text-ink-gray-7"
            >
              {{ eventSubject(item.event) }}
            </div>
            <div class="mt-0.5 text-xs text-ink-gray-5">
              {{ eventWhenLabel(item.event) }}
            </div>
          </div>
        </template>
        <template v-else-if="item.kind === 'note'">
          <div class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center text-violet-600">
            <NoteIcon class="h-3.5 w-3.5" />
          </div>
          <div class="min-w-0 flex-1">
            <div class="text-ink-gray-8">
              <span class="font-medium">{{ noteOwnerName(item.note) }}</span>
              {{ ' ' }}
              <span class="text-ink-gray-6">{{ __('added a note') }}</span>
            </div>
            <div
              class="line-clamp-3 break-words leading-snug text-ink-gray-7"
            >
              {{ noteTitle(item.note) }}
            </div>
            <div class="mt-0.5 text-xs text-ink-gray-5">
              {{ __(timeAgo(item.note.modified || item.note.creation)) }}
            </div>
          </div>
        </template>
        <template v-else>
          <div class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center text-sky-600">
            <TaskIcon class="h-3.5 w-3.5" />
          </div>
          <div class="min-w-0 flex-1 cursor-pointer" @click="taskActions?.edit?.(item.task)">
            <div class="text-ink-gray-8">
              <span class="font-medium">{{ taskAssigneeName(item.task) }}</span>
              {{ ' ' }}
              <span class="text-ink-gray-6">{{ __('To-do') }}</span>
              <span class="text-ink-gray-5"> · {{ __(item.task.status) }}</span>
            </div>
            <div
              class="line-clamp-3 break-words leading-snug text-ink-gray-7"
            >
              {{ taskTitle(item.task) }}
            </div>
            <div class="mt-0.5 text-xs text-ink-gray-5">
              {{ __(timeAgo(item.task.modified || item.task.creation)) }}
            </div>
          </div>
          <div
            v-if="showTodoQuickActions(item.task)"
            class="flex shrink-0 items-start gap-0.5 pt-0.5"
            @click.stop
          >
            <Button
              variant="ghost"
              class="!h-7 !min-h-0 !px-1.5"
              :tooltip="__('Edit')"
              icon="edit-2"
              @click="onEditTask(item.task)"
            />
            <Button
              variant="ghost"
              class="!h-7 !min-h-0 !px-1.5"
              :tooltip="__('Mark as done')"
              icon="check"
              @click="onMarkDone(item.task)"
            />
            <Button
              variant="ghost"
              class="!h-7 !min-h-0 !px-1.5"
              :tooltip="__('Cancel')"
              icon="x"
              @click="onCancelTask(item.task)"
            />
          </div>
        </template>
      </li>
    </ul>
    <div v-else class="py-1 text-sm text-ink-gray-5">
      {{ __('No activity yet.') }}
    </div>
  </div>
</template>

<script setup>
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import CommentIcon from '@/components/Icons/CommentIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import AttachmentIcon from '@/components/Icons/AttachmentIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import DotIcon from '@/components/Icons/DotIcon.vue'
import InboundCallIcon from '@/components/Icons/InboundCallIcon.vue'
import OutboundCallIcon from '@/components/Icons/OutboundCallIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import { timeAgo, formatDate } from '@/utils'
import { usersStore } from '@/stores/users'
import { Button, createResource } from 'frappe-ui'
import { computed, markRaw, watch } from 'vue'

const props = defineProps({
  docname: { type: String, required: true },
  /** DocType for activity cache key (Lead | Opportunity). */
  doctype: { type: String, default: 'Lead' },
  taskActions: {
    type: Object,
    default: () => ({}),
  },
})

const emit = defineEmits(['view-all', 'task-updated'])

const { getUser } = usersStore()

const feed = createResource({
  url: 'havano_crm.api.activities.get_activities',
  params: { name: props.docname },
  cache: ['activity', props.doctype, props.docname],
  auto: true,
  transform: ([versions, calls, notes, tasks, attachments, events = []]) => {
    return { versions, calls, notes, tasks, attachments, events: events || [] }
  },
})

const PREVIEW_LIMIT = 12

function plainText(html) {
  if (!html) return ''
  return String(html)
    .replace(/<[^>]*>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}

const previewItems = computed(() => {
  const d = feed.data
  if (!d) return []

  const items = []

  for (const row of d.versions || []) {
    items.push({
      kind: 'feed',
      row,
      ts: new Date(row.creation).getTime(),
    })
  }
  for (const row of d.calls || []) {
    items.push({
      kind: 'feed',
      row,
      ts: new Date(row.creation).getTime(),
    })
  }
  for (const note of d.notes || []) {
    items.push({
      kind: 'note',
      note,
      ts: new Date(note.modified || note.creation).getTime(),
    })
  }
  for (const event of d.events || []) {
    items.push({
      kind: 'event',
      event,
      ts: new Date(event.starts_on || event.modified || event.creation).getTime(),
    })
  }
  for (const task of d.tasks || []) {
    items.push({
      kind: 'task',
      task,
      ts: new Date(task.modified || task.creation).getTime(),
    })
  }

  items.sort((a, b) => b.ts - a.ts)
  return items.slice(0, PREVIEW_LIMIT)
})

function itemKey(item) {
  if (item.kind === 'feed') {
    const r = item.row
    return `feed-${r.name || ''}-${r.creation}-${r.activity_type}`
  }
  if (item.kind === 'note') {
    return `note-${item.note.name}-${item.note.modified}`
  }
  if (item.kind === 'event') {
    return `event-${item.event.name}-${item.event.modified || item.event.creation}`
  }
  return `task-${item.task.name}-${item.task.modified}`
}

function ownerName(row) {
  return getUser(row.owner).full_name || row.owner || ''
}

function noteOwnerName(note) {
  return getUser(note.owner).full_name || note.owner || ''
}

function taskAssigneeName(task) {
  const u = task.allocated_to
  if (!u) return __('Unassigned')
  return getUser(u).full_name || u
}

function noteTitle(note) {
  const t = (note.title || '').trim()
  if (t) return t
  const plain = plainText(note.content)
  return plain || __('(no title)')
}

function taskTitle(task) {
  const plain = plainText(task.description)
  return plain || __('(no title)')
}

function eventSubject(ev) {
  const t = (ev.subject || '').trim()
  return t || __('(no title)')
}

function eventWhenLabel(ev) {
  if (ev.starts_on) {
    return formatDate(ev.starts_on, '', true, false)
  }
  return __(timeAgo(ev.modified || ev.creation))
}

function previewPhrase(row) {
  switch (row.activity_type) {
    case 'comment':
      return __('commented')
    case 'communication':
      return __('sent an email')
    case 'creation':
      return typeof row.data === 'string' ? __(row.data) : __('created this record')
    case 'added':
      return __('added a field')
    case 'removed':
      return __('removed a value')
    case 'changed':
      return row.data?.field_label
        ? `${__('updated')} ${__(row.data.field_label)}`
        : __('updated the record')
    case 'attachment_log':
      return __('attached a file')
    case 'incoming_call':
      return __('incoming call')
    case 'outgoing_call':
      return __('outgoing call')
    default:
      return __('added an activity')
  }
}

function showTodoQuickActions(task) {
  const s = String(task?.status ?? 'Open')
  if (['Closed', 'Cancelled', 'Canceled', 'Done'].includes(s)) return false
  return true
}

function onEditTask(task) {
  props.taskActions?.edit?.(task)
}

function onMarkDone(task) {
  props.taskActions?.markDone?.(task)
  emit('task-updated')
}

function onCancelTask(task) {
  props.taskActions?.cancel?.(task)
  emit('task-updated')
}

watch(
  () => [props.docname, props.doctype],
  () => {
    if (props.docname) feed.reload()
  },
)

function reloadFeed() {
  feed.reload()
}

defineExpose({ reloadFeed })

function previewIcon(row) {
  const isLead = row.is_lead
  switch (row.activity_type) {
    case 'creation':
      return markRaw(isLead ? LeadsIcon : DealsIcon)
    case 'comment':
      return markRaw(CommentIcon)
    case 'communication':
      return markRaw(Email2Icon)
    case 'event':
      return markRaw(CalendarIcon)
    case 'incoming_call':
      return markRaw(InboundCallIcon)
    case 'outgoing_call':
      return markRaw(OutboundCallIcon)
    case 'attachment_log':
      return markRaw(AttachmentIcon)
    default:
      return markRaw(DotIcon)
  }
}
</script>
