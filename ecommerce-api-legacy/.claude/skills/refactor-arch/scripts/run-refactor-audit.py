#!/usr/bin/env python3
"""
Script para preparar execução da skill refactor-arch com timestamp dinâmico
Detecta projeto e timestamp, então instrui o modelo a executar a skill
"""

from datetime import datetime
from pathlib import Path

def main():
    project_name = Path.cwd().name
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

    # Caminho para relatórios (na raiz, não na skill)
    reports_dir = Path.cwd().parent.parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)

    expected_filename = f"audit-{project_name}-{timestamp}.md"
    expected_path = reports_dir / expected_filename

    print("\n" + "="*80)
    print("🔍 Refactor Architecture Skill - v2.0")
    print("="*80)
    print(f"\n📁 Projeto detectado: {project_name}")
    print(f"⏰ Timestamp: {timestamp}")
    print(f"📝 Relatório será salvo como: {expected_filename}")
    print(f"📂 Caminho: {expected_path}")
    print("\n" + "="*80)
    print("▶️  INSTRUÇÕES:")
    print("  1. Execute a skill: /refactor-arch")
    print(f"  2. Salve o relatório com nome: {expected_filename}")
    print(f"  3. Salve em: {expected_path}")
    print("="*80 + "\n")

    # Guardar config em temp file para possível uso futuro
    config_file = Path("/tmp/refactor_skill_config.txt")
    with open(config_file, 'w') as f:
        f.write(f"project_name={project_name}\n")
        f.write(f"timestamp={timestamp}\n")
        f.write(f"expected_filename={expected_filename}\n")
        f.write(f"expected_path={expected_path}\n")

if __name__ == "__main__":
    main()
