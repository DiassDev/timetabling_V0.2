"""Serviços transacionais (ACID) que integram o ORM Django ao motor matemático."""

from collections import defaultdict

from django.db import transaction
from django.utils import timezone

from .core import (
    Alocacao as CoreAlocacao,
    ConfiguracaoMotor,
    DiaSemana as CoreDia,
    Disciplina as CoreDisciplina,
    InstanciaTimetabling,
    InviabilidadeErro,
    Professor as CoreProfessor,
    Slot as CoreSlot,
    Turma as CoreTurma,
    Turno as CoreTurno,
    gerar_horario,
)

from .models import (
    Alocacao,
    AulaAgendada,
    DiagnosticoInviabilidade,
    Disponibilidade,
    ExecucaoGeracao,
    PeriodoLetivo,
    Slot,
    StatusExecucao,
    TipoDiagnostico,
    Turma,
    Usuario,
)

_MAPA_DIA = {
    "SEG": CoreDia.SEGUNDA,
    "TER": CoreDia.TERCA,
    "QUA": CoreDia.QUARTA,
    "QUI": CoreDia.QUINTA,
    "SEX": CoreDia.SEXTA,
    "SAB": CoreDia.SABADO,
}

_MAPA_TURNO = {
    "MANHA": CoreTurno.MANHA,
    "TARDE": CoreTurno.TARDE,
    "NOITE": CoreTurno.NOITE,
}


@transaction.atomic
def executar_geracao_horario(
    periodo_letivo_id: int,
    solicitado_por_id: int,
    semente: int | None = None,
) -> ExecucaoGeracao:
    """Carrega dados do período, executa AG+SA e persiste grade ou diagnóstico de forma atômica."""
    periodo_letivo = PeriodoLetivo.objects.get(pk=periodo_letivo_id)
    usuario = Usuario.objects.get(pk=solicitado_por_id)

    execucao = ExecucaoGeracao.objects.create(
        periodo_letivo=periodo_letivo,
        solicitado_por=usuario,
        status=StatusExecucao.EM_EXECUCAO,
        iniciada_em=timezone.now(),
        algoritmo="AG_SA_HIBRIDO",
        parametros={"semente": semente},
    )

    instancia = _montar_instancia_core(periodo_letivo)

    try:
        resultado = gerar_horario(instancia, ConfiguracaoMotor(semente=semente))
    except InviabilidadeErro as erro:
        execucao.status = StatusExecucao.FALHA
        execucao.concluida_em = timezone.now()
        execucao.save(update_fields=["status", "concluida_em"])
        DiagnosticoInviabilidade.objects.create(
            execucao=execucao,
            tipo=_classificar_diagnostico(str(erro)),
            mensagem=str(erro),
        )
        return execucao

    if not resultado.metricas.valida:
        execucao.status = StatusExecucao.FALHA
        execucao.concluida_em = timezone.now()
        execucao.save(update_fields=["status", "concluida_em"])
        DiagnosticoInviabilidade.objects.create(
            execucao=execucao,
            tipo=TipoDiagnostico.CONFLITO,
            mensagem="Não foi possível eliminar todos os conflitos de horário com as restrições atuais.",
        )
        return execucao

    aulas_orm = [
        AulaAgendada(
            execucao=execucao,
            alocacao_id=int(item.alocacao_id),
            slot_id=int(item.slot.id),
            professor_id=int(item.professor_id),
            turma_id=int(item.turma_id),
        )
        for item in resultado.grade
    ]
    AulaAgendada.objects.bulk_create(aulas_orm)

    execucao.status = StatusExecucao.CONCLUIDA
    execucao.concluida_em = timezone.now()
    execucao.violacoes_fracas = resultado.metricas.violacoes_fracas
    execucao.save(update_fields=["status", "concluida_em", "violacoes_fracas"])

    return execucao


def _montar_instancia_core(periodo_letivo: PeriodoLetivo) -> InstanciaTimetabling:
    """Converte registros do banco relacional em estruturas imutáveis do motor matemático."""
    slots_db = list(Slot.objects.select_related("periodo_aula").all())
    slots_core = tuple(
        CoreSlot(
            id=str(s.id),
            dia=_MAPA_DIA[s.dia_semana],
            turno=_MAPA_TURNO[s.periodo_aula.turno],
            inicio_minutos=s.periodo_aula.hora_inicio.hour * 60 + s.periodo_aula.hora_inicio.minute,
            duracao_minutos=s.periodo_aula.duracao_min,
        )
        for s in slots_db
    )

    turmas_db = list(Turma.objects.select_related("curso").filter(periodo_letivo=periodo_letivo))
    turmas_core = tuple(
        CoreTurma(
            id=str(t.id),
            nome=f"{t.serie} {t.identificador}",
            curso=t.curso.nome,
            turno=_MAPA_TURNO[t.turno],
        )
        for t in turmas_db
    )

    alocacoes_db = list(
        Alocacao.objects.select_related("professor__usuario", "disciplina", "turma").filter(
            turma__periodo_letivo=periodo_letivo
        )
    )

    disp_por_prof: dict[int, set[str]] = defaultdict(set)
    for disp in Disponibilidade.objects.filter(periodo_letivo=periodo_letivo):
        disp_por_prof[disp.professor_id].add(str(disp.slot_id))

    professores_vistos = {a.professor for a in alocacoes_db}
    professores_core = tuple(
        CoreProfessor(
            id=str(p.id),
            nome=p.usuario.email,
            disponibilidade=frozenset(disp_por_prof[p.id]),
        )
        for p in professores_vistos
    )

    disciplinas_vistas = {a.disciplina for a in alocacoes_db}
    disciplinas_core = tuple(CoreDisciplina(id=str(d.id), nome=d.nome) for d in disciplinas_vistas)

    alocacoes_core = tuple(
        CoreAlocacao(
            id=str(a.id),
            professor_id=str(a.professor_id),
            disciplina_id=str(a.disciplina_id),
            turma_id=str(a.turma_id),
            carga_horaria=a.aulas_semana,
        )
        for a in alocacoes_db
    )

    return InstanciaTimetabling(
        slots=slots_core,
        professores=professores_core,
        disciplinas=disciplinas_core,
        turmas=turmas_core,
        alocacoes=alocacoes_core,
    )


def _classificar_diagnostico(mensagem: str) -> str:
    """Classifica o tipo de inviabilidade com base na mensagem de domínio."""
    texto = mensagem.lower()
    if "disponív" in texto:
        return TipoDiagnostico.DISPONIBILIDADE
    if "cadastrados" in texto or "capacidade" in texto:
        return TipoDiagnostico.CAPACIDADE
    if "sobrepost" in texto or "conflito" in texto:
        return TipoDiagnostico.CONFLITO
    return TipoDiagnostico.OUTRO
