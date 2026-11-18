import { FormEvent, useState } from 'react'
import { CalendarDays, ChevronRight } from 'lucide-react'
import { labels } from '../shared/constants'
import type { Account, Role } from '../shared/types'
import { id } from '../shared/utils'

type LoginProps = {
  first: boolean
  accounts: Account[]
  onCreate: (account: Account) => void
  onLogin: (email: string, password: string, role: Role) => void
  error: string
  role: Role
  setRole: (role: Role) => void
}

export function Login({
  first,
  accounts,
  onCreate,
  onLogin,
  error,
  role,
  setRole,
}: LoginProps) {
  const [setup, setSetup] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [localError, setLocalError] = useState('')

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!email.trim() || !password || (setup && !name.trim())) {
      setLocalError('Preencha todos os campos.')
      return
    }
    if (setup) {
      if (
        accounts.some(
          a => a.email.toLowerCase() === email.trim().toLowerCase()
        )
      ) {
        setLocalError('Já existe um acesso com esse e-mail.')
        return
      }
      if (password.length < 6) {
        setLocalError('Use uma senha com pelo menos 6 caracteres.')
        return
      }
      if (password !== confirm) {
        setLocalError('As senhas não são iguais.')
        return
      }
      onCreate({
        id: id(),
        name: name.trim(),
        email: email.trim(),
        password,
        role: 'ADMIN',
      })
    } else {
      onLogin(email, password, role)
    }
  }

  const clearForm = () => {
    setName('')
    setEmail('')
    setPassword('')
    setConfirm('')
    setLocalError('')
  }

  const title = setup
    ? 'Vamos preparar seu acesso'
    : first
      ? 'Acesse sua escola'
      : 'Que bom ter você de volta'

  const subtitle = setup
    ? 'Cadastre o administrador para começar a organizar os horários.'
    : 'Entre para consultar as grades e os horários da escola.'

  return (
    <div className="login-page">
      <div className="login-brand">
        <i>
          <CalendarDays size={20} />
        </i>
        grade<span>.</span>
      </div>

      <section className="login-card">
        <div className="login-icon">
          <CalendarDays size={22} />
        </div>
        <p className="login-overline">INSTITUTO FAROL</p>
        <h1>{title}</h1>
        <p className="login-sub">{subtitle}</p>

        <form onSubmit={submit}>
          {!setup && (
            <div className="login-role-picker">
              <span>Escolha seu perfil</span>
              <div>
                {(['COORDENADOR', 'ADMIN', 'PROFESSOR'] as Role[]).map(
                  option => (
                    <button
                      type="button"
                      key={option}
                      className={role === option ? 'selected' : ''}
                      onClick={() => setRole(option)}
                    >
                      {labels[option]}
                    </button>
                  )
                )}
              </div>
            </div>
          )}

          {setup && (
            <label>
              Seu nome
              <input
                autoComplete="name"
                value={name}
                onChange={e => setName(e.target.value)}
                required
                placeholder="Seu nome"
              />
            </label>
          )}

          <label>
            E-mail
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              placeholder="voce@escola.com"
            />
          </label>

          <label>
            Senha
            <input
              type="password"
              autoComplete={setup ? 'new-password' : 'current-password'}
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder={setup ? 'Crie uma senha' : 'Digite sua senha'}
            />
          </label>

          {setup && (
            <label>
              Repita a senha
              <input
                type="password"
                autoComplete="new-password"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                required
                placeholder="Digite a senha novamente"
              />
            </label>
          )}

          {(localError || (!setup && error)) && (
            <p className="form-error">{localError || error}</p>
          )}

          <button className="btn primary login-submit">
            {setup ? 'Criar acesso de administrador' : 'Entrar'}{' '}
            <ChevronRight size={16} />
          </button>
        </form>

        {!setup && (
          <button
            className="forgot"
            onClick={() =>
              setLocalError(
                'Peça ao administrador da escola para redefinir seu acesso.'
              )
            }
          >
            Esqueci minha senha
          </button>
        )}

        {!setup && first && (
          <button
            className="first-access"
            onClick={() => {
              clearForm()
              setSetup(true)
            }}
          >
            Primeiro acesso? Cadastre o administrador da escola
          </button>
        )}

        {!setup && !first && accounts.length > 0 && (
          <p className="login-foot">
            Os acessos de professores e coordenadores são criados pelo
            administrador.
          </p>
        )}

        {setup && !first && (
          <button
            className="forgot"
            onClick={() => {
              clearForm()
              setSetup(false)
            }}
          >
            Voltar para entrar
          </button>
        )}
      </section>

      <div className="login-bottom">
        Se precisar de ajuda, fale com a equipe da escola.
      </div>
    </div>
  )
}
