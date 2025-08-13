/**
 * Sistema de Métricas SLA com cálculo correto de horário comercial
 */

class SLAMetricas {
    constructor() {
        this.configuracoes = null;
        this.metricas = null;
        this.chamados = [];
        this.loading = false;
        
        this.initEventListeners();
        this.carregarDashboardCompleto();
    }

    initEventListeners() {
        // Botão de atualizar SLA
        const btnAtualizar = document.getElementById('btnAtualizarSLA');
        if (btnAtualizar) {
            btnAtualizar.addEventListener('click', () => this.carregarDashboardCompleto());
        }

        // Botão de corrigir dados de teste
        const btnCorrigirDados = document.getElementById('btnCorrigirDadosTeste');
        if (btnCorrigirDados) {
            btnCorrigirDados.addEventListener('click', () => this.corrigirDadosTeste());
        }

        // Botão de migrar SLA
        const btnMigrarSLA = document.getElementById('btnMigrarSLA');
        if (btnMigrarSLA) {
            btnMigrarSLA.addEventListener('click', () => this.migrarTabelasSLA());
        }

        // Evento para salvar configurações (será usado na seção de configurações)
        document.addEventListener('configuracoesSLASalvas', () => {
            this.carregarDashboardCompleto();
        });
    }

    async corrigirDadosTeste() {
        if (!confirm('Deseja corrigir os dados de teste para demonstrar o funcionamento correto do SLA considerando horário comercial?')) {
            return;
        }

        const btnCorrigir = document.getElementById('btnCorrigirDadosTeste');
        const textoOriginal = btnCorrigir.innerHTML;

        try {
            btnCorrigir.disabled = true;
            btnCorrigir.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Corrigindo...';

            const response = await fetch('/ti/painel/api/corrigir-dados-teste', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                alert(`✅ Dados corrigidos com sucesso!\n\n${data.chamados_criados} chamados de teste criados.\n\nO sistema agora mostra corretamente:\n- Ronaldo: Chamado crítico com cálculo de horas úteis\n- Maria: Chamado concluído dentro do SLA\n- João: Chamado em risco`);

                // Recarregar dashboard
                this.carregarDashboardCompleto();
            } else {
                throw new Error(data.message || 'Erro desconhecido');
            }

        } catch (error) {
            console.error('Erro ao corrigir dados:', error);
            alert('❌ Erro ao corrigir dados de teste: ' + error.message);
        } finally {
            btnCorrigir.disabled = false;
            btnCorrigir.innerHTML = textoOriginal;
        }
    }

