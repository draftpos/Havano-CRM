<template>
  <div v-if="tasks.length" class="space-y-8 px-4 pb-6 pt-1 sm:px-8">
    <div v-for="group in groupedTasks" :key="group.key" class="space-y-3">
      <h3 class="text-sm font-semibold text-ink-gray-7">
        {{ group.label }}
        <span class="font-normal text-ink-gray-5">({{ group.items.length }})</span>
      </h3>
      <div class="flex flex-col gap-3">
        <div
          v-for="task in group.items"
          :key="task.name"
          class="flex cursor-pointer gap-4 rounded-xl border border-outline-gray-modals bg-white p-4 shadow-sm transition-shadow duration-200 ease-out hover:shadow-md"
          @click="modalRef.showTask(task)"
        >
          <div class="flex min-w-0 flex-1 flex-col gap-2">
            <div class="text-base font-semibold text-ink-gray-9">
              {{ taskHeadline(task) }}
            </div>
            <div
              v-if="taskBody(task)"
              class="line-clamp-3 text-sm text-ink-gray-6"
            >
              {{ taskBody(task) }}
            </div>
            <div class="flex flex-wrap items-center gap-2 text-sm text-ink-gray-7">
              <span
                class="inline-flex rounded-md px-2 py-0.5 text-xs font-medium"
                :class="priorityChipClass(task.priority)"
              >
                {{ task.priority || __('General') }}
              </span>
            </div>
            <div class="flex items-start gap-2 text-sm text-ink-gray-8">
              <UserAvatar :user="taskAssigneeKey(task)" size="xs" class="mt-0.5" />
              <div class="min-w-0 flex-1 leading-snug">
                <span class="font-medium text-ink-gray-9">{{
                  taskOwnerName(task)
                }}</span>
                <template v-if="taskDueSegment(task)">
                  <span class="text-ink-gray-7">
                    . {{ taskDueSegment(task) }}
                  </span>
                </template>
                <template v-if="task.creation">
                  <span class="text-ink-gray-6">
                    . {{ __(timeAgo(task.creation)) }}
                  </span>
                </template>
              </div>
            </div>
          </div>
          <div class="flex shrink-0 items-start gap-1 pt-0.5">
            <Dropdown
              :options="taskStatusOptions(modalRef.updateTaskStatus, task)"
            >
              <Button
                :tooltip="__('Change Status')"
                variant="ghosted"
                class="hover:bg-surface-gray-2"
                @click.stop.prevent
              >
                <TaskStatusIcon :status="task.status" />
              </Button>
            </Dropdown>
            <Dropdown
              :options="[
                {
                  label: __('Delete'),
                  icon: 'trash-2',
                  onClick: () => {
                    $dialog({
                      title: __('Delete Task'),
                      message: __('Are you sure you want to delete this task?'),
                      actions: [
                        {
                          label: __('Delete'),
                          theme: 'red',
                          variant: 'solid',
                          onClick(close) {
                            modalRef.deleteTask(task.name)
                            close()
                          },
                        },
                      ],
                    })
                  },
                },
              ]"
            >
              <Button
                icon="more-horizontal"
                variant="ghosted"
                class="text-ink-gray-9 hover:bg-surface-gray-2"
                @click.stop.prevent
              />
            </Dropdown>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { htmlToText, taskStatusOptions, timeAgo } from '@/utils'
import { usersStore } from '@/stores/users'
import { globalStore } from '@/stores/global'
import { Dropdown, dayjs } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
  modalRef: { type: Object, default: () => ({}) },
})

const { getUser } = usersStore()
const { $dialog } = globalStore()

function plainDescription(html) {
  const t = htmlToText(html || '')
  return t || ''
}

function taskHeadline(task) {
  const p = plainDescription(task.description)
  if (task.title) return task.title
  if (!p) return __('(no title)')
  if (p.length <= 100) return p
  return `${p.slice(0, 97)}…`
}

function taskBody(task) {
  const p = plainDescription(task.description)
  if (!p) return ''
  if (task.title) return p
  if (p.length <= 100) return ''
  return p.slice(97).trim()
}

function statusGroup(status) {
  if (!status) return 'todo'
  const s = String(status)
  if (s === 'Done' || s === 'Closed' || s === 'Canceled' || s === 'Cancelled')
    return 'done'
  if (s === 'In Progress') return 'progress'
  return 'todo'
}

function taskAssigneeKey(task) {
  return task.allocated_to || task.assigned_to || ''
}

function taskOwnerName(task) {
  const k = taskAssigneeKey(task)
  if (!k) return __('Unassigned')
  return getUser(k).full_name || k
}

function taskDueDateRaw(task) {
  return task.date || task.due_date || null
}

function taskDueSegment(task) {
  const d = taskDueDateRaw(task)
  if (!d) return ''
  const formatted = dayjs(d).format('DD/MM/YYYY')
  if (statusGroup(task.status) === 'done') {
    return formatted
  }
  const due = dayjs(d).startOf('day')
  const today = dayjs().startOf('day')
  const diff = due.diff(today, 'day')
  if (diff < 0) {
    return `${formatted} (${__('overdue')})`
  }
  if (diff === 0) {
    return `${formatted} (${__('today')})`
  }
  if (diff === 1) {
    return `${formatted} (${__('in 1 day')})`
  }
  return `${formatted} (${__('in {0} days', [String(diff)])})`
}

const groupedTasks = computed(() => {
  const groups = [
    { key: 'todo', label: __('To do'), items: [] },
    { key: 'progress', label: __('In Progress'), items: [] },
    { key: 'done', label: __('Done'), items: [] },
  ]
  const byKey = {
    todo: groups[0].items,
    progress: groups[1].items,
    done: groups[2].items,
  }
  for (const task of props.tasks) {
    byKey[statusGroup(task.status)].push(task)
  }
  return groups.filter((g) => g.items.length > 0)
})

function priorityChipClass(priority) {
  const map = {
    Low: 'bg-slate-100 text-slate-700',
    Medium: 'bg-violet-100 text-violet-800',
    High: 'bg-amber-100 text-amber-900',
    Urgent: 'bg-red-100 text-red-800',
  }
  return map[priority] || 'bg-emerald-50 text-emerald-800'
}
</script>
