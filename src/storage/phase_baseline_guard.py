"""
Guardião de Integridade da Baseline da Fase 01 e Automação de Governança Git.

Garante que os 16 arquivos homologados da Fase 01 (`WP-01` a `WP-16`) permaneçam 100% imutáveis
na branch `main`. Qualquer alteração na Fase 01 exige Pull Request obrigatório (`gh pr create`),
incremento de versão semântica e registro no `docs/CHANGELOG_FASE01.md`.

Novos arquivos da Fase 02 em diante têm autorização de commit e push direto em `main`, desde que
a integridade da Fase 01 seja atestada pelo `verify_baseline_integrity()`.
"""

import base64
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Optional
import urllib.error

if __name__ == "__main__" or "src" not in sys.modules:
    repo_dir = Path(__file__).resolve().parents[2]
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))

from src.config_loader import REPO_ROOT
from src.storage.github_zero_footprint_sync import (
    _github_api_request,
    collect_tracked_files,
    get_gh_token,
    get_gh_username,
    push_atomic_milestone_to_github,
)

LOCK_FILE_PATH = REPO_ROOT / "config" / "fase01_baseline_lock.json"
CHANGELOG_PATH = REPO_ROOT / "docs" / "CHANGELOG_FASE01.md"


@dataclass
class BaselineIntegrityResult:
    """Resultado da verificacao criptografica da baseline da Fase 01."""
    is_intact: bool
    baseline_version: str
    baseline_commit: str
    checked_count: int
    modified_files: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)
    details: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def summary(self) -> str:
        if self.is_intact:
            return (
                f"✅ BASELINE INTACTA: Todos os {self.checked_count} arquivos da Fase 01 "
                f"({self.baseline_version} / commit {self.baseline_commit[:8]}) conferem 100%."
            )
        issues = []
        if self.modified_files:
            issues.append(f"Modificados ({len(self.modified_files)}): {', '.join(self.modified_files)}")
        if self.missing_files:
            issues.append(f"Ausentes ({len(self.missing_files)}): {', '.join(self.missing_files)}")
        return (
            f"🚨 VIOLACAO DE BASELINE: {'; '.join(issues)}. "
            f"Alteracoes na Fase 01 exigem Pull Request e nova versao semantica!"
        )


MANDATORY_PHASE01_FILES: List[str] = [
    "config/settings.yaml",
    "docs/00_Plano_Implementacao_Historico_v1_0_SUPERSEDED.md",
    "docs/01_Metodologia_Cientifica_e_Estatistica_NotebookLM.md",
    "docs/02_Plano_Validacao_Estatistica.md",
    "docs/03_Termo_de_Emenda_Plano_v1_1_e_ADR.md",
    "docs/Relatorio_Correcoes_Fase01_v3.md",
    "README.md",
    "src/cleaning/lgpd_and_bot_filter.py",
    "src/config_loader.py",
    "src/reporting/pilot_audit_runner.py",
    "src/sampling/stratified_sampler.py",
    "src/stats/opinion_inference_engine.py",
    "src/storage/github_zero_footprint_sync.py",
    "src/storage/zero_footprint_sync.py",
    "tests/test_fase01_audit_compliance.py",
    "tests/test_skills_architecture.py",
]


