"""
Servidor HTTP/REST Local Zero-Footprint para a Bancada Analítica DataSenado.
Permite integração direta e reativa entre o Front-End React e o motor analítico Python.

Atende integralmente ao Pilar 1 da OS-Fase05-v3:
- Porta padrão: 127.0.0.1:8765
- CORS liberado para o proxy Vite (/api) e requisições diretas de bancada
- Endpoints REST:
    GET  /api/health
    GET  /api/themes
    GET  /api/themes/<theme_id>
    POST /api/themes/register
    POST /api/themes/<theme_id>/lifecycle/advance
    POST /api/themes/<theme_id>/medallion/manipulate
    POST /api/themes/<theme_id>/human-validation/submit
    POST /api/sandbox/step-by-step
    GET  /api/radar
    GET  /api/reports/<theme_id>/docx
- Zero-Footprint: Opera 100% em memória volátil sem gravar arquivos em disco
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import secrets
import sys
import threading
from typing import Any, Dict, Optional
import urllib.parse
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler

# Garante chave efêmera em memória caso ausente no ambiente
if not os.environ.get("LGPD_HMAC_SECRET_KEY") or len(os.environ.get("LGPD_HMAC_SECRET_KEY", "").strip()) < 32:
    os.environ["LGPD_HMAC_SECRET_KEY"] = secrets.token_hex(32)

from src.ui.workbench_api_and_contracts import (
    DataSenadoWorkbenchBackendBridge,
    MonitoringLifecycleStateMachine,
    HumanGateStatus,
)


class WorkbenchAPIRequestHandler(BaseHTTPRequestHandler):
    """Handler HTTP com suporte a JSON REST e CORS para a Bancada Analítica."""

    bridge: Optional[DataSenadoWorkbenchBackendBridge] = None

    def log_message(self, format: str, *args: Any) -> None:
        """Suprime logs excessivos para manter stdout limpo e seguro contra vazamento de PII."""
        # Não registra texto das requisições em terminal (Zero-Footprint e AppSec)
        pass

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def _send_error_json(self, message: str, status: int = 400, details: Optional[Dict[str, Any]] = None) -> None:
        err = {"error": message, "status": "ERROR"}
        if details:
            err["details"] = details
        self._send_json(err, status=status)

    def do_OPTIONS(self) -> None:
        """Trata requisições preflight CORS."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _get_bridge(self) -> DataSenadoWorkbenchBackendBridge:
        if self.bridge is None:
            self.__class__.bridge = DataSenadoWorkbenchBackendBridge()
        return self.bridge

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"Payload JSON inválido: {e}")

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed_url.query)
        bridge = self._get_bridge()

        try:
            # 1. Healthcheck
            if path in ["/api/health", "/health"]:
                themes = ["eleicao_presidencia_senado", "pec_escala_6x1", "pl_ia_2338"]
                from src.collectors.base_collector import _CUSTOM_THEMES_REGISTRY
                for ct in _CUSTOM_THEMES_REGISTRY:
                    if isinstance(ct, dict) and "id" in ct:
                        themes.append(ct["id"])

                self._send_json({
                    "status": "UP",
                    "server": "DataSenado Local Workbench REST API",
                    "version": "v5.1.0-fase05-v3",
                    "zero_footprint": True,
                    "fail_closed_hmac": True,
                    "port": getattr(self.server, "server_port", 8765),
                    "server_time_utc": datetime.now(timezone.utc).isoformat(),
                    "themes": sorted(list(set(themes))),
                })
                return

            # 2. Listagem de Temas
            if path == "/api/themes":
                themes_summary = [
                    {"id": "eleicao_presidencia_senado", "title": "Eleição da Presidência e Mesa do Senado 2026", "committee": "Mesa Diretora"},
                    {"id": "pec_escala_6x1", "title": "PEC da Redução da Jornada de Trabalho (Escala 6x1)", "committee": "CCJ"},
                    {"id": "pl_ia_2338", "title": "Marco Regulatório da Inteligência Artificial (PL 2338/2023)", "committee": "CCT"},
                ]
                from src.collectors.base_collector import _CUSTOM_THEMES_REGISTRY
                for ct in _CUSTOM_THEMES_REGISTRY:
                    if isinstance(ct, dict) and "id" in ct:
                        themes_summary.append({
                            "id": ct["id"],
                            "title": ct.get("title") or ct.get("name") or ct["id"],
                            "committee": ct.get("committee") or ct.get("senate_committee") or "CAS",
                        })
                self._send_json({"themes": themes_summary, "total": len(themes_summary)})
                return

            # 3. Radar Legislativo Diário
            if path == "/api/radar":
                window_days = 1
                if "window_days" in query:
                    try:
                        window_days = int(query["window_days"][0])
                    except ValueError:
                        window_days = 1
                radar_data = bridge.get_daily_legislative_radar_payload(window_days=window_days)
                self._send_json(radar_data)
                return

            # 4. Exportação Word .docx
            match_docx = re.match(r"^/api/reports/([a-zA-Z0-9_-]+)/docx$", path)
            if match_docx:
                theme_id = match_docx.group(1)
                docx_buffer = bridge.generate_executive_docx_report(theme_id)
                docx_bytes = docx_buffer.getvalue()
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                self.send_header("Content-Disposition", f'attachment; filename="Dossie_DataSenado_{theme_id}.docx"')
                self.send_header("Content-Length", str(len(docx_bytes)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(docx_bytes)
                return

            # 5. Dossiê Completo de um Tema (ThemeDataset)
            match_theme = re.match(r"^/api/themes/([a-zA-Z0-9_-]+)$", path)
            if match_theme:
                theme_id = match_theme.group(1)
                window = query.get("window", ["7d"])[0]
                target_n = None
                if "n" in query:
                    try:
                        target_n = int(query["n"][0])
                    except ValueError:
                        target_n = None

                platforms = None
                if "platforms" in query:
                    platforms = [p.strip() for p in query["platforms"][0].split(",") if p.strip()]

                dataset = bridge.build_complete_frontend_theme_dataset(
                    theme_id=theme_id,
                    window_spec=window,
                    target_n=target_n,
                    selected_platforms=platforms,
                )
                self._send_json(dataset)
                return

            # Rota não encontrada
            self._send_error_json(f"Endpoint GET não encontrado: {path}", status=404)

        except ValueError as ve:
            self._send_error_json(str(ve), status=400)
        except Exception as e:
            self._send_error_json(f"Erro interno no servidor: {e}", status=500)

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path.rstrip("/")
        bridge = self._get_bridge()

        try:
            body = self._read_json_body()

            # 1. Registro de Novo Tema
            if path == "/api/themes/register":
                res = bridge.register_custom_theme(body)
                self._send_json(res, status=201)
                return

            # 2. Avanço de Ciclo de Vida do Tema
            match_advance = re.match(r"^/api/themes/([a-zA-Z0-9_-]+)/lifecycle/advance$", path)
            if match_advance:
                theme_id = match_advance.group(1)
                target_state = body.get("target_state")
                simulate_contingency = bool(body.get("simulate_contingency", False))
                enforce_gates = bool(body.get("enforce_human_gates", True))
                res = bridge.lifecycle_manager.advance_or_run_monitoring_lifecycle(
                    theme_id=theme_id,
                    target_state=target_state,
                    simulate_contingency=simulate_contingency,
                    enforce_human_gates=enforce_gates,
                )
                self._send_json(res)
                return

            # 3. Manipulação de Camadas Medallion (Bronze, Silver, Gold) & Aprovação de Portão
            match_manipulate = re.match(r"^/api/themes/([a-zA-Z0-9_-]+)/medallion/manipulate$", path)
            if match_manipulate:
                theme_id = match_manipulate.group(1)
                action = body.get("action")
                if not action:
                    raise ValueError("O campo 'action' é obrigatório para manipulação Medallion.")
                res = bridge.manipulate_medallion_layer(
                    theme_id=theme_id,
                    action=action,
                    params=body.get("params") or body,
                )
                self._send_json(res)
                return

            # 4. Submissão de Validação Humana às Cegas
            match_human_val = re.match(r"^/api/themes/([a-zA-Z0-9_-]+)/human-validation/submit$", path)
            if match_human_val:
                theme_id = match_human_val.group(1)
                rec_id = body.get("record_id")
                human_stance = body.get("human_stance")
                if not rec_id or not human_stance:
                    raise ValueError("Campos 'record_id' e 'human_stance' são obrigatórios.")
                res = bridge.submit_blind_human_validation(
                    theme_id=theme_id,
                    record_id=rec_id,
                    human_stance=human_stance,
                )
                self._send_json(res)
                return

            # 5. Simulador Passo a Passo (Sandbox)
            if path == "/api/sandbox/step-by-step":
                text = body.get("text")
                platform = body.get("platform", "x_twitter")
                uf = body.get("uf", "SP")
                theme_id = body.get("theme_id", "pl_ia_2338")
                res = bridge.run_sandbox_step_by_step(
                    text=text,
                    platform=platform,
                    uf=uf,
                    theme_id=theme_id,
                )
                self._send_json(res)
                return

            # Rota não encontrada
            self._send_error_json(f"Endpoint POST não encontrado: {path}", status=404)

        except ValueError as ve:
            self._send_error_json(str(ve), status=400)
        except Exception as e:
            self._send_error_json(f"Erro interno no processamento: {e}", status=500)


class LocalWorkbenchServer:
    """Gerenciador do servidor HTTP REST local com ciclo de vida seguro."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765) -> None:
        self.host = host
        self.port = port
        self.httpd: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self, daemon: bool = True) -> None:
        """Inicia o servidor HTTP em background."""
        self.httpd = ThreadingHTTPServer((self.host, self.port), WorkbenchAPIRequestHandler)
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=daemon)
        self._thread.start()

    def stop(self) -> None:
        """Encerra o servidor e libera o socket."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
            self._thread = None

    def __enter__(self) -> LocalWorkbenchServer:
        self.start(daemon=True)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor REST Local DataSenado Bancada 360")
    parser.add_argument("--host", default="127.0.0.1", help="Endereço de escuta (padrão 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Porta TCP do servidor (padrão 8765)")
    args = parser.parse_args()

    print(f"Iniciando Servidor REST Local DataSenado em http://{args.host}:{args.port}")
    server = LocalWorkbenchServer(host=args.host, port=args.port)
    server.start(daemon=False)


if __name__ == "__main__":
    main()
