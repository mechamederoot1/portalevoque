// ==================== CORREÇÕES DE FILTROS ====================

// Função corrigida para filtrar usuários no painel de permissões
function filtrarListaUsuarios(termoBusca) {
    const usuariosGrid = document.getElementById('usuariosGrid');
    if (!usuariosGrid) return;

    // Corrigir seletores para trabalhar com a estrutura HTML real
    const cards = usuariosGrid.querySelectorAll('.usuario-card, .card');
    let usuariosVisiveis = 0;

    cards.forEach(card => {
        // Buscar o texto em todos os elementos da card, não em classes específicas que não existem
        const cardText = card.textContent.toLowerCase();
        
        if (termoBusca === '' || cardText.includes(termoBusca)) {
            card.style.display = '';
            usuariosVisiveis++;
        } else {
            card.style.display = 'none';
        }
    });

    // Mostrar mensagem se nenhum usuário for encontrado
    let mensagemVazia = usuariosGrid.querySelector('#mensagemUsuariosVazia');
    if (usuariosVisiveis === 0 && termoBusca !== '') {
        if (!mensagemVazia) {
            const mensagem = document.createElement('div');
            mensagem.id = 'mensagemUsuariosVazia';
            mensagem.className = 'text-center py-4';
            mensagem.style.gridColumn = '1 / -1'; // Ocupar toda a largura do grid
            mensagem.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-search"></i>
                    </div>
                    <h4>Nenhum usuário encontrado</h4>
                    <p>Tente usar termos de busca diferentes</p>
                </div>
            `;
            usuariosGrid.appendChild(mensagem);
        }
    } else if (mensagemVazia) {
        mensagemVazia.remove();
    }
}

// Função corrigida para inicializar filtros de permissões com busca em tempo real
function inicializarFiltroPermissoes() {
    const filtroInput = document.getElementById('filtroPermissoes');
    const btnFiltrar = document.getElementById('btnFiltrarPermissoes');

    if (!filtroInput || !btnFiltrar) return;

    // Função para filtrar usuários
    const filtrarUsuarios = () => {
        const termoBusca = filtroInput.value.toLowerCase().trim();
        filtrarListaUsuarios(termoBusca);
    };

    // Event listeners para busca em tempo real
    filtroInput.addEventListener('input', debounce(filtrarUsuarios, 300));
    btnFiltrar.addEventListener('click', filtrarUsuarios);

    // Filtrar ao pressionar Enter
    filtroInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            filtrarUsuarios();
        }
    });
}

// Função corrigida para aplicar filtros avançados de chamados
function aplicarFiltrosAvancados(chamados) {
    let filtrados = [...chamados];

    // Filtro por solicitante
    const filtroSolicitante = document.getElementById('filtroSolicitante');
    if (filtroSolicitante && filtroSolicitante.value.trim()) {
        const termo = filtroSolicitante.value.trim().toLowerCase();
        filtrados = filtrados.filter(chamado =>
            chamado.solicitante && chamado.solicitante.toLowerCase().includes(termo)
        );
    }

    // Filtro por problema
    const filtroProblema = document.getElementById('filtroProblema');
    if (filtroProblema && filtroProblema.value.trim()) {
        const termo = filtroProblema.value.trim().toLowerCase();
        filtrados = filtrados.filter(chamado =>
            chamado.problema && chamado.problema.toLowerCase().includes(termo)
        );
    }

    // Filtro por prioridade
    const filtroPrioridade = document.getElementById('filtroPrioridade');
    if (filtroPrioridade && filtroPrioridade.value) {
        filtrados = filtrados.filter(chamado =>
            chamado.prioridade === filtroPrioridade.value
        );
    }

    // Filtro por agente responsável
    const filtroAgenteResponsavel = document.getElementById('filtroAgenteResponsavel');
    if (filtroAgenteResponsavel && filtroAgenteResponsavel.value) {
        const agenteId = filtroAgenteResponsavel.value;
        if (agenteId === 'sem_agente') {
            filtrados = filtrados.filter(chamado => !chamado.agente_id);
        } else {
            filtrados = filtrados.filter(chamado =>
                chamado.agente_id && chamado.agente_id.toString() === agenteId
            );
        }
    }

    // Filtro por unidade
    const filtroUnidade = document.getElementById('filtroUnidade');
    if (filtroUnidade && filtroUnidade.value) {
        filtrados = filtrados.filter(chamado =>
            chamado.unidade === filtroUnidade.value
        );
    }

    // Filtro por data de início
    const filtroDataInicio = document.getElementById('filtroDataInicio');
    if (filtroDataInicio && filtroDataInicio.value) {
        const dataInicio = new Date(filtroDataInicio.value);
        filtrados = filtrados.filter(chamado => {
            if (!chamado.data_abertura) return false;
            try {
                // Tentar converter diferentes formatos de data
                let dataChamado;
                if (chamado.data_abertura.includes('/')) {
                    // Formato DD/MM/YYYY HH:mm:ss
                    const [data, hora] = chamado.data_abertura.split(' ');
                    const [dia, mes, ano] = data.split('/');
                    dataChamado = new Date(ano, mes - 1, dia);
                } else {
                    // Formato ISO ou outro formato
                    dataChamado = new Date(chamado.data_abertura);
                }
                return dataChamado >= dataInicio;
            } catch (error) {
                console.error('Erro ao converter data:', error, chamado.data_abertura);
                return false;
            }
        });
    }

    // Filtro por data fim
    const filtroDataFim = document.getElementById('filtroDataFim');
    if (filtroDataFim && filtroDataFim.value) {
        const dataFim = new Date(filtroDataFim.value);
        dataFim.setHours(23, 59, 59, 999); // Incluir todo o dia final
        filtrados = filtrados.filter(chamado => {
            if (!chamado.data_abertura) return false;
            try {
                let dataChamado;
                if (chamado.data_abertura.includes('/')) {
                    const [data, hora] = chamado.data_abertura.split(' ');
                    const [dia, mes, ano] = data.split('/');
                    dataChamado = new Date(ano, mes - 1, dia);
                } else {
                    dataChamado = new Date(chamado.data_abertura);
                }
                return dataChamado <= dataFim;
            } catch (error) {
                console.error('Erro ao converter data:', error, chamado.data_abertura);
                return false;
            }
        });
    }

    return filtrados;
}

// Função debounce melhorada
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Função para adicionar mensagem quando nenhum resultado é encontrado
function mostrarMensagemSemResultados(container, tipo = 'chamados') {
    container.innerHTML = `
        <div class="empty-state" style="grid-column: 1 / -1;">
            <div class="empty-icon">
                <i class="fas fa-inbox"></i>
            </div>
            <h4>Nenhum ${tipo} encontrado</h4>
            <p>Não há ${tipo} com os filtros selecionados</p>
            <button class="btn btn-outline-secondary" onclick="limparTodosFiltros()">
                <i class="fas fa-times me-1"></i>Limpar Filtros
            </button>
        </div>
    `;
}

// Função para limpar todos os filtros
function limparTodosFiltros() {
    // Filtros de chamados
    const filtroSolicitante = document.getElementById('filtroSolicitante');
    const filtroProblema = document.getElementById('filtroProblema');
    const filtroPrioridade = document.getElementById('filtroPrioridade');
    const filtroAgenteResponsavel = document.getElementById('filtroAgenteResponsavel');
    const filtroUnidade = document.getElementById('filtroUnidade');
    const filtroDataInicio = document.getElementById('filtroDataInicio');
    const filtroDataFim = document.getElementById('filtroDataFim');

    if (filtroSolicitante) filtroSolicitante.value = '';
    if (filtroProblema) filtroProblema.value = '';
    if (filtroPrioridade) filtroPrioridade.value = '';
    if (filtroAgenteResponsavel) filtroAgenteResponsavel.value = '';
    if (filtroUnidade) filtroUnidade.value = '';
    if (filtroDataInicio) filtroDataInicio.value = '';
    if (filtroDataFim) filtroDataFim.value = '';

    // Filtro de permissões
    const filtroPermissoes = document.getElementById('filtroPermissoes');
    if (filtroPermissoes) filtroPermissoes.value = '';

    // Recarregar dados
    if (window.chamadosData && typeof renderChamadosPage === 'function') {
        currentPage = 1;
        renderChamadosPage(currentPage);
    }
    
    if (window.usuariosData && typeof renderUsuariosPage === 'function') {
        filtrarListaUsuarios('');
    }
}

// Exportar funções para uso global
if (typeof window !== 'undefined') {
    window.filtrarListaUsuarios = filtrarListaUsuarios;
    window.inicializarFiltroPermissoes = inicializarFiltroPermissoes;
    window.aplicarFiltrosAvancados = aplicarFiltrosAvancados;
    window.mostrarMensagemSemResultados = mostrarMensagemSemResultados;
    window.limparTodosFiltros = limparTodosFiltros;
}