    async migrarTabelasSLA() {
        if (!confirm('Deseja migrar as configurações de SLA para as novas tabelas do banco de dados?\n\nIsso criará as estruturas necessárias para gerenciar SLA e horário comercial diretamente no banco.')) {
            return;
        }

        const btnMigrar = document.getElementById('btnMigrarSLA');
        const textoOriginal = btnMigrar.innerHTML;

        try {
            btnMigrar.disabled = true;
            btnMigrar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Migrando...';

            const response = await fetch('/ti/painel/api/sistema/migrar-sla', {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                const resultados = data.resultados;
                let mensagem = '✅ Migração executada com sucesso!\n\n';

                if (resultados.ja_existiam) {
                    mensagem += 'As configurações já existiam no banco de dados.\n';
                } else {
                    mensagem += `📊 Configurações SLA criadas: ${resultados.slas_criadas}\n`;
                    mensagem += `📅 Configurações de horário criadas: ${resultados.horarios_criados}\n\n`;
                    mensagem += 'Agora as configurações são gerenciadas diretamente no banco de dados!';
                }

                alert(mensagem);

                // Recarregar dashboard para mostrar novas configurações
                this.carregarDashboardCompleto();
            } else {
                throw new Error(data.message || 'Erro desconhecido');
            }

        } catch (error) {
            console.error('Erro na migração:', error);
            alert('❌ Erro na migração: ' + error.message);
        } finally {
            btnMigrar.disabled = false;
            btnMigrar.innerHTML = textoOriginal;
        }
    }

    async carregarDashboardCompleto() {
        if (this.loading) return;
        
        this.loading = true;
        this.mostrarLoading(true);

        try {
            // Carregar métricas SLA
            const metricasResponse = await fetch('/ti/painel/api/sla/metricas?period_days=30', {
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!metricasResponse.ok) {
                if (metricasResponse.status === 401 || metricasResponse.status === 302) {
                    throw new Error('N��o autenticado. Faça login para acessar as métricas SLA.');
                }
                throw new Error(`HTTP error! status: ${metricasResponse.status}`);
            }

            const metricasData = await metricasResponse.json();
            this.metricas = metricasData.metricas_gerais;

            // Carregar chamados detalhados
            const chamadosResponse = await fetch('/ti/painel/api/sla/chamados-detalhados', {
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (chamadosResponse.ok) {
                this.chamados = await chamadosResponse.json();
            }

            // Carregar gráfico semanal
            const graficoResponse = await fetch('/ti/painel/api/sla/grafico-semanal', {
                credentials: 'same-origin',
                headers: {
                    'Accept': 'application/json'
                }
            });

            let graficoData = null;
            if (graficoResponse.ok) {
                graficoData = await graficoResponse.json();
            }

            // Atualizar interface
            this.atualizarMetricasPrincipais();
            this.atualizarCardsMetricas();
            this.atualizarConfiguracoesSLA();
            this.atualizarTabelaChamadosSLA();
            if (graficoData) {
                this.atualizarGraficos(graficoData);
            }

            console.log('Dashboard SLA carregado com sucesso');
            
        } catch (error) {
            console.error('Erro ao carregar dashboard SLA:', error);
            this.mostrarErro('Erro ao carregar métricas de SLA: ' + error.message);
        } finally {
            this.loading = false;
            this.mostrarLoading(false);
        }
    }

    atualizarMetricasPrincipais() {
        if (!this.metricas) return;

        // Total de chamados
        const totalChamados = document.getElementById('totalChamados');
        if (totalChamados) {
            totalChamados.textContent = this.metricas.total_chamados || 0;
        }

        // Chamados abertos
        const chamadosAbertos = document.getElementById('chamadosAbertos');
        if (chamadosAbertos) {
            chamadosAbertos.textContent = this.metricas.chamados_abertos || 0;
        }

        // Tempo médio de resposta
        const tempoMedioResposta = document.getElementById('tempoMedioResposta');
        if (tempoMedioResposta) {
            const tempo = this.metricas.tempo_medio_primeira_resposta || 0;
            tempoMedioResposta.textContent = this.formatarTempo(tempo);
        }

        // Tempo médio de resolução
        const tempoMedioResolucao = document.getElementById('tempoMedioResolucao');
        if (tempoMedioResolucao) {
            const tempo = this.metricas.tempo_medio_resolucao || 0;
            tempoMedioResolucao.textContent = this.formatarTempo(tempo);
        }
    }

    atualizarCardsMetricas() {
        if (!this.metricas) return;

        // SLA Percentual
        const slaPercentual = document.getElementById('slaPercentual');
        const slaCard = document.querySelector('.sla-percentual');
        if (slaPercentual && slaCard) {
            const percentual = this.metricas.percentual_cumprimento || 0;
            slaPercentual.textContent = `${percentual}%`;
            
            // Atualizar cor do card baseado no percentual
            slaCard.className = 'card sla-percentual text-white';
            if (percentual >= 95) {
                slaCard.classList.add('bg-success');
            } else if (percentual >= 80) {
                slaCard.classList.add('bg-warning');
            } else {
                slaCard.classList.add('bg-danger');
            }
        }

        // Violações SLA
        const slaViolacoes = document.getElementById('slaViolacoes');
        if (slaViolacoes) {
            slaViolacoes.textContent = this.metricas.chamados_violados || 0;
        }

        // Chamados em risco
        const chamadosRisco = document.getElementById('chamadosRisco');
        const riskCard = document.querySelector('.chamados-risco');
        if (chamadosRisco && riskCard) {
            const risco = this.metricas.chamados_em_risco || 0;
            chamadosRisco.textContent = risco;
            
            // Atualizar cor do card baseado no número de chamados em risco
            riskCard.className = 'card chamados-risco text-white';
            if (risco === 0) {
                riskCard.classList.add('bg-success');
            } else if (risco <= 3) {
                riskCard.classList.add('bg-warning');
            } else {
                riskCard.classList.add('bg-danger');
            }
        }
    }

    atualizarConfiguracoesSLA() {
        if (!this.configuracoes || !this.configuracoes.sla) return;

        const config = this.configuracoes.sla;

        // Atualizar badges de configuração
        this.atualizarBadgeConfig('configPrimeiraResposta', config.primeira_resposta);
        this.atualizarBadgeConfig('configResolucao', config.resolucao_normal);
        this.atualizarBadgeConfig('configCritico', config.resolucao_critica);
        this.atualizarBadgeConfig('configAlto', config.resolucao_alta);
        this.atualizarBadgeConfig('configNormal', config.resolucao_normal);
        this.atualizarBadgeConfig('configBaixo', config.resolucao_baixa);
    }

    atualizarBadgeConfig(elementId, horas) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = this.formatarTempo(horas);
        }
    }

    async atualizarTabelaChamadosSLA() {
        try {
            // Carregar chamados com informações detalhadas de SLA
            const response = await fetch('/ti/painel/api/sla/chamados?limit=20');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            const chamados = data.chamados || [];
            
            const tbody = document.getElementById('tabelaChamadosSLA');
            if (!tbody) return;

            if (chamados.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" class="text-center">Nenhum chamado encontrado</td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = chamados.map(chamado => {
                const sla = chamado.sla || {};
                const statusClass = this.obterClasseStatusSLA(sla.sla_status);
                const prioridadeClass = this.obterClassePrioridade(chamado.prioridade);
                
                return `
                    <tr>
                        <td>${chamado.codigo || 'N/A'}</td>
                        <td>${chamado.solicitante || 'N/A'}</td>
                        <td>${chamado.problema || 'N/A'}</td>
                        <td>
                            <span class="badge bg-${this.obterClasseStatus(chamado.status)}">${chamado.status}</span>
                        </td>
                        <td>${chamado.data_abertura || 'N/A'}</td>
                        <td>${this.formatarTempo(sla.horas_uteis_decorridas)} (úteis)</td>
                        <td>${this.formatarTempo(sla.sla_limite)}</td>
                        <td>
                            <span class="badge bg-${statusClass}">${sla.sla_status || 'Indefinido'}</span>
                            ${sla.percentual_tempo_usado ? `<br><small>${sla.percentual_tempo_usado}% usado</small>` : ''}
                        </td>
                        <td>
                            <span class="badge bg-${prioridadeClass}">${chamado.prioridade || 'Normal'}</span>
                        </td>
                    </tr>
                `;
            }).join('');
            
        } catch (error) {
            console.error('Erro ao carregar tabela de chamados SLA:', error);
            const tbody = document.getElementById('tabelaChamadosSLA');
            if (tbody) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="9" class="text-center text-danger">Erro ao carregar dados</td>
                    </tr>
                `;
            }
        }
    }

    atualizarGraficos(dadosGrafico) {
        if (!dadosGrafico) return;

        // Atualizar gráfico de status
        if (dadosGrafico.distribuicao_status) {
            this.atualizarGraficoStatus(dadosGrafico.distribuicao_status);
        }

        // Atualizar gráfico semanal
        if (dadosGrafico.grafico_semanal) {
            this.atualizarGraficoSemanal(dadosGrafico.grafico_semanal);
        }
    }

    atualizarGraficoStatus(statusData) {
        const ctx = document.getElementById('chartStatus');
        if (!ctx || !statusData) return;

        const data = {
            labels: Object.keys(statusData),
            datasets: [{
                data: Object.values(statusData),
                backgroundColor: [
                    '#007bff', // Aberto - azul
                    '#ffc107', // Aguardando - amarelo
                    '#28a745', // Concluido - verde
                    '#dc3545'  // Cancelado - vermelho
                ],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        };

        // Usar utilitário seguro para Chart.js
        window.chartStatus = createChartSafely('chartStatus', {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            color: '#fff'
                        }
                    }
                }
            }
        });
    }

    atualizarGraficoPrioridade(prioridadeData) {
        const ctx = document.getElementById('chartDistribuicaoPrioridade');
        if (!ctx || !prioridadeData) return;

        const data = {
            labels: Object.keys(prioridadeData),
            datasets: [{
                label: 'Chamados por Prioridade',
                data: Object.values(prioridadeData),
                backgroundColor: [
                    '#dc3545', // Crítica - vermelho
                    '#fd7e14', // Urgente - laranja
                    '#ffc107', // Alta - amarelo
                    '#007bff', // Normal - azul
                    '#6c757d'  // Baixa - cinza
                ],
                borderColor: '#fff',
                borderWidth: 2
            }]
        };

        // Usar utilitário seguro para Chart.js
        window.chartDistribuicaoPrioridade = createChartSafely('chartDistribuicaoPrioridade', {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        }
                    }
                }
            }
        });
    }

    atualizarGraficoSemanal() {
        const ctx = document.getElementById('chartSemanal');
        if (!ctx) return;

        // Dados simulados para as últimas 4 semanas
        const semanas = ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4'];
        const chamadosRecebidos = [12, 19, 15, 23];
        const chamadosResolvidos = [10, 18, 14, 20];

        const data = {
            labels: semanas,
            datasets: [
                {
                    label: 'Chamados Recebidos',
                    data: chamadosRecebidos,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Chamados Resolvidos',
                    data: chamadosResolvidos,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        };

        // Usar utilitário seguro para Chart.js
        window.chartSemanal = createChartSafely('chartSemanal', {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255,255,255,0.1)'
                        }
                    }
                }
            }
        });
    }

    // Métodos utilitários
    formatarTempo(horas) {
        if (horas === null || horas === undefined) return 'N/A';
        
        if (horas < 1) {
            const minutos = Math.round(horas * 60);
            return `${minutos}min`;
        } else if (horas < 24) {
            return `${horas.toFixed(1)}h`;
        } else {
            const dias = Math.floor(horas / 24);
            const horasRestantes = Math.round(horas % 24);
            return `${dias}d ${horasRestantes}h`;
        }
    }

    obterClasseStatusSLA(status) {
        switch (status) {
            case 'Cumprido':
                return 'success';
            case 'Dentro do Prazo':
                return 'primary';
            case 'Em Risco':
                return 'warning';
            case 'Violado':
                return 'danger';
            default:
                return 'secondary';
        }
    }

    obterClassePrioridade(prioridade) {
        switch (prioridade) {
            case 'Crítica':
                return 'danger';
            case 'Urgente':
                return 'warning';
            case 'Alta':
                return 'info';
            case 'Normal':
                return 'primary';
            case 'Baixa':
                return 'secondary';
            default:
                return 'secondary';
        }
    }

    obterClasseStatus(status) {
        switch (status) {
            case 'Aberto':
                return 'primary';
            case 'Aguardando':
                return 'warning';
            case 'Concluido':
                return 'success';
            case 'Cancelado':
                return 'danger';
            default:
                return 'secondary';
        }
    }

    mostrarLoading(show) {
        const btnAtualizar = document.getElementById('btnAtualizarSLA');
        if (btnAtualizar) {
            if (show) {
                btnAtualizar.disabled = true;
                btnAtualizar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Carregando...';
            } else {
                btnAtualizar.disabled = false;
                btnAtualizar.innerHTML = '<i class="fas fa-sync-alt me-1"></i>Atualizar';
            }
        }
    }

    mostrarErro(mensagem) {
        console.error('Erro SLA:', mensagem);
        // Aqui você pode adicionar uma notificação visual para o usuário
    }
}

// Inicializar sistema de métricas SLA quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos na seção SLA
    const slaSection = document.getElementById('sla-dashboard');
    if (slaSection) {
        window.slaMetricas = new SLAMetricas();
    }
});

// Atualizar métricas quando a seção SLA for ativada
document.addEventListener('secaoAtivada', function(event) {
    if (event.detail && event.detail.secao === 'sla-dashboard') {
        if (window.slaMetricas) {
            window.slaMetricas.carregarDashboardCompleto();
        } else {
            window.slaMetricas = new SLAMetricas();
        }
    }
});
