import { NavigateFunction, useNavigate } from 'react-router-dom'

const MultiCopyButton = ({
  url,
  // eslint-disable-next-line react-hooks/rules-of-hooks
  navigate = useNavigate(),
}: {
  url: string
  navigate?: NavigateFunction
}) => {
  return (
    <a
      className="btn btn-outline-secondary"
      href={url}
      onClick={(e) => {
        e.preventDefault()
        navigate(url)
      }}
      title="Multicopy"
    >
      <i className="far fa-copy"></i>
    </a>
  )
}
export default MultiCopyButton
