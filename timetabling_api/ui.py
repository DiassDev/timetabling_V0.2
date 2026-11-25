"""Adaptador REST entre o banco relacional e o formato de registros usado pelas telas React.

As telas trabalham com linhas planas (Row) e identificadores de texto; este módulo traduz essas
linhas para os modelos do banco e devolve o estado completo já no formato que a interface consome.
"""

from datetime import time

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Max, ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Alocacao,
    AulaAgendada,
    Curso,
    CursoDisciplina,
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
from .serializers import ExecucaoGeracaoSerializer
from .services import _obter_periodo_letivo_padrao

DIA_UI = dict(Slot._meta.get_field("dia_semana").choices)  # "SEG" -> "Segunda-feira"
DIA_DB = {v: k for k, v in DIA_UI.items()}
TURNO_UI = {Turno.MANHA: "Manhã", Turno.TARDE: "Tarde", Turno.NOITE: "Noite"}
TURNO_DB = {v: k for k, v in TURNO_UI.items()}


class ErroDominio(Exception):
    """Erro com mensagem pronta para ser exibida à equipe escolar."""


# ---------- Leitura: banco -> formato da interface ----------

def nome_de_email(email: str) -> str:
    """Gera um nome legível a partir do e-mail (o modelo não guarda nome)."""
    return email.split("@")[0].replace(".", " ").replace("_", " ").title()


def conta_ui(u: Usuario) -> dict:
    return {"id": str(u.id), "name": nome_de_email(u.email), "email": u.email, "role": u.papel}


def periodo_ativo() -> PeriodoLetivo:
    return PeriodoLetivo.objects.filter(ativo=True).order_by("-id").first() or _obter_periodo_letivo_padrao()


def estado_completo() -> dict:
    """Monta todas as coleções consumidas pelas telas a partir do banco."""
    periodo = periodo_ativo()

    slots = [
        {
            "id": str(s.id),
            "dia": DIA_UI[s.dia_semana],
            "turno": TURNO_UI[s.periodo_aula.turno],
            "inicio": s.periodo_aula.hora_inicio.strftime("%H:%M"),
            "duracao": str(s.periodo_aula.duracao_min),
        }
        for s in Slot.objects.select_related("periodo_aula").order_by(
            "periodo_aula__turno", "periodo_aula__hora_inicio", "id"
        )
    ]

    academic = [
        {"id": f"curso-{c.id}", "tipo": "Curso", "nome": c.nome, "detalhes": c.get_nivel_ensino_display()}
        for c in Curso.objects.order_by("id")
    ]
    for t in Turma.objects.select_related("curso").filter(periodo_letivo=periodo).order_by("id"):
        academic.append(
            {
                "id": f"turma-{t.id}",
                "tipo": "Turma",
                "nome": f"{t.serie} {t.identificador}".strip(),
                "turno": TURNO_UI[t.turno],
                "curso": t.curso.nome,
                "detalhes": f"{t.curso.nome} · {t.qtd_alunos} alunos",
            }
        )
    academic += [
        {"id": f"disc-{d.id}", "tipo": "Disciplina", "nome": d.nome, "detalhes": "Disciplina curricular"}
        for d in Disciplina.objects.order_by("nome")
    ]

    allocations = [
        {
            "id": str(a.id),
            "materia": f"disc-{a.disciplina_id}",
            "professor": a.professor.usuario.email,
            "turma": f"turma-{a.turma_id}",
            "aulas": str(a.aulas_semana),
        }
        for a in Alocacao.objects.select_related("professor__usuario").filter(turma__periodo_letivo=periodo)
    ]

    availability = [
        {"id": str(d.id), "email": d.professor.usuario.email, "slotId": str(d.slot_id)}
        for d in Disponibilidade.objects.select_related("professor__usuario").filter(periodo_letivo=periodo)
    ]

    ultima = ExecucaoGeracao.objects.filter(periodo_letivo=periodo).order_by("-id").first()

    return {
        "periodo_letivo": {"id": periodo.id, "rotulo": periodo.rotulo},
        "accounts": [conta_ui(u) for u in Usuario.objects.filter(ativo=True).order_by("id")],
        "slots": slots,
        "academic": academic,
        "allocations": allocations,
        "availability": availability,
        "ultima_execucao": ExecucaoGeracaoSerializer(ultima).data if ultima else None,
    }


