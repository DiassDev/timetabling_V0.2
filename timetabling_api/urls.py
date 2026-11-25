"""Rotas REST da API de timetabling."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import ui
from .views import (
    AlocacaoViewSet,
    AulaAgendadaViewSet,
    CursoDisciplinaViewSet,
    CursoViewSet,
    DiagnosticoInviabilidadeViewSet,
    DisciplinaViewSet,
    DisponibilidadeViewSet,
    ExecucaoGeracaoViewSet,
    PeriodoAulaViewSet,
    PeriodoLetivoViewSet,
    PreferenciaDisciplinaViewSet,
    ProfessorDisciplinaViewSet,
    ProfessorViewSet,
    SlotViewSet,
    TurmaViewSet,
    UsuarioViewSet,
)

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet)
router.register("disciplinas", DisciplinaViewSet)
router.register("professores", ProfessorViewSet)
router.register("professores-disciplinas", ProfessorDisciplinaViewSet)
router.register("periodos-letivos", PeriodoLetivoViewSet)
router.register("cursos", CursoViewSet)
router.register("cursos-disciplinas", CursoDisciplinaViewSet)
router.register("turmas", TurmaViewSet)
router.register("periodos-aula", PeriodoAulaViewSet)
router.register("slots", SlotViewSet)
router.register("disponibilidades", DisponibilidadeViewSet)
router.register("alocacoes", AlocacaoViewSet)
router.register("preferencias-disciplinas", PreferenciaDisciplinaViewSet)
router.register("execucoes", ExecucaoGeracaoViewSet)
router.register("aulas-agendadas", AulaAgendadaViewSet)
router.register("diagnosticos", DiagnosticoInviabilidadeViewSet)

urlpatterns = [
    path("ui/estado/", ui.EstadoView.as_view()),
    path("ui/login/", ui.LoginView.as_view()),
    path("ui/contas/", ui.ContasView.as_view()),
    path("ui/contas/<int:conta_id>/", ui.ContasView.as_view()),
    path("ui/disponibilidade/", ui.DisponibilidadeProfessorView.as_view()),
    path("ui/registros/<str:section>/", ui.RegistrosView.as_view()),
    path("ui/registros/<str:section>/<str:row_id>/", ui.RegistrosView.as_view()),
    path("", include(router.urls)),
]
