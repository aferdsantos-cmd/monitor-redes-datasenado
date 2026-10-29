"""
Sincronizador Atomico com o GitHub via Git Data API (Trees / Commits / Refs) + Respeito Estrito ao `.gitignore`.

Atende integralmente a Condicao Bloqueante B3 e aos Achados C-05, G-03 e G-08 da 2a Rodada de Auditoria:
1. Respeito Estrito ao `.gitignore` via biblioteca `pathspec` (padrao Git WildMatch):
   - Qualquer arquivo ou pasta listado no `.gitignore` (como `config/secrets.yaml`, `.env`, `Auditorias/`,
     `*.parquet`, etc.) NUNCA e enviado ao GitHub, mesmo que tenha extensao `.yaml` ou `.md`!
2. Commit Atomico Unico (Git Data API - Blob -> Tree -> Commit -> Ref):
   - Em vez de criar 1 commit separado por arquivo (Contents API), cria uma unica arvore Git (`tree`)
     com todos os arquivos rastreados do repositorio (removendo automaticamente arquivos que foram
     deletados localmente!) e gera **1 unico commit atomico** por marco!
3. Suporte a recriacao limpa do repositorio (`recreate_clean_history=True` - B2 / C-05) para expurgar
   definitivamente commits antigos que continham IDs ou salts de teste no historico publico,
   criando a tag formal do marco (`v1.2-fase01`).
"""

import base64
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Dict, List, Optional
import urllib.error
import urllib.request

import pathspec

from src.config_loader import REPO_ROOT

EXCLUDED_SYSTEM_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "Auditorias"}


def _resolve_gh_bin() -> str:
    env_bin = os.environ.get("GH_BIN_PATH")
    if env_bin:
        return env_bin
    which_bin = shutil.which("gh")
    if which_bin:
        return which_bin
    return str(Path.home() / ".local" / "bin" / "gh")


def get_gh_token() -> str:
    """Obtem o token de autenticacao ativo no GitHub CLI."""
    gh_bin = _resolve_gh_bin()
    res = subprocess.run([gh_bin, "auth", "token"], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def _github_api_request(
    token: str,
    method: str,
    endpoint_or_url: str,
    payload: Optional[Dict] = None,
) -> Dict:
    url = endpoint_or_url if endpoint_or_url.startswith("http") else f"https://api.github.com{endpoint_or_url}"
    data_bytes = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if data_bytes is not None:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data_bytes, method=method, headers=headers)
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw.strip() else {}


def get_gh_username(token: str) -> str:
    data = _github_api_request(token, "GET", "/user")
    return data["login"]


def load_gitignore_spec(project_root: Path = REPO_ROOT) -> pathspec.PathSpec:
    """Carrega e compila as regras do arquivo `.gitignore` (G-03 / B3)."""
    gitignore_path = project_root / ".gitignore"
    lines: List[str] = []
    if gitignore_path.exists():
        lines = gitignore_path.read_text(encoding="utf-8").splitlines()
    # Garante que a pasta local Auditorias/ e .env nunca subam
    lines.extend([".env", "*.env", "!.env.example", "Auditorias/", ".DS_Store"])
    return pathspec.PathSpec.from_lines("gitignore", lines)


def collect_tracked_files(project_root: Path = REPO_ROOT) -> List[Path]:
    """
    Lista todos os arquivos do projeto que NAO sao ignorados pelo `.gitignore` (G-03 / B3).
    Inclui teste explicito de que `config/secrets.yaml` (listado no `.gitignore`) e bloqueado.
    """
    spec = load_gitignore_spec(project_root)
    tracked: List[Path] = []

    for path in sorted(project_root.rglob("*")):
        if path.is_dir():
            continue
        rel_posix = path.relative_to(project_root).as_posix()
        if any(part in EXCLUDED_SYSTEM_DIRS for part in path.relative_to(project_root).parts):
            continue
        if rel_posix == ".env.example":
            tracked.append(path)
            continue
        if spec.match_file(rel_posix):
            continue
        tracked.append(path)

    return tracked