# ---------- Escrita: formato da interface -> banco ----------

def _id_numerico(valor: str, prefixo: str = "") -> int:
    texto = str(valor or "")
    if prefixo and texto.startswith(prefixo):
        texto = texto[len(prefixo):]
    if not texto.isdigit():
        raise ErroDominio("Registro não encontrado. Atualize a página e tente novamente.")
    return int(texto)


def _professor_por_email(email: str) -> Professor:
    prof = Professor.objects.select_related("usuario").filter(usuario__email__iexact=email).first()
    if prof is None:
        raise ErroDominio("Professor não encontrado.")
    return prof


def _hora(valor: str) -> time:
    try:
        h, m = (int(x) for x in str(valor).split(":")[:2])
        return time(h, m)
    except (ValueError, TypeError):
        raise ErroDominio("Confira o horário informado.")


def salvar_slot(row: dict, slot_id: int | None) -> None:
    turno = TURNO_DB.get(row.get("turno"))
    dia = DIA_DB.get(row.get("dia"))
    if not turno or not dia:
        raise ErroDominio("Informe dia e turno válidos.")
    inicio, duracao = _hora(row.get("inicio")), int(row.get("duracao") or 0)

    periodo = PeriodoAula.objects.filter(turno=turno, hora_inicio=inicio).first()
    if periodo is None:
        ordem = (PeriodoAula.objects.filter(turno=turno).aggregate(m=Max("ordem"))["m"] or 0) + 1
        periodo = PeriodoAula(turno=turno, ordem=ordem, hora_inicio=inicio, duracao_min=duracao)
        periodo.full_clean()
        periodo.save()

    slot = Slot.objects.get(pk=slot_id) if slot_id else Slot()
    antigo = slot.periodo_aula if slot_id else None
    slot.periodo_aula, slot.dia_semana = periodo, dia
    slot.save()
    if antigo and antigo != periodo and not antigo.slots.exists():
        antigo.delete()


def salvar_academico(row: dict, row_id: str | None) -> None:
    tipo, nome = row.get("tipo"), str(row.get("nome") or "").strip()
    if not nome:
        raise ErroDominio("Informe o nome.")

    if tipo == "Curso":
        nivel = NivelEnsino.FUNDAMENTAL if "fundamental" in str(row.get("detalhes", "")).lower() else NivelEnsino.MEDIO
        curso = Curso.objects.get(pk=_id_numerico(row_id, "curso-")) if row_id else Curso()
        curso.nome, curso.nivel_ensino = nome, nivel
        curso.save()
    elif tipo == "Disciplina":
        disc = Disciplina.objects.get(pk=_id_numerico(row_id, "disc-")) if row_id else Disciplina()
        disc.nome = nome
        disc.save()
    elif tipo == "Turma":
        partes = nome.rsplit(" ", 1)
        serie, identificador = (partes[0], partes[1]) if len(partes) == 2 else (nome, "A")
        curso = Curso.objects.filter(nome=row.get("curso")).first() or Curso.objects.order_by("id").first()
        if curso is None:
            curso = Curso.objects.create(nome="Ensino Médio", nivel_ensino=NivelEnsino.MEDIO)
        turma = Turma.objects.get(pk=_id_numerico(row_id, "turma-")) if row_id else Turma(qtd_alunos=30)
        turma.curso, turma.periodo_letivo = curso, periodo_ativo()
        turma.serie, turma.identificador = serie[:20], identificador[:20]
        turma.turno = TURNO_DB.get(row.get("turno"), Turno.MANHA)
        turma.save()
    else:
        raise ErroDominio("Escolha o tipo de cadastro.")


