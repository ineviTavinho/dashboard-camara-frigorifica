import os
import sys
import streamlit.web.cli as stcli

# TRUQUE MÁGICO: Redireciona as mensagens do sistema para o "vazio".
# Isso evita que o programa quebre por não encontrar a tela preta (cmd).
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

def resolve_path(path):
    resolved_path = os.path.abspath(os.path.join(os.path.dirname(__file__), path))
    return resolved_path

if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("dashboard.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())