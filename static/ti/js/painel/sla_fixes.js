/**
 * Fixes for SLA Dashboard JavaScript Errors
 * This file provides corrected functions that override problematic ones
 */

// Override the createChartSafely function for Chart.js
function createChartSafely(canvasId, config, instanceName = null) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas with ID '${canvasId}' not found`);
        return null;
    }
    
    // Destroy any existing chart on this canvas
    const existingChart = Chart.getChart(canvas);
    if (existingChart) {
        existingChart.destroy();
    }
    
    try {
        // Create new chart
        const chart = new Chart(canvas, config);
        
        // Store globally if instance name provided
        if (instanceName) {
            window[instanceName] = chart;
        }
        
        return chart;
        
    } catch (error) {
        console.error(`Error creating chart for ${canvasId}:`, error);
        return null;
    }
}

// Override the criarGraficoSemanal function with better error handling
function criarGraficoSemanal(dados) {
    const ctx = document.getElementById('chartSemanal');
    if (!ctx) return;
    
    // Safely destroy existing chart
    try {
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        if (window.graficoSemanalInstance) {
            window.graficoSemanalInstance.destroy();
            window.graficoSemanalInstance = null;
        }
    } catch (error) {
        console.warn('Error destroying existing weekly chart:', error);
    }
    
    // Prepare data
    const labels = dados.map(item => {
        const data = new Date(item.data);
        return data.toLocaleDateString('pt-BR', { 
            day: '2-digit', 
            month: '2-digit' 
        });
    });
    
    const valores = dados.map(item => item.quantidade);
    
    try {
        window.graficoSemanalInstance = new Chart(ctx, {
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
        
    } catch (error) {
        console.error('Error creating weekly chart:', error);
    }
}

// Override the criarGraficoDistribuicaoStatus function
function criarGraficoDistribuicaoStatus(dados) {
    const ctx = document.getElementById('chartStatus');
    if (!ctx) return;
    
    // Safely destroy existing chart
    try {
        const existingChart = Chart.getChart(ctx);
        if (existingChart) {
            existingChart.destroy();
        }
        
        if (window.graficoStatusInstance) {
            window.graficoStatusInstance.destroy();
            window.graficoStatusInstance = null;
        }
    } catch (error) {
        console.warn('Error destroying existing status chart:', error);
    }
    
    const cores = {
        'Aberto': '#f59e0b',
        'Aguardando': '#3b82f6',
        'Concluido': '#10b981',
        'Cancelado': '#ef4444'
    };

    try {
        window.graficoStatusInstance = new Chart(ctx, {
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
        
    } catch (error) {
        console.error('Error creating status chart:', error);
    }
}

// Fix for safeFetch to handle non-JSON responses properly
async function safeFetchFixed(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        // Check content type
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            return {
                ok: response.ok,
                status: response.status,
                data: data
            };
        } else {
            // HTML or other format - probably error
            const text = await response.text();
            console.error(`Server returned ${contentType} instead of JSON for ${url}. Status: ${response.status}`);
            console.error('Response text:', text.substring(0, 500) + '...');
            throw new Error(`Servidor retornou ${contentType} em vez de JSON. Status: ${response.status}`);
        }
        
    } catch (error) {
        console.error(`Erro em safeFetch para ${url}:`, error);
        throw error;
    }
}

// Override global functions
window.createChartSafely = createChartSafely;
window.criarGraficoSemanal = criarGraficoSemanal;
window.criarGraficoDistribuicaoStatus = criarGraficoDistribuicaoStatus;
window.safeFetch = safeFetchFixed;

console.log('SLA Fixes loaded - Chart.js error handling improved');
