import HostViewPage from '@/routes/storage/host/view'
import NoteListPage from '@/routes/storage/note/list'
import NoteViewPage from '@/routes/storage/note/view'
import { fireEvent, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import httpClient from '@/lib/httpClient'

import { renderWithProviders } from '@/tests/utils/renderWithProviders'

describe('Note list page', () => {
  it('shows table of notes', async () => {
    sessionStorage.setItem('dt_toolboxes_visible', 'false')
    sessionStorage.setItem('dt_viatarget_column_visible', 'false')

    renderWithProviders({ element: <NoteListPage />, path: '/storage/note/list' })
    expect(screen.getByRole('list')).toHaveTextContent('Notes')

    await waitFor(() => {
      expect(screen.getByText('127.4.4.4')).toBeInTheDocument()
      expect(screen.getByText('testhost.testdomain.test<script>alert(1);</script>')).toBeInTheDocument()
      expect(screen.getByText('12345/tcp')).toBeInTheDocument()
      expect(screen.getByText('deb')).toBeInTheDocument()
      expect(screen.getByText('["cpe:/o:microsoft:windows_nt:3.5.1"]')).toBeInTheDocument()

      expect(screen.getByText('127.3.3.3')).toBeInTheDocument()
      expect(screen.getByText('testhost1.testdomain.test')).toBeInTheDocument()
      expect(screen.getByText('sner.testnote')).toBeInTheDocument()
      expect(screen.getByText('testnote data')).toBeInTheDocument()

      expect(screen.getByText('127.0.0.1')).toBeInTheDocument()
      expect(screen.getByText('46865/tcp')).toBeInTheDocument()
      expect(screen.getByText('testssl')).toBeInTheDocument()
    })

    sessionStorage.setItem('dt_toolboxes_visible', 'true')
    sessionStorage.setItem('dt_viatarget_column_visible', 'true')
  })

  it('views host', async () => {
    renderWithProviders({
      element: <NoteListPage />,
      path: '/storage/note/list',
      routes: [
        {
          element: <HostViewPage />,
          path: '/storage/host/view/1',
          loader: () =>
            Promise.resolve({
              address: '127.4.4.4',
              comment: '',
              created: 'Mon, 17 Jul 2023 20:01:09 GMT',
              hostname: 'testhost.testdomain.test<script>alert(1);</script>',
              id: 1,
              modified: 'Fri, 01 Sep 2023 12:01:37 GMT',
              notesCount: 3,
              os: 'Test Linux 1',
              rescan_time: 'Mon, 17 Jul 2023 20:01:09 GMT',
              servicesCount: 1,
              tags: ['reviewed'],
              vulnsCount: 12,
            }),
        },
      ],
    })

    await waitFor(() => {
      const addressLink = screen.getByRole('link', { name: '127.4.4.4' })

      fireEvent.click(addressLink)
    })

    await waitFor(() => {
      const listItems = screen.getAllByRole('listitem').map((item) => item.textContent)
      expect(listItems.includes('Host')).toBeTruthy()
      expect(listItems.includes('127.4.4.4 testhost.testdomain.test<script>alert(1);</script>')).toBeTruthy()
    })
  })

  it('filters results', async () => {
    renderWithProviders({
      element: <NoteListPage />,
      path: '/storage/note/list',
    })

    const filterForm = screen.getByTestId('filter-form')
    const filterInput = filterForm.querySelector('input')!
    const filterButton = screen.getByTestId('filter-btn')

    fireEvent.change(filterInput, { target: { value: 'Host.address=="127.4.4.4"' } })
    fireEvent.click(filterButton)

    await waitFor(() => {
      expect(screen.getByText('127.4.4.4')).toBeInTheDocument()
      expect(screen.queryByText('127.3.3.3')).toBeNull()
      expect(screen.queryByText('127.128.129.130')).toBeNull()
    })
  })

  it('deletes host', async () => {
    renderWithProviders({
      element: <NoteListPage />,
      path: '/storage/note/list',
    })

    vi.spyOn(httpClient, 'post').mockResolvedValue('')

    await waitFor(() => {
      // selects first row
      const cells = screen.getAllByRole('cell')
      fireEvent.click(cells[0])

      window.confirm = vi.fn(() => true)

      const deleteRowButton = screen.getByTestId('delete-row-btn')

      fireEvent.click(deleteRowButton)
    })
  })

  it('redirects to view page', async () => {
    renderWithProviders({
      element: <NoteListPage />,
      path: '/storage/note/list',
      routes: [
        {
          element: <NoteViewPage />,
          path: '/storage/note/view/1',
          loader: () =>
            Promise.resolve({
              address: '127.4.4.4',
              comment: null,
              created: 'Mon, 17 Jul 2023 20:01:09 GMT',
              data: '["cpe:/o:microsoft:windows_nt:3.5.1"]',
              host_id: 1,
              hostname: 'testhost.testdomain.test<script>alert(1);</script>',
              id: 1,
              import_time: null,
              modified: 'Thu, 31 Aug 2023 17:50:08 GMT',
              service_id: 1,
              service_port: 12345,
              service_proto: 'tcp',
              tags: ['report', 'falsepositive', 'info'],
              via_target: null,
              xtype: 'deb',
            }),
        },
      ],
    })

    await waitFor(() => {
      const viewButton = screen.getAllByTestId('view-btn')[0]

      fireEvent.click(viewButton)
    })
  })

  it('annotates note', async () => {
    renderWithProviders({
      element: <NoteListPage />,
      path: '/storage/note/list',
    })

    await waitFor(() => {
      const tagsCell = screen.getAllByTestId('note_tags_annotate')[0]
      const tagsCellEmptyComment = screen.getAllByTestId('note_tags_annotate')[1]
      const commentCell = screen.getAllByTestId('note_comment_annotate')[0]
      const commentCellEmptyComment = screen.getAllByTestId('note_comment_annotate')[1]

      fireEvent.doubleClick(tagsCell)
      expect(screen.getByText('Annotate')).toBeInTheDocument()

      fireEvent.doubleClick(tagsCellEmptyComment)
      expect(screen.getByText('Annotate')).toBeInTheDocument()

      fireEvent.doubleClick(commentCell)
      expect(screen.getByText('Annotate')).toBeInTheDocument()

      fireEvent.doubleClick(commentCellEmptyComment)
      expect(screen.getByText('Annotate')).toBeInTheDocument()
    })
  })

  it('sets multiple tags', async () => {
    renderWithProviders({
      element: <NoteListPage />,
      path: '/storage/note/list',
    })

    const tagMultipleButton = screen.getByTestId('note_set_multiple_tag')

    fireEvent.click(tagMultipleButton)

    await waitFor(() => {
      expect(screen.getByText('Tag multiple items')).toBeInTheDocument()
    })
  })

  it('unsets multiple tags', async () => {
    renderWithProviders({
      element: <NoteListPage />,
      path: '/storage/note/list',
    })

    const tagMultipleButton = screen.getByTestId('note_unset_multiple_tag')

    fireEvent.click(tagMultipleButton)

    await waitFor(() => {
      expect(screen.getByText('Untag multiple items')).toBeInTheDocument()
    })
  })
})
