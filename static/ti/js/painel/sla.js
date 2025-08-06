// SLA & Métricas - JavaScript

let graficoSemanalInstance;
let graficoStatusInstance;
let slaConfiguracoes = {}; // Armazenar configurações SLA

// Função para formatar tempo de forma legível
function formatarTempo(horas) {
    if (horas === null || horas === undefined || isNaN(horas)) {
        return 'N/A';
    }
    
    // Se for menor que 1 hora, mostrar em minutos
    if (horas < 1) {
        const minutos = Math.round(horas * 60);
        return minutos <= 0 ? '< 1 min' : `${minutos} min`;
    }
    
    // Se for menor que 24 horas, mostrar em horas com 1 decimal se necessário
    if (horas < 24) {
        return horas % 1 === 0 ? `${Math.round(horas)}h` : `${horas.toFixed(1)}h`;
    }
    
    // Se for maior que 24 horas, mostrar em dias e horas
    const dias = Math.floor(horas / 24);
    const horasRestantes = horas % 24;
    
    if (horasRestantes < 1) {
        // Se as horas restantes são menos de 1 hora, não mostrar
        return dias === 1 ? '1 dia' : `${dias} dias`;
    } else {
        // Arredondar as horas restantes
        const horasArredondadas = Math.round(horasRestantes);
        if (dias === 1) {
            return horasArredondadas === 1 ? '1 dia 1h' : `1 dia ${horasArredondadas}h`;
        } else {
            return horasArredondadas === 1 ? `${dias} dias 1h` : `${dias} dias ${horasArredondadas}h`;
        }
    }
}

// Função para formatar percentual
function formatarPercentual(valor) {
    if (valor === null || valor === undefined || isNaN(valor)) {
        return '0%';
    }
    
    // Arredondar para 1 casa decimal se necessário
    if (valor % 1 === 0) {
        return `${Math.round(valor)}%`;
    } else {
        return `${valor.toFixed(1)}%`;
    }
}

// Carregar dados SLA
function carregarSLA() {
    carregarConfiguracoesSLA(); // Carregar configurações primeiro
    carregarMetricasSLA();
    carregarGraficoSemanal();
    carregarChamadosDetalhados();
    
    // Atualizar a cada 2 minutos
    setInterval(() => {
        carregarMetricasSLA();
        carregarChamadosDetalhados();
    }, 120000);
}

// Carregar métricas gerais de SLA
function carregarMetricasSLA() {
    fetch('/ti/painel/api/sla/metricas')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            const metricas = data.metricas_gerais;
            
            // Atualizar cards de métricas principais com formatação melhorada
            const elementos = {
                'totalChamados': metricas.total_chamados,
                'chamadosAbertos': metricas.chamados_abertos,
                'tempoMedioResposta': formatarTempo(metricas.tempo_medio_resposta),
                'tempoMedioResolucao': formatarTempo(metricas.tempo_medio_resolucao),
                'slaPercentual': formatarPercentual(metricas.sla_cumprimento),
                'slaViolacoes': metricas.sla_violacoes,
                'chamadosRisco': metricas.chamados_risco
            };
            
            // Atualizar elementos com verificação de existência
            Object.entries(elementos).forEach(([id, valor]) => {
                const elemento = document.getElementById(id);
                if (elemento) {
                    elemento.textContent = valor;
                }
            });
            
            // Atualizar indicadores visuais com cores
            atualizarIndicadorSLA('slaPercentual', metricas.sla_cumprimento);
            atualizarIndicadorSLA('slaViolacoes', metricas.sla_violacoes, true);
            atualizarIndicadorSLA('chamadosRisco', metricas.chamados_risco, true);
            
            console.log('Métricas SLA atualizadas:', metricas);
        })
        .catch(error => {
            console.error('Erro ao carregar métricas SLA:', error);
            mostrarToast('Erro ao carregar métricas SLA', 'error');
        });
}

// Atualizar indicadores visuais com cores baseadas no desempenho
function atualizarIndicadorSLA(elementId, valor, isNegativo = false) {
    const elemento = document.getElementById(elementId);
    if (!elemento) return;
    
    const card = elemento.closest('.card');
    if (!card) return;
    
    // Remover classes anteriores
    card.classList.remove('bg-success', 'bg-warning', 'bg-danger', 'bg-info', 'bg-secondary');
    
    if (elementId === 'slaPercentual') {
        if (valor >= 95) {
            card.classList.add('bg-success');
        } else if (valor >= 80) {
            card.classList.add('bg-warning');
        } else {
            card.classList.add('bg-danger');
        }
    } else if (isNegativo) {
        if (valor === 0) {
            card.classList.add('bg-success');
        } else if (valor <= 5) {
            card.classList.add('bg-warning');
        } else {
            card.classList.add('bg-danger');
        }
    }
}

