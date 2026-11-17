"""Testes unitários e de integração do motor de timetabling."""

import unittest

from timetabling_api.benchmarks.dados_teste import gerar_instancia_pequena, gerar_instancia_referencia
from timetabling_api.core import (
    Alocacao,
    ConfiguracaoAG,
    ConfiguracaoMotor,
    ConfiguracaoSA,
    DiaSemana,
    Disciplina,
    InstanciaTimetabling,
    InviabilidadeErro,
    Professor,
    Slot,
    Turma,
    Turno,
    avaliar_solucao,
    gerar_horario,
    validar_instancia,
)
from timetabling_api.core.validador import construir_contexto


class TestValidador(unittest.TestCase):
    def test_rejeita_slots_sobrepostos(self) -> None:
        slots = (
            Slot("S1", DiaSemana.SEGUNDA, Turno.MANHA, 450, 50),
            Slot("S2", DiaSemana.SEGUNDA, Turno.MANHA, 480, 50),
        )
        instancia = InstanciaTimetabling(
            slots=slots,
            professores=(Professor("P1", "Ana", frozenset({"S1", "S2"})),),
            disciplinas=(Disciplina("D1", "Matemática"),),
            turmas=(Turma("T1", "1A", "EM", Turno.MANHA),),
            alocacoes=(Alocacao("A1", "P1", "D1", "T1", 1),),
        )
        with self.assertRaises(InviabilidadeErro) as ctx:
            validar_instancia(instancia)
        self.assertIn("sobrepostos", str(ctx.exception))

    def test_rejeita_professor_sem_disponibilidade_suficiente(self) -> None:
        slots = (
            Slot("S1", DiaSemana.SEGUNDA, Turno.MANHA, 450, 50),
            Slot("S2", DiaSemana.SEGUNDA, Turno.MANHA, 500, 50),
        )
        instancia = InstanciaTimetabling(
            slots=slots,
            professores=(Professor("P1", "Ana", frozenset({"S1"})),),
            disciplinas=(Disciplina("D1", "Matemática"),),
            turmas=(Turma("T1", "1A", "EM", Turno.MANHA),),
            alocacoes=(Alocacao("A1", "P1", "D1", "T1", 2),),
        )
        with self.assertRaises(InviabilidadeErro) as ctx:
            validar_instancia(instancia)
        msg = str(ctx.exception).lower()
        self.assertIn("ana", msg)
        self.assertNotIn("infeasible", msg)
        self.assertNotIn("constraint", msg)

    def test_rejeita_professor_sem_horario_no_turno_da_turma(self) -> None:
        slots = (
            Slot("S1", DiaSemana.SEGUNDA, Turno.MANHA, 450, 50),
            Slot("S2", DiaSemana.SEGUNDA, Turno.NOITE, 1140, 50),
        )
        instancia = InstanciaTimetabling(
            slots=slots,
            professores=(Professor("P1", "Bruno", frozenset({"S1"})),),
            disciplinas=(Disciplina("D1", "Física"),),
            turmas=(Turma("T1", "ADS 1", "ADS", Turno.NOITE),),
            alocacoes=(Alocacao("A1", "P1", "D1", "T1", 1),),
        )
        with self.assertRaises(InviabilidadeErro) as ctx:
            validar_instancia(instancia)
        self.assertIn("noite", str(ctx.exception).lower())


class TestAvaliador(unittest.TestCase):
    def test_detecta_conflitos_e_janelas(self) -> None:
        slots = (
            Slot("S1", DiaSemana.SEGUNDA, Turno.MANHA, 450, 50),
            Slot("S2", DiaSemana.SEGUNDA, Turno.MANHA, 500, 50),
            Slot("S3", DiaSemana.SEGUNDA, Turno.MANHA, 550, 50),
        )
        instancia = InstanciaTimetabling(
            slots=slots,
            professores=(
                Professor("P1", "Ana", frozenset({"S1", "S2", "S3"})),
                Professor("P2", "Carlos", frozenset({"S1", "S2", "S3"})),
            ),
            disciplinas=(Disciplina("D1", "Mat"), Disciplina("D2", "Port")),
            turmas=(
                Turma("T1", "1A", "EM", Turno.MANHA),
                Turma("T2", "1B", "EM", Turno.MANHA),
            ),
            alocacoes=(
                Alocacao("A1", "P1", "D1", "T1", 2),
                Alocacao("A2", "P2", "D2", "T2", 1),
            ),
        )
        contexto = construir_contexto(instancia)

        # Aula 0 (P1, T1) em S1 (idx 0), Aula 1 (P1, T1) em S3 (idx 2) -> 1 janela para P1 e 1 para T1
        # Aula 2 (P2, T2) em S1 (idx 0) -> sem conflitos
        metricas_janela = avaliar_solucao([0, 2, 0], contexto)
        self.assertTrue(metricas_janela.valida)
        self.assertEqual(metricas_janela.janelas_professor, 1)
        self.assertEqual(metricas_janela.janelas_turma, 1)

        # Aula 0 e Aula 1 no mesmo slot -> conflito de professor e de turma
        metricas_conflito = avaliar_solucao([0, 0, 1], contexto)
        self.assertFalse(metricas_conflito.valida)
        self.assertEqual(metricas_conflito.conflitos_professor, 1)
        self.assertEqual(metricas_conflito.conflitos_turma, 1)


class TestMotorHibrido(unittest.TestCase):
    def test_gera_grade_valida_instancia_pequena(self) -> None:
        instancia = gerar_instancia_pequena()
        resultado = gerar_horario(instancia, ConfiguracaoMotor(semente=123))
        self.assertTrue(resultado.metricas.valida)
        self.assertEqual(resultado.metricas.violacoes_fortes, 0)
        self.assertEqual(len(resultado.grade), 23)

    def test_gera_grade_valida_escala_referencia(self) -> None:
        instancia = gerar_instancia_referencia(semente=42)
        config = ConfiguracaoMotor(
            ag=ConfiguracaoAG(tamanho_populacao=40, geracoes=50),
            sa=ConfiguracaoSA(
                temperatura_inicial=350.0,
                taxa_resfriamento=0.985,
                iteracoes_por_temperatura=15,
            ),
            semente=42,
        )
        resultado = gerar_horario(instancia, config)
        self.assertTrue(resultado.metricas.valida)
        self.assertEqual(resultado.metricas.violacoes_fortes, 0)
        self.assertEqual(len(resultado.grade), 252)


if __name__ == "__main__":
    unittest.main()
