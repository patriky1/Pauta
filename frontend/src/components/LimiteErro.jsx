import { Component } from 'react'

/** Impede que um erro de renderização derrube a aplicação inteira (tela branca). */
export default class LimiteErro extends Component {
  constructor(props) {
    super(props)
    this.state = { erro: null }
  }

  static getDerivedStateFromError(erro) {
    return { erro }
  }

  componentDidCatch(erro, info) {
    // eslint-disable-next-line no-console
    console.error('Erro de interface capturado:', erro, info?.componentStack)
  }

  componentDidUpdate(anterior) {
    if (this.state.erro && anterior.chave !== this.props.chave) {
      this.setState({ erro: null })
    }
  }

  render() {
    if (!this.state.erro) return this.props.children
    return (
      <div className="container">
        <div className="estado" role="alert" style={{ padding: '72px 16px' }}>
          <h3>Esta página não carregou direito</h3>
          <p>Tente recarregar. Se continuar, volte para a página inicial.</p>
          <div className="grupo-botoes" style={{ justifyContent: 'center' }}>
            <button type="button" className="botao botao--primario" onClick={() => window.location.reload()}>
              Recarregar
            </button>
            <a className="botao" href="/">Página inicial</a>
          </div>
        </div>
      </div>
    )
  }
}