// Carregar configurações SLA com tratamento robusto de erros
function carregarConfiguracoesSLA(forcarRecarregamento = false) {
    // Adicionar timestamp para evitar cache quando forçar recarregamento
    const url = forcarRecarregamento ?
        `/ti/painel/api/configuracoes?t=${Date.now()}` :
        '/ti/painel/api/configuracoes';

    console.log('Carregando configurações SLA...', forcarRecarregamento ? '(forçado)' : '');

    fetch(url)
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers.get('content-type'));
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Verificar se a resposta é JSON válido
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Resposta não é JSON válido - recebido: ' + contentType);
            }
            
            return response.json();
        })
        .then(data => {
            console.log('Dados recebidos:', data);
            
            // Verificar se a seção SLA existe
            if (!data || typeof data !== 'object') {
                throw new Error('Dados de configuração inválidos');
            }
            
            if (!data.sla) {
                console.warn('Seção SLA não encontrada, usando configurações padrão');
                data.sla = {
                    primeira_resposta: 4,
                    resolucao_critico: 2,
                    resolucao_alto: 8,
                    resolucao_normal: 24,
                    resolucao_baixo: 72
                };
            }
            
            slaConfiguracoes = data.sla; // Armazenar configurações globalmente
            
            // Atualizar badges de configuração com verificação de existência
            const configElements = {
                'configPrimeiraResposta': slaConfiguracoes.primeira_resposta || 4,
                'configResolucao': slaConfiguracoes.resolucao_normal || 24,
                'configCritico': slaConfiguracoes.resolucao_critico || 2,
                'configAlto': slaConfiguracoes.resolucao_alto || 8,
                'configNormal': slaConfiguracoes.resolucao_normal || 24,
                'configBaixo': slaConfiguracoes.resolucao_baixo || 72
            };
            
            Object.entries(configElements).forEach(([elementId, value]) => {
                const element = document.getElementById(elementId);
                if (element) {
                    element.textContent = formatarTempo(value);
                } else {
                    console.warn(`Elemento ${elementId} não encontrado`);
                }
            });
            
            console.log('Configurações SLA carregadas:', slaConfiguracoes);
        })
        .catch(error => {
            console.error('Erro ao carregar configurações SLA:', error);
            
            // Usar configurações padrão em caso de erro
            slaConfiguracoes = {
                primeira_resposta: 4,
                resolucao_critico: 2,
                resolucao_alto: 8,
                resolucao_normal: 24,
                resolucao_baixo: 72
            };
            
            // Atualizar com valores padrão
            const configElements = {
                'configPrimeiraResposta': 4,
                'configResolucao': 24,
                'configCritico': 2,
                'configAlto': 8,
                'configNormal': 24,
                'configBaixo': 72
            };
            
            Object.entries(configElements).forEach(([elementId, value]) => {
                const element = document.getElementById(elementId);
                if (element) {
                    element.textContent = formatarTempo(value);
                }
            });
            
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showWarning(
                    'Configurações SLA', 
                    'Erro ao carregar configurações. Usando valores padrão.'
                );
            }
        });
}

// Função para obter limite SLA baseado na prioridade
function obterLimiteSLAPorPrioridade(prioridade) {
    if (!slaConfiguracoes || Object.keys(slaConfiguracoes).length === 0) {
        // Valores padrão caso as configurações não tenham sido carregadas
        const padroes = {
            'Crítica': 2,
            'Crítico': 2,
            'Alta': 8,
            'Alto': 8,
            'Normal': 24,
            'Baixa': 72,
            'Baixo': 72
        };
        return padroes[prioridade] || 24;
    }
    
    // Mapear prioridades para configurações SLA
    const mapeamentoPrioridades = {
        'Crítica': slaConfiguracoes.resolucao_critico || 2,
        'Crítico': slaConfiguracoes.resolucao_critico || 2,
        'Alta': slaConfiguracoes.resolucao_alto || 8,
        'Alto': slaConfiguracoes.resolucao_alto || 8,
        'Normal': slaConfiguracoes.resolucao_normal || 24,
        'Baixa': slaConfiguracoes.resolucao_baixo || 72,
        'Baixo': slaConfiguracoes.resolucao_baixo || 72
    };
    
    return mapeamentoPrioridades[prioridade] || slaConfiguracoes.resolucao_normal || 24;
}

