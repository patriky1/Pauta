import { useTema } from '../contexts/TemaContext'
import Icone from './Icone'

export default function BotaoTema() {
  const { tema, alternar } = useTema()
  const escuro = tema === 'escuro'
  return (
    <button
      type="button"
      className="icone-botao"
      onClick={alternar}
      aria-label={escuro ? 'Usar tema claro' : 'Usar tema escuro'}
      title={escuro ? 'Tema claro' : 'Tema escuro'}
    >
      <Icone nome={escuro ? 'sol' : 'lua'} tamanho={18} />
    </button>
  )
}
