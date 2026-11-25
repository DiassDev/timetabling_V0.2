#!/usr/bin/env python
"""Popula o SQLite com uma base de teste: 3 turmas, 10 professores, 12 disciplinas e disponibilidade aleatória.

Uso: python seed_teste.py [semente]   (sem semente, a disponibilidade muda a cada execução)
"""

import os
import random
import sys
from datetime import date, time


def configurar_django() -> None:
    """Inicializa o Django e aplica as migrações pendentes."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)


DISCIPLINAS = [
    "Matemática", "Português", "História", "Geografia", "Física", "Química",
    "Biologia", "Inglês", "Artes", "Educação Física", "Filosofia", "Sociologia",
]
PROFESSORES = [
    "ana.silva", "bruno.costa", "carla.dias", "diego.melo", "elena.rocha",
    "fabio.lima", "gabriela.souza", "henrique.alves", "isabela.nunes", "joao.pereira",
]
HORARIOS_MANHA = [time(7, 10), time(8, 0), time(8, 50), time(9, 55), time(10, 45)]
DIAS_UTEIS = ["SEG", "TER", "QUA", "QUI", "SEX"]
AULAS_POR_DISCIPLINA = 2  # 12 disciplinas x 2 = 24 aulas por turma (25 slots no turno)


def popular_banco(semente: int | None) -> None:
    """Recria atomicamente toda a base de teste."""
    from django.contrib.auth.hashers import make_password
    from django.db import transaction

    from timetabling_api.models import (
        Alocacao, AulaAgendada, Curso, CursoDisciplina, DiagnosticoInviabilidade,
        Disciplina, Disponibilidade, ExecucaoGeracao, NivelEnsino, PapelUsuario,
        PeriodoAula, PeriodoLetivo, PreferenciaDisciplina, Professor,
        ProfessorDisciplina, Slot, Turma, Turno, Usuario,
    )
    from timetabling_api.services import executar_geracao_horario

    rng = random.Random(semente)

    with transaction.atomic():
        # Limpeza respeitando as dependências PROTECT
        for modelo in (
            AulaAgendada, DiagnosticoInviabilidade, ExecucaoGeracao, Alocacao,
            Disponibilidade, PreferenciaDisciplina, ProfessorDisciplina, Slot,
            PeriodoAula, Turma, CursoDisciplina, Curso, PeriodoLetivo, Professor,
            Disciplina, Usuario,
        ):
            modelo.objects.all().delete()

        senha = make_password("123456")
        dominio = "@institutofarol.edu.br"
        Usuario.objects.create(email="admin" + dominio, senha_hash=senha, papel=PapelUsuario.ADMIN)
        coordenador = Usuario.objects.create(
            email="coordenacao" + dominio, senha_hash=senha, papel=PapelUsuario.COORDENADOR
        )

        periodo = PeriodoLetivo.objects.create(
            rotulo="2026.1", data_inicio=date(2026, 2, 1), data_fim=date(2026, 12, 15), ativo=True
        )
        curso = Curso.objects.create(nome="Ensino Médio", nivel_ensino=NivelEnsino.MEDIO)
        disciplinas = [Disciplina.objects.create(nome=n) for n in DISCIPLINAS]

        # Slots: turno da manhã, segunda a sexta
        slots = []
        for ordem, hora in enumerate(HORARIOS_MANHA, start=1):
            pa = PeriodoAula.objects.create(turno=Turno.MANHA, ordem=ordem, hora_inicio=hora, duracao_min=50)
            slots += [Slot.objects.create(periodo_aula=pa, dia_semana=d) for d in DIAS_UTEIS]

        # Turmas e matriz curricular
        series = ["1ª Série", "2ª Série", "3ª Série"]
        turmas = [
            Turma.objects.create(
                curso=curso, periodo_letivo=periodo, serie=s, identificador="A",
                turno=Turno.MANHA, qtd_alunos=rng.randint(28, 38),
            )
            for s in series
        ]
        for s in series:
            for d in disciplinas:
                CursoDisciplina.objects.create(curso=curso, disciplina=d, serie=s, aulas_semana=AULAS_POR_DISCIPLINA)

        # Professores: cada disciplina tem um responsável (round-robin); 2 professores ficam com 2 disciplinas
        professores = []
        for i, nome in enumerate(PROFESSORES, start=1):
            u = Usuario.objects.create(email=nome + dominio, senha_hash=senha, papel=PapelUsuario.PROFESSOR)
            professores.append(Professor.objects.create(usuario=u, matricula=f"PROF{i:03d}"))

        responsavel = {d.id: professores[i % len(professores)] for i, d in enumerate(disciplinas)}
        for prof in professores:
            proprias = [d for d in disciplinas if responsavel[d.id] == prof]
            for ordem, d in enumerate(proprias, start=1):
                ProfessorDisciplina.objects.create(professor=prof, disciplina=d)
                PreferenciaDisciplina.objects.create(professor=prof, disciplina=d, ordem=ordem)

            # Disponibilidade aleatória, sempre com folga sobre a carga semanal do professor
            carga = len(proprias) * AULAS_POR_DISCIPLINA * len(turmas)
            minimo = min(len(slots), carga + 3)
            quantidade = rng.randint(minimo, len(slots))
            for slot in rng.sample(slots, quantidade):
                Disponibilidade.objects.create(professor=prof, slot=slot, periodo_letivo=periodo)

        # Alocações: todas as disciplinas em todas as turmas
        for turma in turmas:
            for d in disciplinas:
                Alocacao.objects.create(
                    turma=turma, disciplina=d, professor=responsavel[d.id], aulas_semana=AULAS_POR_DISCIPLINA
                )

    execucao = executar_geracao_horario(
        periodo_letivo_id=periodo.id, solicitado_por_id=coordenador.id, semente=semente or 42
    )

    print("=" * 60)
    print(f"Turmas: {Turma.objects.count()} | Professores: {Professor.objects.count()} | "
          f"Disciplinas: {Disciplina.objects.count()} | Slots: {Slot.objects.count()}")
    print(f"Alocações: {Alocacao.objects.count()} | Disponibilidades: {Disponibilidade.objects.count()}")
    for prof in professores:
        print(f"  {prof.usuario.email:<40} {prof.disponibilidade_set.count():>2}/{len(slots)} slots")
    print(f"Geração: {execucao.status} | aulas agendadas: {execucao.aulas_agendadas.count()}")
    print("Senha padrão de todos os acessos: 123456")
    print("=" * 60)


if __name__ == "__main__":
    configurar_django()
    popular_banco(int(sys.argv[1]) if len(sys.argv) > 1 else None)