// Carregar gráfico semanal
function carregarGraficoSemanal() {
    fetch('/ti/painel/api/sla/grafico-semanal')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            criarGraficoSemanal(data.grafico_semanal);
            criarGraficoDistribuicaoStatus(data.distribuicao_status);
        })
        .catch(error => {
            console.error('Erro ao carregar gráfico semanal:', error);
            mostrarToast('Erro ao carregar gráficos', 'error');
        });
}

// Criar gráfico de chamados por dia
function criarGraficoSemanal(dados) {
    const ctx = document.getElementById('chartSemanal');
    if (!ctx) return;
    
    // Destruir gráfico existente
    if (graficoSemanalInstance) {
        graficoSemanalInstance.destroy();
    }
    
    // Preparar dados dos últimos 28 dias
    const labels = dados.map(item => {
        const data = new Date(item.data);
        return data.toLocaleDateString('pt-BR', { 
            day: '2-digit', 
            month: '2-digit' 
        });
    });
    
    const valores = dados.map(item => item.quantidade);
    
    graficoSemanalInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Chamados por Dia',
                data: valores,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#3b82f6',
                pointBorderColor: '#ffffff',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#3b82f6',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#6b7280',
                        maxTicksLimit: 14
                    }
                },
                y: {
                    display: true,
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(107, 114, 128, 0.1)'
                    },
                    ticks: {
                        color: '#6b7280',
                        stepSize: 1
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
}

