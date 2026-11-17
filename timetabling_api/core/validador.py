"""Validação prévia de viabilidade e construção do contexto indexado de execução."""

from collections import defaultdict

from .dominio import (
    Aula,
    ContextoExecucao,
    DiaSemana,
    InstanciaTimetabling,
    InviabilidadeErro,
    Slot,
    Turno,
)


def validar_instancia(instancia: InstanciaTimetabling) -> None:
    """Verifica a viabilidade da instância antes da execução e lança InviabilidadeErro em linguagem de domínio."""
    if not instancia.slots:
        raise InviabilidadeErro("Não foi possível gerar o horário: nenhum horário (slot) foi cadastrado.")

    if not instancia.alocacoes:
        raise InviabilidadeErro("Não foi possível gerar o horário: nenhuma alocação foi informada.")

    _validar_sobreposicao_slots(instancia.slots)

    professores_por_id = {p.id: p for p in instancia.professores}
    disciplinas_por_id = {d.id: d for d in instancia.disciplinas}
    turmas_por_id = {t.id: t for t in instancia.turmas}
    slots_por_id = {s.id: s for s in instancia.slots}

    slots_por_turno: dict[Turno, list[Slot]] = defaultdict(list)
    for slot in instancia.slots:
        slots_por_turno[slot.turno].append(slot)

    carga_por_professor: dict[str, int] = defaultdict(int)
    carga_por_professor_turno: dict[tuple[str, Turno], int] = defaultdict(int)
    carga_por_turma: dict[str, int] = defaultdict(int)

    for alocacao in instancia.alocacoes:
        if alocacao.carga_horaria <= 0:
            raise InviabilidadeErro(
                f"Não foi possível gerar o horário: a alocação {alocacao.id} possui carga horária inválida ({alocacao.carga_horaria})."
            )

        professor = professores_por_id.get(alocacao.professor_id)
        if professor is None:
            raise InviabilidadeErro(
                f"Não foi possível gerar o horário: professor '{alocacao.professor_id}' não encontrado no cadastro."
            )

        disciplina = disciplinas_por_id.get(alocacao.disciplina_id)
        if disciplina is None:
            raise InviabilidadeErro(
                f"Não foi possível gerar o horário: disciplina '{alocacao.disciplina_id}' não encontrada no cadastro."
            )

        turma = turmas_por_id.get(alocacao.turma_id)
        if turma is None:
            raise InviabilidadeErro(
                f"Não foi possível gerar o horário: turma '{alocacao.turma_id}' não encontrada no cadastro."
            )

        slots_compativeis = [
            sid
            for sid in professor.disponibilidade
            if sid in slots_por_id and slots_por_id[sid].turno == turma.turno
        ]
        if not slots_compativeis:
            raise InviabilidadeErro(
                f"Não foi possível gerar o horário: o professor {professor.nome} não possui horários disponíveis "
                f"no turno {turma.turno.value} para ministrar {disciplina.nome} na turma {turma.nome}."
            )

        carga_por_professor[professor.id] += alocacao.carga_horaria
        carga_por_professor_turno[(professor.id, turma.turno)] += alocacao.carga_horaria
        carga_por_turma[turma.id] += alocacao.carga_horaria

    for prof_id, carga_total in carga_por_professor.items():
        professor = professores_por_id[prof_id]
        disponiveis_validos = sum(1 for sid in professor.disponibilidade if sid in slots_por_id)
        if carga_total > disponiveis_validos:
            raise InviabilidadeErro(
                f"Não foi possível gerar o horário: o professor {professor.nome} possui {carga_total} aulas "
                f"alocadas, mas declarou apenas {disponiveis_validos} horários disponíveis."
            )

    for (prof_id, turno), carga_turno in carga_por_professor_turno.items():
        professor = professores_por_id[prof_id]
        disponiveis_turno = sum(
            1 for sid in professor.disponibilidade if sid in slots_por_id and slots_por_id[sid].turno == turno
        )
        if carga_turno > disponiveis_turno:
            raise InviabilidadeErro(
                f"Não foi possível gerar o horário: o professor {professor.nome} possui {carga_turno} aulas "
                f"no turno {turno.value}, mas tem apenas {disponiveis_turno} horários disponíveis nesse turno."
            )

    for turma_id, carga_turma in carga_por_turma.items():
        turma = turmas_por_id[turma_id]
        total_slots_turno = len(slots_por_turno[turma.turno])
        if carga_turma > total_slots_turno:
            raise InviabilidadeErro(
                f"Não foi possível gerar o horário: a turma {turma.nome} possui {carga_turma} aulas alocadas, "
                f"mas existem apenas {total_slots_turno} horários cadastrados para o turno {turma.turno.value}."
            )


