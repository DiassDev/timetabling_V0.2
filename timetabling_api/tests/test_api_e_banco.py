"""Testes de integridade ACID/SQLite3, API REST e integração com o motor matemático."""

from datetime import date, time

from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import (
    Alocacao,
    Curso,
    Disciplina,
    Disponibilidade,
    ExecucaoGeracao,
    NivelEnsino,
    PapelUsuario,
    PeriodoAula,
    PeriodoLetivo,
    Professor,
    Slot,
    StatusExecucao,
    Turma,
    Turno,
    Usuario,
)


class TestIntegridadeBanco(TestCase):
    """Valida restrições ACID e regras de integridade espelhadas de docs/queries.sql."""

    def test_sqlite_foreign_keys_ativadas(self) -> None:
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_keys;")
            valor = cursor.fetchone()[0]
        self.assertEqual(valor, 1)

    def test_regra_admin_unico(self) -> None:
        Usuario.objects.create(email="admin1@escola.com", senha_hash="h1", papel=PapelUsuario.ADMIN)
        Usuario.objects.create(email="prof1@escola.com", senha_hash="h2", papel=PapelUsuario.PROFESSOR)
        Usuario.objects.create(email="prof2@escola.com", senha_hash="h3", papel=PapelUsuario.PROFESSOR)

        with self.assertRaises(IntegrityError):
            Usuario.objects.create(email="admin2@escola.com", senha_hash="h4", papel=PapelUsuario.ADMIN)

    def test_impede_sobreposicao_periodo_aula(self) -> None:
        PeriodoAula.objects.create(
            turno=Turno.MANHA,
            ordem=1,
            hora_inicio=time(7, 0),
            duracao_min=50,
        )
        sobreposto = PeriodoAula(
            turno=Turno.MANHA,
            ordem=2,
            hora_inicio=time(7, 20),
            duracao_min=50,
        )
        with self.assertRaises(ValidationError):
            sobreposto.clean()


class TestApiRestTimetabling(APITestCase):
    """Valida endpoints REST e geração transacional ponta a ponta."""

    def setUp(self) -> None:
        self.admin = Usuario.objects.create(
            email="coord@escola.com",
            senha_hash="hash",
            papel=PapelUsuario.COORDENADOR,
        )
        self.u_prof = Usuario.objects.create(
            email="ana@escola.com",
            senha_hash="hash",
            papel=PapelUsuario.PROFESSOR,
        )
        self.prof = Professor.objects.create(usuario=self.u_prof, matricula="PROF01")
        self.periodo = PeriodoLetivo.objects.create(
            rotulo="2026-1",
            data_inicio=date(2026, 2, 1),
            data_fim=date(2026, 6, 30),
        )
        self.curso = Curso.objects.create(nome="Ensino Médio", nivel_ensino=NivelEnsino.MEDIO)
        self.disc = Disciplina.objects.create(nome="Matemática")
        self.turma = Turma.objects.create(
            curso=self.curso,
            periodo_letivo=self.periodo,
            serie="1SERIE",
            identificador="A",
            turno=Turno.MANHA,
            qtd_alunos=30,
        )
        pa1 = PeriodoAula.objects.create(turno=Turno.MANHA, ordem=1, hora_inicio=time(7, 0), duracao_min=50)
        pa2 = PeriodoAula.objects.create(turno=Turno.MANHA, ordem=2, hora_inicio=time(7, 50), duracao_min=50)
        self.s1 = Slot.objects.create(periodo_aula=pa1, dia_semana="SEG")
        self.s2 = Slot.objects.create(periodo_aula=pa2, dia_semana="SEG")

    def test_crud_e_geracao_com_sucesso(self) -> None:
        Disponibilidade.objects.create(professor=self.prof, slot=self.s1, periodo_letivo=self.periodo)
        Disponibilidade.objects.create(professor=self.prof, slot=self.s2, periodo_letivo=self.periodo)
        Alocacao.objects.create(turma=self.turma, disciplina=self.disc, professor=self.prof, aulas_semana=2)

        resp = self.client.post(
            "/api/execucoes/gerar/",
            {
                "periodo_letivo_id": self.periodo.id,
                "solicitado_por_id": self.admin.id,
                "semente": 42,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], StatusExecucao.CONCLUIDA)
        self.assertEqual(len(resp.data["aulas_agendadas"]), 2)
        self.assertEqual(ExecucaoGeracao.objects.count(), 1)

    def test_geracao_inviavel_registra_diagnostico(self) -> None:
        # Apenas 1 slot disponível para 2 aulas alocadas
        Disponibilidade.objects.create(professor=self.prof, slot=self.s1, periodo_letivo=self.periodo)
        Alocacao.objects.create(turma=self.turma, disciplina=self.disc, professor=self.prof, aulas_semana=2)

        resp = self.client.post(
            "/api/execucoes/gerar/",
            {
                "periodo_letivo_id": self.periodo.id,
                "solicitado_por_id": self.admin.id,
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(resp.data["status"], StatusExecucao.FALHA)
        self.assertEqual(len(resp.data["diagnosticos"]), 1)
        self.assertEqual(len(resp.data["aulas_agendadas"]), 0)

    def test_geracao_via_payload_frontend(self) -> None:
        payload = {
            "solicitado_por": {"email": "coord@escola.com", "role": "COORDENADOR"},
            "accounts": [
                {"id": "p1", "name": "Prof. Ana", "email": "ana@escola.com", "role": "PROFESSOR"},
            ],
            "slots": [
                {"id": "s1", "dia": "Segunda-feira", "turno": "Manhã", "inicio": "07:10", "duracao": "50"},
                {"id": "s2", "dia": "Terça-feira", "turno": "Manhã", "inicio": "07:10", "duracao": "50"},
            ],
            "academic": [
                {"id": "c1", "tipo": "Curso", "nome": "Ensino Médio", "detalhes": "Regular"},
                {"id": "t1", "tipo": "Turma", "nome": "1º Ano A", "turno": "Manhã", "detalhes": "Manhã"},
                {"id": "d1", "tipo": "Disciplina", "nome": "Matemática", "detalhes": ""},
            ],
            "availability": [
                {"id": "av1", "email": "ana@escola.com", "slotId": "s1"},
                {"id": "av2", "email": "ana@escola.com", "slotId": "s2"},
            ],
            "allocations": [
                {"id": "al1", "materia": "d1", "professor": "ana@escola.com", "turma": "t1", "aulas": "2"},
            ],
            "semente": 42,
        }
        resp = self.client.post("/api/execucoes/gerar/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], StatusExecucao.CONCLUIDA)
        self.assertEqual(len(resp.data["grade"]), 2)
        self.assertTrue(resp.data["metricas"]["valida"])

    def test_geracao_via_payload_vazio_carrega_demonstracao(self) -> None:
        resp = self.client.post("/api/execucoes/gerar/", {"semente": 42}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["status"], StatusExecucao.CONCLUIDA)
        self.assertIn("dados_sincronizados", resp.data)
        self.assertGreater(len(resp.data["grade"]), 0)

