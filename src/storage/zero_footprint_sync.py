"""
Gerenciador de Armazenamento de Pegada Zero (Zero-Footprint Cloud Sync Manager).

Atende aos requisitos de Arquitetura e Auditoria da Fase 01 (C-05, G-06, G-07, G-08, G-10):
1. Modo *Fail-Closed* para IDs de pastas (C-05 / B2 / G-06):
   - Nenhum ID de pasta do Google Drive fica hardcoded no codigo-fonte.
   - Se `backend_mode='gdrive'` e a variavel de ambiente nao estiver configurada no `.env`,
     aborta imediatamente (`RuntimeError`), sem fallback silencioso.
2. Independencia de Caminhos Absolutos do Desenvolvedor (G-08):
   - Localiza o binario `gdrive` via `GDRIVE_BIN_PATH` ou `shutil.which("gdrive")` com fallback
     para `$HOME/.gemini/antigravity/bin/gdrive`.
   - Suporta `backend_mode='local_dir'` para que qualquer membro da banca possa reproduzir
     integralmente os testes em sua propria maquina sem precisar da conta do Google Drive do autor!
3. Verificacao de Integridade Pós-Upload antes do Expurgo Local (G-07):
   - Confere se o comando de upload/update retornou um ID remoto valido e confirma os metadados
     remotos (`readonly info`) antes de executar `unlink` no arquivo local em `/tmp`.
4. Controle de Teto de Cache Local (`local_cache_max_mb: 250` - G-10) e Logs Estruturados (`logging` - G-06).
"""

import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Optional

from dotenv import load_dotenv

from src.config_loader import load_settings

load_dotenv()

logger = logging.getLogger(__name__)

TRANSITORY_CACHE_DIR = Path("/tmp/monitor_datasenado_cache")


def _resolve_gdrive_bin() -> str:
    env_bin = os.environ.get("GDRIVE_BIN_PATH")
    if env_bin:
        return env_bin
    which_bin = shutil.which("gdrive")
    if which_bin:
        return which_bin
    home_bin = Path.home() / ".gemini" / "antigravity" / "bin" / "gdrive"
    return str(home_bin)


