#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

echo "=== [GATE 1/4] Executando Suíte de Testes Automatizados (pytest) ==="
UV_BIN="/Users/anderson/.local/bin/uv"
if [ ! -x "$UV_BIN" ]; then
    UV_BIN=$(which uv || echo "uv")
fi

"$UV_BIN" run --extra dev pytest -v

echo "=== [GATE 2/4] Verificando Diretório Efêmero de Cache (/tmp) ==="
CACHE_DIR="/tmp/monitor_datasenado_cache"
if [ -d "$CACHE_DIR" ]; then
    SIZE_KB=$(du -sk "$CACHE_DIR" | cut -f1)
    echo "Tamanho atual do cache efêmero: ${SIZE_KB} KB"
    if [ "$SIZE_KB" -gt 256000 ]; then
        echo "ERRO: O cache em $CACHE_DIR excedeu o teto de 250 MB!"
        exit 1
    fi
else
    echo "Cache efêmero não existe ou já foi limpo (OK)."
fi

echo "=== [GATE 3/4] Varredura SAST de Segurança e Arquivos Proibidos ==="
PROHIBITED_FILES=$(find "$REPO_ROOT" -maxdepth 3 \( -name "*.parquet" -o -name "*.duckdb" -o -name "secrets.yaml" \) -not -path "*/.venv/*" -not -path "*/.git/*" || true)

if [ -n "$PROHIBITED_FILES" ]; then
    echo "ERRO: Arquivos proibidos encontrados na árvore do repositório:"
    echo "$PROHIBITED_FILES"
    exit 1
fi

# Scanner SAST para primitivas inseguras em src/
SAST_VIOLATIONS=$(grep -rnE '\b(eval\(|exec\(|pickle\.loads?|shell=True)\b' "$REPO_ROOT/src" || true)
if [ -n "$SAST_VIOLATIONS" ]; then
    echo "ERRO SAST: Primitivas inseguras detectadas em src/:"
    echo "$SAST_VIOLATIONS"
    exit 1
fi
echo "Varredura SAST: Nenhuma primitiva insegura detectada em src/ (OK)."

echo "=== [GATE 4/4] Verificando Mapeador Sintático AST ==="
AST_MAP_BIN="$REPO_ROOT/skills/eng-python-zero-footprint/scripts/ast_repo_map.py"
if [ ! -x "$AST_MAP_BIN" ]; then
    echo "ERRO: ast_repo_map.py ausente ou sem permissão executável!"
    exit 1
fi
"$AST_MAP_BIN" > /dev/null
echo "Mapeador AST executado com sucesso (OK)."

echo "=== Todos os 4 Gates de Verificação Aprovados com Sucesso! ==="