def salvar_alocacao(row: dict, aloc_id: int | None) -> None:
    aulas = int(row.get("aulas") or 0)
    if aulas <= 0:
        raise ErroDominio("Informe a quantidade de aulas por semana.")
    aloc = Alocacao.objects.get(pk=aloc_id) if aloc_id else Alocacao()
    aloc.turma_id = _id_numerico(row.get("turma"), "turma-")
    aloc.disciplina_id = _id_numerico(row.get("materia"), "disc-")
    aloc.professor = _professor_por_email(row.get("professor"))
    aloc.aulas_semana = aulas
    aloc.save()
    ProfessorDisciplina.objects.get_or_create(professor=aloc.professor, disciplina_id=aloc.disciplina_id)


def salvar_disponibilidade(row: dict, disp_id: int | None) -> None:
    disp = Disponibilidade.objects.get(pk=disp_id) if disp_id else Disponibilidade()
    disp.professor = _professor_por_email(row.get("email"))
    disp.slot_id = _id_numerico(row.get("slotId"))
    disp.periodo_letivo = periodo_ativo()
    disp.save()


SALVAR = {
    "slots": lambda row, rid: salvar_slot(row, _id_numerico(rid) if rid else None),
    "academic": salvar_academico,
    "allocations": lambda row, rid: salvar_alocacao(row, _id_numerico(rid) if rid else None),
    "availability": lambda row, rid: salvar_disponibilidade(row, _id_numerico(rid) if rid else None),
}


def remover(section: str, row_id: str) -> None:
    """Remove um registro e as dependências que pertencem exclusivamente a ele."""
    if section == "slots":
        slot = Slot.objects.get(pk=_id_numerico(row_id))
        AulaAgendada.objects.filter(slot=slot).delete()
        Disponibilidade.objects.filter(slot=slot).delete()
        periodo = slot.periodo_aula
        slot.delete()
        if not periodo.slots.exists():
            periodo.delete()
    elif section == "allocations":
        aloc = Alocacao.objects.get(pk=_id_numerico(row_id))
        AulaAgendada.objects.filter(alocacao=aloc).delete()
        aloc.delete()
    elif section == "availability":
        Disponibilidade.objects.filter(pk=_id_numerico(row_id)).delete()
    elif section == "academic":
        if row_id.startswith("curso-"):
            Curso.objects.get(pk=_id_numerico(row_id, "curso-")).delete()
        elif row_id.startswith("turma-"):
            Turma.objects.get(pk=_id_numerico(row_id, "turma-")).delete()
        else:
            disc = Disciplina.objects.get(pk=_id_numerico(row_id, "disc-"))
            for modelo in (ProfessorDisciplina, PreferenciaDisciplina, CursoDisciplina):
                modelo.objects.filter(disciplina=disc).delete()
            disc.delete()
    else:
        raise ErroDominio("Tipo de registro desconhecido.")


def remover_conta(usuario: Usuario) -> None:
    prof = Professor.objects.filter(usuario=usuario).first()
    if prof:
        if Alocacao.objects.filter(professor=prof).exists():
            raise ErroDominio("Este professor possui aulas cadastradas. Remova as aulas antes do acesso.")
        for modelo in (Disponibilidade, ProfessorDisciplina, PreferenciaDisciplina):
            modelo.objects.filter(professor=prof).delete()
        prof.delete()
    usuario.delete()


# ---------- Views ----------