// Criar gráfico de distribuição por status
function criarGraficoDistribuicaoStatus(dados) {
    const ctx = document.getElementById('chartStatus');
    if (!ctx) return;
    
    // Destruir gráfico existente
    if (graficoStatusInstance) {
        graficoStatusInstance.destroy();
    }
    
    const cores = {
        'Aberto': '#f59e0b',
        'Aguardando': '#3b82f6',
        'Concluido': '#10b981',
        'Cancelado': '#ef4444'
    };
    
    graficoStatusInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: dados.map(item => item.status),
            datasets: [{
                data: dados.map(item => item.quantidade),
                backgroundColor: dados.map(item => cores[item.status] || '#6b7280'),
                borderWidth: 3,
                borderColor: '#ffffff',
                hoverBorderWidth: 4,
                hoverBorderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {
                            size: 12
                        },
                        color: '#ffffff'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#ffffff',
                    bodyColor: '#ffffff',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0;
                            return `${context.label}: ${context.parsed} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%',
            animation: {
                animateRotate: true,
                animateScale: true
            }
        }
    });
}

// Carregar chamados detalhados com informações de SLA
function carregarChamadosDetalhados() {
    fetch('/ti/painel/api/sla/chamados-detalhados')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            const tbody = document.getElementById('tabelaChamadosSLA');
            if (!tbody) return;
            
            tbody.innerHTML = '';
            
            data.forEach(chamado => {
                const row = document.createElement('tr');
                
                // Calcular limite SLA baseado na prioridade usando as configurações carregadas
                const limiteSLA = obterLimiteSLAPorPrioridade(chamado.prioridade);
                
                // Recalcular status SLA baseado no limite correto
                let slaStatus = 'Dentro do Prazo';
                let slaClass = 'badge bg-success';
                let slaIcon = 'fas fa-clock';
                
                if (chamado.status === 'Concluido' || chamado.status === 'Cancelado') {
                    if (chamado.horas_decorridas <= limiteSLA) {
                        slaStatus = 'Cumprido';
                        slaClass = 'badge bg-success';
                        slaIcon = 'fas fa-check-circle';
                    } else {
                        slaStatus = 'Violado';
                        slaClass = 'badge bg-danger';
                        slaIcon = 'fas fa-times-circle';
                    }
                } else {
                    // Chamado ainda aberto
                    const percentualSLA = (chamado.horas_decorridas / limiteSLA) * 100;
                    
                    if (percentualSLA >= 100) {
                        slaStatus = 'Violado';
                        slaClass = 'badge bg-danger';
                        slaIcon = 'fas fa-times-circle';
                    } else if (percentualSLA >= 80) {
                        slaStatus = 'Em Risco';
                        slaClass = 'badge bg-warning';
                        slaIcon = 'fas fa-exclamation-triangle';
                    } else {
                        slaStatus = 'Dentro do Prazo';
                        slaClass = 'badge bg-success';
                        slaIcon = 'fas fa-clock';
                    }
                }
                
                // Classe para status do chamado
                const statusClass = getStatusBadgeClass(chamado.status);
                
                // Classe para prioridade
                const prioridadeClass = getPrioridadeBadgeClass(chamado.prioridade);
                
                // Calcular progresso do SLA usando o limite correto
                const progressoSLA = Math.min((chamado.horas_decorridas / limiteSLA) * 100, 100);
                let progressoColor = 'bg-success';
                if (progressoSLA > 80) progressoColor = 'bg-danger';
                else if (progressoSLA > 60) progressoColor = 'bg-warning';
                
                row.innerHTML = `
                    <td><span class="badge badge-outline">${chamado.codigo}</span></td>
                    <td>${chamado.solicitante}</td>
                    <td class="text-truncate" style="max-width: 200px;" title="${chamado.problema}">${chamado.problema}</td>
                    <td><span class="badge ${statusClass}">${chamado.status}</span></td>
                    <td>${chamado.data_abertura}</td>
                    <td>
                        <div class="d-flex align-items-center gap-2">
                            <span class="font-monospace">${formatarTempo(chamado.horas_decorridas)}</span>
                            <div class="progress" style="width: 60px; height: 8px;">
                                <div class="progress-bar ${progressoColor}" 
                                     style="width: ${progressoSLA}%" 
                                     title="${progressoSLA.toFixed(1)}% do SLA"></div>
                            </div>
                        </div>
                    </td>
                    <td><span class="badge badge-outline">${formatarTempo(limiteSLA)}</span></td>
                    <td>
                        <span class="${slaClass}">
                            <i class="${slaIcon}"></i>
                            ${slaStatus}
                        </span>
                    </td>
                    <td><span class="badge ${prioridadeClass}">${chamado.prioridade}</span></td>
                `;
                
                tbody.appendChild(row);
            });
            
            // Adicionar estatísticas rápidas
            atualizarEstatisticasRapidas(data);
        })
        .catch(error => {
            console.error('Erro ao carregar chamados detalhados:', error);
            mostrarToast('Erro ao carregar detalhes dos chamados', 'error');
        });
}

// Função auxiliar para obter classe do badge de status
function getStatusBadgeClass(status) {
    const classes = {
        'Aberto': 'bg-warning',
        'Aguardando': 'bg-info',
        'Concluido': 'bg-success',
        'Cancelado': 'bg-danger'
    };
    return classes[status] || 'bg-secondary';
}

// Função auxiliar para obter classe do badge de prioridade
function getPrioridadeBadgeClass(prioridade) {
    const classes = {
        'Crítica': 'bg-danger',
        'Crítico': 'bg-danger',
        'Alta': 'bg-warning',
        'Alto': 'bg-warning',
        'Normal': 'bg-info',
        'Baixa': 'bg-secondary',
        'Baixo': 'bg-secondary'
    };
    return classes[prioridade] || 'bg-info';
}

// Atualizar estatísticas rápidas da tabela
function atualizarEstatisticasRapidas(chamados) {
    const total = chamados.length;
    let cumpridos = 0;
    let emRisco = 0;
    let violados = 0;
    
    chamados.forEach(chamado => {
        const limiteSLA = obterLimiteSLAPorPrioridade(chamado.prioridade);
        const percentualSLA = (chamado.horas_decorridas / limiteSLA) * 100;
        
        if (chamado.status === 'Concluido' || chamado.status === 'Cancelado') {
            if (chamado.horas_decorridas <= limiteSLA) {
                cumpridos++;
            } else {
                violados++;
            }
        } else {
            if (percentualSLA >= 100) {
                violados++;
            } else if (percentualSLA >= 80) {
                emRisco++;
            } else {
                cumpridos++;
            }
        }
    });
    
    console.log(`SLA - Total: ${total}, Cumpridos: ${cumpridos}, Em Risco: ${emRisco}, Violados: ${violados}`);
}

// Função para atualizar SLA manualmente
function atualizarSLA() {
    mostrarToast('Atualizando dados SLA...', 'info');
    carregarSLA();
}

// Função para exportar relatório SLA
function exportarRelatorioSLA() {
    fetch('/ti/painel/api/sla/chamados-detalhados')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Processar dados com limites SLA corretos
            const dadosProcessados = data.map(chamado => {
                const limiteSLA = obterLimiteSLAPorPrioridade(chamado.prioridade);
                const percentualSLA = (chamado.horas_decorridas / limiteSLA) * 100;
                
                let slaStatus = 'Dentro do Prazo';
                if (chamado.status === 'Concluido' || chamado.status === 'Cancelado') {
                    slaStatus = chamado.horas_decorridas <= limiteSLA ? 'Cumprido' : 'Violado';
                } else {
                    if (percentualSLA >= 100) {
                        slaStatus = 'Violado';
                    } else if (percentualSLA >= 80) {
                        slaStatus = 'Em Risco';
                    }
                }
                
                return {
                    ...chamado,
                    sla_limite: limiteSLA,
                    sla_status: slaStatus,
                    horas_decorridas_formatado: formatarTempo(chamado.horas_decorridas),
                    sla_limite_formatado: formatarTempo(limiteSLA)
                };
            });
            
            // Converter para CSV
            const headers = ['Código', 'Solicitante', 'Problema', 'Status', 'Data Abertura', 'Tempo Decorrido', 'Limite SLA', 'Status SLA', 'Prioridade'];
            const csvContent = [
                headers.join(','),
                ...dadosProcessados.map(chamado => [
                    chamado.codigo,
                    `"${chamado.solicitante}"`,
                    `"${chamado.problema}"`,
                    chamado.status,
                    chamado.data_abertura,
                    `"${chamado.horas_decorridas_formatado}"`,
                    `"${chamado.sla_limite_formatado}"`,
                    chamado.sla_status,
                    chamado.prioridade
                ].join(','))
            ].join('\n');
            
            // Download do arquivo
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', `relatorio_sla_${new Date().toISOString().split('T')[0]}.csv`);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            mostrarToast('Relatório exportado com sucesso', 'success');
        })
        .catch(error => {
            console.error('Erro ao exportar relatório:', error);
            mostrarToast('Erro ao exportar relatório', 'error');
        });
}

// Função para mostrar toast (se não existir)
function mostrarToast(mensagem, tipo = 'info') {
    // Usar sistema de notificações avançado se disponível
    if (window.advancedNotificationSystem) {
        switch(tipo) {
            case 'success':
                window.advancedNotificationSystem.showSuccess('SLA', mensagem);
                break;
            case 'error':
                window.advancedNotificationSystem.showError('SLA', mensagem);
                break;
            case 'warning':
                window.advancedNotificationSystem.showWarning('SLA', mensagem);
                break;
            default:
                window.advancedNotificationSystem.showInfo('SLA', mensagem);
        }
        return;
    }
    
    // Implementação simples de toast como fallback
    const toast = document.createElement('div');
    toast.className = `alert alert-${tipo === 'error' ? 'danger' : tipo} position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="fas fa-${tipo === 'error' ? 'exclamation-circle' : tipo === 'success' ? 'check-circle' : 'info-circle'} me-2"></i>
            ${mensagem}
            <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Remover automaticamente após 5 segundos
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Botão de atualizar SLA
    const btnAtualizarSLA = document.getElementById('btnAtualizarSLA');
    if (btnAtualizarSLA) {
        btnAtualizarSLA.addEventListener('click', atualizarSLA);
    }
    
    // Carregar dados SLA se estivermos na seção correta
    if (document.getElementById('sla-dashboard')) {
        carregarSLA();
    }
});

// Função para forçar recarregamento completo de SLA (chamada externamente)
function forcarRecarregamentoSLA() {
    console.log('=== FORÇANDO RECARREGAMENTO COMPLETO DE SLA ===');

    // Resetar configurações para forçar reload
    slaConfiguracoes = {};

    // Recarregar configurações forçadamente
    carregarConfiguracoesSLA(true);

    // Pequeno delay e recarregar métricas
    setTimeout(() => {
        carregarMetricasSLA();
        carregarChamadosDetalhados();
    }, 1000);
}

// Exportar funções para uso global
window.carregarSLA = carregarSLA;
window.carregarConfiguracoesSLA = carregarConfiguracoesSLA;
window.carregarMetricasSLA = carregarMetricasSLA;
window.carregarChamadosDetalhados = carregarChamadosDetalhados;
window.forcarRecarregamentoSLA = forcarRecarregamentoSLA;
window.atualizarSLA = atualizarSLA;
window.exportarRelatorioSLA = exportarRelatorioSLA;
window.formatarTempo = formatarTempo;
window.formatarPercentual = formatarPercentual;
