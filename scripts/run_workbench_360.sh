#!/usr/bin/env bash
# ==============================================================================
# Atalho Único (1-Click Launcher): Bancada Analítica DataSenado 360º
# Inicia simultaneamente o Backend Python REST e o Frontend React (Vite)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "======================================================================"
echo "🏛️  SENADO FEDERAL — INSTITUTO DE PESQUISA DATASENADO"
echo "📊  Bancada de Inteligência do Debate Público Digital 360º"
echo "======================================================================"

# 1. Garante chave criptográfica efêmera em RAM (Fail-Closed LGPD / ADR-002)
if [ -z "${LGPD_HMAC_SECRET_KEY:-}" ] || [ "${#LGPD_HMAC_SECRET_KEY}" -lt 32 ]; then
    echo "🔐 Gerando chave criptográfica HMAC efêmera em memória RAM para a sessão..."
    export LGPD_HMAC_SECRET_KEY="$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)"
fi

BACKEND_PORT=8765
FRONTEND_PORT=3000

# Função de limpeza na saída
cleanup() {
    echo ""
    echo "🛑 Encerrando a Bancada Analítica DataSenado de forma segura..."
    if [ -n "${BACKEND_PID:-}" ] && kill -0 "${BACKEND_PID}" 2>/dev/null; then
        kill "${BACKEND_PID}" 2>/dev/null || true
    fi
    if [ -n "${FRONTEND_PID:-}" ] && kill -0 "${FRONTEND_PID}" 2>/dev/null; then
        kill "${FRONTEND_PID}" 2>/dev/null || true
    fi
    echo "✅ Processos finalizados. Memória RAM limpa (Zero-Footprint estrito)."
}
trap cleanup EXIT INT TERM

# 2. Inicia o Servidor REST Local Python em background
echo "🚀 [1/3] Iniciando Servidor REST Local (porta ${BACKEND_PORT})..."
UV_BIN="${HOME}/.local/bin/uv"
if [ ! -x "${UV_BIN}" ]; then
    UV_BIN="uv"
fi

"${UV_BIN}" run python -m src.ui.local_workbench_server --port "${BACKEND_PORT}" &
BACKEND_PID=$!

# 3. Aguarda o Backend responder ao healthcheck
echo "⏳ [2/3] Aguardando inicialização do motor analítico..."
MAX_WAIT=20
WAIT_COUNT=0
HEALTH_URL="http://127.0.0.1:${BACKEND_PORT}/api/health"

until curl -s -f "${HEALTH_URL}" > /dev/null 2>&1; do
    sleep 0.5
    WAIT_COUNT=$((WAIT_COUNT + 1))
    if [ "${WAIT_COUNT}" -ge "${MAX_WAIT}" ]; then
        echo "❌ Tempo limite excedido aguardando o Backend Python."
        exit 1
    fi
done
echo "✅ Backend Python ativo e pronto para consultas!"

# 4. Inicia o Frontend React (Vite)
echo "🌐 [3/3] Iniciando Frontend React (porta ${FRONTEND_PORT})..."
cd "${REPO_ROOT}/datasenado-bancada-360"

# Se dependências não estiverem instaladas, instala rapidamente
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando pacotes do front-end via npm..."
    npm install --silent
fi

npm run dev -- --port "${FRONTEND_PORT}" &
FRONTEND_PID=$!

sleep 1.5

# Abre o navegador no macOS se interativo
if [ -t 0 ] || [ -n "${TERM:-}" ]; then
    if command -v open > /dev/null 2>&1; then
        echo "🖥️  Abrindo a Bancada Analítica no seu navegador padrão: http://localhost:${FRONTEND_PORT}"
        open "http://localhost:${FRONTEND_PORT}" || true
    fi
fi

echo "======================================================================"
echo "✨ BANCADA ANALÍTICA DATASENADO OPERACIONAL!"
echo "   • Frontend: http://localhost:${FRONTEND_PORT}"
echo "   • API REST: http://localhost:${BACKEND_PORT}/api/health"
echo "   Pressione Ctrl+C para encerrar todos os serviços."
echo "======================================================================"

# Mantém o script aguardando término dos processos
wait "${FRONTEND_PID}" || true