def _executar(acao) -> Response:
    """Executa a alteração em transação e devolve o estado atualizado ou uma mensagem amigável."""
    try:
        with transaction.atomic():
            acao()
    except ErroDominio as erro:
        return Response({"detail": str(erro)}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as erro:
        return Response({"detail": " ".join(erro.messages)}, status=status.HTTP_400_BAD_REQUEST)
    except ProtectedError:
        return Response(
            {"detail": "Este registro está em uso por outros cadastros e não pode ser removido."},
            status=status.HTTP_409_CONFLICT,
        )
    except IntegrityError:
        return Response({"detail": "Já existe um cadastro com esses dados."}, status=status.HTTP_409_CONFLICT)
    except (Slot.DoesNotExist, Curso.DoesNotExist, Turma.DoesNotExist, Disciplina.DoesNotExist,
            Alocacao.DoesNotExist, Disponibilidade.DoesNotExist, Usuario.DoesNotExist):
        return Response({"detail": "Registro não encontrado."}, status=status.HTTP_404_NOT_FOUND)
    return Response(estado_completo())


class EstadoView(APIView):
    def get(self, request):
        return Response(estado_completo())


class LoginView(APIView):
    def post(self, request):
        email = str(request.data.get("email") or "").strip()
        usuario = Usuario.objects.filter(email__iexact=email, ativo=True).first()
        if usuario is None:
            return Response({"motivo": "email"}, status=status.HTTP_400_BAD_REQUEST)
        if not check_password(str(request.data.get("password") or ""), usuario.senha_hash):
            return Response({"motivo": "senha"}, status=status.HTTP_400_BAD_REQUEST)
        if usuario.papel != request.data.get("role"):
            return Response({"motivo": "perfil", "papel": usuario.papel}, status=status.HTTP_400_BAD_REQUEST)
        return Response(conta_ui(usuario))


class ContasView(APIView):
    def post(self, request):
        email = str(request.data.get("email") or "").strip().lower()
        papel = request.data.get("role")
        senha = str(request.data.get("password") or "")
        if papel not in PapelUsuario.values or not email or not senha:
            return Response({"detail": "Preencha e-mail, senha e perfil."}, status=status.HTTP_400_BAD_REQUEST)
        if papel == PapelUsuario.ADMIN and Usuario.objects.filter(papel=PapelUsuario.ADMIN).exists():
            return Response({"detail": "Já existe um administrador."}, status=status.HTTP_409_CONFLICT)

        criado: dict = {}

        def criar():
            usuario = Usuario.objects.create(email=email, senha_hash=make_password(senha), papel=papel)
            if papel == PapelUsuario.PROFESSOR:
                Professor.objects.create(usuario=usuario, matricula=f"PROF{usuario.id:04d}")
            criado["conta"] = conta_ui(usuario)

        resposta = _executar(criar)
        if resposta.status_code == 200:
            resposta.data["conta"] = criado["conta"]
        return resposta

    def delete(self, request, conta_id: int):
        return _executar(lambda: remover_conta(Usuario.objects.get(pk=conta_id)))


class RegistrosView(APIView):
    def post(self, request, section: str):
        if section not in SALVAR:
            return Response({"detail": "Tipo de registro desconhecido."}, status=status.HTTP_404_NOT_FOUND)
        return _executar(lambda: SALVAR[section](request.data, None))

    def put(self, request, section: str, row_id: str):
        if section not in SALVAR:
            return Response({"detail": "Tipo de registro desconhecido."}, status=status.HTTP_404_NOT_FOUND)
        return _executar(lambda: SALVAR[section](request.data, row_id))

    def delete(self, request, section: str, row_id: str):
        return _executar(lambda: remover(section, row_id))


class DisponibilidadeProfessorView(APIView):
    """Substitui, de uma vez, os horários disponíveis de um professor no período ativo."""

    def put(self, request):
        def substituir():
            prof = _professor_por_email(request.data.get("email"))
            periodo = periodo_ativo()
            desejados = {_id_numerico(s) for s in request.data.get("slotIds") or []}
            existentes = Disponibilidade.objects.filter(professor=prof, periodo_letivo=periodo)
            existentes.exclude(slot_id__in=desejados).delete()
            atuais = set(existentes.values_list("slot_id", flat=True))
            Disponibilidade.objects.bulk_create(
                Disponibilidade(professor=prof, slot_id=s, periodo_letivo=periodo) for s in desejados - atuais
            )

        return _executar(substituir)
