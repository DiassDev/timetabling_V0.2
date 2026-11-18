import { Plus, RotateCcw, Trash2 } from 'lucide-react'
import { labels } from '../shared/constants'
import type { Account, Role } from '../shared/types'

type UsersManagementProps = {
  accounts: Account[]
  onResetAll: () => void
  onCreateRole: (role: Role) => void
  onDeleteAccount: (accountId: string) => void
}

export function UsersManagement({
  accounts,
  onResetAll,
  onCreateRole,
  onDeleteAccount,
}: UsersManagementProps) {
  return (
    <section className="table-panel">
      <div className="table-title">
        <div>
          <h2>Acessos da escola</h2>
          <p>Crie ou remova acessos de coordenadores e professores.</p>
        </div>
        <div className="account-actions">
          <button className="btn secondary" onClick={onResetAll}>
            <RotateCcw size={14} />
            Recomeçar do zero
          </button>
          <button
            className="btn secondary"
            onClick={() => onCreateRole('PROFESSOR')}
          >
            <Plus size={15} />
            Cadastrar professor
          </button>
          <button
            className="btn primary"
            onClick={() => onCreateRole('COORDENADOR')}
          >
            <Plus size={15} />
            Cadastrar coordenador
          </button>
        </div>
      </div>

      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Nome</th>
              <th>E-mail</th>
              <th>Perfil</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {accounts
              .filter(a => a.role !== 'ADMIN')
              .map(a => (
                <tr key={a.id}>
                  <td>{a.name}</td>
                  <td>{a.email}</td>
                  <td>{labels[a.role]}</td>
                  <td>
                    <button
                      className="icon danger"
                      onClick={() => onDeleteAccount(a.id)}
                      title="Remover acesso"
                    >
                      <Trash2 size={15} />
                    </button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {accounts.length === 1 && (
        <p className="empty">Ainda não há outros acessos cadastrados.</p>
      )}
    </section>
  )
}
