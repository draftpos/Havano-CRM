<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body-title>
      <div class="flex items-center gap-3">
        <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
          {{ editMode ? __('Edit Task') : __('Create Task') }}
        </h3>
        <Button
          v-if="task?.reference_docname"
          size="sm"
          :label="
            task.reference_doctype == 'Opportunity'
              ? __('Open Deal')
              : __('Open Lead')
          "
          :iconRight="ArrowUpRightIcon"
          @click="redirect()"
        />
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="space-y-1.5">
          <FormLabel :label="__('Title')" required />
          <TextInput
            ref="title"
            v-model="_task.title"
            :placeholder="__('Call with John Doe')"
            required
          />
        </div>
        <div>
          <div class="mb-1.5 text-xs text-ink-gray-5">
            {{ __('Description') }}
          </div>
          <TextEditor
            ref="description"
            variant="outline"
            editor-class="!prose-sm overflow-auto min-h-[180px] max-h-80 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
            :bubbleMenu="true"
            :content="_task.description"
            :placeholder="
              __('Took a call with John Doe and discussed the new project.')
            "
            @change="(val) => (_task.description = val)"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <Dropdown :options="taskStatusOptions(updateTaskStatus)">
            <Button :label="_task.status">
              <template #prefix>
                <TaskStatusIcon :status="_task.status" />
              </template>
            </Button>
          </Dropdown>
          <Link
            class="form-control"
            :value="getUser(_task.assigned_to).full_name"
            doctype="User"
            :placeholder="__('John Doe')"
            :filters="{
              name: ['in', users.data.crmUsers?.map((user) => user.name)],
              ignore_user_type: 1,
            }"
            :hideMe="true"
            @change="(option) => (_task.assigned_to = option)"
          >
            <template #prefix>
              <UserAvatar class="mr-2 !h-4 !w-4" :user="_task.assigned_to" />
            </template>
            <template #item-prefix="{ option }">
              <UserAvatar class="mr-2" :user="option.value" size="sm" />
            </template>
            <template #item-label="{ option }">
              <Tooltip :text="option.value">
                <div class="cursor-pointer text-ink-gray-9">
                  {{ getUser(option.value).full_name }}
                </div>
              </Tooltip>
            </template>
          </Link>
          <div class="w-36">
            <DateTimePicker
              v-model="_task.due_date"
              class="datepicker"
              :placeholder="__('01/04/2024 11:30 PM')"
              :format="getFormat('', '', true, true, false)"
              input-class="border-none"
            />
          </div>
          <Dropdown :options="taskPriorityOptions(updateTaskPriority)">
            <Button :label="_task.priority">
              <template #prefix>
                <TaskPriorityIcon :priority="_task.priority" />
              </template>
            </Button>
          </Dropdown>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end">
        <Button
          :label="editMode ? __('Update') : __('Create')"
          variant="solid"
          :loading="createTaskResource.loading || updateTaskResource.loading"
          @click="updateTask"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import { taskStatusOptions, taskPriorityOptions, getFormat } from '@/utils'
import { usersStore } from '@/stores/users'
import { useTelemetry } from 'frappe-ui/frappe'
import {
  TextEditor,
  Dropdown,
  Tooltip,
  DateTimePicker,
  createResource,
  toast,
  TextInput,
  FormLabel,
  dayjs,
} from 'frappe-ui'
import { useOnboarding } from 'frappe-ui/frappe'
import { ref, watch, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  task: { type: Object, default: () => ({}) },
  doctype: { type: String, default: 'Lead' },
  doc: { type: String, default: '' },
})

const show = defineModel({ type: Boolean })
const tasks = defineModel('reloadTasks', { type: Object, default: () => ({}) })

const emit = defineEmits(['updateTask', 'after'])

const router = useRouter()
const { users, getUser } = usersStore()
const { updateOnboardingStep } = useOnboarding('frappecrm')
const { capture } = useTelemetry()

const title = ref(null)
const editMode = ref(false)

function defaultTaskState() {
  return {
    title: '',
    description: '',
    assigned_to: '',
    due_date: '',
    status: 'Backlog',
    priority: 'Low',
    reference_doctype: props.doctype,
    reference_docname: null,
  }
}

const _task = ref(defaultTaskState())

