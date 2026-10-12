
from core.catalog import Catalog
from core.grammar.grammar import parse_candidate, render_html
from core.types import (
    CandidateProfile,
    ClassificationResult,
    ContactInfo,
    Evaluation,
    ExperienceEntry,
    ExtractedData,
    NormalizedQualifications,
)
from pipeline import run
from profiles.full_stack import FULL_STACK


catalog = Catalog.from_json()


resume_text = """
Juan Pérez
juan.perez@example.com
Cali, Colombia

Professional Summary
Desarrollador de software interesado en aplicaciones web.

Professional Experience
Desarrollador web
Empresa Demo | 2024-2026
- Construcción de aplicaciones web

Education
Ingeniería de Sistemas

Technical Skills
Python, JavaScript, React, PostgreSQL, Git
"""

result = run(resume_text, FULL_STACK, catalog)

assert result.html_output, "El pipeline no generó HTML"
assert "Juan Pérez" in result.html_output, "No aparece el nombre"
assert "Qualification Evaluation" in result.html_output
assert "Full Stack Developer" in result.html_output

print("HTML generado correctamente.")
print("Clasificación:", result.classification.accepted)
print("Tamaño HTML:", len(result.html_output), "caracteres")

with open("test_candidate_output.html", "w", encoding="utf-8") as file:
    file.write(result.html_output)

print("Archivo generado: test_candidate_output.html")