def _validar_sobreposicao_slots(slots: tuple[Slot, ...]) -> None:
    """Impede que dois slots no mesmo dia tenham horários sobrepostos."""
    por_dia: dict[DiaSemana, list[Slot]] = defaultdict(list)
    for slot in slots:
        por_dia[slot.dia].append(slot)

    for dia, lista in por_dia.items():
        ordenados = sorted(lista, key=lambda s: s.inicio_minutos)
        for atual, proximo in zip(ordenados, ordenados[1:]):
            if proximo.inicio_minutos < atual.fim_minutos:
                raise InviabilidadeErro(
                    f"Não foi possível gerar o horário: os horários '{atual.id}' e '{proximo.id}' "
                    f"estão sobrepostos em {dia.value}."
                )


def construir_contexto(instancia: InstanciaTimetabling) -> ContextoExecucao:
    """Valida a instância e constrói o contexto indexado para uso direto pelos algoritmos."""
    validar_instancia(instancia)

    slots_ordenados = tuple(
        sorted(instancia.slots, key=lambda s: (s.dia.value, s.turno.value, s.inicio_minutos))
    )
    slot_idx_por_id = {slot.id: idx for idx, slot in enumerate(slots_ordenados)}

    blocos: dict[tuple[DiaSemana, Turno], list[int]] = defaultdict(list)
    for idx, slot in enumerate(slots_ordenados):
        blocos[(slot.dia, slot.turno)].append(idx)

    ordem_slot_no_bloco: dict[int, tuple[tuple[DiaSemana, Turno], int]] = {}
    for chave_bloco, indices in blocos.items():
        for pos, slot_idx in enumerate(indices):
            ordem_slot_no_bloco[slot_idx] = (chave_bloco, pos)

    professores_por_id = {p.id: p for p in instancia.professores}
    turmas_por_id = {t.id: t for t in instancia.turmas}

    indice_professor = {p.id: idx for idx, p in enumerate(instancia.professores)}
    indice_turma = {t.id: idx for idx, t in enumerate(instancia.turmas)}

    aulas: list[Aula] = []
    slots_permitidos_set: list[frozenset[int]] = []

    for alocacao in instancia.alocacoes:
        professor = professores_por_id[alocacao.professor_id]
        turma = turmas_por_id[alocacao.turma_id]
        permitidos = tuple(
            slot_idx_por_id[sid]
            for sid in professor.disponibilidade
            if sid in slot_idx_por_id and slots_ordenados[slot_idx_por_id[sid]].turno == turma.turno
        )
        permitidos_ordenados = tuple(sorted(permitidos))
        permitidos_fset = frozenset(permitidos_ordenados)

        for _ in range(alocacao.carga_horaria):
            aulas.append(
                Aula(
                    indice=len(aulas),
                    alocacao_id=alocacao.id,
                    professor_id=alocacao.professor_id,
                    disciplina_id=alocacao.disciplina_id,
                    turma_id=alocacao.turma_id,
                    slots_permitidos=permitidos_ordenados,
                )
            )
            slots_permitidos_set.append(permitidos_fset)

    return ContextoExecucao(
        instancia=instancia,
        aulas=tuple(aulas),
        slots=slots_ordenados,
        ordem_slot_no_bloco=ordem_slot_no_bloco,
        indice_professor=indice_professor,
        indice_turma=indice_turma,
        slots_permitidos_set=tuple(slots_permitidos_set),
    )
