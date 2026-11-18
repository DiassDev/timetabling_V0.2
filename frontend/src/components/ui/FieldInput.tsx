import type { Field } from '../shared/types'

type FieldInputProps = {
  field: Field
  value: string
  onChange: (value: string) => void
}

export function FieldInput({ field, value, onChange }: FieldInputProps) {
  return (
    <label>
      {field.label}
      {field.type === 'select' ? (
        <select
          required={field.required !== false}
          value={value}
          onChange={e => onChange(e.target.value)}
        >
          <option value="">Selecione</option>
          {field.options?.map(([v, l]) => (
            <option key={v} value={v}>
              {l}
            </option>
          ))}
        </select>
      ) : (
        <input
          type={field.type}
          min={field.type === 'number' ? 1 : undefined}
          required={field.required !== false}
          value={value}
          onChange={e => onChange(e.target.value)}
          placeholder={field.type === 'number' ? 'Ex.: 4' : ''}
        />
      )}
    </label>
  )
}
