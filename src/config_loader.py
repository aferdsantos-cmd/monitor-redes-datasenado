"""
Carregador Central e Validador de Configuracao (`config/settings.yaml`).

Resolve o achado G-01 da Auditoria Cientifica:
- Garante que todos os modulos do sistema (`lgpd_and_bot_filter`, `opinion_inference_engine`,
  `stratified_sampler` e `pilot_audit_runner`) leiam seus parametros diretamente do arquivo
  `config/settings.yaml`, sem valores duplicados ou decorativos.
- Utiliza caminhos relativos ao repositorio (`Path(__file__).resolve().parents[1]`),
  eliminando caminhos absolutos da maquina do desenvolvedor (G-08).
"""

from pathlib import Path
from typing import Any, Dict, Optional
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SETTINGS_PATH = REPO_ROOT / "config" / "settings.yaml"


def load_settings(custom_path: Optional[Path] = None) -> Dict[str, Any]:
    """Carrega e valida a estrutura obrigatoria do arquivo `config/settings.yaml`."""
    target_path = Path(custom_path) if custom_path else DEFAULT_SETTINGS_PATH
    if not target_path.exists():
        raise FileNotFoundError(f"Arquivo de configuracao central nao encontrado: {target_path}")

    with target_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError("O arquivo settings.yaml deve conter um mapeamento YAML valido na raiz.")

    required_sections = [
        "project",
        "statistical_parameters",
        "cib_and_bot_detection",
        "platform_reference_weights_brazil",
        "ibge_macroregion_weights_brazil",
    ]
    for sec in required_sections:
        if sec not in data:
            raise KeyError(f"Secao obrigatoria ausente no settings.yaml: '{sec}'")

    return data
