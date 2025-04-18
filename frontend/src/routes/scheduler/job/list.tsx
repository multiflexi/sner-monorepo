import { Helmet } from 'react-helmet-async'
import { Link, useSearchParams } from 'react-router-dom'

import { Column, ColumnButtons, renderElements } from '@/lib/DataTables'
import { toQueryString, urlFor } from '@/lib/urlHelper'

import DataTable from '@/components/DataTable'
import FilterForm from '@/components/FilterForm'
import Heading from '@/components/Heading'
import ButtonGroup from '@/components/buttons/ButtonGroup'
import DeleteButton from '@/components/buttons/DeleteButton'
import ReconcileButton from '@/components/buttons/ReconcileButton'
import RepeatButton from '@/components/buttons/RepeatButton'


const renderAssignmentCell = (cell: Node, data: string) => {
  const maxLength = 100
  renderElements(
    cell,
    <div title={data}>{data.length >= maxLength ? `${data.substring(0, maxLength - 1)}...` : data}</div>
  )
}

const JobListPage = () => {
  const [searchParams] = useSearchParams()

  const columns = [
    Column('id'),
    Column('queue_name'),
    Column('assignment', { createdCell: renderAssignmentCell }),
    Column('retval'),
    Column('time_start'),
    Column('time_end'),
    Column('time_taken'),
    ColumnButtons({
      createdCell: (cell, _data: string, row: JobRow) =>
        renderElements(
          cell,
          <ButtonGroup>
            <a
              className="btn btn-outline-secondary"
              title="Download job output"
              data-testid="view-btn"
              href={urlFor(`/backend/scheduler/job/download/${row['id']}`)}
            >
              <i className="fas fa-download"></i>
            </a>
            <RepeatButton url={urlFor(`/backend/scheduler/job/repeat/${row['id']}`)} tableId="job_list_table" />
            <ReconcileButton url={urlFor(`/backend/scheduler/job/reconcile/${row['id']}`)} tableId="job_list_table" />
            <DeleteButton url={urlFor(`/backend/scheduler/job/delete/${row['id']}`)} tableId="job_list_table" />
          </ButtonGroup>,
        ),
    }),
  ]

  return (
    <div>
      <Helmet>
        <title>Jobs / List - SNER</title>
      </Helmet>

      <Heading headings={['Jobs']} />
      <div id="job_list_table_toolbar" className="dt_toolbar">
        <div id="job_list_table_toolbox" className="dt_toolbar_toolbox_alwaysvisible">
          <div className="btn-group">
            <a className="btn btn-outline-secondary disabled">
              <i className="fas fa-filter"></i>
            </a>
            <Link className="btn btn-outline-secondary" to='/scheduler/job/list?filter=Job.retval+is_null+""'>
              Running
            </Link>
          </div>
        </div>
        <FilterForm url="/scheduler/job/list" />
      </div>
      <DataTable
        id="job_list_table"
        columns={columns}
        ajax_url={urlFor(`/backend/scheduler/job/list.json${toQueryString(searchParams)}`)}
      />
    </div>
  )
}
export default JobListPage