/** ERPNext ToDo uses description (HTML), allocated_to, date, reference_type/name, status Open|Closed|Cancelled */
function escapeHtml(text) {
  if (!text) return ''
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function stripHtml(html) {
  if (!html) return ''
  return String(html).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
}

function mapUiStatusToTodo(status) {
  if (status === 'Done') return 'Closed'
  if (status === 'Canceled') return 'Cancelled'
  return 'Open'
}

function mapTodoStatusToUi(status) {
  if (status === 'Closed') return 'Done'
  if (status === 'Cancelled') return 'Canceled'
  return 'Backlog'
}

function buildTodoDescription(title, descriptionHtml) {
  const t = (title || '').trim()
  const body = (descriptionHtml || '').trim()
  const bodyPlain = stripHtml(body)
  if (!t && !bodyPlain) return '<p></p>'
  if (!bodyPlain) return `<p>${escapeHtml(t)}</p>`
  return `<p><strong>${escapeHtml(t)}</strong></p>${body}`
}

function todoDueDateOnly(due) {
  if (!due) return ''
  const d = dayjs(due)
  return d.isValid() ? d.format('YYYY-MM-DD') : ''
}

function normalizeTaskFromProps(task) {
  const t = task && typeof task === 'object' ? { ...task } : {}
  const base = defaultTaskState()

  if (t.allocated_to && !t.assigned_to) t.assigned_to = t.allocated_to
  if (t.date && !t.due_date) {
    t.due_date = String(t.date).includes(' ')
      ? t.date
      : `${t.date} 00:00:00`
  }
  if (t.reference_type && !t.reference_doctype) {
    t.reference_doctype = t.reference_type
  }
  if (t.reference_name != null && t.reference_docname == null) {
    t.reference_docname = t.reference_name
  }
  if (!t.title && t.description) {
    const plain = stripHtml(t.description)
    t.title = plain.slice(0, 200) || ''
  }
  if (['Open', 'Closed', 'Cancelled'].includes(t.status)) {
    t.status = mapTodoStatusToUi(t.status)
  }

  return {
    ...base,
    ...t,
    reference_doctype: t.reference_doctype || props.doctype,
  }
}

const validateTask = () => {
  if (!_task.value.title?.trim()) {
    toast.error(__('Title is required'))
    return false
  }
  return true
}

const createTaskResource = createResource({
  url: 'frappe.client.insert',
  makeParams() {
    const description = buildTodoDescription(
      _task.value.title,
      _task.value.description,
    )
    const dateStr = todoDueDateOnly(_task.value.due_date)
    const doc = {
      doctype: 'ToDo',
      description,
      status: mapUiStatusToTodo(_task.value.status),
      priority: _task.value.priority || 'Medium',
      allocated_to: _task.value.assigned_to,
      reference_type: props.doctype || _task.value.reference_doctype || undefined,
      reference_name: props.doc || _task.value.reference_docname || undefined,
    }
    if (dateStr) doc.date = dateStr
    return { doc }
  },
  validate: validateTask,
  onSuccess(d) {
    if (d.name) {
      updateOnboardingStep('create_first_task')
      capture('task_created')
      tasks.value?.reload?.()
      emit('after', d, true)
      show.value = false
      toast.success(__('Task created'))
    }
  },
})

const updateTaskResource = createResource({
  url: 'frappe.client.set_value',
  makeParams() {
    const description = buildTodoDescription(
      _task.value.title,
      _task.value.description,
    )
    const dateStr = todoDueDateOnly(_task.value.due_date)
    const fieldname = {
      description,
      status: mapUiStatusToTodo(_task.value.status),
      priority: _task.value.priority || 'Medium',
      allocated_to: _task.value.assigned_to,
    }
    if (dateStr) fieldname.date = dateStr
    const rtype = props.doctype || _task.value.reference_doctype
    const rname = props.doc || _task.value.reference_docname
    if (rtype) fieldname.reference_type = rtype
    if (rname) fieldname.reference_name = rname
    return {
      doctype: 'ToDo',
      name: _task.value.name,
      fieldname,
    }
  },
  validate: validateTask,
  onSuccess(d) {
    if (d.name) {
      tasks.value?.reload?.()
      emit('after', d)
      show.value = false
    }
  },
})

function updateTaskStatus(status) {
  _task.value.status = status
}

function updateTaskPriority(priority) {
  _task.value.priority = priority
}

function redirect() {
  if (!props.task?.reference_docname) return
  let name = props.task.reference_doctype == 'Opportunity' ? 'Deal' : 'Lead'
  let params = { leadId: props.task.reference_docname }
  if (name == 'Deal') {
    params = { dealId: props.task.reference_docname }
  }
  router.push({ name: name, params: params })
}

async function updateTask() {
  if (!_task.value.assigned_to) {
    _task.value.assigned_to = getUser().name
  }
  if (_task.value.name) {
    updateTaskResource.submit()
  } else {
    createTaskResource.submit()
  }
}

function render() {
  editMode.value = false
  setTimeout(() => title.value?.el?.focus?.(), 100)
  nextTick(() => {
    _task.value = normalizeTaskFromProps(props.task)
    editMode.value = !!_task.value.name
  })
}

onMounted(() => show.value && render())

watch(show, (value) => {
  if (!value) return
  render()
})
</script>

<style scoped>
:deep(.datepicker svg) {
  width: 0.875rem;
  height: 0.875rem;
}
</style>
