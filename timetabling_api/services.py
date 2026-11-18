"""Serviços transacionais (ACID) que integram o ORM Django e a API ao motor matemático."""

from collections import defaultdict
from datetime import date, time

from django.db import models, transaction
from django.utils import timezone

from .benchmarks.dados_teste import gerar_instancia_pequena
from .core import (
    Alocacao as CoreAlocacao,
    ConfiguracaoMotor,
    DiaSemana as CoreDia,
    Disciplina as CoreDisciplina,
    InstanciaTimetabling,
    InviabilidadeErro,
    Professor as CoreProfessor,
    ResultadoOtimizacao,
    Slot as CoreSlot,
    Turma as CoreTurma,
    Turno as CoreTurno,
    gerar_horario,
)
from .models import (
    Alocacao,
    AulaAgendada,
    Curso,
    DiagnosticoInviabilidade,
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

_MAPA_DIA_INVERSO = {v: k for k, v in _MAPA_DIA.items()}

_ROTULO_DIA_UI = {
    CoreDia.SEGUNDA: "Segunda-feira",
    CoreDia.TERCA: "Terça-feira",
    CoreDia.QUARTA: "Quarta-feira",
    CoreDia.QUINTA: "Quinta-feira",
    CoreDia.SEXTA: "Sexta-feira",
    CoreDia.SABADO: "Sábado",
}

_MAPA_TURNO = {
    "MANHA": CoreTurno.MANHA,
    "TARDE": CoreTurno.TARDE,
    "NOITE": CoreTurno.NOITE,
}

_MAPA_TURNO_INVERSO = {v: k for k, v in _MAPA_TURNO.items()}

_ROTULO_TURNO_UI = {
    CoreTurno.MANHA: "Manhã",
    CoreTurno.TARDE: "Tarde",
    CoreTurno.NOITE: "Noite",
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
        return _registrar_falha(execucao, str(erro))

    if not resultado.metricas.valida:
        return _registrar_falha(
            execucao,
            "Não foi possível eliminar todos os conflitos de horário com as restrições atuais.",
            tipo=TipoDiagnostico.CONFLITO,
        )

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

    grade_ui = _serializar_grade_resultado(instancia, resultado)
    metricas_dict = _serializar_metricas(resultado)

    execucao.status = StatusExecucao.CONCLUIDA
    execucao.concluida_em = timezone.now()
    execucao.violacoes_fracas = resultado.metricas.violacoes_fracas
    execucao.parametros = {
        "semente": semente,
        "metricas": metricas_dict,
        "grade": grade_ui,
    }
    execucao.save(update_fields=["status", "concluida_em", "violacoes_fracas", "parametros"])

    return execucao


@transaction.atomic
def executar_geracao_via_api(dados: dict) -> tuple[ExecucaoGeracao, dict | None]:
    """Executa o motor matemático a partir de IDs do banco ou do payload enviado pelo frontend."""
    periodo_id = dados.get("periodo_letivo_id")
    solicitante_id = dados.get("solicitado_por_id")
    semente = dados.get("semente")

    if periodo_id is not None and solicitante_id is not None:
        execucao = executar_geracao_horario(
            periodo_letivo_id=int(periodo_id),
            solicitado_por_id=int(solicitante_id),
            semente=semente,
        )
        return execucao, None

    slots_in = dados.get("slots") or []
    academic_in = dados.get("academic") or []
    allocations_in = dados.get("allocations") or []
    availability_in = dados.get("availability") or []
    accounts_in = dados.get("accounts") or []
    solicitante_in = dados.get("solicitado_por") or {}

    periodo_letivo = _obter_periodo_letivo_padrao()

    dados_sincronizados: dict | None = None
    if not slots_in and not allocations_in and not academic_in:
        if Slot.objects.exists() and Alocacao.objects.filter(turma__periodo_letivo=periodo_letivo).exists():
            dados_sincronizados = _construir_payload_do_banco(periodo_letivo, accounts_in)
        else:
            dados_sincronizados = _construir_payload_demonstracao(accounts_in)
        slots_in = dados_sincronizados["slots"]
        academic_in = dados_sincronizados["academic"]
        allocations_in = dados_sincronizados["allocations"]
        availability_in = dados_sincronizados["availability"]
        accounts_in = dados_sincronizados["accounts"]

    usuario_solicitante = _obter_ou_criar_usuario(
        email=solicitante_in.get("email") or "coordenacao@institutofarol.edu.br",
        papel=solicitante_in.get("role") or PapelUsuario.COORDENADOR,
    )

    execucao = ExecucaoGeracao.objects.create(
        periodo_letivo=periodo_letivo,
        solicitado_por=usuario_solicitante,
        status=StatusExecucao.EM_EXECUCAO,
        iniciada_em=timezone.now(),
        algoritmo="AG_SA_HIBRIDO",
        parametros={"semente": semente},
    )

    instancia, metadados = _montar_instancia_de_payload(
        slots_in=slots_in,
        academic_in=academic_in,
        allocations_in=allocations_in,
        availability_in=availability_in,
        accounts_in=accounts_in,
    )

    try:
        resultado = gerar_horario(instancia, ConfiguracaoMotor(semente=semente))
    except InviabilidadeErro as erro:
        return _registrar_falha(execucao, str(erro)), dados_sincronizados

    if not resultado.metricas.valida:
        return (
            _registrar_falha(
                execucao,
                "Não foi possível eliminar todos os conflitos de horário com as restrições atuais.",
                tipo=TipoDiagnostico.CONFLITO,
            ),
            dados_sincronizados,
        )

    _persistir_resultado_no_banco(
        execucao=execucao,
        periodo_letivo=periodo_letivo,
        instancia=instancia,
        resultado=resultado,
        metadados=metadados,
    )

    grade_ui = _serializar_grade_resultado(instancia, resultado, metadados)
    metricas_dict = _serializar_metricas(resultado)

    execucao.status = StatusExecucao.CONCLUIDA
    execucao.concluida_em = timezone.now()
    execucao.violacoes_fracas = resultado.metricas.violacoes_fracas
    execucao.parametros = {
        "semente": semente,
        "metricas": metricas_dict,
        "grade": grade_ui,
    }
    execucao.save(update_fields=["status", "concluida_em", "violacoes_fracas", "parametros"])

    return execucao, dados_sincronizados


def _registrar_falha(
    execucao: ExecucaoGeracao,
    mensagem: str,
    tipo: str | None = None,
) -> ExecucaoGeracao:
    """Atualiza a execução como falha e registra o diagnóstico de inviabilidade."""
    execucao.status = StatusExecucao.FALHA
    execucao.concluida_em = timezone.now()
    execucao.save(update_fields=["status", "concluida_em"])
    DiagnosticoInviabilidade.objects.create(
        execucao=execucao,
        tipo=tipo or _classificar_diagnostico(mensagem),
        mensagem=mensagem,
    )
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
            nome=f"{t.serie} {t.identificador}".strip(),
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


def _normalizar_dia(valor: str) -> CoreDia:
    texto = str(valor or "").strip().lower()
    if texto.startswith("seg"):
        return CoreDia.SEGUNDA
    if texto.startswith("ter"):
        return CoreDia.TERCA
    if texto.startswith("qua"):
        return CoreDia.QUARTA
    if texto.startswith("qui"):
        return CoreDia.QUINTA
    if texto.startswith("sex"):
        return CoreDia.SEXTA
    if texto.startswith("sab") or texto.startswith("sáb"):
        return CoreDia.SABADO
    return CoreDia.SEGUNDA


def _normalizar_turno(valor: str) -> CoreTurno:
    texto = str(valor or "").strip().lower()
    if "tarde" in texto:
        return CoreTurno.TARDE
    if "noite" in texto or "noturno" in texto:
        return CoreTurno.NOITE
    return CoreTurno.MANHA


def _para_minutos(horario_str: str) -> int:
    partes = str(horario_str or "07:00").strip().split(":")
    try:
        horas = int(partes[0])
        minutos = int(partes[1]) if len(partes) > 1 else 0
        return max(0, min(1439, horas * 60 + minutos))
    except ValueError:
        return 420


def _formatar_horario(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def _montar_instancia_de_payload(
    slots_in: list[dict],
    academic_in: list[dict],
    allocations_in: list[dict],
    availability_in: list[dict],
    accounts_in: list[dict],
) -> tuple[InstanciaTimetabling, dict]:
    """Constrói uma InstanciaTimetabling a partir dos registros do frontend."""
    slots_core = tuple(
        CoreSlot(
            id=str(s.get("id") or f"slot-{i}"),
            dia=_normalizar_dia(s.get("dia", "Segunda-feira")),
            turno=_normalizar_turno(s.get("turno", "Manhã")),
            inicio_minutos=_para_minutos(s.get("inicio", "07:10")),
            duracao_minutos=max(1, int(s.get("duracao") or 50)),
        )
        for i, s in enumerate(slots_in, start=1)
    )
    turno_padrao = slots_core[0].turno if slots_core else CoreTurno.MANHA

    disciplinas_map: dict[str, CoreDisciplina] = {}
    disciplinas_por_nome: dict[str, CoreDisciplina] = {}
    turmas_map: dict[str, CoreTurma] = {}
    turmas_por_nome: dict[str, CoreTurma] = {}
    cursos_nomes: list[str] = []

    for item in academic_in:
        tipo = str(item.get("tipo") or "").strip().lower()
        item_id = str(item.get("id") or "").strip()
        nome = str(item.get("nome") or item_id).strip()
        detalhes = str(item.get("detalhes") or "").strip()

        if tipo == "curso":
            if nome:
                cursos_nomes.append(nome)
        elif tipo in ("disciplina", "matéria", "materia"):
            disc = CoreDisciplina(id=item_id or nome, nome=nome)
            disciplinas_map[disc.id] = disc
            disciplinas_por_nome[nome.lower()] = disc
        elif tipo == "turma":
            turno_Explicito = str(item.get("turno") or "").strip()
            if turno_Explicito:
                turno_turma = _normalizar_turno(turno_Explicito)
            elif any(p in detalhes.lower() for p in ("manhã", "manha", "tarde", "noite", "noturno")):
                turno_turma = _normalizar_turno(detalhes)
            else:
                turno_turma = turno_padrao
            curso_nome = str(item.get("curso") or (cursos_nomes[0] if cursos_nomes else "Ensino Regular"))
            turma = CoreTurma(
                id=item_id or nome,
                nome=nome,
                curso=curso_nome,
                turno=turno_turma,
            )
            turmas_map[turma.id] = turma
            turmas_por_nome[nome.lower()] = turma

    disp_por_chave: dict[str, set[str]] = defaultdict(set)
    for av in availability_in:
        email_av = str(av.get("email") or "").strip().lower()
        slot_id = str(av.get("slotId") or "").strip()
        if email_av and slot_id:
            disp_por_chave[email_av].add(slot_id)

    professores_map: dict[str, CoreProfessor] = {}
    email_por_prof_id: dict[str, str] = {}

    for acc in accounts_in:
        if str(acc.get("role") or "").upper() != "PROFESSOR":
            continue
        email = str(acc.get("email") or "").strip()
        chave = email.lower()
        nome = str(acc.get("name") or email).strip()
        prof_id = chave or str(acc.get("id") or nome)
        prof = CoreProfessor(
            id=prof_id,
            nome=nome,
            disponibilidade=frozenset(disp_por_chave.get(chave, set())),
        )
        professores_map[prof_id] = prof
        email_por_prof_id[prof_id] = email

    alocacoes_core: list[CoreAlocacao] = []
    for idx, aloc in enumerate(allocations_in, start=1):
        aloc_id = str(aloc.get("id") or f"aloc-{idx}")
        raw_prof = str(aloc.get("professor") or "").strip()
        raw_mat = str(aloc.get("materia") or "").strip()
        raw_turma = str(aloc.get("turma") or "").strip()
        try:
            carga = int(aloc.get("aulas") or 0)
        except ValueError:
            carga = 0

        prof_id = raw_prof.lower()
        if prof_id not in professores_map:
            for pid, p_obj in professores_map.items():
                if p_obj.nome.lower() == prof_id:
                    prof_id = pid
                    break

        if raw_mat in disciplinas_map:
            disc_id = raw_mat
        elif raw_mat.lower() in disciplinas_por_nome:
            disc_id = disciplinas_por_nome[raw_mat.lower()].id
        else:
            disc_id = raw_mat

        if raw_turma in turmas_map:
            turma_id = raw_turma
        elif raw_turma.lower() in turmas_por_nome:
            turma_id = turmas_por_nome[raw_turma.lower()].id
        else:
            turma_id = raw_turma

        slot_preferencial = str(aloc.get("slotId") or "").strip()
        if slot_preferencial and prof_id in professores_map:
            prof_atual = professores_map[prof_id]
            if not prof_atual.disponibilidade:
                slots_mesmo_turno = {
                    s.id
                    for s in slots_core
                    if s.turno == (turmas_map[turma_id].turno if turma_id in turmas_map else turno_padrao)
                }
                professores_map[prof_id] = CoreProfessor(
                    id=prof_atual.id,
                    nome=prof_atual.nome,
                    disponibilidade=frozenset(slots_mesmo_turno | {slot_preferencial}),
                )

        alocacoes_core.append(
            CoreAlocacao(
                id=aloc_id,
                professor_id=prof_id,
                disciplina_id=disc_id,
                turma_id=turma_id,
                carga_horaria=carga,
            )
        )

    instancia = InstanciaTimetabling(
        slots=slots_core,
        professores=tuple(professores_map.values()),
        disciplinas=tuple(disciplinas_map.values()),
        turmas=tuple(turmas_map.values()),
        alocacoes=tuple(alocacoes_core),
    )

    metadados = {
        "email_por_prof_id": email_por_prof_id,
    }
    return instancia, metadados


def _persistir_resultado_no_banco(
    execucao: ExecucaoGeracao,
    periodo_letivo: PeriodoLetivo,
    instancia: InstanciaTimetabling,
    resultado: ResultadoOtimizacao,
    metadados: dict,
) -> None:
    """Sincroniza entidades da instância e grava as aulas agendadas no SQLite."""
    email_por_prof = metadados.get("email_por_prof_id", {})

    slot_orm_por_id: dict[str, Slot] = {}
    for s in instancia.slots:
        turno_db = _MAPA_TURNO_INVERSO[s.turno]
        dia_db = _MAPA_DIA_INVERSO[s.dia]
        hora_obj = time(s.inicio_minutos // 60, s.inicio_minutos % 60)

        pa = PeriodoAula.objects.filter(turno=turno_db, hora_inicio=hora_obj).first()
        if pa is None:
            max_ordem = (
                PeriodoAula.objects.filter(turno=turno_db).aggregate(m=models.Max("ordem"))["m"] or 0
            )
            pa = PeriodoAula.objects.create(
                turno=turno_db,
                ordem=max_ordem + 1,
                hora_inicio=hora_obj,
                duracao_min=s.duracao_minutos,
            )

        slot_orm, _ = Slot.objects.get_or_create(periodo_aula=pa, dia_semana=dia_db)
        slot_orm_por_id[s.id] = slot_orm

    disc_orm_por_id: dict[str, Disciplina] = {}
    for d in instancia.disciplinas:
        disc_orm, _ = Disciplina.objects.get_or_create(nome=d.nome)
        disc_orm_por_id[d.id] = disc_orm

    turma_orm_por_id: dict[str, Turma] = {}
    for t in instancia.turmas:
        curso_orm, _ = Curso.objects.get_or_create(
            nome=t.curso or "Ensino Médio",
            defaults={"nivel_ensino": NivelEnsino.MEDIO},
        )
        turno_db = _MAPA_TURNO_INVERSO[t.turno]
        partes = t.nome.split()
        serie = partes[0][:20] if partes else "1SERIE"
        identificador = " ".join(partes[1:])[:20] if len(partes) > 1 else t.id[:20]
        turma_orm, _ = Turma.objects.update_or_create(
            curso=curso_orm,
            periodo_letivo=periodo_letivo,
            serie=serie,
            identificador=identificador,
            defaults={"turno": turno_db, "qtd_alunos": 30},
        )
        turma_orm_por_id[t.id] = turma_orm

    prof_orm_por_id: dict[str, Professor] = {}
    for idx, p in enumerate(instancia.professores, start=1):
        email = email_por_prof.get(p.id) or (
            p.id if "@" in p.id else f"{p.id.lower()}@institutofarol.edu.br"
        )
        u_prof = _obter_ou_criar_usuario(email=email, papel=PapelUsuario.PROFESSOR)
        prof_orm = Professor.objects.filter(usuario=u_prof).first()
        if prof_orm is None:
            matricula_base = f"PROF{u_prof.id:04d}"
            prof_orm = Professor.objects.create(usuario=u_prof, matricula=matricula_base)
        prof_orm_por_id[p.id] = prof_orm

        for sid in p.disponibilidade:
            if sid in slot_orm_por_id:
                Disponibilidade.objects.get_or_create(
                    professor=prof_orm,
                    slot=slot_orm_por_id[sid],
                    periodo_letivo=periodo_letivo,
                )

    aloc_orm_por_id: dict[str, Alocacao] = {}
    for a in instancia.alocacoes:
        turma_orm = turma_orm_por_id[a.turma_id]
        disc_orm = disc_orm_por_id[a.disciplina_id]
        prof_orm = prof_orm_por_id[a.professor_id]
        aloc_orm, _ = Alocacao.objects.update_or_create(
            turma=turma_orm,
            disciplina=disc_orm,
            defaults={
                "professor": prof_orm,
                "aulas_semana": a.carga_horaria,
            },
        )
        aloc_orm_por_id[a.id] = aloc_orm

    aulas_agendadas_orm: list[AulaAgendada] = []
    pares_prof_slot: set[tuple[int, int]] = set()
    pares_turma_slot: set[tuple[int, int]] = set()

    for item in resultado.grade:
        aloc_orm = aloc_orm_por_id[item.alocacao_id]
        slot_orm = slot_orm_por_id[item.slot.id]
        prof_orm = prof_orm_por_id[item.professor_id]
        turma_orm = turma_orm_por_id[item.turma_id]

        chave_p = (prof_orm.id, slot_orm.id)
        chave_t = (turma_orm.id, slot_orm.id)
        if chave_p in pares_prof_slot or chave_t in pares_turma_slot:
            continue
        pares_prof_slot.add(chave_p)
        pares_turma_slot.add(chave_t)

        aulas_agendadas_orm.append(
            AulaAgendada(
                execucao=execucao,
                alocacao=aloc_orm,
                slot=slot_orm,
                professor=prof_orm,
                turma=turma_orm,
            )
        )

    AulaAgendada.objects.bulk_create(aulas_agendadas_orm)


def _serializar_metricas(resultado: ResultadoOtimizacao) -> dict:
    m = resultado.metricas
    return {
        "conflitos_professor": m.conflitos_professor,
        "conflitos_turma": m.conflitos_turma,
        "fora_disponibilidade": m.fora_disponibilidade,
        "janelas_professor": m.janelas_professor,
        "janelas_turma": m.janelas_turma,
        "violacoes_fortes": m.violacoes_fortes,
        "violacoes_fracas": m.violacoes_fracas,
        "custo_total": round(m.custo_total, 2),
        "tempo_execucao_segundos": round(resultado.tempo_execucao_segundos, 4),
        "valida": m.valida,
    }


def _serializar_grade_resultado(
    instancia: InstanciaTimetabling,
    resultado: ResultadoOtimizacao,
    metadados: dict | None = None,
) -> list[dict]:
    profs = {p.id: p for p in instancia.professores}
    discs = {d.id: d for d in instancia.disciplinas}
    turmas = {t.id: t for t in instancia.turmas}
    alocs = {a.id: a for a in instancia.alocacoes}
    emails = (metadados or {}).get("email_por_prof_id", {})

    itens: list[dict] = []
    for idx, item in enumerate(resultado.grade, start=1):
        prof = profs.get(item.professor_id)
        disc = discs.get(item.disciplina_id)
        turma = turmas.get(item.turma_id)
        aloc = alocs.get(item.alocacao_id)
        prof_email = emails.get(item.professor_id) or (
            prof.nome if prof and "@" in prof.nome else item.professor_id
        )

        itens.append(
            {
                "id": f"aula-{idx}-{item.alocacao_id}-{item.slot.id}",
                "alocacaoId": item.alocacao_id,
                "slotId": item.slot.id,
                "dia": _ROTULO_DIA_UI[item.slot.dia],
                "turno": _ROTULO_TURNO_UI[item.slot.turno],
                "inicio": _formatar_horario(item.slot.inicio_minutos),
                "duracao": str(item.slot.duracao_minutos),
                "materia": disc.nome if disc else item.disciplina_id,
                "materiaId": item.disciplina_id,
                "professor": prof.nome if prof else item.professor_id,
                "professorEmail": prof_email,
                "turma": turma.nome if turma else item.turma_id,
                "turmaId": item.turma_id,
                "curso": turma.curso if turma else "",
                "aulas": str(aloc.carga_horaria if aloc else 1),
            }
        )
    return itens


def _construir_payload_do_banco(
    periodo_letivo: PeriodoLetivo,
    accounts_existentes: list[dict],
) -> dict:
    """Lê os registros existentes no SQLite (ex.: populados via seed_conteudo.py) para o formato do frontend."""
    slots_db = list(Slot.objects.select_related("periodo_aula").order_by("id"))
    slots = [
        {
            "id": str(s.id),
            "dia": _ROTULO_DIA_UI[_MAPA_DIA[s.dia_semana]],
            "turno": _ROTULO_TURNO_UI[_MAPA_TURNO[s.periodo_aula.turno]],
            "inicio": s.periodo_aula.hora_inicio.strftime("%H:%M"),
            "duracao": str(s.periodo_aula.duracao_min),
        }
        for s in slots_db
    ]

    academic: list[dict] = []
    for c in Curso.objects.all().order_by("id"):
        academic.append(
            {
                "id": f"CURSO_{c.id}",
                "tipo": "Curso",
                "nome": c.nome,
                "detalhes": c.get_nivel_ensino_display(),
            }
        )

    for t in Turma.objects.select_related("curso").filter(periodo_letivo=periodo_letivo).order_by("id"):
        turno_ui = _ROTULO_TURNO_UI[_MAPA_TURNO[t.turno]]
        nome_turma = f"{t.serie} {t.identificador}".strip()
        academic.append(
            {
                "id": str(t.id),
                "tipo": "Turma",
                "nome": nome_turma,
                "turno": turno_ui,
                "curso": t.curso.nome,
                "detalhes": f"{t.curso.nome} · {turno_ui}",
            }
        )

    for d in Disciplina.objects.all().order_by("id"):
        academic.append(
            {
                "id": str(d.id),
                "tipo": "Disciplina",
                "nome": d.nome,
                "detalhes": "Disciplina curricular",
            }
        )

    accounts = list(accounts_existentes)
    emails_existentes = {str(a.get("email") or "").lower() for a in accounts}

    for p in Professor.objects.select_related("usuario").all().order_by("id"):
        email = p.usuario.email.lower()
        nome_legivel = email.split("@")[0].replace(".", " ").title()
        if email not in emails_existentes:
            accounts.append(
                {
                    "id": str(p.id),
                    "name": f"Prof. {nome_legivel}",
                    "email": email,
                    "password": "123456",
                    "role": "PROFESSOR",
                }
            )
            emails_existentes.add(email)

    availability = [
        {
            "id": str(disp.id),
            "email": disp.professor.usuario.email.lower(),
            "slotId": str(disp.slot_id),
        }
        for disp in Disponibilidade.objects.select_related("professor__usuario").filter(
            periodo_letivo=periodo_letivo
        )
    ]

    allocations = [
        {
            "id": str(aloc.id),
            "materia": str(aloc.disciplina_id),
            "professor": aloc.professor.usuario.email.lower(),
            "turma": str(aloc.turma_id),
            "aulas": str(aloc.aulas_semana),
        }
        for aloc in Alocacao.objects.select_related("professor__usuario").filter(
            turma__periodo_letivo=periodo_letivo
        )
    ]

    return {
        "slots": slots,
        "academic": academic,
        "accounts": accounts,
        "availability": availability,
        "allocations": allocations,
    }


def _construir_payload_demonstracao(accounts_existentes: list[dict]) -> dict:
    """Converte a instância padrão de referência pequena em registros compatíveis com o frontend."""
    inst = gerar_instancia_pequena()

    slots = [
        {
            "id": s.id,
            "dia": _ROTULO_DIA_UI[s.dia],
            "turno": _ROTULO_TURNO_UI[s.turno],
            "inicio": _formatar_horario(s.inicio_minutos),
            "duracao": str(s.duracao_minutos),
        }
        for s in inst.slots
    ]

    cursos_vistos = sorted({t.curso for t in inst.turmas})
    academic: list[dict] = [
        {
            "id": f"CURSO_{idx}",
            "tipo": "Curso",
            "nome": nome_curso,
            "detalhes": "Grade curricular padrão",
        }
        for idx, nome_curso in enumerate(cursos_vistos, start=1)
    ]

    for t in inst.turmas:
        academic.append(
            {
                "id": t.id,
                "tipo": "Turma",
                "nome": t.nome,
                "turno": _ROTULO_TURNO_UI[t.turno],
                "curso": t.curso,
                "detalhes": f"{t.curso} · {_ROTULO_TURNO_UI[t.turno]}",
            }
        )

    for d in inst.disciplinas:
        academic.append(
            {
                "id": d.id,
                "tipo": "Disciplina",
                "nome": d.nome,
                "detalhes": "Disciplina obrigatória",
            }
        )

    accounts = list(accounts_existentes)
    emails_existentes = {str(a.get("email") or "").lower() for a in accounts}
    email_por_prof: dict[str, str] = {}

    for p in inst.professores:
        slug = p.nome.lower().split()[0]
        email = f"{slug}@institutofarol.edu.br"
        email_por_prof[p.id] = email
        if email not in emails_existentes:
            accounts.append(
                {
                    "id": p.id,
                    "name": p.nome,
                    "email": email,
                    "password": "123456",
                    "role": "PROFESSOR",
                }
            )
            emails_existentes.add(email)

    availability: list[dict] = []
    for p in inst.professores:
        email = email_por_prof[p.id]
        for sid in sorted(p.disponibilidade):
            availability.append(
                {
                    "id": f"AV_{p.id}_{sid}",
                    "email": email,
                    "slotId": sid,
                }
            )

    allocations = [
        {
            "id": a.id,
            "materia": a.disciplina_id,
            "professor": email_por_prof[a.professor_id],
            "turma": a.turma_id,
            "aulas": str(a.carga_horaria),
        }
        for a in inst.alocacoes
    ]

    return {
        "slots": slots,
        "academic": academic,
        "accounts": accounts,
        "availability": availability,
        "allocations": allocations,
    }


def _obter_periodo_letivo_padrao() -> PeriodoLetivo:
    periodo = PeriodoLetivo.objects.filter(ativo=True).order_by("-id").first()
    if periodo is not None:
        return periodo
    periodo, _ = PeriodoLetivo.objects.get_or_create(
        rotulo="2026.1",
        defaults={
            "data_inicio": date(2026, 2, 1),
            "data_fim": date(2026, 12, 15),
            "ativo": True,
        },
    )
    return periodo


def _obter_ou_criar_usuario(email: str, papel: str) -> Usuario:
    email_limpo = email.strip().lower()
    papel_limpo = papel if papel in PapelUsuario.values else PapelUsuario.COORDENADOR

    existente = Usuario.objects.filter(email=email_limpo).first()
    if existente is not None:
        return existente

    if papel_limpo == PapelUsuario.ADMIN:
        admin_existente = Usuario.objects.filter(papel=PapelUsuario.ADMIN).first()
        if admin_existente is not None:
            return admin_existente

    return Usuario.objects.create(
        email=email_limpo,
        senha_hash="pbkdf2_sha256$timetabling",
        papel=papel_limpo,
        ativo=True,
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
