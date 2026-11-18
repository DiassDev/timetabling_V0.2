#!/usr/bin/env python
"""Popula o banco SQLite3 com dados escolares completos para testes do motor matemático (AG + SA)."""

import os
import sys
from datetime import date, time


def configurar_django() -> None:
    """Inicializa o ambiente Django e garante que as migrações estejam aplicadas."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)


def popular_banco() -> None:
    """Recria de forma atômica os registros necessários para executar o motor de timetabling."""
    from django.contrib.auth.hashers import make_password
    from django.db import transaction

    from timetabling_api.models import (
        Alocacao,
        AulaAgendada,
        Curso,
        CursoDisciplina,
        DiagnosticoInviabilidade,
        Disciplina,
        Disponibilidade,
        ExecucaoGeracao,
        NivelEnsino,
        PapelUsuario,
        PeriodoAula,
        PeriodoLetivo,
        PreferenciaDisciplina,
        Professor,
        ProfessorDisciplina,
        Slot,
        Turma,
        Turno,
        Usuario,
    )
    from timetabling_api.services import executar_geracao_horario

    with transaction.atomic():
        # 1. Limpeza em ordem reversa de dependência (respeitando on_delete=PROTECT)
        AulaAgendada.objects.all().delete()
        DiagnosticoInviabilidade.objects.all().delete()
        ExecucaoGeracao.objects.all().delete()
        Alocacao.objects.all().delete()
        Disponibilidade.objects.all().delete()
        PreferenciaDisciplina.objects.all().delete()
        ProfessorDisciplina.objects.all().delete()
        Slot.objects.all().delete()
        PeriodoAula.objects.all().delete()
        Turma.objects.all().delete()
        CursoDisciplina.objects.all().delete()
        Curso.objects.all().delete()
        PeriodoLetivo.objects.all().delete()
        Professor.objects.all().delete()
        Disciplina.objects.all().delete()
        Usuario.objects.all().delete()

        senha_padrao = make_password("123456")

        # 2. Usuários base (Admin único e Coordenador)
        admin = Usuario.objects.create(
            email="admin@institutofarol.edu.br",
            senha_hash=senha_padrao,
            papel=PapelUsuario.ADMIN,
            ativo=True,
        )
        coordenador = Usuario.objects.create(
            email="coordenacao@institutofarol.edu.br",
            senha_hash=senha_padrao,
            papel=PapelUsuario.COORDENADOR,
            ativo=True,
        )

        # 3. Período letivo ativo
        periodo = PeriodoLetivo.objects.create(
            rotulo="2026.1",
            data_inicio=date(2026, 2, 1),
            data_fim=date(2026, 12, 15),
            ativo=True,
        )

        # 4. Cursos e Disciplinas
        curso_em = Curso.objects.create(
            nome="Ensino Médio",
            nivel_ensino=NivelEnsino.MEDIO,
        )
        curso_ef = Curso.objects.create(
            nome="Ensino Fundamental II",
            nivel_ensino=NivelEnsino.FUNDAMENTAL,
        )

        nomes_disciplinas = [
            "Matemática",
            "Português",
            "História",
            "Geografia",
            "Física",
            "Química",
            "Biologia",
            "Inglês",
        ]
        disciplinas = {
            nome: Disciplina.objects.create(nome=nome)
            for nome in nomes_disciplinas
        }

        # 5. Períodos de aula e Slots (Segunda a Sexta — Manhã, Tarde e Noite)
        dias_uteis = ["SEG", "TER", "QUA", "QUI", "SEX"]
        grade_horarios = {
            Turno.MANHA: [
                time(7, 10),
                time(8, 0),
                time(8, 50),
                time(9, 55),
                time(10, 45),
            ],
            Turno.TARDE: [
                time(13, 10),
                time(14, 0),
                time(14, 50),
                time(15, 55),
                time(16, 45),
            ],
            Turno.NOITE: [
                time(19, 0),
                time(19, 50),
                time(20, 40),
                time(21, 30),
            ],
        }

        slots_por_turno: dict[str, list[Slot]] = {
            Turno.MANHA: [],
            Turno.TARDE: [],
            Turno.NOITE: [],
        }

        for turno, horarios in grade_horarios.items():
            for ordem, hora in enumerate(horarios, start=1):
                pa = PeriodoAula.objects.create(
                    turno=turno,
                    ordem=ordem,
                    hora_inicio=hora,
                    duracao_min=50,
                )
                for dia in dias_uteis:
                    slot = Slot.objects.create(periodo_aula=pa, dia_semana=dia)
                    slots_por_turno[turno].append(slot)

        # 6. Professores, Habilitações e Disponibilidades
        catalogo_professores = [
            (
                "PROF001",
                "ana.silva@institutofarol.edu.br",
                ["Matemática", "Física"],
                [Turno.MANHA, Turno.TARDE],
            ),
            (
                "PROF002",
                "bruno.costa@institutofarol.edu.br",
                ["Português", "Inglês"],
                [Turno.MANHA, Turno.NOITE],
            ),
            (
                "PROF003",
                "carla.dias@institutofarol.edu.br",
                ["História", "Geografia"],
                [Turno.MANHA, Turno.TARDE],
            ),
            (
                "PROF004",
                "diego.melo@institutofarol.edu.br",
                ["Física", "Matemática"],
                [Turno.MANHA, Turno.NOITE],
            ),
            (
                "PROF005",
                "elena.rocha@institutofarol.edu.br",
                ["Química", "Biologia"],
                [Turno.MANHA, Turno.TARDE],
            ),
            (
                "PROF006",
                "fabio.lima@institutofarol.edu.br",
                ["Geografia", "História"],
                [Turno.TARDE, Turno.NOITE],
            ),
            (
                "PROF007",
                "gabriela.souza@institutofarol.edu.br",
                ["Biologia", "Química"],
                [Turno.MANHA, Turno.NOITE],
            ),
            (
                "PROF008",
                "henrique.alves@institutofarol.edu.br",
                ["Inglês", "Português"],
                [Turno.MANHA, Turno.TARDE],
            ),
        ]

        professores: dict[str, Professor] = {}
        for matricula, email, discs_hab, turnos_disp in catalogo_professores:
            u_prof = Usuario.objects.create(
                email=email,
                senha_hash=senha_padrao,
                papel=PapelUsuario.PROFESSOR,
                ativo=True,
            )
            prof = Professor.objects.create(usuario=u_prof, matricula=matricula)
            professores[matricula] = prof

            for ordem_pref, nome_disc in enumerate(discs_hab, start=1):
                disc_obj = disciplinas[nome_disc]
                ProfessorDisciplina.objects.create(professor=prof, disciplina=disc_obj)
                PreferenciaDisciplina.objects.create(
                    professor=prof,
                    disciplina=disc_obj,
                    ordem=ordem_pref,
                )

            for turno_disp in turnos_disp:
                for slot in slots_por_turno[turno_disp]:
                    Disponibilidade.objects.create(
                        professor=prof,
                        slot=slot,
                        periodo_letivo=periodo,
                    )

        # 7. Turmas e Matriz Curricular
        turma_1a = Turma.objects.create(
            curso=curso_em,
            periodo_letivo=periodo,
            serie="1ª Série",
            identificador="A",
            turno=Turno.MANHA,
            qtd_alunos=35,
        )
        turma_2a = Turma.objects.create(
            curso=curso_em,
            periodo_letivo=periodo,
            serie="2ª Série",
            identificador="A",
            turno=Turno.MANHA,
            qtd_alunos=32,
        )
        turma_3a = Turma.objects.create(
            curso=curso_em,
            periodo_letivo=periodo,
            serie="3ª Série",
            identificador="A",
            turno=Turno.MANHA,
            qtd_alunos=30,
        )
        turma_8a = Turma.objects.create(
            curso=curso_ef,
            periodo_letivo=periodo,
            serie="8º Ano",
            identificador="A",
            turno=Turno.TARDE,
            qtd_alunos=28,
        )
        turma_9a = Turma.objects.create(
            curso=curso_ef,
            periodo_letivo=periodo,
            serie="9º Ano",
            identificador="A",
            turno=Turno.TARDE,
            qtd_alunos=29,
        )
        turma_1n = Turma.objects.create(
            curso=curso_em,
            periodo_letivo=periodo,
            serie="1ª Série",
            identificador="Noturno",
            turno=Turno.NOITE,
            qtd_alunos=34,
        )

        # Matriz curricular base (CursoDisciplina)
        for serie_em in ["1ª Série", "2ª Série", "3ª Série"]:
            for nome_disc, carga in [
                ("Matemática", 4),
                ("Português", 4),
                ("História", 2),
                ("Geografia", 2),
                ("Física", 3),
                ("Química", 2),
                ("Biologia", 2),
                ("Inglês", 2),
            ]:
                CursoDisciplina.objects.create(
                    curso=curso_em,
                    disciplina=disciplinas[nome_disc],
                    serie=serie_em,
                    aulas_semana=carga,
                )

        for serie_ef in ["8º Ano", "9º Ano"]:
            for nome_disc, carga in [
                ("Matemática", 4),
                ("Português", 4),
                ("História", 3),
                ("Geografia", 3),
                ("Biologia", 2),
                ("Inglês", 2),
            ]:
                CursoDisciplina.objects.create(
                    curso=curso_ef,
                    disciplina=disciplinas[nome_disc],
                    serie=serie_ef,
                    aulas_semana=carga,
                )

        # 8. Alocações semanais (Professor + Disciplina + Turma + Aulas/semana)
        alocacoes_seed = [
            # 1ª Série A (Manhã) - 17 aulas
            (turma_1a, "Matemática", "PROF001", 4),
            (turma_1a, "Português", "PROF002", 4),
            (turma_1a, "História", "PROF003", 2),
            (turma_1a, "Física", "PROF004", 3),
            (turma_1a, "Química", "PROF005", 2),
            (turma_1a, "Inglês", "PROF008", 2),
            # 2ª Série A (Manhã) - 16 aulas
            (turma_2a, "Matemática", "PROF001", 4),
            (turma_2a, "Português", "PROF008", 3),
            (turma_2a, "Geografia", "PROF003", 2),
            (turma_2a, "Física", "PROF004", 3),
            (turma_2a, "Biologia", "PROF007", 2),
            (turma_2a, "Química", "PROF005", 2),
            # 3ª Série A (Manhã) - 15 aulas
            (turma_3a, "Matemática", "PROF004", 4),
            (turma_3a, "Português", "PROF002", 4),
            (turma_3a, "História", "PROF003", 2),
            (turma_3a, "Biologia", "PROF005", 3),
            (turma_3a, "Química", "PROF007", 2),
            # 8º Ano A (Tarde) - 14 aulas
            (turma_8a, "Matemática", "PROF001", 4),
            (turma_8a, "Português", "PROF008", 4),
            (turma_8a, "História", "PROF003", 2),
            (turma_8a, "Geografia", "PROF006", 2),
            (turma_8a, "Biologia", "PROF005", 2),
            # 9º Ano A (Tarde) - 14 aulas
            (turma_9a, "Matemática", "PROF001", 4),
            (turma_9a, "Inglês", "PROF008", 3),
            (turma_9a, "História", "PROF006", 3),
            (turma_9a, "Geografia", "PROF003", 2),
            (turma_9a, "Química", "PROF005", 2),
            # 1ª Série Noturno (Noite) - 12 aulas
            (turma_1n, "Português", "PROF002", 3),
            (turma_1n, "Física", "PROF004", 3),
            (turma_1n, "Geografia", "PROF006", 2),
            (turma_1n, "Biologia", "PROF007", 2),
            (turma_1n, "História", "PROF006", 2),
        ]

        for turma_obj, nome_disc, mat_prof, carga in alocacoes_seed:
            Alocacao.objects.create(
                turma=turma_obj,
                disciplina=disciplinas[nome_disc],
                professor=professores[mat_prof],
                aulas_semana=carga,
            )

        # 9. Executa uma geração inicial pelo motor matemático para validar a base
        execucao = executar_geracao_horario(
            periodo_letivo_id=periodo.id,
            solicitado_por_id=coordenador.id,
            semente=42,
        )

    print("=" * 62)
    print("SEED CONCLUÍDO COM SUCESSO - BANCO SQLITE POPULADO")
    print("=" * 62)
    print(f"Período letivo ativo : {periodo.rotulo}")
    print(f"Usuários criados     : {Usuario.objects.count()} (1 Admin, 1 Coordenador, {Professor.objects.count()} Professores)")
    print(f"Cursos / Turmas      : {Curso.objects.count()} cursos / {Turma.objects.count()} turmas (Manhã, Tarde e Noite)")
    print(f"Disciplinas          : {Disciplina.objects.count()}")
    print(f"Slots de horário     : {Slot.objects.count()} slots distribuídos em {PeriodoAula.objects.count()} períodos")
    print(f"Disponibilidades     : {Disponibilidade.objects.count()} registros")
    print(f"Alocações semanais   : {Alocacao.objects.count()} alocações ({sum(a[3] for a in alocacoes_seed)} aulas/semana)")
    print("-" * 62)
    print("TESTE DO MOTOR MATEMÁTICO (AG + SIMULATED ANNEALING):")
    print(f"Status da execução   : {execucao.status}")
    print(f"Aulas agendadas      : {execucao.aulas_agendadas.count()}")
    print(f"Violações fracas     : {execucao.violacoes_fracas}")
    print("-" * 62)
    print("CREDENCIAIS DE ACESSO PADRÃO (Senha: 123456):")
    print(f"  Admin       : {admin.email}")
    print(f"  Coordenador : {coordenador.email}")
    print("  Professores : ana.silva@institutofarol.edu.br (e demais professores)")
    print("=" * 62)


if __name__ == "__main__":
    configurar_django()
    popular_banco()
    sys.exit(0)
