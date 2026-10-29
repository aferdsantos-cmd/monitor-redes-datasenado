#!/usr/bin/env -S /Users/anderson/.local/bin/uv run python
"""
Mapeador Sintático via AST (Abstract Syntax Tree) para Repositório Python.

Extrai assinaturas compactas, tipos de argumentos, tipos de retorno e intervalos
exatos de linhas (Lstart-Lend) de módulos, classes e funções dentro de src/.
Projetado para economia de tokens no Antigravity: permite localizar cirurgicamente
o trecho de código a ser lido com read_file(StartLine, EndLine).
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TARGET = REPO_ROOT / "src"


def _format_arg(arg: ast.arg) -> str:
    if arg.annotation:
        return f"{arg.arg}: {ast.unparse(arg.annotation)}"
    return arg.arg


def _format_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args_list = []

    # Positional only
    for a in getattr(node.args, "posonlyargs", []):
        args_list.append(_format_arg(a))
    if getattr(node.args, "posonlyargs", []):
        args_list.append("/")

    # Normal args
    for a in node.args.args:
        args_list.append(_format_arg(a))

    # *vararg
    if node.args.vararg:
        args_list.append(f"*{_format_arg(node.args.vararg)}")

    # Keyword only
    for a in node.args.kwonlyargs:
        args_list.append(_format_arg(a))

    # **kwarg
    if node.args.kwarg:
        args_list.append(f"**{_format_arg(node.args.kwarg)}")

    sig = f"({', '.join(args_list)})"
    if node.returns:
        sig += f" -> {ast.unparse(node.returns)}"
    return sig


def map_file_ast(file_path: Path, base_dir: Path) -> list[str]:
    rel_path = file_path.relative_to(base_dir).as_posix()
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except Exception as e:
        return [f"[ERRO ao analisar {rel_path}: {e}]"]

    total_lines = len(source.splitlines())
    lines_output = [f"\n📄 {rel_path} (L1-L{total_lines})"]

    for node in tree.body:
        # Top-level functions
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            sig = _format_function_signature(node)
            end_line = getattr(node, "end_lineno", node.lineno)
            lines_output.append(f"  ⚡ {prefix} {node.name}{sig} (L{node.lineno}-L{end_line})")

        # Classes
        elif isinstance(node, ast.ClassDef):
            decorators = []
            for dec in node.decorator_list:
                try:
                    decorators.append(f"@{ast.unparse(dec)}")
                except Exception:
                    pass
            dec_str = f" [{' '.join(decorators)}]" if decorators else ""
            end_line = getattr(node, "end_lineno", node.lineno)
            lines_output.append(f"  🏛️ class {node.name}{dec_str} (L{node.lineno}-L{end_line})")

            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_prefix = "async def" if isinstance(item, ast.AsyncFunctionDef) else "def"
                    m_sig = _format_function_signature(item)
                    m_end = getattr(item, "end_lineno", item.lineno)
                    lines_output.append(f"    ▪ {m_prefix} {item.name}{m_sig} (L{item.lineno}-L{m_end})")

        # Top-level constants
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    val_str = ""
                    try:
                        val_str = f" = {ast.unparse(node.value)}"
                        if len(val_str) > 40:
                            val_str = val_str[:37] + "..."
                    except Exception:
                        pass
                    end_line = getattr(node, "end_lineno", node.lineno)
                    lines_output.append(f"  🔹 CONST {target.id}{val_str} (L{node.lineno}-L{end_line})")

    return lines_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Mapeador AST de Assinaturas e Linhas de Código")
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help="Diretório alvo para mapeamento sintático (padrão: src/)",
    )
    args = parser.parse_args()

    target_dir = args.target.resolve()
    if not target_dir.exists():
        print(f"[ERRO] Diretório alvo não encontrado: {target_dir}")
        return 1

    py_files = sorted(target_dir.rglob("*.py"))
    if not py_files:
        print(f"[AVISO] Nenhum arquivo .py encontrado em {target_dir}")
        return 0

    print(f"=== Mapeamento Sintático AST de Assinaturas (Base: {target_dir.name}/) ===")
    print(f"Arquivos analisados: {len(py_files)}")

    output_lines: list[str] = []
    for file_path in py_files:
        lines = map_file_ast(file_path, REPO_ROOT)
        output_lines.extend(lines)

    for line in output_lines:
        print(line)

    print("\n✅ Mapeamento AST concluído com sucesso. Use read_file(StartLine, EndLine) cirurgicamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
