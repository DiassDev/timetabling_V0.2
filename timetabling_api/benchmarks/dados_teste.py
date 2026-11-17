"""Gerador de instâncias simuladas de teste (pequena e escala de referência)."""

import random

from timetabling_api.core import (
    Alocacao,
    DiaSemana,
    Disciplina,
    InstanciaTimetabling,
    Professor,
    Slot,
    Turma,
    Turno,
)


def criar_slots_padrao(
    dias: tuple[DiaSemana, ...] = (
        DiaSemana.SEGUNDA,
        DiaSemana.TERCA,
        DiaSemana.QUARTA,
        DiaSemana.QUINTA,
        DiaSemana.SEXTA,
    ),
    aulas_por_turno: int = 4,
    duracao_minutos: int = 50,
) -> tuple[Slot, ...]:
    """Cria grade de slots sem sobreposição para os turnos da manhã e da noite."""
    slots: list[Slot] = []
    inicios_turno = {
        Turno.MANHA: 7 * 60 + 30,
        Turno.NOITE: 19 * 60,
    }

    for dia in dias:
        for turno, inicio_base in inicios_turno.items():
            for ordem in range(aulas_por_turno):
                inicio = inicio_base + ordem * duracao_minutos
                slots.append(
                    Slot(
                        id=f"{dia.value[:3]}_{turno.value}_{ordem + 1}",
                        dia=dia,
                        turno=turno,
                        inicio_minutos=inicio,
                        duracao_minutos=duracao_minutos,
                    )
                )

    return tuple(slots)


def gerar_instancia_pequena() -> InstanciaTimetabling:
    """Gera uma instância enxuta e determinística para validação funcional rápida."""
    slots = criar_slots_padrao(
        dias=(DiaSemana.SEGUNDA, DiaSemana.TERCA, DiaSemana.QUARTA),
        aulas_por_turno=3,
    )
    ids_manha = frozenset(s.id for s in slots if s.turno == Turno.MANHA)
    ids_noite = frozenset(s.id for s in slots if s.turno == Turno.NOITE)

    professores = (
        Professor("P1", "Ana Silva", ids_manha),
        Professor("P2", "Bruno Costa", ids_manha | ids_noite),
        Professor("P3", "Carla Dias", ids_manha),
        Professor("P4", "Diego Melo", ids_noite),
    )
    disciplinas = (
        Disciplina("D1", "Matemática"),
        Disciplina("D2", "Português"),
        Disciplina("D3", "História"),
        Disciplina("D4", "Física"),
    )
    turmas = (
        Turma("T1", "1º Ano A", "Ensino Médio", Turno.MANHA),
        Turma("T2", "2º Ano A", "Ensino Médio", Turno.MANHA),
        Turma("T3", "ADS 1º Sem", "Superior ADS", Turno.NOITE),
    )
    alocacoes = (
        Alocacao("A1", "P1", "D1", "T1", 3),
        Alocacao("A2", "P2", "D2", "T1", 3),
        Alocacao("A3", "P3", "D3", "T1", 2),
        Alocacao("A4", "P1", "D1", "T2", 3),
        Alocacao("A5", "P3", "D3", "T2", 3),
        Alocacao("A6", "P2", "D2", "T2", 2),
        Alocacao("A7", "P2", "D1", "T3", 3),
        Alocacao("A8", "P4", "D4", "T3", 4),
    )

    return InstanciaTimetabling(
        slots=slots,
        professores=professores,
        disciplinas=disciplinas,
        turmas=turmas,
        alocacoes=alocacoes,
    )


def gerar_instancia_referencia(semente: int = 42) -> InstanciaTimetabling:
    """Gera instância na escala de referência do requisito 15.4 (50 professores, 14 turmas, manhã e noite)."""
    rng = random.Random(semente)
    slots = criar_slots_padrao(aulas_por_turno=4)
    slots_manha = [s.id for s in slots if s.turno == Turno.MANHA]
    slots_noite = [s.id for s in slots if s.turno == Turno.NOITE]

    disciplinas = tuple(
        Disciplina(f"D{i}", nome)
        for i, nome in enumerate(
            [
                "Matemática",
                "Português",
                "História",
                "Geografia",
                "Física",
                "Química",
                "Biologia",
                "Inglês",
                "Filosofia",
                "Sociologia",
                "Algoritmos",
                "Banco de Dados",
            ],
            start=1,
        )
    )

    turmas = tuple(
        [Turma(f"TM{i}", f"EM {i}º Ano", "Ensino Médio", Turno.MANHA) for i in range(1, 8)]
        + [Turma(f"TN{i}", f"Sup {i}º Período", "Superior", Turno.NOITE) for i in range(1, 8)]
    )

    alocacoes: list[Alocacao] = []
    carga_prof_manha: dict[int, int] = {i: 0 for i in range(1, 51)}
    carga_prof_noite: dict[int, int] = {i: 0 for i in range(1, 51)}

    cargas_disciplinas = [4, 4, 3, 3, 2, 2]
    idx_aloc = 1

    for t_idx, turma in enumerate(turmas):
        base_prof = (t_idx * 3) % 50
        for d_offset, carga in enumerate(cargas_disciplinas):
            prof_num = ((base_prof + d_offset) % 50) + 1
            disc = disciplinas[(t_idx + d_offset) % len(disciplinas)]
            alocacoes.append(
                Alocacao(
                    id=f"A{idx_aloc}",
                    professor_id=f"P{prof_num}",
                    disciplina_id=disc.id,
                    turma_id=turma.id,
                    carga_horaria=carga,
                )
            )
            if turma.turno == Turno.MANHA:
                carga_prof_manha[prof_num] += carga
            else:
                carga_prof_noite[prof_num] += carga
            idx_aloc += 1

    professores: list[Professor] = []
    for i in range(1, 51):
        disp: set[str] = set()
        qtd_manha = min(len(slots_manha), max(carga_prof_manha[i] + 5, 10))
        qtd_noite = min(len(slots_noite), max(carga_prof_noite[i] + 5, 10))

        if carga_prof_manha[i] > 0 or i % 2 == 1:
            disp.update(rng.sample(slots_manha, qtd_manha))
        if carga_prof_noite[i] > 0 or i % 2 == 0:
            disp.update(rng.sample(slots_noite, qtd_noite))

        professores.append(Professor(f"P{i}", f"Professor {i:02d}", frozenset(disp)))

    return InstanciaTimetabling(
        slots=slots,
        professores=tuple(professores),
        disciplinas=disciplinas,
        turmas=turmas,
        alocacoes=tuple(alocacoes),
    )
