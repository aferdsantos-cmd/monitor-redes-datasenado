#!/usr/bin/env bash
# ==============================================================================
# Atalho Único (1-Click Launcher): Bancada Analítica DataSenado 360º
# Inicia simultaneamente o Backend Python REST e o Frontend React (Vite)
# ==============================================================================
set -euo pipefail

# Garante caminhos de binários essenciais no macOS (inclusive para sessões .command do Finder)
export PATH="${HOME}/.local/bin:${HOME}/.local/opt/node-v22.14.0-darwin-arm64/bin:/opt/homebrew/bin:/usr/local/bin:${PATH}"

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

# 2. Localiza ou configura o executor Python (uv)
UV_BIN="${HOME}/.local/bin/uv"
if [ ! -x "${UV_BIN}" ]; then
    UV_BIN="$(command -v uv 2>/dev/null || echo "uv")"
fi

# 3. Localiza ou instala automaticamente o ambiente Node.js / npm
NPM_BIN="$(command -v npm 2>/dev/null || true)"
if [ -z "${NPM_BIN}" ] && [ -x "${HOME}/.local/bin/npm" ]; then
    NPM_BIN="${HOME}/.local/bin/npm"
elif [ -z "${NPM_BIN}" ] && [ -x "${HOME}/.local/opt/node-v22.14.0-darwin-arm64/bin/npm" ]; then
    NPM_BIN="${HOME}/.local/opt/node-v22.14.0-darwin-arm64/bin/npm"
fi

if [ -z "${NPM_BIN}" ]; then
    echo "⚡ Node.js não detectado no sistema. Baixando versão standalone segura (v22 LTS)..."
    mkdir -p "${HOME}/.local/opt" "${HOME}/.local/bin"
    curl -fsSL https://nodejs.org/dist/v22.14.0/node-v22.14.0-darwin-arm64.tar.gz | tar -xz -C "${HOME}/.local/opt/"
    ln -sf "${HOME}/.local/opt/node-v22.14.0-darwin-arm64/bin/node" "${HOME}/.local/bin/node"
    ln -sf "${HOME}/.local/opt/node-v22.14.0-darwin-arm64/bin/npm" "${HOME}/.local/bin/npm"
    ln -sf "${HOME}/.local/opt/node-v22.14.0-darwin-arm64/bin/npx" "${HOME}/.local/bin/npx"
    NPM_BIN="${HOME}/.local/bin/npm"
    echo "✅ Node.js v22 LTS configurado com sucesso!"
fi

# 4. Inicia o Servidor REST Local Python em background
echo "🚀 [1/3] Iniciando Servidor REST Local (porta ${BACKEND_PORT})..."
"${UV_BIN}" run python -m src.ui.local_workbench_server --port "${BACKEND_PORT}" &
BACKEND_PID=$!

# 5. Aguarda o Backend responder ao healthcheck
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

# 6. Inicia o Frontend React (Vite)
echo "🌐 [3/3] Iniciando Frontend React (porta ${FRONTEND_PORT})..."
cd "${REPO_ROOT}/datasenado-bancada-360"

# Se dependências não estiverem instaladas, instala rapidamente
if [ ! -d "node_modules" ]; then
    echo "📦 Instalando pacotes do front-end via npm..."
    "${NPM_BIN}" install --silent
fi

"${NPM_BIN}" run dev -- --port "${FRONTEND_PORT}" &
FRONTEND_PID=$!

sleep 1.5

# Abre o navegador no macOS
if command -v open > /dev/null 2>&1; then
    echo "🖥️  Abrindo a Bancada Analítica no seu navegador padrão: http://localhost:${FRONTEND_PORT}"
    open "http://localhost:${FRONTEND_PORT}" || true
fi

echo "======================================================================"
echo "✨ BANCADA ANALÍTICA DATASENADO OPERACIONAL!"
echo "   • Frontend: http://localhost:${FRONTEND_PORT}"
echo "   • API REST: http://localhost:${BACKEND_PORT}/api/health"
echo "   Pressione Ctrl+C para encerrar todos os serviços."
echo "======================================================================"

# Mantém o script aguardando término dos processos
wait "${FRONTEND_PID}" || true
