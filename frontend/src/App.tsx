import { routes } from './routes'
import jQuery from 'jquery'
import { useEffect, useState } from 'react'
import { RouterProvider, createBrowserRouter } from 'react-router-dom'
import { useRecoilState } from 'recoil'

import { userState } from '@/atoms/userAtom'

import httpClient from '@/lib/httpClient'

export default function App() {
  const [, setUser] = useRecoilState(userState)
  const [isChecking, setIsChecking] = useState<boolean>(true)

  const authHandler = () => {
    httpClient
      .get<User>(import.meta.env.VITE_SERVER_URL + '/auth/user/@me')
      .then((resp) => {
        setUser({ ...resp.data, isAuthenticated: true })
        setIsChecking(false)
      })
      .catch(() => {
        setIsChecking(false)
      })
  }

  useEffect(() => {
    // eslint-disable-next-line @typescript-eslint/ban-ts-comment
    // @ts-ignore
    window.jQuery = jQuery // helper for selenium tests
    authHandler()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (isChecking) return <></>

  const router = createBrowserRouter(routes)

  return <RouterProvider router={router} />
}
