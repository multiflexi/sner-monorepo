import env from 'app-env'
import clsx from 'clsx'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { Column, renderElements } from '@/lib/DataTables'
import { getServiceFilterInfo } from '@/lib/sner/storage'

import DataTable from '@/components/DataTable'
import FilterForm from '@/components/FilterForm'
import Heading from '@/components/Heading'

const ServiceGroupedPage = () => {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const columns = [
    Column('info', {
      createdCell: (cell, data, row) =>
        renderElements(
          cell,
          <a
            href={`/storage/service/list?filter=${getServiceFilterInfo(row['info'])}`}
            onClick={(e) => {
              e.preventDefault()
              navigate(`/storage/service/list?filter=${getServiceFilterInfo(row['info'])}`)
            }}
          >
            {row['info'] ? (
              row['info']
            ) : (
              <>
                <em>null</em>
                <i className="fas fa-exclamation-circle text-warning"></i>
              </>
            )}
          </a>,
        ),
    }),
    Column('cnt_services'),
  ]

  return (
    <div>
      <Heading headings={['Services', 'Grouped']}>
        <div className="breadcrumb-buttons pl-2">
          <a className="btn btn-outline-secondary" data-toggle="collapse" href="#filter_form">
            <i className="fas fa-filter"></i>
          </a>
        </div>
      </Heading>

      <div id="service_grouped_table_toolbar" className="dt_toolbar">
        <div id="service_grouped_table_toolbox" className="dt_toolbar_toolbox_alwaysvisible">
          <div className="btn-group">
            <a className="btn btn-outline-secondary disabled">crop at:</a>
            {['1', '2', '3', '4', '5'].map((crop) => (
              <Link
                className={clsx('btn btn-outline-secondary', searchParams.get('crop') === crop && 'active')}
                to={`/storage/service/grouped?crop=${crop}`}
                key={crop}
              >
                {crop}
              </Link>
            ))}
            <Link
              className={clsx('btn btn-outline-secondary', !searchParams.get('crop') && 'active')}
              to="/storage/service/grouped"
            >
              no crop
            </Link>
          </div>
        </div>
        <FilterForm url="/storage/service/grouped" />
      </div>

      <DataTable
        columns={columns}
        ajax={{
          url:
            env.VITE_SERVER_URL +
            '/storage/service/grouped.json' +
            (searchParams.has('filter') ? `?filter=${searchParams.get('filter')}` : ''),
          type: 'POST',
          xhrFields: { withCredentials: true },
        }}
        order={[1, 'desc']}
      />
    </div>
  )
}
export default ServiceGroupedPage
