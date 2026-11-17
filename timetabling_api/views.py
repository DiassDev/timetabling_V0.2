"""ViewSets do Django REST Framework expondo o banco de dados e a geração de horários."""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Alocacao,
    AulaAgendada,
    Curso,
    CursoDisciplina,
    DiagnosticoInviabilidade,
    Disciplina,
    Disponibilidade,
    ExecucaoGeracao,
    PeriodoAula,
    PeriodoLetivo,
    PreferenciaDisciplina,
    Professor,
    ProfessorDisciplina,
    Slot,
    StatusExecucao,
    Turma,
    Usuario,
)
from .serializers import (
    AlocacaoSerializer,
    AulaAgendadaSerializer,
    CursoDisciplinaSerializer,
    CursoSerializer,
    DiagnosticoInviabilidadeSerializer,
    DisciplinaSerializer,
    DisponibilidadeSerializer,
    ExecucaoGeracaoSerializer,
    PeriodoAulaSerializer,
    PeriodoLetivoSerializer,
    PreferenciaDisciplinaSerializer,
    ProfessorDisciplinaSerializer,
    ProfessorSerializer,
    SlotSerializer,
    SolicitarGeracaoSerializer,
    TurmaSerializer,
    UsuarioSerializer,
)
from .services import executar_geracao_horario


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by("id")
    serializer_class = UsuarioSerializer


class DisciplinaViewSet(viewsets.ModelViewSet):
    queryset = Disciplina.objects.all().order_by("id")
    serializer_class = DisciplinaSerializer


class ProfessorViewSet(viewsets.ModelViewSet):
    queryset = Professor.objects.select_related("usuario").prefetch_related("disciplinas").order_by("id")
    serializer_class = ProfessorSerializer


class ProfessorDisciplinaViewSet(viewsets.ModelViewSet):
    queryset = ProfessorDisciplina.objects.all().order_by("id")
    serializer_class = ProfessorDisciplinaSerializer


class PeriodoLetivoViewSet(viewsets.ModelViewSet):
    queryset = PeriodoLetivo.objects.all().order_by("id")
    serializer_class = PeriodoLetivoSerializer


class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all().order_by("id")
    serializer_class = CursoSerializer


class CursoDisciplinaViewSet(viewsets.ModelViewSet):
    queryset = CursoDisciplina.objects.all().order_by("id")
    serializer_class = CursoDisciplinaSerializer


class TurmaViewSet(viewsets.ModelViewSet):
    queryset = Turma.objects.select_related("curso", "periodo_letivo").order_by("id")
    serializer_class = TurmaSerializer


class PeriodoAulaViewSet(viewsets.ModelViewSet):
    queryset = PeriodoAula.objects.all().order_by("turno", "ordem")
    serializer_class = PeriodoAulaSerializer


class SlotViewSet(viewsets.ModelViewSet):
    queryset = Slot.objects.select_related("periodo_aula").order_by("id")
    serializer_class = SlotSerializer


class DisponibilidadeViewSet(viewsets.ModelViewSet):
    queryset = Disponibilidade.objects.all().order_by("id")
    serializer_class = DisponibilidadeSerializer


class AlocacaoViewSet(viewsets.ModelViewSet):
    queryset = Alocacao.objects.select_related("turma", "disciplina", "professor").order_by("id")
    serializer_class = AlocacaoSerializer


class PreferenciaDisciplinaViewSet(viewsets.ModelViewSet):
    queryset = PreferenciaDisciplina.objects.all().order_by("id")
    serializer_class = PreferenciaDisciplinaSerializer


class ExecucaoGeracaoViewSet(viewsets.ReadOnlyModelViewSet):
    """Consulta execuções históricas e dispara novas gerações de horário."""

    queryset = (
        ExecucaoGeracao.objects.select_related("periodo_letivo", "solicitado_por")
        .prefetch_related("aulas_agendadas", "diagnosticos")
        .order_by("-id")
    )
    serializer_class = ExecucaoGeracaoSerializer

    @action(detail=False, methods=["post"], url_path="gerar")
    def gerar(self, request) -> Response:
        entrada = SolicitarGeracaoSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        execucao = executar_geracao_horario(
            periodo_letivo_id=entrada.validated_data["periodo_letivo_id"],
            solicitado_por_id=entrada.validated_data["solicitado_por_id"],
            semente=entrada.validated_data.get("semente"),
        )
        saida = self.get_serializer(execucao)
        codigo_http = (
            status.HTTP_201_CREATED
            if execucao.status == StatusExecucao.CONCLUIDA
            else status.HTTP_422_UNPROCESSABLE_ENTITY
        )
        return Response(saida.data, status=codigo_http)


class AulaAgendadaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AulaAgendada.objects.select_related("execucao", "alocacao", "slot", "professor", "turma").order_by("id")
    serializer_class = AulaAgendadaSerializer


class DiagnosticoInviabilidadeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DiagnosticoInviabilidade.objects.all().order_by("id")
    serializer_class = DiagnosticoInviabilidadeSerializer
