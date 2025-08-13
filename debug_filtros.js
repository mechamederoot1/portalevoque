// Script de debug para testar filtros
console.log('Script de debug carregado');

// Função para testar filtros manualmente
function testarFiltros() {
    console.log('=== TESTE DE FILTROS ===');
    console.log('chamadosData:', window.chamadosData);
    console.log('currentFilter:', window.currentFilter);
    
    if (window.chamadosData && window.chamadosData.length > 0) {
        const exemplo = window.chamadosData[0];
        console.log('Exemplo de chamado:', exemplo);
        console.log('Status do primeiro chamado:', exemplo.status);
        
        // Testar filtro manual
        const filtrados = window.chamadosData.filter(c => c.status === 'Aberto');
        console.log('Chamados com status "Aberto":', filtrados.length);
        
        const todos = ['Aberto', 'Aguardando', 'Concluido', 'Cancelado'];
        todos.forEach(status => {
            const count = window.chamadosData.filter(c => c.status === status).length;
            console.log(`Status "${status}": ${count} chamados`);
        });
    } else {
        console.warn('Nenhum dado de chamados disponível');
    }
}

// Função para forçar aplicação de filtro
function aplicarFiltroManual(status) {
    console.log('Aplicando filtro manual para:', status);
    if (window.currentFilter !== undefined) {
        window.currentFilter = status;
    }
    if (window.renderChamadosPage) {
        window.renderChamadosPage(1);
    }
}

// Tornar funções globais
window.testarFiltros = testarFiltros;
window.aplicarFiltroManual = aplicarFiltroManual;

console.log('Funções de debug disponíveis: testarFiltros(), aplicarFiltroManual(status)');
