"""
URL Patterns for the Analyzer App
===================================
Route map:
    /                         → index (home/input form)
    /analyze/                 → analyze (POST: triggers loading page)
    /run/<owner>/<repo>/      → run_analysis (AJAX: runs CrewAI)
    /report/<owner>/<repo>/   → report (renders HTML report)
    /download/<owner>/<repo>/ → download_report (Markdown download)
"""

from django.urls import path
from . import views

app_name = "analyzer"

urlpatterns = [
    path("", views.index, name="index"),
    path("analyze/", views.analyze, name="analyze"),
    path("run/<str:owner>/<str:repo>/", views.run_analysis, name="run_analysis"),
    path("report/<str:owner>/<str:repo>/", views.report, name="report"),
    path("download/<str:owner>/<str:repo>/", views.download_report, name="download_report"),
]
