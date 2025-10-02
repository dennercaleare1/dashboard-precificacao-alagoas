#!/bin/bash

# Script para gerenciar o Dashboard de Precificação
# Uso: ./manage_dashboard.sh [start|stop|restart|status|logs]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/.venv"
DASHBOARD_FILE="$SCRIPT_DIR/dashboard_precificacao.py"
LOG_FILE="$SCRIPT_DIR/streamlit.log"
PID_FILE="$SCRIPT_DIR/streamlit.pid"
PORT=8520

case "$1" in
    start)
        echo "🚀 Iniciando Dashboard de Precificação..."
        cd "$SCRIPT_DIR"
        source "$VENV_PATH/bin/activate"
        
        # Verifica se já está rodando
        if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "⚠️  Dashboard já está rodando na porta $PORT"
            echo "🌐 Acesse: http://localhost:$PORT"
            exit 1
        fi
        
        # Inicia o servidor
        nohup streamlit run "$DASHBOARD_FILE" \
            --server.port $PORT \
            --server.headless true \
            --server.runOnSave true \
            --server.address localhost > "$LOG_FILE" 2>&1 &
        
        echo $! > "$PID_FILE"
        sleep 3
        
        if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "✅ Dashboard iniciado com sucesso!"
            echo "🌐 Acesse: http://localhost:$PORT"
            echo "📋 Logs: tail -f $LOG_FILE"
        else
            echo "❌ Erro ao iniciar o dashboard"
            rm -f "$PID_FILE"
            exit 1
        fi
        ;;
        
    stop)
        echo "🛑 Parando Dashboard de Precificação..."
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                kill $PID
                rm -f "$PID_FILE"
                echo "✅ Dashboard parado com sucesso"
            else
                echo "⚠️  Dashboard não estava rodando"
                rm -f "$PID_FILE"
            fi
        else
            echo "⚠️  Arquivo PID não encontrado"
            # Tenta parar qualquer processo streamlit na porta
            pkill -f "streamlit.*$PORT" && echo "✅ Processos streamlit finalizados"
        fi
        ;;
        
    restart)
        echo "🔄 Reiniciando Dashboard de Precificação..."
        $0 stop
        sleep 2
        $0 start
        ;;
        
    status)
        if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
            echo "✅ Dashboard está rodando (PID: $(cat "$PID_FILE"))"
            echo "🌐 URL: http://localhost:$PORT"
            echo "📊 Uso de memória: $(ps -p $(cat "$PID_FILE") -o rss= | awk '{print $1/1024 " MB"}')"
        else
            echo "❌ Dashboard não está rodando"
            [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
        fi
        ;;
        
    logs)
        echo "📋 Logs do Dashboard (Ctrl+C para sair):"
        tail -f "$LOG_FILE"
        ;;
        
    *)
        echo "🗺️  Dashboard de Precificação - Municípios de Alagoas"
        echo ""
        echo "Uso: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Comandos:"
        echo "  start   - Inicia o dashboard"
        echo "  stop    - Para o dashboard"
        echo "  restart - Reinicia o dashboard"
        echo "  status  - Verifica status do dashboard"
        echo "  logs    - Mostra logs em tempo real"
        echo ""
        echo "Exemplo: $0 start"
        exit 1
        ;;
esac