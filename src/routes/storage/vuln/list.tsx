import { escapeHtml } from '@/utils'
import env from 'app-env'
import clsx from 'clsx'
import { Fragment, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useSessionStorage } from 'react-use'

import { Column, ColumnButtons, ColumnSelect, renderElements } from '@/lib/DataTables'
import {
  deleteRow,
  getColorForSeverity,
  getColorForTag,
  getLinksForService,
  getTextForRef,
  getUrlForRef,
} from '@/lib/sner/storage'

import ButtonGroup from '@/components/Buttons/ButtonGroup'
import DeleteButton from '@/components/Buttons/DeleteButton'
import DropdownButton from '@/components/Buttons/DropdownButton'
import EditButton from '@/components/Buttons/EditButton'
import MultiCopyButton from '@/components/Buttons/MultiCopyButton'
import TagButton from '@/components/Buttons/TagButton'
import TagsDropdownButton from '@/components/Buttons/TagsDropdownButton'
import DataTable from '@/components/DataTable'
import FilterForm from '@/components/FilterForm'
import Heading from '@/components/Heading'
import AnnotateModal from '@/components/Modals/AnnotateModal'
import MultipleTagModal from '@/components/Modals/MultipleTagModal'

const VulnListPage = () => {
  const [searchParams] = useSearchParams()
  const [toolboxesVisible] = useSessionStorage('dt_toolboxes_visible')
  const [viaTargetVisible] = useSessionStorage('dt_viatarget_column_visible')
  const navigate = useNavigate()
  const [annotate, setAnnotate] = useState<Annotate>({
    show: false,
    tags: [],
    comment: '',
    tableId: '',
    url: '',
  })
  const [multipleTag, setMultipleTag] = useState<MultipleTag>({
    show: false,
    action: 'set',
    tableId: '',
    url: '',
  })

  const columns = [
    ColumnSelect({ visible: true }),
    Column('id', { visible: false }),
    Column('host_id', { visible: false }),
    Column('host_address', {
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <a
            href={`/storage/host/view/${row['host_id']}`}
            onClick={(e) => {
              e.preventDefault()
              navigate(`/storage/host/view/${row['host_id']}`)
            }}
          >
            {row['host_address']}
          </a>,
        ),
    }),
    Column('host_hostname'),
    Column('service_proto', { visible: false }),
    Column('service_port', { visible: false }),
    Column('service', {
      className: 'service_endpoint_dropdown',
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <div className="dropdown d-flex">
            <a className="flex-fill" data-toggle="dropdown">
              {row['service']}
            </a>
            <div className="dropdown-menu">
              <h6 className="dropdown-header">Service endpoint URIs</h6>
              {getLinksForService(
                row['host_address'],
                row['host_hostname'],
                row['service_proto'],
                row['service_port'],
              ).map((link) => (
                <span className="dropdown-item" key={link}>
                  <i className="far fa-clipboard" title="Copy to clipboard"></i>{' '}
                  <a rel="noreferrer" href={escapeHtml(link)}>
                    {escapeHtml(link)}
                  </a>
                </span>
              ))}
            </div>
          </div>,
        ),
    }),
    Column('via_target', {
      visible: viaTargetVisible,
    }),
    Column('name', {
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <a
            href={`/storage/vuln/view/${row['id']}`}
            onClick={(e) => {
              e.preventDefault()
              navigate(`/storage/vuln/view/${row['id']}`)
            }}
          >
            {row['name']}
          </a>,
        ),
    }),
    Column('xtype', { visible: false }),
    Column('severity', {
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <span className={clsx('badge', getColorForSeverity(row['severity']))}>{row['severity']}</span>,
        ),
    }),
    Column('refs', {
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <>
            {row['refs'].map((ref) => (
              <Fragment key={ref}>
                <a rel="noreferrer" href={getUrlForRef(ref)}>
                  {getTextForRef(ref)}
                </a>{' '}
              </Fragment>
            ))}
          </>,
        ),
    }),
    Column('tags', {
      className: 'abutton_annotate_dt',
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <div
            onDoubleClick={() =>
              setAnnotate({
                show: true,
                tags: data,
                comment: row['comment'],
                tableId: 'vuln_list_table',
                url: `/storage/vuln/annotate/${row['id']}`,
              })
            }
          >
            {row['tags'].map((tag: string) => (
              <Fragment key={tag}>
                <span className={clsx('badge tag-badge', getColorForTag(tag))}>{tag}</span>{' '}
              </Fragment>
            ))}
          </div>,
        ),
    }),
    Column('comment', {
      className: 'abutton_annotate_dt forcewrap',
      title: 'cmnt',
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <div
            onDoubleClick={() =>
              setAnnotate({
                show: true,
                tags: row['tags'],
                comment: row['comment'],
                tableId: 'vuln_list_table',
                url: `/storage/vuln/annotate/${row['id']}`,
              })
            }
          >
            {row['comment']}
          </div>,
        ),
    }),
    ColumnButtons({
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <ButtonGroup>
            <DropdownButton
              title="More data"
              options={[
                {
                  name: 'created',
                  data: row['created'],
                },
                {
                  name: 'modified',
                  data: row['modified'],
                },
                {
                  name: 'rescan_time',
                  data: row['rescan_time'],
                },
                {
                  name: 'import_time',
                  data: row['import_time'],
                },
              ]}
            />
            <EditButton url={`/storage/vuln/edit/${row['id']}`} navigate={navigate} />
            <MultiCopyButton url={`/storage/vuln/multicopy/${row['id']}`} navigate={navigate} />
            <DeleteButton url={`/storage/vuln/delete/${row['id']}`} />
          </ButtonGroup>,
        ),
    }),
  ]
  return (
    <div>
      <Heading headings={['Vulns']}>
        <div className="breadcrumb-buttons pl-2">
          <a className="btn btn-outline-primary" href="/storage/vuln/report">
            Report
          </a>{' '}
          <a className="btn btn-outline-primary" href="/storage/vuln/report?group_by_host=True">
            Report by host
          </a>{' '}
          <a className="btn btn-outline-primary" href="/storage/vuln/export">
            Export
          </a>{' '}
          <a className="btn btn-outline-secondary" data-toggle="collapse" href="#filter_form">
            <i className="fas fa-filter"></i>
          </a>
        </div>
      </Heading>

      <div id="vuln_list_table_toolbar" className="dt_toolbar">
        <div id="vuln_list_table_toolbox" className="dt_toolbar_toolbox_alwaysvisible">
          <div className="btn-group">
            <a className="btn btn-outline-secondary disabled">
              <i className="fas fa-check-square"></i>
            </a>
            <a className="btn btn-outline-secondary abutton_selectall" href="#" title="select all">
              All
            </a>
            <a className="btn btn-outline-secondary abutton_selectnone" href="#" title="unselect all">
              None
            </a>
          </div>{' '}
          <div className="btn-group">
            <a
              className="btn btn-outline-secondary"
              href="#"
              onClick={() =>
                setMultipleTag({
                  show: true,
                  action: 'set',
                  tableId: 'vuln_list_table',
                  url: '/storage/vuln/tag_multiid',
                })
              }
            >
              <i className="fas fa-tag"></i>
            </a>
            {env.VITE_VULN_TAGS.map((tag) => (
              <TagButton tag={tag} key={tag} url="/storage/vuln/tag_multiid" tableId="vuln_list_table" />
            ))}
          </div>{' '}
          <div className="btn-group">
            <a
              className="btn btn-outline-secondary abutton_freetag_unset_multiid"
              href="#"
              onClick={() =>
                setMultipleTag({
                  show: true,
                  action: 'unset',
                  tableId: 'vuln_list_table',
                  url: '/storage/vuln/tag_multiid',
                })
              }
            >
              <i className="fas fa-eraser"></i>
            </a>
            <div className="btn-group">
              <a
                className="btn btn-outline-secondary dropdown-toggle"
                data-toggle="dropdown"
                href="#"
                title="remove tag dropdown"
              >
                <i className="fas fa-remove-format"></i>
              </a>
              <TagsDropdownButton tags={env.VITE_VULN_TAGS} url="/storage/vuln/tag_multiid" tableId="vuln_list_table" />
            </div>
            <a
              className="btn btn-outline-secondary"
              href="#"
              onClick={() => deleteRow('vuln_list_table', '/storage/vuln/delete_multiid')}
            >
              <i className="fas fa-trash text-danger"></i>
            </a>
          </div>{' '}
          <div className="btn-group">
            <a className="btn btn-outline-secondary disabled">
              <i className="fas fa-filter"></i>
            </a>
            <Link className="btn btn-outline-secondary" to='/storage/vuln/list?filter=Vuln.tags=="{}"'>
              Not tagged
            </Link>
            <Link className="btn btn-outline-secondary" to='/storage/vuln/list?filter=Vuln.tags!="{}"'>
              Tagged
            </Link>
            <Link
              className="btn btn-outline-secondary"
              to='/storage/vuln/list?filter=Vuln.tags not_any "report" AND Vuln.tags not_any "report:data" AND Vuln.tags not_any "info"'
            >
              Exclude reviewed
            </Link>
            <Link
              className="btn btn-outline-secondary"
              to='/storage/vuln/list?filter=Vuln.tags any "report" OR Vuln.tags any "report:data"'
            >
              Only Report
            </Link>
          </div>
        </div>
        <FilterForm url="/storage/vuln/list" />
      </div>
      <DataTable
        id="vuln_list_table"
        columns={columns}
        ajax={{
          url:
            env.VITE_SERVER_URL +
            '/storage/vuln/list.json' +
            (searchParams.has('filter') ? `?filter=${searchParams.get('filter')}` : ''),
          type: 'POST',
          xhrFields: { withCredentials: true },
        }}
        order={[1, 'asc']}
        select={toolboxesVisible ? { style: 'multi', selector: 'td:first-child' } : false}
      />

      <AnnotateModal annotate={annotate} setAnnotate={setAnnotate} />
      <MultipleTagModal multipleTag={multipleTag} setMultipleTag={setMultipleTag} />
    </div>
  )
}
export default VulnListPage