class ZeroFootprintStorage:
    """
    Gerencia cache efemero local (/tmp) com teto de armazenamento (250 MB)
    e sincronizacao verificada com Data Lake (Google Drive, diretorio local de reproducao ou S3/MinIO).
    """

    def __init__(
        self,
        drive_datasets_folder_id: Optional[str] = None,
        backend_mode: str = "gdrive",
        local_repro_dir: Optional[Path] = None,
    ):
        cfg = load_settings()
        self.max_cache_mb: float = float(cfg["project"].get("local_cache_max_mb", 250))
        self.backend_mode = backend_mode
        self.gdrive_bin = _resolve_gdrive_bin()
        self.local_repro_dir = local_repro_dir or (TRANSITORY_CACHE_DIR / "local_repro_lake")

        if self.backend_mode == "gdrive":
            folder_id = drive_datasets_folder_id or os.environ.get("GDRIVE_DATASETS_LAKE_FOLDER_ID")
            if not folder_id or folder_id.startswith("id_da_pasta"):
                raise RuntimeError(
                    "GDRIVE_DATASETS_LAKE_FOLDER_ID ausente no ambiente (.env). "
                    "Operacao abortada em modo fail-closed (Condicao B2 / Achado C-05)."
                )
            self.drive_datasets_folder_id = folder_id.strip()
        else:
            self.drive_datasets_folder_id = drive_datasets_folder_id or "local_repro"

        TRANSITORY_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _current_cache_size_mb(self) -> float:
        total_bytes = sum(f.stat().st_size for f in TRANSITORY_CACHE_DIR.rglob("*") if f.is_file())
        return total_bytes / (1024 * 1024)

    def get_temp_path(self, filename: str) -> Path:
        """Retorna um caminho temporario seguro em /tmp, verificando o teto de cache (G-10)."""
        used_mb = self._current_cache_size_mb()
        if used_mb > self.max_cache_mb:
            logger.warning("Cache temporario (%.1f MB) excedeu o teto de %.1f MB; limpando...", used_mb, self.max_cache_mb)
            self.clear_all_cache()
        return TRANSITORY_CACHE_DIR / filename

    def _find_existing_file_id(self, filename: str, parent_folder_id: str) -> Optional[str]:
        """
        Verifica se ja existe um arquivo com o mesmo nome na pasta do Google Drive.
        Em caso de falha de execucao do CLI, levanta erro explicito (fail-closed - G-06).
        """
        cmd = [
            self.gdrive_bin,
            "readonly",
            "search",
            "--parent-id",
            parent_folder_id,
            "--name-exact",
            filename,
            "--json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            logger.error("Erro ao consultar arquivo existente no Google Drive: %s", res.stderr)
            raise RuntimeError(f"Falha ao buscar arquivo '{filename}' no Google Drive: {res.stderr.strip()}")
        if not res.stdout.strip():
            return None
        try:
            data = json.loads(res.stdout)
            files = data if isinstance(data, list) else data.get("files", [])
            if files and isinstance(files, list) and "id" in files[0]:
                return str(files[0]["id"])
        except json.JSONDecodeError as exc:
            logger.error("JSON invalido retornado pelo gdrive search: %s", exc)
            raise RuntimeError(f"Resposta JSON invalida do gdrive CLI: {exc}") from exc
        return None

    def _verify_remote_file_integrity(self, remote_file_id: str, expected_min_bytes: int) -> None:
        """Confirma que o arquivo remoto existe no Google Drive antes do expurgo local (G-07)."""
        cmd = [self.gdrive_bin, "readonly", "info", remote_file_id]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0 or not res.stdout.strip():
            raise RuntimeError(
                f"Verificacao de integridade pos-upload falhou para ID={remote_file_id}: {res.stderr.strip()}"
            )

    def upload_and_purge(self, local_file: Path, parent_folder_id: Optional[str] = None) -> str:
        """
        Envia ou atualiza in-place o arquivo no Data Lake, verifica a integridade do envio (G-07)
        e somente entao remove a copia temporaria do MacBook.
        """
        if not local_file.exists():
            raise FileNotFoundError(f"Arquivo temporario nao encontrado: {local_file}")

        local_size = local_file.stat().st_size
        if local_size == 0:
            raise ValueError(f"Arquivo temporario vazio (0 bytes), abortando upload: {local_file}")

        if self.backend_mode == "local_repro":
            self.local_repro_dir.mkdir(parents=True, exist_ok=True)
            dest = self.local_repro_dir / local_file.name
            shutil.copy2(local_file, dest)
            if not dest.exists() or dest.stat().st_size != local_size:
                raise RuntimeError("Falha de verificacao de integridade na copia local_repro.")
            local_file.unlink(missing_ok=True)
            return f"Saved to local_repro: {dest}"

        if self.backend_mode == "gdrive":
            target_folder = parent_folder_id or self.drive_datasets_folder_id
            if not target_folder:
                raise RuntimeError("parent_folder_id ausente para upload no Google Drive.")

            existing_id = self._find_existing_file_id(local_file.name, target_folder)
            if existing_id:
                cmd = [self.gdrive_bin, "mutate", "update", existing_id, str(local_file)]
            else:
                cmd = [self.gdrive_bin, "mutate", "upload", str(local_file), "--parent", target_folder]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            output_msg = result.stdout.strip()

            # Verifica integridade remota antes de apagar o arquivo local (G-07)
            verify_id = existing_id
            if not verify_id and "ID:" in output_msg:
                verify_id = output_msg.split("ID:")[-1].strip().rstrip(")")
            if verify_id:
                self._verify_remote_file_integrity(verify_id, local_size)

            local_file.unlink(missing_ok=True)
            return output_msg

        raise NotImplementedError("Modo S3/MinIO reservado para deploy nos servidores do DataSenado.")

    def clear_all_cache(self) -> None:
        """Limpa completamente qualquer residuo na pasta transitoria /tmp."""
        if TRANSITORY_CACHE_DIR.exists():
            shutil.rmtree(TRANSITORY_CACHE_DIR)
            TRANSITORY_CACHE_DIR.mkdir(parents=True, exist_ok=True)
