import env from 'app-env'
import { isAxiosError } from 'axios'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { toast } from 'react-toastify'

import httpClient from '@/lib/httpClient'

import BooleanField from '@/components/Fields/BooleanField'
import NumberField from '@/components/Fields/NumberField'
import SubmitField from '@/components/Fields/SubmitField'
import TagsField from '@/components/Fields/TagsField'
import TextAreaField from '@/components/Fields/TextAreaField'
import TextField from '@/components/Fields/TextField'
import Heading from '@/components/Heading'

const QueueAddPage = () => {
  const navigate = useNavigate()

  const [name, setName] = useState<string>('')
  const [config, setConfig] = useState<string>('')
  const [groupSize, setGroupSize] = useState<number>(1)
  const [priority, setPriority] = useState<number>(0)
  const [active, setActive] = useState<boolean>(false)
  const [requirements, setRequirements] = useState<string[]>([])

  const [nameErrors, setNameErrors] = useState<string[]>([])
  const [configErrors, setConfigErrors] = useState<string[]>([])
  const [groupSizeErrors, setGroupSizeErrors] = useState<string[]>([])
  const [priorityErrors, setPriorityErrors] = useState<string[]>([])

  const addQueueHandler = async () => {
    setNameErrors([])
    setConfigErrors([])
    setGroupSizeErrors([])
    setPriorityErrors([])

    const formData = new FormData()
    formData.append('name', name)
    formData.append('config', config)
    formData.append('group_size', groupSize.toString())
    formData.append('priority', priority.toString())
    formData.append('active', active ? 'true' : 'false')
    formData.append('reqs', requirements.join('\n'))

    try {
      const resp = await httpClient.post<{ message: string }>(env.VITE_SERVER_URL + '/scheduler/queue/add', formData)

      toast.success(resp.data.message)
      navigate('/scheduler/queue/list')
    } catch (err) {
      if (
        isAxiosError<{
          error: {
            code: number
            errors?: { name?: string[]; config?: string[]; group_size?: string[]; priority?: string[] }
          }
        }>(err)
      ) {
        const errors = err.response?.data.error.errors

        setNameErrors(errors?.name ?? [])
        setConfigErrors(errors?.config ?? [])
        setGroupSizeErrors(errors?.group_size ?? [])
        setPriorityErrors(errors?.priority ?? [])
      }
    }
  }

  return (
    <div>
      <Heading headings={['Queues', 'Add']} />
      <form id="queue_form" method="post">
        {/* {{ form.csrf_token }}*/}
        {/* <input id="csrf_token" name="csrf_token" type="hidden" value="random-csrf-value-4654654" /> */}
        <TextField
          name="name"
          label="Name"
          placeholder="Name"
          required={true}
          _state={name}
          _setState={setName}
          errors={nameErrors}
        />
        <TextAreaField
          name="config"
          label="Config"
          placeholder="Config"
          rows={10}
          _state={config}
          _setState={setConfig}
          errors={configErrors}
        />
        <NumberField
          name="group_size"
          label="Group size"
          placeholder="Group size"
          minValue={1}
          required={true}
          _state={groupSize}
          _setState={setGroupSize}
          errors={groupSizeErrors}
        />
        <NumberField
          name="priority"
          label="Priority"
          placeholder="Priority"
          minValue={1}
          required={true}
          _state={priority}
          _setState={setPriority}
          errors={priorityErrors}
        />
        <BooleanField name="active" label="Active" _state={active} _setState={setActive} />
        <TagsField
          name="requirements"
          label="Requirements"
          placeholder="Requirements"
          _state={requirements}
          _setState={setRequirements}
        />
        <SubmitField name="Add" handler={addQueueHandler} />
      </form>
    </div>
  )
}
export default QueueAddPage