class Phase01BaselineGuard:
    """
    Controlador de governanca para imutabilidade da Fase 01 e sincronizacao da Fase 02+.
    """

    def __init__(
        self,
        repo_root: Path = REPO_ROOT,
        lock_path: Optional[Path] = None,
        changelog_path: Optional[Path] = None,
    ) -> None:
        self.repo_root = repo_root
        self.lock_path = lock_path or LOCK_FILE_PATH
        self.changelog_path = changelog_path or CHANGELOG_PATH

    def load_lock_manifest(self) -> Dict[str, Any]:
        """Carrega o manifesto de trava da Fase 01."""
        if not self.lock_path.exists():
            raise FileNotFoundError(
                f"Arquivo de trava da baseline nao encontrado: {self.lock_path}. "
                "Execute a geracao inicial de config/fase01_baseline_lock.json."
            )
        return json.loads(self.lock_path.read_text(encoding="utf-8"))

    def verify_baseline_integrity(self) -> BaselineIntegrityResult:
        """
        Calcula o hash SHA-256 de todos os 16 arquivos da Fase 01 e compara com o lock.
        """
        manifest = self.load_lock_manifest()
        frozen_files = manifest.get("frozen_files", {})
        baseline_version = manifest.get("baseline_version", "v1.2.0-fase01")
        baseline_commit = manifest.get("baseline_commit", "7af3548b")

        modified: List[str] = []
        missing: List[str] = []
        details: Dict[str, Dict[str, Any]] = {}

        # 1. Valida presenca dos 16 arquivos mandatorios da Fase 01 no lock
        for req_file in MANDATORY_PHASE01_FILES:
            if req_file not in frozen_files:
                missing.append(req_file)
                details[req_file] = {"status": "MISSING_FROM_LOCK", "expected": None}

        for rel_posix, expected in frozen_files.items():
            target_path = self.repo_root / rel_posix
            if not target_path.exists():
                if rel_posix not in missing:
                    missing.append(rel_posix)
                details[rel_posix] = {"status": "MISSING", "expected": expected}
                continue

            current_bytes = target_path.read_bytes()
            current_hash = hashlib.sha256(current_bytes).hexdigest()
            current_lines = len(current_bytes.splitlines())

            expected_hash = expected.get("sha256_full")
            if current_hash != expected_hash:
                modified.append(rel_posix)
                details[rel_posix] = {
                    "status": "MODIFIED",
                    "expected_sha256": expected_hash,
                    "actual_sha256": current_hash,
                    "expected_bytes": expected.get("bytes"),
                    "actual_bytes": len(current_bytes),
                }
            else:
                details[rel_posix] = {
                    "status": "INTACT",
                    "sha256": current_hash,
                    "bytes": len(current_bytes),
                    "lines": current_lines,
                }

        is_intact = (len(modified) == 0 and len(missing) == 0 and len(frozen_files) == len(MANDATORY_PHASE01_FILES))
        return BaselineIntegrityResult(
            is_intact=is_intact,
            baseline_version=baseline_version,
            baseline_commit=baseline_commit,
            checked_count=len(frozen_files),
            modified_files=modified,
            missing_files=missing,
            details=details,
        )

    def enforce_direct_push_allowed(self) -> BaselineIntegrityResult:
        """
        Garante que o commit direto na `main` so prossiga se a baseline da Fase 01 estiver intacta.
        """
        result = self.verify_baseline_integrity()
        if not result.is_intact:
            raise PermissionError(
                f"BLOQUEIO DE GOVERNANCA GIT (Owner's Intent):\n"
                f"{result.summary()}\n\n"
                f"Para alterar arquivos da Fase 01, utilize o fluxo de Pull Request: "
                f"sync_repository_with_governance(..., authorize_fase01_pr=True, new_fase01_version='v1.2.1-fase01', ...)."
            )
        return result

    def ensure_github_baseline_tag(
        self,
        tag_name: str = "v1.2.0-fase01-baseline",
        commit_sha: str = "7af3548bce908475b5fe480666c427b91733ca4a",
        repo_name: str = "monitor-redes-datasenado",
    ) -> str:
        """
        Assegura via GitHub API que a tag da baseline congelada exista apontando para o commit da Fase 01.
        """
        token = get_gh_token()
        username = get_gh_username(token)
        full_name = f"{username}/{repo_name}"

        # Resolve commit_sha curto para o hash de 40 chars se necessario
        target_sha = commit_sha
        if len(commit_sha) < 40:
            commit_info = _github_api_request(token, "GET", f"/repos/{full_name}/commits/{commit_sha}")
            target_sha = commit_info["sha"]

        # Cria ou atualiza a tag
        try:
            _github_api_request(
                token,
                "POST",
                f"/repos/{full_name}/git/refs",
                payload={"ref": f"refs/tags/{tag_name}", "sha": target_sha},
            )
            print(f"Tag {tag_name} criada com sucesso apontando para {target_sha[:8]}.")
        except urllib.error.HTTPError as e:
            if e.code == 422:  # Ja existe -> atualiza se for necessario
                _github_api_request(
                    token,
                    "PATCH",
                    f"/repos/{full_name}/git/refs/tags/{tag_name}",
                    payload={"sha": target_sha, "force": True},
                )
                print(f"Tag {tag_name} atualizada com sucesso para {target_sha[:8]}.")
            else:
                raise
        return target_sha

    def sync_repository_with_governance(
        self,
        commit_message: str,
        repo_name: str = "monitor-redes-datasenado",
        tag_name: Optional[str] = None,
        authorize_fase01_pr: bool = False,
        new_fase01_version: Optional[str] = None,
        change_justification: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Orquestra a sincronizacao Git aplicando as regras de governanca:
        1. Se a Fase 01 estiver intacta: commit e push direto em `main` (Fase 02+).
        2. Se a Fase 01 foi modificada sem autorizacao: lanca PermissionError.
        3. Se a Fase 01 foi modificada com `authorize_fase01_pr=True`:
           - Atualiza docs/CHANGELOG_FASE01.md;
           - Cria branch remota `pr/fase01-<versao>`;
           - Abre Pull Request via `gh pr create` (ou simula em dry_run).
        """
        integrity = self.verify_baseline_integrity()

        # Fluxo 1: Fase 01 intacta -> commit direto na main sem impedimento
        if integrity.is_intact:
            if dry_run:
                return {
                    "action": "DIRECT_MAIN_PUSH_ALLOWED",
                    "status": "DRY_RUN_SUCCESS",
                    "branch": "main",
                    "commit_message": commit_message,
                    "tag_name": tag_name,
                    "integrity_summary": integrity.summary(),
                }
            sha = push_atomic_milestone_to_github(
                repo_name=repo_name,
                commit_message=commit_message,
                tag_name=tag_name,
                orphan_clean_history=False,
            )
            return {
                "action": "DIRECT_MAIN_PUSH_EXECUTED",
                "status": "SUCCESS",
                "branch": "main",
                "commit_sha": sha,
                "tag_name": tag_name,
                "integrity_summary": integrity.summary(),
            }

        # Fluxo 2: Tentativa nao autorizada de commit direto com arquivos da Fase 01 alterados
        if not authorize_fase01_pr:
            raise PermissionError(
                f"BLOQUEIO DE SEGURANCA GIT (Owner's Intent):\n"
                f"Foram detectadas alteracoes nao autorizadas em arquivos da Fase 01:\n"
                f"{integrity.summary()}\n"
                f"Para prosseguir, defina authorize_fase01_pr=True, new_fase01_version e change_justification."
            )

        # Fluxo 3: Alteracao da Fase 01 formalizada via Pull Request
        if not new_fase01_version or not change_justification:
            raise ValueError(
                "O fluxo de Pull Request da Fase 01 exige obrigatoriamente "
                "'new_fase01_version' (ex.: 'v1.2.1-fase01') e 'change_justification'."
            )

        pr_branch = f"pr/fase01-{new_fase01_version}"
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 1. Registra no CHANGELOG_FASE01.md se o arquivo existir
        changelog_entry = (
            f"\n\n## [{new_fase01_version}] — {date_str} (Pull Request de Manutencao)\n"
            f"- **Branch:** `{pr_branch}`\n"
            f"- **Justificativa Tecnica:** {change_justification}\n"
            f"- **Arquivos Afetados:**\n"
        )
        for mod in integrity.modified_files:
            det = integrity.details.get(mod, {})
            changelog_entry += (
                f"  - `{mod}`: hash anterior `{det.get('expected_sha256', '')[:12]}`, "
                f"novo hash `{det.get('actual_sha256', '')[:12]}`\n"
            )

        if not dry_run and self.changelog_path.exists():
            current_log = self.changelog_path.read_text(encoding="utf-8")
            self.changelog_path.write_text(current_log + changelog_entry, encoding="utf-8")

        # 2. Retorna payload estruturado ou executa PR no GitHub
        pr_title = f"Fase 01 ({new_fase01_version}): {change_justification[:70]}"
        pr_body = (
            f"### Pull Request de Manutencao Controlada da Fase 01\n\n"
            f"- **Versao Proposta:** `{new_fase01_version}`\n"
            f"- **Data:** {date_str}\n"
            f"- **Justificativa:** {change_justification}\n\n"
            f"#### Arquivos Modificados da Fase 01:\n"
            + "\n".join(f"- `{f}`" for f in integrity.modified_files)
        )

        pr_result: Dict[str, Any] = {
            "action": "PULL_REQUEST_WORKFLOW",
            "branch": pr_branch,
            "new_version": new_fase01_version,
            "justification": change_justification,
            "modified_files": integrity.modified_files,
            "pr_title": pr_title,
            "pr_body": pr_body,
            "dry_run": dry_run,
        }

        if dry_run:
            pr_result["status"] = "DRY_RUN_PR_PREPARED"
            return pr_result

        # Executa criacao da branch remota e chamada ao `gh pr create`
        token = get_gh_token()
        username = get_gh_username(token)
        full_name = f"{username}/{repo_name}"

        # Obtem SHA da HEAD de main
        ref_main = _github_api_request(token, "GET", f"/repos/{full_name}/git/ref/heads/main")
        main_sha = ref_main["object"]["sha"]

        # Cria commit real na branch de PR antes de abrir o Pull Request (1 commit ahead of main)
        files_for_pr = list(integrity.modified_files) + ["docs/CHANGELOG_FASE01.md"]
        commit_sha = self._commit_working_tree_to_branch(
            token=token,
            full_name=full_name,
            branch_name=pr_branch,
            parent_sha=main_sha,
            commit_message=pr_title,
            files_to_commit=files_for_pr,
        )
        pr_result["commit_sha"] = commit_sha

        # Invoca a API de Pull Request (/pulls)
        try:
            pr_data = _github_api_request(
                token,
                "POST",
                f"/repos/{full_name}/pulls",
                payload={"title": pr_title, "head": pr_branch, "base": "main", "body": pr_body},
            )
            pr_result["status"] = "PULL_REQUEST_CREATED"
            pr_result["pr_url"] = pr_data.get("html_url", "")
            pr_result["pr_number"] = pr_data.get("number")
        except urllib.error.HTTPError as e:
            pr_result["status"] = "BRANCH_CREATED_READY_FOR_PR"
            pr_result["error"] = str(e)

        return pr_result

    def _commit_working_tree_to_branch(
        self,
        token: str,
        full_name: str,
        branch_name: str,
        parent_sha: str,
        commit_message: str,
        files_to_commit: Optional[List[str]] = None,
    ) -> str:
        """
        Cria uma arvore Git e um commit na branch de PR antes de chamar a API de Pull Request.
        Garante que a branch tenha '1 commit ahead of main' real no GitHub.
        Ordem de operacoes da Git Data API:
        1. POST .../git/refs (cria branch remota se nao existir)
        2. POST .../git/trees (cria arvore com base_tree: parent_sha)
        3. POST .../git/commits (cria commit com pai parent_sha)
        4. PATCH .../git/refs/heads/{branch_name} (aponta a ref para o novo commit)
        """
        # 1. Cria a ref da branch a partir do parent_sha se nao existir
        try:
            _github_api_request(
                token,
                "POST",
                f"/repos/{full_name}/git/refs",
                payload={"ref": f"refs/heads/{branch_name}", "sha": parent_sha},
            )
        except urllib.error.HTTPError:
            pass

        # 2. Constrói os itens da árvore com base_tree: parent_sha
        target_files = list(files_to_commit) if files_to_commit else [p.relative_to(self.repo_root).as_posix() for p in collect_tracked_files(self.repo_root)]
        changelog_rel = "docs/CHANGELOG_FASE01.md"
        if changelog_rel not in target_files and (self.repo_root / changelog_rel).exists():
            target_files.append(changelog_rel)

        tree_items = []
        for rel_path in target_files:
            p = self.repo_root / rel_path
            if p.exists() and p.is_file():
                try:
                    content_str = p.read_text(encoding="utf-8")
                    tree_items.append({
                        "path": rel_path,
                        "mode": "100644",
                        "type": "blob",
                        "content": content_str,
                    })
                except UnicodeDecodeError:
                    content_b64 = base64.b64encode(p.read_bytes()).decode("ascii")
                    blob_resp = _github_api_request(
                        token,
                        "POST",
                        f"/repos/{full_name}/git/blobs",
                        payload={"content": content_b64, "encoding": "base64"},
                    )
                    tree_items.append({
                        "path": rel_path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_resp["sha"],
                    })

        tree_resp = _github_api_request(
            token,
            "POST",
            f"/repos/{full_name}/git/trees",
            payload={"base_tree": parent_sha, "tree": tree_items},
        )
        new_tree_sha = tree_resp.get("sha", "mock_tree_sha")

        # 3. Cria o objeto de commit
        commit_resp = _github_api_request(
            token,
            "POST",
            f"/repos/{full_name}/git/commits",
            payload={
                "message": commit_message,
                "tree": new_tree_sha,
                "parents": [parent_sha],
            },
        )
        new_commit_sha = commit_resp.get("sha", "mock_commit_sha")

        # 4. Atualiza a ref da branch para apontar para o novo commit
        _github_api_request(
            token,
            "PATCH",
            f"/repos/{full_name}/git/refs/heads/{branch_name}",
            payload={"sha": new_commit_sha, "force": True},
        )

        return new_commit_sha


if __name__ == "__main__":
    guard = Phase01BaselineGuard()
    if "--verify" in sys.argv:
        res = guard.verify_baseline_integrity()
        print(res.summary())
        sys.exit(0 if res.is_intact else 1)
    elif "--ensure-tag" in sys.argv:
        guard.ensure_github_baseline_tag()
    elif "--sync" in sys.argv:
        msg = sys.argv[sys.argv.index("--sync") + 1] if len(sys.argv) > sys.argv.index("--sync") + 1 else "Milestone v3.0.0-fase03: Conectores 6 Plataformas, Radar Diario e Emenda Diretora v2.2"
        tag = None
        if "--tag" in sys.argv and len(sys.argv) > sys.argv.index("--tag") + 1:
            tag = sys.argv[sys.argv.index("--tag") + 1]
        elif "fase03" in msg.lower():
            tag = "v3.0.0-fase03-inicial"
        else:
            tag = "v2.0.0-fase02-inicial"
        sync_res = guard.sync_repository_with_governance(commit_message=msg, tag_name=tag)
        print(json.dumps(sync_res, indent=2))
    else:
        res = guard.verify_baseline_integrity()
        print(res.summary())