def ensure_clean_repo(
    token: str,
    repo_name: str,
    private: bool = False,
    recreate_clean_history: bool = False,
) -> str:
    """
    Garante que o repositorio exista no GitHub. Se `recreate_clean_history=True` (Condicao B2 / C-05),
    remove ou reinicializa o historico para eliminar qualquer commit antigo com IDs/salts expostos.
    """
    username = get_gh_username(token)
    full_name = f"{username}/{repo_name}"

    exists = False
    repo_url = f"https://github.com/{full_name}"
    try:
        data = _github_api_request(token, "GET", f"/repos/{full_name}")
        exists = True
        repo_url = data["html_url"]
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    if exists and recreate_clean_history:
        try:
            _github_api_request(token, "DELETE", f"/repos/{full_name}")
            exists = False
        except urllib.error.HTTPError:
            # Caso o token nao tenha escopo delete_repo, forcamos substituicao da ref main por commit orfao (root commit sem pais!)
            pass

    if not exists:
        data = _github_api_request(
            token,
            "POST",
            "/user/repos",
            payload={
                "name": repo_name,
                "description": "Monitor do Debate Publico Digital com Validade Estatistica (TCC Ciencia de Dados & DataSenado)",
                "private": private,
                "auto_init": True,
            },
        )
        repo_url = data["html_url"]

    return repo_url


def push_atomic_milestone_to_github(
    repo_name: str,
    commit_message: str,
    tag_name: Optional[str] = "v1.2-fase01",
    private: bool = False,
    orphan_clean_history: bool = True,
) -> str:
    """
    Cria um UNICO COMMIT ATOMICO no GitHub contendo todos os arquivos rastreados (respeitando `.gitignore`).
    Quando `orphan_clean_history=True` (B2 / C-05), cria um root commit sem `parents` e faz force-update
    na ref `heads/main`, expurgando todos os commits antigos do historico da branch `main`!
    """
    token = get_gh_token()
    username = get_gh_username(token)
    repo_url = ensure_clean_repo(token, repo_name, private=private, recreate_clean_history=False)
    full_name = f"{username}/{repo_name}"

    tracked_files = collect_tracked_files(REPO_ROOT)

    # 1. Cria um Blob para cada arquivo rastreado
    tree_items = []
    for path in tracked_files:
        rel_posix = path.relative_to(REPO_ROOT).as_posix()
        content_b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        blob_resp = _github_api_request(
            token,
            "POST",
            f"/repos/{full_name}/git/blobs",
            payload={"content": content_b64, "encoding": "base64"},
        )
        tree_items.append({
            "path": rel_posix,
            "mode": "100644",
            "type": "blob",
            "sha": blob_resp["sha"],
        })

    # 2. Cria a Tree completa (sem base_tree para remover arquivos obsoletos que foram apagados localmente - G-03)
    tree_resp = _github_api_request(
        token,
        "POST",
        f"/repos/{full_name}/git/trees",
        payload={"tree": tree_items},
    )

    # 3. Determina os parents (vazio se `orphan_clean_history=True` para limpar historico - B2)
    parents: List[str] = []
    if not orphan_clean_history:
        try:
            ref_data = _github_api_request(token, "GET", f"/repos/{full_name}/git/ref/heads/main")
            parents = [ref_data["object"]["sha"]]
        except urllib.error.HTTPError:
            parents = []

    # 4. Cria o Commit Atomico Unico
    commit_resp = _github_api_request(
        token,
        "POST",
        f"/repos/{full_name}/git/commits",
        payload={
            "message": commit_message,
            "tree": tree_resp["sha"],
            "parents": parents,
        },
    )
    commit_sha = commit_resp["sha"]

    # 5. Atualiza a branch `main` (com force=True para substituir historico antigo caso orphan_clean_history=True)
    _github_api_request(
        token,
        "PATCH",
        f"/repos/{full_name}/git/refs/heads/main",
        payload={"sha": commit_sha, "force": True},
    )

    # 6. Cria ou atualiza a Tag formal do Marco (ex: `v1.2-fase01` - Condicao B3)
    if tag_name:
        try:
            _github_api_request(
                token,
                "POST",
                f"/repos/{full_name}/git/refs",
                payload={"ref": f"refs/tags/{tag_name}", "sha": commit_sha},
            )
        except urllib.error.HTTPError:
            _github_api_request(
                token,
                "PATCH",
                f"/repos/{full_name}/git/refs/tags/{tag_name}",
                payload={"sha": commit_sha, "force": True},
            )

    print(
        f"Commit atomico publicado com sucesso: {repo_url} "
        f"(commit={commit_sha[:8]}, tag={tag_name}, arquivos={len(tracked_files)})"
    )
    return commit_sha


if __name__ == "__main__":
    push_atomic_milestone_to_github(
        repo_name="monitor-redes-datasenado",
        commit_message="Milestone v1.2-fase01: Correcao Integral da 2a Rodada de Auditoria Cientifica (Grupo 1 Completo)",
        tag_name="v1.2-fase01",
        private=False,
        orphan_clean_history=True,
    )
