// Sidebar toggle for mobile
const sidebar = document.getElementById('sidebar');
const sidebarToggleBtn = document.getElementById('sidebarToggle');
const mobileSidebarToggleBtn = document.getElementById('mobileSidebarToggle');

function toggleSidebar() {
    sidebar.classList.toggle('active');
}

sidebarToggleBtn?.addEventListener('click', toggleSidebar);
mobileSidebarToggleBtn?.addEventListener('click', toggleSidebar);

// Submenu toggle
document.querySelectorAll('.sidebar nav ul li.has-submenu > a').forEach(anchor => {
    anchor.addEventListener('click', e => {
        e.preventDefault();
        const parentLi = anchor.parentElement;
        const isOpen = parentLi.classList.contains('open');
        document.querySelectorAll('.sidebar nav ul li.has-submenu.open').forEach(li => {
            if (li !== parentLi) li.classList.remove('open');
        });
        if (isOpen) {
            parentLi.classList.remove('open');
            anchor.setAttribute('aria-expanded', 'false');
        } else {
            parentLi.classList.add('open');
            anchor.setAttribute('aria-expanded', 'true');
        }
    });
});

// Navigation links activate section
const navLinks = document.querySelectorAll('.sidebar nav ul li a, .navbar-panel .nav-link-panel');
const sections = document.querySelectorAll('section.content-section');

navLinks.forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const href = link.getAttribute('href');
        if (!href || href === '#') {
            console.log('Link sem href válido:', link);
            return;
        }

        const targetId = href.substring(1);
        console.log('Navegando para seção:', targetId);

        // Verificar se a seção existe
        const targetSection = document.getElementById(targetId);
        if (!targetSection) {
            console.error('Seção não encontrada:', targetId);
            return;
        }

        activateSection(targetId);
        navLinks.forEach(l => l.classList.remove('active'));
        navLinks.forEach(l => {
            if (l.getAttribute('href') === href) l.classList.add('active');
        });

        // Atualizar hash da URL
        window.location.hash = targetId;
    });
});

function activateSection(id) {
    console.log('Ativando seção:', id);

    if (!sections || sections.length === 0) {
        console.error('Nenhuma seção encontrada!');
        return;
    }

    sections.forEach(section => {
        if (section.id === id) {
            section.classList.add('active');
            section.setAttribute('tabindex', '0');
            console.log('Seção ativada:', id);

            // Carregar conteúdo específico da seção
            setTimeout(() => {
                loadSectionContent(id);
            }, 50);
        } else {
            section.classList.remove('active');
            section.removeAttribute('tabindex');
        }
    });
}

// Theme toggle
const themeToggleBtn = document.getElementById('themeToggle');
if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
        if (document.body.getAttribute('data-theme') === 'dark') {
            document.body.setAttribute('data-theme', 'light');
            themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
        } else {
            document.body.setAttribute('data-theme', 'dark');
            themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
        }
    });
}

// Variáveis globais para chamados
let chamadosData = [];
const chamadosPerPage = 6;
let currentPage = 1;
let currentFilter = 'all';

const chamadosGrid = document.getElementById('chamadosGrid');
const pagination = document.getElementById('pagination');

// Função para carregar os chamados da API
async function loadChamados() {
    try {
        const response = await fetch('/ti/painel/api/chamados');
        if (!response.ok) {
            throw new Error('Erro ao carregar chamados');
        }
        chamadosData = await response.json();
        renderChamadosPage(currentPage);

        // Atualizar contadores da visão geral
        atualizarContadoresVisaoGeral();

        // Popular filtros dinâmicos
        popularFiltrosDinamicos();
    } catch (error) {
        console.error('Erro ao carregar chamados:', error);
        chamadosGrid.innerHTML = '<p class="text-center py-4">Erro ao carregar chamados. Tente novamente mais tarde.</p>';
        // Usar sistema de notificações avançado
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar chamados');
        }
    }
}

// Funç��o para popular filtros com dados dinâmicos
function popularFiltrosDinamicos() {
    // Popular filtro de unidades
    const filtroUnidade = document.getElementById('filtroUnidade');
    if (filtroUnidade && chamadosData.length > 0) {
        const unidades = [...new Set(chamadosData.map(c => c.unidade))].sort();

        // Limpar opções existentes (exceto a primeira)
        while (filtroUnidade.children.length > 1) {
            filtroUnidade.removeChild(filtroUnidade.lastChild);
        }

        unidades.forEach(unidade => {
            const option = document.createElement('option');
            option.value = unidade;
            option.textContent = unidade;
            filtroUnidade.appendChild(option);
        });
    }

    // Popular filtro de agentes respons��veis
    const filtroAgenteResponsavel = document.getElementById('filtroAgenteResponsavel');
    if (filtroAgenteResponsavel && chamadosData.length > 0) {
        const agentes = chamadosData
            .filter(c => c.agente)
            .map(c => ({id: c.agente.id, nome: c.agente.nome}))
            .reduce((acc, agente) => {
                if (!acc.find(a => a.id === agente.id)) {
                    acc.push(agente);
                }
                return acc;
            }, [])
            .sort((a, b) => a.nome.localeCompare(b.nome));

        // Limpar opções existentes (exceto a primeira)
        while (filtroAgenteResponsavel.children.length > 1) {
            filtroAgenteResponsavel.removeChild(filtroAgenteResponsavel.lastChild);
        }

        agentes.forEach(agente => {
            const option = document.createElement('option');
            option.value = agente.id;
            option.textContent = agente.nome;
            filtroAgenteResponsavel.appendChild(option);
        });
    }
}

// Função para atualizar contadores da visão geral
async function atualizarContadoresVisaoGeral() {
    try {
        console.log('Atualizando contadores da visão geral...');
        const response = await fetch('/ti/painel/api/chamados/estatisticas');
        if (!response.ok) {
            throw new Error('Erro ao carregar estatísticas');
        }
        const stats = await response.json();

        const countAbertos = document.getElementById('countAbertos');
        const countAguardando = document.getElementById('countAguardando');
        const countConcluidos = document.getElementById('countConcluidos');
        const countCancelados = document.getElementById('countCancelados');

        if (countAbertos) countAbertos.textContent = stats.Aberto || 0;
        if (countAguardando) countAguardando.textContent = stats.Aguardando || 0;
        if (countConcluidos) countConcluidos.textContent = stats.Concluido || 0;
        if (countCancelados) countCancelados.textContent = stats.Cancelado || 0;

        console.log('Contadores atualizados:', stats);
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
        // Usar dados locais se disponíveis
        if (chamadosData && chamadosData.length > 0) {
            const localStats = {
                Aberto: chamadosData.filter(c => c.status === 'Aberto').length,
                Aguardando: chamadosData.filter(c => c.status === 'Aguardando').length,
                Concluido: chamadosData.filter(c => c.status === 'Concluido').length,
                Cancelado: chamadosData.filter(c => c.status === 'Cancelado').length
            };

            const countAbertos = document.getElementById('countAbertos');
            const countAguardando = document.getElementById('countAguardando');
            const countConcluidos = document.getElementById('countConcluidos');
            const countCancelados = document.getElementById('countCancelados');

            if (countAbertos) countAbertos.textContent = localStats.Aberto;
            if (countAguardando) countAguardando.textContent = localStats.Aguardando;
            if (countConcluidos) countConcluidos.textContent = localStats.Concluido;
            if (countCancelados) countCancelados.textContent = localStats.Cancelado;

            console.log('Usando dados locais para estatísticas:', localStats);
        } else {
            console.log('Nenhum dado disponível para estatísticas');
        }
    }
}

// Função para filtrar chamados
function filterChamados(status) {
    let filtrados = [...chamadosData];

    // Filtrar por status
    if (status !== 'all') {
        filtrados = filtrados.filter(chamado => chamado.status === status);
    }

    // Aplicar filtros avançados se estiverem ativos
    filtrados = aplicarFiltrosAvancados(filtrados);

    return filtrados;
}

// Função para aplicar filtros avançados
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
                let dataChamado;
                if (chamado.data_abertura.includes('/')) {
                    const [data, hora] = chamado.data_abertura.split(' ');
                    const [dia, mes, ano] = data.split('/');
                    dataChamado = new Date(ano, mes - 1, dia);
                } else {
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

// Função para atualizar o status de um chamado
async function updateChamadoStatus(chamadoId, novoStatus) {
    try {
        // Primeiro atualiza o status
        const response = await fetch(`/ti/painel/api/chamados/${chamadoId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: novoStatus })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao atualizar status');
        }

        const data = await response.json();
        
        // Se o status foi atualizado com sucesso e é um dos status que requer notificação
        if (['Aguardando', 'Cancelado', 'Concluido'].includes(novoStatus)) {
            // Envia a notificação
            const notificacaoResponse = await fetch(`/ti/painel/api/chamados/${chamadoId}/notificar`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    status: novoStatus,
                    chamadoId: chamadoId
                })
            });

            if (!notificacaoResponse.ok) {
                console.error('Erro ao enviar notificação:', await notificacaoResponse.text());
                throw new Error('Erro ao enviar notificação por e-mail');
            }
        }

        // Atualiza o chamado na lista local
        const chamado = chamadosData.find(c => c.id == chamadoId);
        if (chamado) {
            chamado.status = novoStatus;
        }

        return data;
    } catch (error) {
        console.error('Erro ao atualizar status:', error);
        throw error;
    }
}

// Função para renderizar a página de chamados
function renderChamadosPage(page) {
    chamadosGrid.innerHTML = '';
    const start = (page - 1) * chamadosPerPage;
    const end = start + chamadosPerPage;
    const filteredChamados = filterChamados(currentFilter);
    const pageChamados = filteredChamados.slice(start, end);

    if (pageChamados.length === 0) {
        chamadosGrid.innerHTML = `
            <div class="empty-state" style="grid-column: 1 / -1;">
                <div class="empty-icon">
                    <i class="fas fa-inbox"></i>
                </div>
                <h4>Nenhum chamado encontrado</h4>
                <p>Não há chamados com os filtros selecionados</p>
                <button class="btn btn-outline-secondary" onclick="limparTodosFiltros()">
                    <i class="fas fa-times me-1"></i>Limpar Filtros
                </button>
            </div>
        `;
        pagination.innerHTML = '';
        return;
    }

    pageChamados.forEach(chamado => {
        const card = document.createElement('div');
        card.className = 'chamado-card';
        card.tabIndex = 0;

        const statusClass = chamado.status.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        const statusIcon = {
            'aberto': 'fa-circle-notch',
            'aguardando': 'fa-clock',
            'concluido': 'fa-check-circle',
            'cancelado': 'fa-times-circle'
        }[statusClass] || 'fa-circle';

card.innerHTML = `
    <div class="card-header">
        <h3>${chamado.codigo}</h3>
        <div class="status-badge status-${statusClass}">
            <i class="fas ${statusIcon}"></i>
            ${chamado.status}
        </div>
    </div>
    <div class="card-body">
        <div class="info-row">
            <strong>Solicitante:</strong>
            <span>${chamado.solicitante}</span>
        </div>
        <div class="info-row">
            <strong>Problema:</strong>
            <span>${chamado.problema}</span>
        </div>
        <div class="info-row">
            <strong>Unidade:</strong>
            <span>${chamado.unidade}</span>
        </div>
        <div class="info-row">
            <strong>Data:</strong>
            <span>${formatarData(chamado.data_abertura)}</span>
        </div>
        <div class="info-row">
            <strong>Agente:</strong>
            ${chamado.agente ? `
                <span class="badge bg-info">${chamado.agente.nome}</span>
                <button class="btn btn-sm btn-outline-warning ms-2" onclick="alterarAgente(${chamado.id})" title="Alterar agente">
                    <i class="fas fa-user-edit"></i>
                </button>
            ` : `
                <button class="btn btn-sm btn-success" onclick="atribuirAgente(${chamado.id})" title="Atribuir agente">
                    <i class="fas fa-user-plus"></i> Atribuir
                </button>
            `}
        </div>
    </div>
    <div class="card-footer">
        <select id="status-${chamado.id}">
            <option value="Aberto" ${chamado.status === 'Aberto' ? 'selected' : ''}>Aberto</option>
            <option value="Aguardando" ${chamado.status === 'Aguardando' ? 'selected' : ''}>Aguardando</option>
            <option value="Concluido" ${chamado.status === 'Concluido' ? 'selected' : ''}>Concluído</option>
            <option value="Cancelado" ${chamado.status === 'Cancelado' ? 'selected' : ''}>Cancelado</option>
        </select>
        <button class="btn btn-update-sm" data-id="${chamado.id}" title="Atualizar status">
            <i class="fas fa-save"></i> Atualizar
        </button>
        <button class="btn btn-danger-sm" data-id="${chamado.id}" title="Excluir chamado">
            <i class="fas fa-trash"></i> Excluir
        </button>
        <button class="btn btn-ticket-sm" data-id="${chamado.id}" title="Enviar ticket">
            <i class="fas fa-envelope"></i> Ticket
        </button>
    </div>
        `;

        // Abrir modal ao clicar no card (exceto nos elementos interativos)
        card.addEventListener('click', function(e) {
            if (!e.target.closest('.card-footer') && !e.target.closest('.status-badge')) {
                openModal(chamado);
            }
        });

        chamadosGrid.appendChild(card);
    });

    renderPagination(filteredChamados.length);
    attachCardEventListeners();
}

function formatarData(dataString) {
    if (!dataString) return 'Não informado';
    const [data, hora] = dataString.split(' ');
    const [dia, mes, ano] = data.split('/');
    return `${dia}/${mes}/${ano}`;
}

// Funç��o para renderizar a paginação
function renderPagination(totalItems) {
    pagination.innerHTML = '';
    const totalPages = Math.ceil(totalItems / chamadosPerPage);

    function createPageButton(num, active = false) {
        const btn = document.createElement('button');
        btn.textContent = num;
        btn.disabled = active;
        if (active) btn.classList.add('active');
        btn.addEventListener('click', () => {
            currentPage = num;
            renderChamadosPage(currentPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        return btn;
    }

    const prevBtn = document.createElement('button');
    prevBtn.textContent = '«';
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderChamadosPage(currentPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
    pagination.appendChild(prevBtn);

    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(startPage + 4, totalPages);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }
    for (let i = startPage; i <= endPage; i++) {
        pagination.appendChild(createPageButton(i, i === currentPage));
    }

    const nextBtn = document.createElement('button');
    nextBtn.textContent = '»';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderChamadosPage(currentPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
    pagination.appendChild(nextBtn);
}

// Função para anexar event listeners aos cards de chamados
function attachCardEventListeners() {
    // Listener para mudan��a no select de status dos chamados (apenas selects de status específicos)
    document.querySelectorAll('select[id^="status-"]:not(#filtroPrioridade):not(#filtroAgenteResponsavel):not(#filtroUnidade)').forEach(select => {
        select.addEventListener('click', function(e) {
            e.stopPropagation();
        });

        select.addEventListener('change', async function(e) {
            e.stopPropagation();
            const chamadoId = this.id.replace('status-', '');
            const novoStatus = this.value;
            
            try {
                await updateChamadoStatus(chamadoId, novoStatus);
                const mensagem = `Status atualizado para "${novoStatus}"${novoStatus === 'Aguardando' || novoStatus === 'Cancelado' || novoStatus === 'Concluido' ? '. E-mail enviado ao solicitante.' : ''}`;
                
                // Usar sistema de notificações avançado
                if (window.advancedNotificationSystem) {
                    window.advancedNotificationSystem.showSuccess('Status Atualizado', mensagem);
                }
            } catch (error) {
                if (window.advancedNotificationSystem) {
                    window.advancedNotificationSystem.showError('Erro', error.message);
                }
                const chamado = chamadosData.find(c => c.id == chamadoId);
                if (chamado) {
                    this.value = chamado.status;
                }
            }
        });
    });

    // Listener para botão Atualizar
    document.querySelectorAll('.btn-update-sm').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.stopPropagation();
            const chamadoId = this.dataset.id;
            const statusSelect = document.getElementById(`status-${chamadoId}`);
            const novoStatus = statusSelect.value;
            
            try {
                await updateChamadoStatus(chamadoId, novoStatus);
                const mensagem = `Status atualizado para "${novoStatus}"${novoStatus === 'Aguardando' || novoStatus === 'Cancelado' || novoStatus === 'Concluido' ? '. E-mail enviado ao solicitante.' : ''}`;
                
                // Usar sistema de notificações avançado
                if (window.advancedNotificationSystem) {
                    window.advancedNotificationSystem.showSuccess('Status Atualizado', mensagem);
                }
                renderChamadosPage(currentPage); // Atualiza a visualização
            } catch (error) {
                if (window.advancedNotificationSystem) {
                    window.advancedNotificationSystem.showError('Erro', error.message);
                }
                const chamado = chamadosData.find(c => c.id == chamadoId);
                if (chamado) {
                    statusSelect.value = chamado.status;
                }
            }
        });
    });

    // Listener para botão Excluir
    document.querySelectorAll('.btn-danger-sm').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.stopPropagation();
            const chamadoId = this.dataset.id;
            await excluirChamado(chamadoId);
        });
    });

    // Listener para botão Enviar Ticket
    document.querySelectorAll('.btn-ticket-sm').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            const id = btn.dataset.id;
            
    const chamado = chamadosData.find(c => c.id == id);
    if (chamado) {
        openTicketModal(chamado);
    } else {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Chamado não encontrado.');
        }
    }
    ;
        });
    });
}

// Event listener para os links do submenu de gerenciar chamados
document.querySelectorAll('#submenu-gerenciar-chamados a').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const status = this.getAttribute('data-status');
        currentFilter = status;
        currentPage = 1;
        renderChamadosPage(currentPage);
        activateSection('gerenciar-chamados');
        
        // Atualizar o item ativo no menu
        document.querySelectorAll('.sidebar a.active').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
        const parentSubmenuToggle = this.closest('.submenu').previousElementSibling;
        parentSubmenuToggle.classList.add('active');
    });
});

// Modal Chamado - Elementos
const modal = document.getElementById('modalChamado');
const modalCloseBtn = document.getElementById('modalClose');
const modalCancelBtn = document.getElementById('modalCancel');
const modalSaveBtn = document.getElementById('modalSave');
const modalSendTicketBtn = document.getElementById('modalSendTicket');

const modalCodigo = document.getElementById('modalCodigo');
const modalProtocolo = document.getElementById('modalProtocolo');
const modalSolicitante = document.getElementById('modalSolicitante');
const modalCargo = document.getElementById('modalCargo');
const modalTelefone = document.getElementById('modalTelefone');
const modalUnidade = document.getElementById('modalUnidade');
const modalProblema = document.getElementById('modalProblema');
const modalDescricao = document.getElementById('modalDescricao');
const modalVisita = document.getElementById('modalVisita');
const modalData = document.getElementById('modalData');
const modalStatusSelect = document.getElementById('modalStatus');

let currentModalChamadoId = null;

// Funções do Modal de Chamados
function openModal(chamado) {
    currentModalChamadoId = chamado.id;
    modalCodigo.textContent = chamado.codigo;
    modalProtocolo.textContent = chamado.protocolo;
    modalSolicitante.textContent = chamado.solicitante;
    modalCargo.textContent = chamado.cargo;
    modalTelefone.textContent = chamado.telefone;
    modalUnidade.textContent = chamado.unidade;
    modalProblema.textContent = chamado.problema;
    modalDescricao.textContent = chamado.descricao;
    modalVisita.textContent = chamado.visita_tecnica ? 'Sim' : 'Não';
    modalData.textContent = chamado.data_abertura.split(' ')[0];
    modalStatusSelect.value = chamado.status;

    modal.classList.add('active');
}

function closeModal() {
    modal.classList.remove('active');
    currentModalChamadoId = null;
}

// Event Listeners do Modal de Chamados
modalCloseBtn.addEventListener('click', closeModal);
modalCancelBtn.addEventListener('click', closeModal);
modal.addEventListener('click', e => {
    if (e.target === modal) closeModal();
});

// No modalSaveBtn
modalSaveBtn.addEventListener('click', async () => {
    if (!currentModalChamadoId) {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Nenhum chamado selecionado.');
        }
        return;
    }
    
    const novoStatus = modalStatusSelect.value;
    
    try {
        await updateChamadoStatus(currentModalChamadoId, novoStatus);
        closeModal();
        const mensagem = `Status atualizado para "${novoStatus}"${novoStatus === 'Aguardando' || novoStatus === 'Cancelado' || novoStatus === 'Concluido' ? '. E-mail enviado ao solicitante.' : ''}`;
        
        // Usar sistema de notificações avançado
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Status Atualizado', mensagem);
        }
        renderChamadosPage(currentPage); // Atualiza a visualização
    } catch (error) {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
});

modalSendTicketBtn.addEventListener('click', () => {
    if (!currentModalChamadoId) {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Nenhum chamado selecionado.');
        }
        return;
    }
    
    const chamado = chamadosData.find(c => c.id == currentModalChamadoId);
    if (chamado) {
        openTicketModal(chamado);
    } else {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Chamado não encontrado.');
        }
    }
    ;
});

// Funcionalidades de Usuário
// Função para gerar nome de usuário automaticamente
function gerarNomeUsuario() {
    const nome = document.getElementById('nomeUsuario').value.trim().toLowerCase();
    const sobrenome = document.getElementById('sobrenomeUsuario').value.trim().toLowerCase();

    if (nome && sobrenome) {
        // Remove acentos e caracteres especiais
        const nomeNormalizado = nome.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        const sobrenomeNormalizado = sobrenome.normalize('NFD').replace(/[\u0300-\u036f]/g, '');

        // Gera o nome de usuário
        const usuario = `${nomeNormalizado.split(' ')[0]}.${sobrenomeNormalizado.split(' ')[0]}`;
        document.getElementById('usuarioLogin').value = usuario;
    }
}

// Event listener para botão de gerar usuário automaticamente
document.getElementById('btnGerarUsuario')?.addEventListener('click', function() {
    gerarNomeUsuario();
    if (window.advancedNotificationSystem) {
        window.advancedNotificationSystem.showInfo('Nome de usuário gerado', 'Nome de usuário gerado automaticamente baseado no nome e sobrenome.');
    }
});

// Não gerar automaticamente mais - só quando clicar no botão
// document.getElementById('nomeUsuario')?.addEventListener('input', gerarNomeUsuario);
// document.getElementById('sobrenomeUsuario')?.addEventListener('input', gerarNomeUsuario);

// Prevenir comportamento padrão dos selects e detectar Agente de Suporte
document.getElementById('nivelAcesso')?.addEventListener('click', function(e) {
    e.stopPropagation();
});

// Detectar quando usuário seleciona "Agente de Suporte"
document.getElementById('nivelAcesso')?.addEventListener('change', function(e) {
    if (this.value === 'Agente de Suporte') {
        // Automaticamente criar agente de suporte após criar o usuário
        console.log('Nível "Agente de Suporte" selecionado - agente será criado automaticamente');
    }
});

document.getElementById('setorUsuario')?.addEventListener('click', function(e) {
    e.stopPropagation();
});

// Função para gerar senha
async function gerarSenha() {
    try {
        const response = await fetch('/ti/painel/api/gerar-senha');
        if (!response.ok) {
            throw new Error('Erro ao gerar senha');
        }
        
        const data = await response.json();
        
        // Atualiza campos da senha gerada de forma compacta no formulário
        document.getElementById('senhaGeradaInput').value = data.senha;

        // Mostra container compacto
        document.getElementById('senhaGeradaContainer').style.display = 'block';
    } catch (error) {
        console.error('Erro ao gerar senha:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao gerar senha. Tente novamente.');
        }
    }
}

// Event listener para o botão de gerar senha
document.getElementById('btnGerarSenha')?.addEventListener('click', function(e) {
    e.preventDefault();
    gerarSenha();
});

// Função para validar dados do usuário
function validarDadosUsuario(dados) {
    const erros = [];
    
    if (!dados.nome) erros.push('Nome é obrigat��rio');
    if (!dados.sobrenome) erros.push('Sobrenome é obrigatório');
    if (!dados.email) erros.push('E-mail é obrigatório');
    if (!dados.usuario) erros.push('Nome de usuário é obrigatório');
    if (!dados.senha) erros.push('Senha é obrigatória. Clique em "Gerar Senha"');
    if (!dados.nivel_acesso) erros.push('N��vel de acesso é obrigatório');
    if (!dados.setor || dados.setor.length === 0) erros.push('Selecione pelo menos um setor');
    
    // Validação de e-mail
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (dados.email && !emailRegex.test(dados.email)) {
        erros.push('E-mail inválido');
    }
    
    return erros;
}

// Event listener para o formulário de criar usuário
document.getElementById('formCriarUsuario')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Elementos de mensagem
    const mensagemErro = document.getElementById('mensagemErro');
    const mensagemSucesso = document.getElementById('mensagemSucesso');
    
    // Esconde mensagens anteriores
    mensagemErro.style.display = 'none';
    mensagemSucesso.style.display = 'none';
    
    // Desabilita o botão de submit para evitar duplo envio
    const submitButton = this.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Criando usuário...';
    
    try {
        // Coleta dados do formulário
        const usuarioData = {
            nome: document.getElementById('nomeUsuario').value.trim(),
            sobrenome: document.getElementById('sobrenomeUsuario').value.trim(),
            email: document.getElementById('emailUsuario').value.trim(),
            usuario: document.getElementById('usuarioLogin').value.trim(),
            senha: document.getElementById('senhaGeradaInput').value,
            nivel_acesso: document.getElementById('nivelAcesso').value,
            setor: Array.from(document.getElementById('setorUsuario').selectedOptions).map(opt => opt.value),
            alterar_senha_primeiro_acesso: document.getElementById('alterarSenhaPrimeiroAcesso').checked
        };

        // Validaç����o
        const errosValidacao = validarDadosUsuario(usuarioData);
        if (errosValidacao.length > 0) {
            throw new Error(errosValidacao.join('<br>'));
        }

        // Enviar para a API
        const response = await fetch('/ti/painel/api/usuarios', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(usuarioData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Erro ao criar usuário');
        }

        // Se foi selecionado "Agente de Suporte", criar automaticamente o agente
        if (usuarioData.nivel_acesso === 'Agente de Suporte') {
            try {
                const agenteResponse = await fetch('/ti/painel/api/agentes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        usuario_id: data.id,
                        ativo: true,
                        nivel_experiencia: 'junior',
                        max_chamados_simultaneos: 10,
                        especialidades: []
                    })
                });

                if (agenteResponse.ok) {
                    if (window.advancedNotificationSystem) {
                        window.advancedNotificationSystem.showSuccess('Usuário e Agente Criados', `Usuário ${data.nome} criado e registrado como agente de suporte!`);
                    }
                } else {
                    if (window.advancedNotificationSystem) {
                        window.advancedNotificationSystem.showWarning('Usuário Criado', `Usuário ${data.nome} criado, mas houve erro ao registrar como agente.`);
                    }
                }
            } catch (agenteError) {
                console.error('Erro ao criar agente:', agenteError);
                if (window.advancedNotificationSystem) {
                    window.advancedNotificationSystem.showWarning('Usuário Criado', `Usuário ${data.nome} criado, mas houve erro ao registrar como agente.`);
                }
            }
        } else {
            // Usar sistema de notificações avançado para usuário normal
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showSuccess('Usuário Criado', `Usuário ${data.nome} criado com sucesso!`);
            }
        }

        // Mostrar credenciais no modal
        document.getElementById('credenciaisNome').textContent = `${data.nome} ${data.sobrenome}`;
        document.getElementById('credenciaisUsuario').textContent = data.usuario;
        document.getElementById('credenciaisSenha').textContent = usuarioData.senha;

        // Abrir modal de credenciais
        document.getElementById('modalCredenciais').classList.add('active');

        // Limpar formulário
        this.reset();
        document.getElementById('senhaGeradaContainer').style.display = 'none';

        // Atualizar lista de usuários se estiver visível
        if (document.getElementById('permissoes').classList.contains('active')) {
            await loadUsuarios();
        }

        // Atualizar lista de agentes se estiver visível
        if (document.getElementById('agentes-suporte').classList.contains('active')) {
            await carregarAgentes();
        }
        
    } catch (error) {
        console.error('Erro ao criar usuário:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    } finally {
        // Reabilita o botão de submit
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    }
});

// Validação em tempo real do e-mail
document.getElementById('emailUsuario')?.addEventListener('input', function() {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (this.value && !emailRegex.test(this.value)) {
        this.classList.add('is-invalid');
        this.classList.remove('is-valid');
    } else if (this.value) {
        this.classList.add('is-valid');
        this.classList.remove('is-invalid');
    } else {
        this.classList.remove('is-valid', 'is-invalid');
    }
});

// Validação em tempo real para campos obrigatórios
['nomeUsuario', 'sobrenomeUsuario', 'nivelAcesso', 'setorUsuario'].forEach(id => {
    const elemento = document.getElementById(id);
    if (elemento) {
        elemento.addEventListener('change', function() {
            if (this.value) {
                this.classList.add('is-valid');
                this.classList.remove('is-invalid');
            } else {
                this.classList.add('is-invalid');
                this.classList.remove('is-valid');
            }
        });
    }
});

// Modal Add Unidade
const modalAddUnidade = document.getElementById('modalAddUnidade');
const btnOpenAddUnitModal = document.getElementById('btnOpenAddUnitModal');
const modalAddUnidadeClose = document.getElementById('modalAddUnidadeClose');
const btnSalvarUnidade = document.getElementById('btnSalvarUnidade');
const btnCancelarUnidade = document.getElementById('btnCancelarUnidade');
const inputIdUnidade = document.getElementById('inputIdUnidade');
const inputNomeUnidade = document.getElementById('inputNomeUnidade');
const errorAddUnidade = document.getElementById('errorAddUnidade');

function openAddUnidadeModal() {
    inputIdUnidade.value = '';
    inputNomeUnidade.value = '';
    errorAddUnidade.style.display = 'none';
    modalAddUnidade.classList.add('active');
}

function closeAddUnidadeModal() {
    modalAddUnidade.classList.remove('active');
    errorAddUnidade.style.display = 'none';
    inputNomeUnidade.value = '';
    inputIdUnidade.value = '';
}

// Função para buscar unidades
async function fetchUnidades() {
    try {
        const response = await fetch('/ti/painel/api/unidades');
        if (!response.ok) {
            throw new Error(`Erro HTTP: ${response.status} - ${response.statusText}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Erro ao buscar unidades:', error);
        throw error;
    }
}

// Função para renderizar a lista de unidades
async function renderListarUnidades() {
    const lista = document.getElementById('listaUnidades');
    try {
        lista.innerHTML = '<tr><td colspan="3" class="text-center">Carregando unidades...</td></tr>';
        
        const unidades = await fetchUnidades();
        
        if (unidades.length === 0) {
            lista.innerHTML = '<tr><td colspan="3" class="text-center">Nenhuma unidade cadastrada.</td></tr>';
            return;
        }
        
        lista.innerHTML = '';
        
        unidades.forEach(unidade => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${unidade.id}</td>
                <td>${unidade.nome}</td>
                <td>
                    <button class="btn btn-danger btn-sm btn-remover-unidade" data-id="${unidade.id}">
                        <i class="fas fa-trash"></i> Remover
                    </button>
                </td>
            `;
            lista.appendChild(row);
        });

        // Adiciona event listeners aos botões de remover
        document.querySelectorAll('.btn-remover-unidade').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.dataset.id;
                const unidadeNome = btn.closest('tr').querySelector('td:nth-child(2)').textContent;
                
                if (confirm(`Tem certeza que deseja remover a unidade "${unidadeNome}"?`)) {
                    try {
                        const response = await fetch(`/ti/painel/api/unidades/${id}`, {
                            method: 'DELETE'
                        });
                        
                        if (response.ok) {
                            if (window.advancedNotificationSystem) {
                                window.advancedNotificationSystem.showSuccess('Unidade Removida', 'Unidade removida com sucesso!');
                            }
                            await renderListarUnidades();
                        } else {
                            const errorData = await response.json();
                            if (window.advancedNotificationSystem) {
                                window.advancedNotificationSystem.showError('Erro', errorData.error || 'Erro ao remover unidade');
                            }
                        }
                    } catch (error) {
                        console.error('Erro ao remover unidade:', error);
                        if (window.advancedNotificationSystem) {
                            window.advancedNotificationSystem.showError('Erro', 'Erro ao remover unidade');
                        }
                    }
                }
            });
        });
    } catch (error) {
        lista.innerHTML = `<tr><td colspan="3" class="text-center text-danger">${error.message}</td></tr>`;
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar unidades');
        }
    }
}

// Event listeners para modal de unidade
btnOpenAddUnitModal.addEventListener('click', openAddUnidadeModal);
modalAddUnidadeClose.addEventListener('click', closeAddUnidadeModal);
btnCancelarUnidade.addEventListener('click', closeAddUnidadeModal);

// Event listener para o botão de salvar unidade
btnSalvarUnidade.addEventListener('click', async () => {
    const id = inputIdUnidade.value.trim();
    const nome = inputNomeUnidade.value.trim();

    // Validações
    if (!id || isNaN(id) || parseInt(id) <= 0) {
        errorAddUnidade.textContent = 'Por favor, informe um ID válido maior que zero.';
        errorAddUnidade.style.display = 'block';
        return;
    }
    if (!nome) {
        errorAddUnidade.textContent = 'Por favor, informe o nome da unidade.';
        errorAddUnidade.style.display = 'block';
        return;
    }

    try {
        const response = await fetch('/ti/painel/api/unidades', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                id: parseInt(id), 
                nome: nome 
            })
        });
        
        if (response.ok) {
            closeAddUnidadeModal();
            await renderListarUnidades();
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showSuccess('Unidade Adicionada', 'Unidade adicionada com sucesso!');
            }
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao adicionar unidade');
        }
    } catch (error) {
        errorAddUnidade.textContent = error.message;
        errorAddUnidade.style.display = 'block';
    }
});

// Event listeners para o modal de credenciais
document.getElementById('btnCopiarCredenciais')?.addEventListener('click', function() {
    const nome = document.getElementById('credenciaisNome').textContent;
    const usuario = document.getElementById('credenciaisUsuario').textContent;
    const senha = document.getElementById('credenciaisSenha').textContent;
    
    const texto = `Nome: ${nome}\nUsuário: ${usuario}\nSenha: ${senha}`;
    
    navigator.clipboard.writeText(texto).then(() => {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Copiado', 'Credenciais copiadas para a área de transferência!');
        }
    }).catch(err => {
        console.error('Erro ao copiar texto: ', err);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showWarning('Aviso', 'Não foi possível copiar as credenciais automaticamente. Por favor, copie manualmente.');
        }
    });
});

document.getElementById('btnFecharCredenciais')?.addEventListener('click', function() {
    document.getElementById('modalCredenciais').classList.remove('active');
});

// Função para excluir chamado
async function excluirChamado(chamadoId) {
    if (!confirm('Tem certeza que deseja excluir este chamado? Esta ação não pode ser desfeita.')) {
        return false; // Retorna false se o usuário cancelar
    }
    
    try {
        const response = await fetch(`/ti/painel/api/chamados/${chamadoId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao excluir chamado');
        }
        
        // Remove o chamado da lista local
        chamadosData = chamadosData.filter(chamado => chamado.id != chamadoId);
        
        // Atualiza a visualização
        renderChamadosPage(currentPage);
        
        // Usar sistema de notificações avançado
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Chamado Excluído', 'Chamado excluído com sucesso');
        }
        return true; // Retorna true se a exclusão foi bem-sucedida
    } catch (error) {
        console.error('Erro ao excluir chamado:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', `Erro: ${error.message}`);
        }
        return false;
    }
}

// Listener para botão Excluir no modal
document.getElementById('modalDelete')?.addEventListener('click', async function() {
    if (!currentModalChamadoId) {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Nenhum chamado selecionado.');
        }
        return;
    }
    await excluirChamado(currentModalChamadoId);
    closeModal();
});

// Variáveis globais para usuários
let usuariosData = [];
const usuariosPerPage = 6;
let currentUsuariosPage = 1;

const usuariosGrid = document.getElementById('usuariosGrid');
const usuariosPagination = document.getElementById('usuariosPagination');

// Função para carregar os usuários da API
async function loadUsuarios() {
    try {
        const response = await fetch('/ti/painel/api/usuarios');
        if (!response.ok) {
            throw new Error('Erro ao carregar usuários');
        }
        usuariosData = await response.json();
        renderUsuariosPage(currentUsuariosPage);

        // Inicializar filtro após carregar usuários
        setTimeout(() => {
            if (typeof inicializarFiltroPermissoes === 'function') {
                inicializarFiltroPermissoes();
            }
        }, 100);

    } catch (error) {
        console.error('Erro ao carregar usuários:', error);
        usuariosGrid.innerHTML = '<p class="text-center py-4">Erro ao carregar usuários. Tente novamente mais tarde.</p>';
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar usuários');
        }
    }
}

// Função para renderizar a página de usuários
function renderUsuariosPage(page) {
    usuariosGrid.innerHTML = '';
    const start = (page - 1) * usuariosPerPage;
    const end = start + usuariosPerPage;
    const pageUsuarios = usuariosData.slice(start, end);

    if (pageUsuarios.length === 0) {
        usuariosGrid.innerHTML = '<p class="text-center py-4">Nenhum usuário encontrado.</p>';
        usuariosPagination.innerHTML = '';
        return;
    }

    pageUsuarios.forEach(usuario => {
        const card = document.createElement('div');
        card.className = 'card usuario-card';
        card.tabIndex = 0;

        const bloqueadoClass = usuario.bloqueado ? 'status-cancelado' : 'status-concluido';
        const bloqueadoText = usuario.bloqueado ? 'Bloqueado' : 'Ativo';

        card.innerHTML = `
            <div class="card-header">
                <h3>${usuario.nome} ${usuario.sobrenome}</h3>
                <div class="status-badge ${bloqueadoClass}">
                    <i class="fas ${usuario.bloqueado ? 'fa-lock' : 'fa-check-circle'}"></i>
                    ${bloqueadoText}
                </div>
            </div>
            <div class="card-body">
                <div class="info-row">
                    <strong>Usuário:</strong>
                    <span>${usuario.usuario}</span>
                </div>
                <div class="info-row">
                    <strong>E-mail:</strong>
                    <span>${usuario.email}</span>
                </div>
                <div class="info-row">
                    <strong>Nível:</strong>
                    <span>${usuario.nivel_acesso}</span>
                </div>
                <div class="info-row">
                    <strong>Setor(es):</strong>
                    <span>${Array.isArray(usuario.setores) ? usuario.setores.join(', ') : usuario.setor}</span>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary btn-sm btn-editar" data-id="${usuario.id}">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="btn ${usuario.bloqueado ? 'btn-success' : 'btn-warning'} btn-sm" 
                        data-id="${usuario.id}">
                    <i class="fas ${usuario.bloqueado ? 'fa-unlock' : 'fa-lock'}"></i>
                    ${usuario.bloqueado ? 'Desbloquear' : 'Bloquear'}
                </button>
                <button class="btn btn-info btn-sm btn-ticket" data-id="${usuario.id}">
                    <i class="fas fa-key"></i> Nova Senha
                </button>
                <button class="btn btn-danger btn-sm" data-id="${usuario.id}">
                    <i class="fas fa-trash"></i> Excluir
                </button>
            </div>
        `;

        usuariosGrid.appendChild(card);
    });

    renderUsuariosPagination(usuariosData.length);
    attachUsuariosEventListeners();
}

// Função para renderizar a paginação de usuários
function renderUsuariosPagination(totalItems) {
    usuariosPagination.innerHTML = '';
    const totalPages = Math.ceil(totalItems / usuariosPerPage);

    function createPageButton(num, active = false) {
        const btn = document.createElement('button');
        btn.textContent = num;
        btn.disabled = active;
        if (active) btn.classList.add('active');
        btn.addEventListener('click', () => {
            currentUsuariosPage = num;
            renderUsuariosPage(currentUsuariosPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        return btn;
    }

    const prevBtn = document.createElement('button');
    prevBtn.textContent = '«';
    prevBtn.disabled = currentUsuariosPage === 1;
    prevBtn.addEventListener('click', () => {
        if (currentUsuariosPage > 1) {
            currentUsuariosPage--;
            renderUsuariosPage(currentUsuariosPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
    usuariosPagination.appendChild(prevBtn);

    let startPage = Math.max(1, currentUsuariosPage - 2);
    let endPage = Math.min(startPage + 4, totalPages);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }
    for (let i = startPage; i <= endPage; i++) {
        usuariosPagination.appendChild(createPageButton(i, i === currentUsuariosPage));
    }

    const nextBtn = document.createElement('button');
    nextBtn.textContent = '»';
    nextBtn.disabled = currentUsuariosPage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (currentUsuariosPage < totalPages) {
            currentUsuariosPage++;
            renderUsuariosPage(currentUsuariosPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
    usuariosPagination.appendChild(nextBtn);
}

// Função para anexar event listeners aos cards de usuários
function attachUsuariosEventListeners() {
    // Listener para botão Editar
    document.querySelectorAll('.btn-editar').forEach(btn => {
        btn.addEventListener('click', function() {
            const usuarioId = this.dataset.id;
            abrirModalEditarUsuario(usuarioId);
        });
    });

    // Listener para botão Gerar Senha
    document.querySelectorAll('.btn-ticket').forEach(btn => {
        btn.addEventListener('click', async function() {
            const usuarioId = this.dataset.id;
            await gerarNovaSenha(usuarioId);
        });
    });

    // Listener para botão Bloquear/Desbloquear
    document.querySelectorAll('.btn-warning, .btn-success').forEach(btn => {
        btn.addEventListener('click', async function() {
            const usuarioId = this.dataset.id;
            await toggleBloqueioUsuario(usuarioId);
        });
    });

    // Listener para botão Excluir
    document.querySelectorAll('.btn-danger').forEach(btn => {
        btn.addEventListener('click', async function() {
            const usuarioId = this.dataset.id;
            await excluirUsuario(usuarioId);
        });
    });
}

// Função para abrir modal de edição
function abrirModalEditarUsuario(usuarioId) {
    const usuario = usuariosData.find(u => u.id == usuarioId);
    if (!usuario) return;

    // Preencher formulário
    document.getElementById('editUsuarioId').value = usuario.id;
    document.getElementById('editNomeUsuario').value = usuario.nome;
    document.getElementById('editSobrenomeUsuario').value = usuario.sobrenome;
    document.getElementById('editUsuarioLogin').value = usuario.usuario;
    document.getElementById('editEmailUsuario').value = usuario.email;
    document.getElementById('editNivelAcesso').value = usuario.nivel_acesso;
    document.getElementById('editBloqueado').checked = usuario.bloqueado;

    // Limpar e selecionar setores
    const setorSelect = document.getElementById('editSetorUsuario');
    Array.from(setorSelect.options).forEach(option => {
        option.selected = usuario.setores.includes(option.value);
    });

    // Abrir modal
    document.getElementById('modalEditarUsuario').classList.add('active');
}

// Função para gerar nova senha
async function gerarNovaSenha(usuarioId) {
    if (!confirm('Tem certeza que deseja gerar uma nova senha para este usuário?')) return;
    
    try {
        const response = await fetch(`/ti/painel/api/usuarios/${usuarioId}/gerar-senha`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao gerar nova senha');
        }
        
        const data = await response.json();
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Nova Senha Gerada', `Nova senha gerada: ${data.nova_senha}`);
        }
    } catch (error) {
        console.error('Erro ao gerar nova senha:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', `Erro: ${error.message}`);
        }
    }
}

// Função para bloquear/desbloquear usuário
async function toggleBloqueioUsuario(usuarioId) {
    try {
        const response = await fetch(`/ti/painel/api/usuarios/${usuarioId}/bloquear`, {
            method: 'PUT'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao alterar status');
        }
        
        const data = await response.json();
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Status Alterado', `Usuário ${data.bloqueado ? 'bloqueado' : 'desbloqueado'} com sucesso!`);
        }
        await loadUsuarios();
    } catch (error) {
        console.error('Erro ao alterar status do usuário:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', `Erro: ${error.message}`);
        }
    }
}

// Função para excluir usuário
async function excluirUsuario(usuarioId) {
    if (!confirm('Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita.')) return;
    
    try {
        const response = await fetch(`/ti/painel/api/usuarios/${usuarioId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao excluir usuário');
        }
        
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Usuário Excluído', 'Usuário excluído com sucesso!');
        }
        await loadUsuarios();
    } catch (error) {
        console.error('Erro ao excluir usuário:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', `Erro: ${error.message}`);
        }
    }
}

// Event listener para salvar edição
document.getElementById('btnSalvarUsuario').addEventListener('click', async () => {
    const usuarioId = document.getElementById('editUsuarioId').value;
    const nome = document.getElementById('editNomeUsuario').value.trim();
    const sobrenome = document.getElementById('editSobrenomeUsuario').value.trim();
    const usuario = document.getElementById('editUsuarioLogin').value.trim();
    const email = document.getElementById('editEmailUsuario').value.trim();
    const nivelAcesso = document.getElementById('editNivelAcesso').value;
    const setorSelect = document.getElementById('editSetorUsuario');
    const setores = Array.from(setorSelect.selectedOptions).map(option => option.value);
    const bloqueado = document.getElementById('editBloqueado').checked;

    try {
        const response = await fetch(`/ti/painel/api/usuarios/${usuarioId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nome,
                sobrenome,
                usuario,
                email,
                nivel_acesso: nivelAcesso,
                setores,
                bloqueado
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao atualizar usuário');
        }
        
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Usuário Atualizado', 'Usuário atualizado com sucesso!');
        }
        document.getElementById('modalEditarUsuario').classList.remove('active');
        await loadUsuarios();
    } catch (error) {
        console.error('Erro ao atualizar usu��rio:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', `Erro: ${error.message}`);
        }
    }
});

// Event listener para cancelar edição
document.getElementById('btnCancelarEdicao').addEventListener('click', () => {
    document.getElementById('modalEditarUsuario').classList.remove('active');
});

// Adicione estas variáveis globais junto com as outras
let usuariosBloqueadosData = [];
const usuariosBloqueadosPerPage = 6;
let currentBloqueadosPage = 1;

// Função para carregar usuários bloqueados
async function loadUsuariosBloqueados() {
    try {
        const response = await fetch('/ti/painel/api/usuarios');
        if (!response.ok) {
            throw new Error('Erro ao carregar usuários');
        }
        const allUsers = await response.json();
        usuariosBloqueadosData = allUsers.filter(user => user.bloqueado);
        renderUsuariosBloqueadosPage(currentBloqueadosPage);
    } catch (error) {
        console.error('Erro ao carregar usuários bloqueados:', error);
        document.getElementById('usuariosBloqueadosGrid').innerHTML = 
            '<p class="text-center py-4">Erro ao carregar usuários bloqueados. Tente novamente mais tarde.</p>';
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar usuários bloqueados');
        }
    }
}

// Função para renderizar a página de usuários bloqueados
function renderUsuariosBloqueadosPage(page) {
    const bloqueadosGrid = document.getElementById('usuariosBloqueadosGrid');
    const bloqueadosPagination = document.getElementById('usuariosBloqueadosPagination');
    
    bloqueadosGrid.innerHTML = '';
    const start = (page - 1) * usuariosBloqueadosPerPage;
    const end = start + usuariosBloqueadosPerPage;
    const pageBloqueados = usuariosBloqueadosData.slice(start, end);

    if (pageBloqueados.length === 0) {
        bloqueadosGrid.innerHTML = '<p class="text-center py-4">Nenhum usuário bloqueado encontrado.</p>';
        bloqueadosPagination.innerHTML = '';
        return;
    }

    pageBloqueados.forEach(usuario => {
        const card = document.createElement('div');
        card.className = 'card usuario-card';
        card.tabIndex = 0;

        card.innerHTML = `
            <div class="card-header">
                <h3>${usuario.nome} ${usuario.sobrenome}</h3>
                <div class="status-container status-cancelado">Bloqueado</div>
            </div>
            <div class="card-body">
                <p><strong>Usuário:</strong> ${usuario.usuario}</p>
                <p><strong>E-mail:</strong> ${usuario.email}</p>
                <p><strong>Nível de Acesso:</strong> ${usuario.nivel_acesso}</p>
                <p><strong>Setor(es):</strong> ${usuario.setores.join(', ')}</p>
                <small><strong>Criado em:</strong> ${usuario.data_criacao}</small>
            </div>
            <div class="card-footer">
                <button class="btn btn-success btn-desbloquear" data-id="${usuario.id}" 
                    aria-label="Desbloquear usuário ${usuario.usuario}">
                    <i class="fas fa-unlock"></i> Desbloquear
                </button>
            </div>
        `;

        bloqueadosGrid.appendChild(card);
    });

    renderBloqueadosPagination(usuariosBloqueadosData.length);
    attachBloqueadosEventListeners();
}

// Função para renderizar a paginação dos bloqueados
function renderBloqueadosPagination(totalItems) {
    const bloqueadosPagination = document.getElementById('usuariosBloqueadosPagination');
    bloqueadosPagination.innerHTML = '';
    const totalPages = Math.ceil(totalItems / usuariosBloqueadosPerPage);

    // ... (similar à função renderPagination existente, mas para bloqueados)
}

// Função para anexar event listeners aos cards de usuários bloqueados
function attachBloqueadosEventListeners() {
    document.querySelectorAll('.btn-desbloquear').forEach(btn => {
        btn.addEventListener('click', async function() {
            const usuarioId = this.dataset.id;
            try {
                await toggleBloqueioUsuario(usuarioId);
                // Recarrega tanto a lista de bloqueados quanto a lista geral
                await loadUsuariosBloqueados();
                if (document.getElementById('permissoes').classList.contains('active')) {
                    await loadUsuarios();
                }
            } catch (error) {
                console.error('Erro ao desbloquear usuário:', error);
                if (window.advancedNotificationSystem) {
                    window.advancedNotificationSystem.showError('Erro', 'Erro ao desbloquear usuário');
                }
            }
        });
    });
}

// Função para carregar conteúdo específico da seção quando ativada
function loadSectionContent(sectionId) {
    console.log('Carregando conteúdo da seção:', sectionId);

    switch(sectionId) {
        case 'listar-unidades':
            if (typeof renderListarUnidades === 'function') {
                renderListarUnidades();
            }
            break;
        case 'gerenciar-chamados':
            loadChamados();
            // Adicionar filtro de agente após carregar chamados
            setTimeout(() => {
                if (typeof adicionarFiltroAgente === 'function') {
                    adicionarFiltroAgente();
                }
            }, 500);
            break;
        case 'permissoes':
            loadUsuarios();
            // Inicializar filtro de permissões após carregar usuários
            setTimeout(() => {
                if (typeof inicializarFiltroPermissoes === 'function') {
                    inicializarFiltroPermissoes();
                }
            }, 100);
            break;
        case 'bloqueios':
            if (typeof loadUsuariosBloqueados === 'function') {
                loadUsuariosBloqueados();
            }
            break;
        case 'sla-dashboard':
            // Carregar dados SLA se a função existir
            if (typeof carregarSLA === 'function') {
                carregarSLA();
            }
            break;
        case 'configuracoes':
            // Carregar configurações de prioridades
            if (window.prioridadesManager && typeof window.prioridadesManager.carregarProblemas === 'function') {
                window.prioridadesManager.carregarProblemas();
            }
            atualizarContadoresVisaoGeral();
            break;
        case 'agentes-suporte':
            // Carregar agentes de suporte
            console.log('Carregando seção de agentes de suporte...');
            if (typeof carregarAgentes === 'function') {
                console.log('Função carregarAgentes encontrada, executando...');
                carregarAgentes();
            } else {
                console.log('Função carregarAgentes não encontrada, tentando novamente em 100ms...');
                setTimeout(() => {
                    if (typeof carregarAgentes === 'function') {
                        console.log('Função carregarAgentes encontrada no retry, executando...');
                        carregarAgentes();
                    } else {
                        console.error('Função carregarAgentes ainda não disponível. Verifique o carregamento dos scripts.');
                    }
                }, 100);
            }
            break;
        case 'grupos-usuarios':
            // Carregar grupos de usuários
            console.log('Carregando seção de grupos de usuários...');
            if (typeof inicializarGrupos === 'function') {
                console.log('Função inicializarGrupos encontrada, executando...');
                inicializarGrupos();
            } else if (typeof carregarGrupos === 'function') {
                console.log('Função carregarGrupos encontrada, executando...');
                carregarGrupos();
            } else {
                console.log('Funções de grupos não encontradas, tentando novamente em 100ms...');
                setTimeout(() => {
                    if (typeof inicializarGrupos === 'function') {
                        console.log('Função inicializarGrupos encontrada no retry, executando...');
                        inicializarGrupos();
                    } else if (typeof carregarGrupos === 'function') {
                        console.log('Função carregarGrupos encontrada no retry, executando...');
                        carregarGrupos();
                    } else {
                        console.error('Funções de grupos ainda não disponíveis. Verifique o carregamento dos scripts.');
                    }
                }, 100);
            }
            break;
        case 'visao-geral':
            atualizarContadoresVisaoGeral();
            break;
        case 'configuracoes-avancadas':
            if (typeof carregarConfiguracoesAvancadas === 'function') {
                carregarConfiguracoesAvancadas();
            }
            break;
        case 'alertas-sistema':
            if (typeof carregarAlertasSistema === 'function') {
                carregarAlertasSistema();
            }
            break;
        case 'backup-manutencao':
            if (typeof carregarBackupManutencao === 'function') {
                carregarBackupManutencao();
            }
            break;
        case 'logs-acesso':
            if (typeof carregarLogsAcesso === 'function') {
                carregarLogsAcesso();
            }
            break;
        case 'logs-acoes':
            if (typeof carregarLogsAcoes === 'function') {
                carregarLogsAcoes();
            }
            break;
        case 'analise-problemas':
            if (typeof carregarAnaliseProblemas === 'function') {
                carregarAnaliseProblemas();
            }
            break;
        case 'monitoramento-catraca':
            if (typeof carregarMonitoramentoCatraca === 'function') {
                carregarMonitoramentoCatraca();
            }
            break;
        case 'monitoramento-mikrotiks':
            if (typeof carregarMonitoramentoMikrotiks === 'function') {
                carregarMonitoramentoMikrotiks();
            }
            break;
        case 'monitoramento-usuarios':
            if (typeof carregarMonitoramentoUsuarios === 'function') {
                carregarMonitoramentoUsuarios();
            }
            break;
        case 'dashboard-avancado':
            if (typeof carregarDashboardAvancado === 'function') {
                carregarDashboardAvancado();
            }
            break;
    }
}

// Controle de inatividade (15 minutos)
let inactivityTimer;

function resetInactivityTimer() {
    clearTimeout(inactivityTimer);
    // 15 minutos = 900000 ms
    inactivityTimer = setTimeout(() => {
        window.location.href = "{{ url_for('auth.logout') }}?timeout=1";
    }, 900000);
}

// Resetar o timer em eventos de interação
['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
    document.addEventListener(event, resetInactivityTimer);
});

// Iniciar o timer quando a página carregar
resetInactivityTimer();

// Função de inicialização compreensiva
function inicializarSistemaPainel() {
    console.log('=== INICIALIZANDO SISTEMA DO PAINEL ===');

    try {
        // 1. Verificar elementos essenciais da interface
        const sidebar = document.getElementById('sidebar');
        const mainContent = document.getElementById('mainContent');
        const sections = document.querySelectorAll('section.content-section');

        console.log('Elementos encontrados:', {
            sidebar: !!sidebar,
            mainContent: !!mainContent,
            sections: sections.length
        });

        // 2. Ativar seção inicial
        const hash = window.location.hash.substring(1);
        if (hash && document.getElementById(hash)) {
            console.log('Ativando seção do hash:', hash);
            activateSection(hash);
        } else {
            console.log('Ativando seção padrão: visao-geral');
            activateSection('visao-geral');
        }

        // 3. Carregar dados críticos
        setTimeout(() => {
            console.log('Carregando dados iniciais do sistema...');

            // Carregar chamados para métricas
            if (typeof loadChamados === 'function') {
                console.log('Carregando chamados...');
                loadChamados();
            }

            // Atualizar contadores
            if (typeof atualizarContadoresVisaoGeral === 'function') {
                console.log('Atualizando contadores...');
                atualizarContadoresVisaoGeral();
            }

        }, 300);

        // 4. Verificar funções essenciais
        const funcoesCriticas = [
            'activateSection',
            'loadSectionContent',
            'atualizarContadoresVisaoGeral',
            'loadChamados'
        ];

        funcoesCriticas.forEach(funcao => {
            if (typeof window[funcao] === 'function') {
                console.log(`✓ Função ${funcao} disponível`);
            } else {
                console.warn(`⚠ Função ${funcao} não encontrada`);
            }
        });

        console.log('=== INICIALIZAÇÃO DO PAINEL CONCLUÍDA ===');

    } catch (error) {
        console.error('ERRO na inicialização do painel:', error);
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM carregado - inicializando painel.js');

    // Aguardar carregamento completo dos scripts
    setTimeout(inicializarSistemaPainel, 100);
});

// Adiciona event listeners para links de navegação do submenu
document.querySelectorAll('.submenu a').forEach(link => {
    link.addEventListener('click', function(e) {
        // Previne o comportamento padrão
        e.preventDefault();
        
        // Obtém o ID da seção alvo
        const targetId = this.getAttribute('href').substring(1);
        
        // Ativa a seção
        activateSection(targetId);
        
        // Atualiza a classe active nos links
        document.querySelectorAll('.sidebar a.active').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
        
        // Adiciona active ao link pai do submenu
        const parentSubmenuToggle = this.closest('.submenu').previousElementSibling;
        if (parentSubmenuToggle) {
            parentSubmenuToggle.classList.add('active');
        }
        
        // Atualiza a URL com o hash
        window.location.hash = targetId;
    });
});

// Adiciona event listeners para links diretos (sem submenu)
document.querySelectorAll('.sidebar nav > ul > li > a:not(.submenu-toggle)').forEach(link => {
    link.addEventListener('click', function(e) {
        // Previne o comportamento padrão
        e.preventDefault();
        
        // Obtém o ID da seção alvo
        const targetId = this.getAttribute('href').substring(1);
        
        // Ativa a seção
        activateSection(targetId);
        
        // Atualiza a classe active nos links
        document.querySelectorAll('.sidebar a.active').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
        
        // Atualiza a URL com o hash
        window.location.hash = targetId;
        
        // Em dispositivos móveis, fecha o sidebar após a navegação
        if (window.innerWidth < 992) {
            sidebar.classList.remove('active');
        }
    });
});

// Função para lidar com mudanças de hash na URL
window.addEventListener('hashchange', function() {
    const hash = window.location.hash.substring(1);
    if (hash) {
        activateSection(hash);
        
        // Atualiza a classe active nos links
        document.querySelectorAll('.sidebar a.active').forEach(item => {
            item.classList.remove('active');
        });
        
        // Encontra e ativa o link correspondente
        const targetLink = document.querySelector(`.sidebar a[href="#${hash}"]`);
        if (targetLink) {
            targetLink.classList.add('active');
            
            // Se for um item de submenu, ativa também o link pai
            const submenu = targetLink.closest('.submenu');
            if (submenu) {
                const parentLink = submenu.previousElementSibling;
                if (parentLink) {
                    parentLink.classList.add('active');
                    parentLink.parentElement.classList.add('open');
                }
            }
        }
    }
});

// Adiciona suporte a teclas de acessibilidade para o menu
document.querySelectorAll('.sidebar nav ul li').forEach(item => {
    item.addEventListener('keydown', function(e) {
        // Enter ou espaço ativa o item
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            const link = this.querySelector('a');
            if (link) link.click();
        }
    });
});

// Melhora a acessibilidade dos submenus
document.querySelectorAll('.has-submenu').forEach(item => {
    const toggle = item.querySelector('.submenu-toggle');
    const submenu = item.querySelector('.submenu');
    
    if (toggle && submenu) {
        toggle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
                toggle.setAttribute('aria-expanded', !isExpanded);
                item.classList.toggle('open');
            }
        });
    }
});

// Função para verificar se uma seção existe
function sectionExists(id) {
    return Array.from(sections).some(section => section.id === id);
}

// Verifica o hash inicial e redireciona se necessário
window.addEventListener('load', function() {
    const hash = window.location.hash.substring(1);
    if (hash && sectionExists(hash)) {
        activateSection(hash);
        
        // Atualiza a classe active nos links
        document.querySelectorAll('.sidebar a.active').forEach(item => {
            item.classList.remove('active');
        });
        
        // Encontra e ativa o link correspondente
        const targetLink = document.querySelector(`.sidebar a[href="#${hash}"]`);
        if (targetLink) {
            targetLink.classList.add('active');
            
            // Se for um item de submenu, ativa também o link pai
            const submenu = targetLink.closest('.submenu');
            if (submenu) {
                const parentLink = submenu.previousElementSibling;
                if (parentLink) {
                    parentLink.classList.add('active');
                    parentLink.parentElement.classList.add('open');
                }
            }
        }
    } else {
        // Se não houver hash ou a seção não existir, vai para a seção padrão
        activateSection('visao-geral');
    }
});

// Função para abrir modal de ticket
function openTicketModal(chamado) {
    document.getElementById('ticketChamadoId').value = chamado.id;
    document.getElementById('ticketAssunto').value = `Atualização do Chamado ${chamado.codigo}`;
    document.getElementById('ticketMensagem').value = '';
    document.getElementById('modalTicket').classList.add('active');
}

// Event listeners para modal de ticket
document.getElementById('modalTicketClose')?.addEventListener('click', () => {
    document.getElementById('modalTicket').classList.remove('active');
});

document.getElementById('btnCancelarTicket')?.addEventListener('click', () => {
    document.getElementById('modalTicket').classList.remove('active');
});

document.getElementById('btnEnviarTicket')?.addEventListener('click', async () => {
    const chamadoId = document.getElementById('ticketChamadoId').value;
    const assunto = document.getElementById('ticketAssunto').value;
    const mensagem = document.getElementById('ticketMensagem').value;
    const prioridade = document.getElementById('ticketPrioridade').checked;
    const enviarCopia = document.getElementById('ticketCopia').checked;

    if (!mensagem.trim()) {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'A mensagem é obrigatória');
        }
        return;
    }

    try {
        const response = await fetch(`/ti/painel/api/chamados/${chamadoId}/ticket`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                assunto,
                mensagem,
                prioridade,
                enviar_copia: enviarCopia
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao enviar ticket');
        }

        document.getElementById('modalTicket').classList.remove('active');
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Ticket Enviado', 'Ticket enviado com sucesso!');
        }
    } catch (error) {
        console.error('Erro ao enviar ticket:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', `Erro: ${error.message}`);
        }
    }
});

// Event listeners para modelos de ticket
document.getElementById('ticketModelo')?.addEventListener('change', function() {
    const modelo = this.value;
    const mensagemField = document.getElementById('ticketMensagem');
    
    const modelos = {
        'atualizacao': 'Prezado(a) cliente,\n\nInformamos que o status do seu chamado foi atualizado.\n\nAtenciosamente,\nEquipe de Suporte',
        'confirmacao': 'Prezado(a) cliente,\n\nConfirmamos o recebimento do seu chamado e nossa equipe já está trabalhando na solução.\n\nAtenciosamente,\nEquipe de Suporte',
        'conclusao': 'Prezado(a) cliente,\n\nSeu chamado foi concluído com sucesso. Caso tenha alguma dúvida, entre em contato conosco.\n\nAtenciosamente,\nEquipe de Suporte'
    };
    
    if (modelo && modelos[modelo]) {
        mensagemField.value = modelos[modelo];
    }
});

// Event listeners para fechar modais
document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', function() {
        this.closest('.modal').classList.remove('active');
    });
});

// Fechar modais ao clicar fora
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.remove('active');
        }
    });
});

// Configuração do Socket.IO
let socket = null;

function initializeSocketIO() {
    try {
        console.log('Inicializando Socket.IO...');
        
        socket = io({
            transports: ['websocket', 'polling'],
            timeout: 20000,
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionAttempts: 5,
            maxReconnectionAttempts: 10
        });

        socket.on('connect', function() {
            console.log('Socket.IO conectado com sucesso!');
            updateSocketStatus('Conectado', 'success');
            
            // Enviar ping para manter conexão ativa
            setInterval(() => {
                if (socket.connected) {
                    socket.emit('ping');
                }
            }, 25000);
        });

        socket.on('disconnect', function(reason) {
            console.log('Socket.IO desconectado:', reason);
            updateSocketStatus('Desconectado', 'danger');
        });

        socket.on('connect_error', function(error) {
            console.error('Erro de conexão Socket.IO:', error);
            updateSocketStatus('Erro de Conexão', 'warning');
        });

        socket.on('reconnect', function(attemptNumber) {
            console.log('Socket.IO reconectado após', attemptNumber, 'tentativas');
            updateSocketStatus('Reconectado', 'success');
        });

        socket.on('reconnect_error', function(error) {
            console.error('Erro ao reconectar Socket.IO:', error);
            updateSocketStatus('Erro ao Reconectar', 'danger');
        });

        socket.on('reconnect_failed', function() {
            console.error('Falha ao reconectar Socket.IO');
            updateSocketStatus('Falha na Reconexão', 'danger');
        });

        // Event listeners para notificações
        socket.on('notification_test', function(data) {
            console.log('Teste de notificação recebido:', data);
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showInfo('Teste Socket.IO', data.message);
            }
        });

        socket.on('status_atualizado', function(data) {
            console.log('Status de chamado atualizado:', data);
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showInfo(
                    'Status Atualizado',
                    `Chamado ${data.codigo} alterado para ${data.novo_status}`
                );
            }
            // Recarregar dados se necessário
            if (document.getElementById('gerenciar-chamados').classList.contains('active')) {
                loadChamados();
            }
        });

        socket.on('chamado_deletado', function(data) {
            console.log('Chamado deletado:', data);
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showWarning(
                    'Chamado Excluído',
                    `Chamado ${data.codigo} foi exclu��do`
                );
            }
            // Recarregar dados se necessário
            if (document.getElementById('gerenciar-chamados').classList.contains('active')) {
                loadChamados();
            }
        });

        socket.on('usuario_criado', function(data) {
            console.log('Usuário criado:', data);
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showSuccess(
                    'Novo Usuário',
                    `Usuário ${data.nome} ${data.sobrenome} foi criado`
                );
            }
        });

        socket.on('pong', function(data) {
            console.log('Pong recebido:', data.timestamp);
        });

        // Disponibilizar socket globalmente
        window.socket = socket;
        
        console.log('Socket.IO inicializado com sucesso');
        
    } catch (error) {
        console.error('Erro ao inicializar Socket.IO:', error);
        updateSocketStatus('Erro de Inicialização', 'danger');
    }
}

function updateSocketStatus(status, type) {
    const socketStatus = document.getElementById('socketStatus');
    const socketConnectionStatus = document.getElementById('socketConnectionStatus');
    
    const classMap = {
        'success': 'bg-success',
        'danger': 'bg-danger',
        'warning': 'bg-warning'
    };
    
    if (socketStatus) {
        socketStatus.textContent = status;
        socketStatus.className = `ms-2 badge ${classMap[type] || 'bg-secondary'}`;
    }
    
    if (socketConnectionStatus) {
        socketConnectionStatus.textContent = status;
        socketConnectionStatus.className = `badge ${classMap[type] || 'bg-secondary'}`;
    }
}

// Inicializar Socket.IO quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    // Aguardar um pouco para garantir que tudo esteja carregado
    setTimeout(() => {
        initializeSocketIO();
    }, 1000);
    
    // Botão para reconectar Socket.IO
    document.getElementById('btnReconectarSocket')?.addEventListener('click', function() {
        console.log('Tentando reconectar Socket.IO...');
        updateSocketStatus('Reconectando...', 'warning');
        
        if (socket) {
            socket.disconnect();
            setTimeout(() => {
                socket.connect();
            }, 1000);
        } else {
            initializeSocketIO();
        }
    });
});

// ==================== FUNCIONALIDADES DE AGENTES ====================
let agentesData = [];

// Event listener para botão "Criar Agente"
document.getElementById('btnCriarAgente')?.addEventListener('click', async function() {
    await carregarUsuariosParaAgente();
    document.getElementById('modalCriarAgente').classList.add('active');
});

// Event listeners para modal de agente
document.getElementById('modalCriarAgenteClose')?.addEventListener('click', function() {
    document.getElementById('modalCriarAgente').classList.remove('active');
});

document.getElementById('btnCancelarAgente')?.addEventListener('click', function() {
    document.getElementById('modalCriarAgente').classList.remove('active');
});

document.getElementById('btnSalvarAgente')?.addEventListener('click', async function() {
    await criarAgente();
});

document.getElementById('formCriarAgente')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    await criarAgente();
});

// Carregar usuários para seleção no modal de agente
async function carregarUsuariosParaAgente() {
    try {
        const response = await fetch('/ti/painel/api/usuarios-disponiveis');
        if (!response.ok) {
            throw new Error('Erro ao carregar usuários');
        }
        const usuarios = await response.json();
        const select = document.getElementById('selectUsuarioAgente');

        // Limpar opções existentes (exceto a primeira)
        select.innerHTML = '<option value="">Selecione um usuário</option>';

        // Adicionar usuários não bloqueados
        usuarios.filter(u => !u.bloqueado).forEach(usuario => {
            const option = document.createElement('option');
            option.value = usuario.id;
            option.textContent = `${usuario.nome} ${usuario.sobrenome} (${usuario.usuario})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar usuários:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar lista de usuários');
        }
    }
}

// Criar agente
async function criarAgente() {
    const usuarioId = document.getElementById('selectUsuarioAgente').value;
    const nivelExperiencia = document.getElementById('nivelExperienciaAgente').value;
    const maxChamados = parseInt(document.getElementById('maxChamadosAgente').value);
    const ativo = document.getElementById('ativoAgente').checked;

    // Coletar especialidades selecionadas
    const especialidades = [];
    document.querySelectorAll('#modalCriarAgente input[type="checkbox"]:checked').forEach(checkbox => {
        if (checkbox.id !== 'ativoAgente') {
            especialidades.push(checkbox.value);
        }
    });

    if (!usuarioId) {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Selecione um usuário');
        }
        return;
    }

    try {
        const response = await fetch('/ti/painel/api/agentes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                usuario_id: parseInt(usuarioId),
                nivel_experiencia: nivelExperiencia,
                max_chamados_simultaneos: maxChamados,
                especialidades: especialidades,
                ativo: ativo
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao criar agente');
        }

        const data = await response.json();

        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Agente Criado', `Agente ${data.nome} criado com sucesso!`);
        }

        // Fechar modal e resetar formulário
        document.getElementById('modalCriarAgente').classList.remove('active');
        document.getElementById('formCriarAgente').reset();

        // Recarregar lista de agentes se estiver na seç��o
        if (document.getElementById('agentes-suporte').classList.contains('active')) {
            await carregarAgentes();
        }

    } catch (error) {
        console.error('Erro ao criar agente:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

// Carregar agentes
async function carregarAgentes() {
    try {
        console.log('Carregando agentes...');
        const response = await fetch('/ti/painel/api/agentes');
        if (!response.ok) {
            throw new Error('Erro ao carregar agentes');
        }
        agentesData = await response.json();
        console.log('Agentes carregados:', agentesData);
        renderizarAgentes(agentesData);

        // Carregar estatísticas dos agentes
        await carregarEstatisticasAgentes();

    } catch (error) {
        console.error('Erro ao carregar agentes:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar agentes');
        }
    }
}

// Renderizar lista de agentes
function renderizarAgentes(agentes = null) {
    // Usar dados passados como parâmetro ou dados globais
    const dadosAgentes = agentes || agentesData;

    const container = document.querySelector('#agentes-suporte .cards-grid') || document.getElementById('agentesGrid');
    if (!container) return;

    container.innerHTML = '';

    if (!dadosAgentes || dadosAgentes.length === 0) {
        container.innerHTML = '<p class="text-center py-4">Nenhum agente cadastrado.</p>';
        return;
    }

    dadosAgentes.forEach(agente => {
        const card = document.createElement('div');
        card.className = 'card';

        const statusClass = agente.ativo ? 'status-concluido' : 'status-cancelado';
        const statusText = agente.ativo ? 'Ativo' : 'Inativo';

        card.innerHTML = `
            <div class="card-header">
                <h3>${agente.nome} ${agente.sobrenome}</h3>
                <div class="status-badge ${statusClass}">
                    <i class="fas ${agente.ativo ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                    ${statusText}
                </div>
            </div>
            <div class="card-body">
                <div class="info-row">
                    <strong>Usuário:</strong>
                    <span>${agente.usuario}</span>
                </div>
                <div class="info-row">
                    <strong>Nível:</strong>
                    <span>${agente.nivel_experiencia}</span>
                </div>
                <div class="info-row">
                    <strong>Máx. Chamados:</strong>
                    <span>${agente.max_chamados_simultaneos}</span>
                </div>
                <div class="info-row">
                    <strong>Chamados Ativos:</strong>
                    <span>${agente.chamados_ativos || 0}</span>
                </div>
                <div class="info-row">
                    <strong>Especialidades:</strong>
                    <span>${agente.especialidades ? agente.especialidades.join(', ') : 'Nenhuma'}</span>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary btn-sm" onclick="editarAgente(${agente.id})">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="btn ${agente.ativo ? 'btn-warning' : 'btn-success'} btn-sm"
                        onclick="toggleAgenteStatus(${agente.id}, ${!agente.ativo})">
                    <i class="fas ${agente.ativo ? 'fa-pause' : 'fa-play'}"></i>
                    ${agente.ativo ? 'Desativar' : 'Ativar'}
                </button>
                <button class="btn btn-danger btn-sm" onclick="excluirAgente(${agente.id})">
                    <i class="fas fa-trash"></i> Excluir
                </button>
            </div>
        `;

        container.appendChild(card);
    });
}

// Toggle status do agente
async function toggleAgenteStatus(agenteId, novoStatus) {
    try {
        const response = await fetch(`/ti/painel/api/agentes/${agenteId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ativo: novoStatus })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao alterar status');
        }

        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Status Alterado', `Agente ${novoStatus ? 'ativado' : 'desativado'} com sucesso!`);
        }

        await carregarAgentes();

    } catch (error) {
        console.error('Erro ao alterar status:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

// Excluir agente
async function excluirAgente(agenteId) {
    if (!confirm('Tem certeza que deseja excluir este agente?')) return;

    try {
        const response = await fetch(`/ti/painel/api/agentes/${agenteId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao excluir agente');
        }

        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Agente Excluído', 'Agente excluído com sucesso!');
        }

        await carregarAgentes();

    } catch (error) {
        console.error('Erro ao excluir agente:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

// ==================== FUNCIONALIDADES DE GRUPOS ====================
let gruposData = [];

// Event listener para botão "Criar Grupo"
document.getElementById('btnCriarGrupo')?.addEventListener('click', function() {
    document.getElementById('modalCriarGrupo').classList.add('active');
});

// Event listeners para modal de grupo
document.getElementById('modalCriarGrupoClose')?.addEventListener('click', function() {
    document.getElementById('modalCriarGrupo').classList.remove('active');
});

document.getElementById('btnCancelarGrupo')?.addEventListener('click', function() {
    document.getElementById('modalCriarGrupo').classList.remove('active');
});

document.getElementById('btnSalvarGrupo')?.addEventListener('click', async function() {
    await criarGrupo();
});

document.getElementById('formCriarGrupo')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    await criarGrupo();
});

// Criar grupo
async function criarGrupo() {
    const nome = document.getElementById('nomeGrupo').value.trim();
    const descricao = document.getElementById('descricaoGrupo').value.trim();

    if (!nome) {
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Nome do grupo é obrigatório');
        }
        return;
    }

    try {
        const response = await fetch('/ti/painel/api/grupos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nome: nome,
                descricao: descricao
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao criar grupo');
        }

        const data = await response.json();

        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Grupo Criado', `Grupo "${data.nome}" criado com sucesso!`);
        }

        // Fechar modal e resetar formulário
        document.getElementById('modalCriarGrupo').classList.remove('active');
        document.getElementById('formCriarGrupo').reset();

        // Recarregar lista de grupos se estiver na seção
        if (document.getElementById('grupos-usuarios').classList.contains('active')) {
            await carregarGrupos();
        }

    } catch (error) {
        console.error('Erro ao criar grupo:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

// Carregar grupos
async function carregarGrupos() {
    try {
        const response = await fetch('/ti/painel/api/grupos');
        if (!response.ok) {
            throw new Error('Erro ao carregar grupos');
        }
        gruposData = await response.json();
        renderizarGrupos();
    } catch (error) {
        console.error('Erro ao carregar grupos:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar grupos');
        }
    }
}

// Renderizar lista de grupos
function renderizarGrupos() {
    const container = document.querySelector('#grupos-usuarios .cards-grid');
    if (!container) return;

    container.innerHTML = '';

    if (gruposData.length === 0) {
        container.innerHTML = '<p class="text-center py-4">Nenhum grupo cadastrado.</p>';
        return;
    }

    gruposData.forEach(grupo => {
        const card = document.createElement('div');
        card.className = 'card';

        const statusClass = grupo.ativo ? 'status-concluido' : 'status-cancelado';
        const statusText = grupo.ativo ? 'Ativo' : 'Inativo';

        card.innerHTML = `
            <div class="card-header">
                <h3>${grupo.nome}</h3>
                <div class="status-badge ${statusClass}">
                    <i class="fas ${grupo.ativo ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                    ${statusText}
                </div>
            </div>
            <div class="card-body">
                <div class="info-row">
                    <strong>Descrição:</strong>
                    <span>${grupo.descricao || 'Sem descrição'}</span>
                </div>
                <div class="info-row">
                    <strong>Membros:</strong>
                    <span>${grupo.membros_count || 0}</span>
                </div>
                <div class="info-row">
                    <strong>Unidades:</strong>
                    <span>${grupo.unidades_count || 0}</span>
                </div>
                <div class="info-row">
                    <strong>Criado por:</strong>
                    <span>${grupo.criador_nome || 'N/A'}</span>
                </div>
            </div>
            <div class="card-footer">
                <button class="btn btn-primary btn-sm" onclick="gerenciarMembrosGrupo(${grupo.id})">
                    <i class="fas fa-users"></i> Membros
                </button>
                <button class="btn btn-info btn-sm" onclick="editarGrupo(${grupo.id})">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="btn btn-danger btn-sm" onclick="excluirGrupo(${grupo.id})">
                    <i class="fas fa-trash"></i> Excluir
                </button>
            </div>
        `;

        container.appendChild(card);
    });
}

// Excluir grupo
async function excluirGrupo(grupoId) {
    if (!confirm('Tem certeza que deseja excluir este grupo?')) return;

    try {
        const response = await fetch(`/ti/painel/api/grupos/${grupoId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao excluir grupo');
        }

        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Grupo Excluído', 'Grupo excluído com sucesso!');
        }

        await carregarGrupos();

    } catch (error) {
        console.error('Erro ao excluir grupo:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

// Garantir que agentes e grupos sejam carregados corretamente
function loadSectionContentEnhanced(sectionId) {
    // Chamar a função original primeiro
    if (typeof loadSectionContent === 'function') {
        loadSectionContent(sectionId);
    }

    // Adicionar funcionalidades específicas
    switch(sectionId) {
        case 'agentes-suporte':
            setTimeout(() => {
                if (typeof carregarAgentes === 'function') {
                    carregarAgentes();
                }
            }, 100);
            break;
        case 'auditoria-logs':
            setTimeout(() => {
                if (typeof inicializarAuditoria === 'function') {
                    inicializarAuditoria();
                }
            }, 100);
            break;
        case 'grupos-usuarios':
            setTimeout(() => {
                if (typeof inicializarGrupos === 'function') {
                    inicializarGrupos();
                }
                if (typeof carregarGrupos === 'function') {
                    carregarGrupos();
                }
                inicializarModalGrupos();
            }, 100);
            break;
    }
}

// Sobrescrever apenas se necessário
if (typeof loadSectionContent !== 'undefined') {
    const originalFunction = loadSectionContent;
    loadSectionContent = function(sectionId) {
        originalFunction(sectionId);
        loadSectionContentEnhanced(sectionId);
    };
} else {
    loadSectionContent = loadSectionContentEnhanced;
}

// Placeholder functions para funcionalidades futuras
function editarAgente(agenteId) {
    console.log('Editar agente:', agenteId);
    // TODO: Implementar modal de edição de agente
}

function editarGrupo(grupoId) {
    console.log('Editar grupo:', grupoId);
    // TODO: Implementar modal de edição de grupo
}

function gerenciarMembrosGrupo(grupoId) {
    console.log('Gerenciar membros do grupo:', grupoId);
    // TODO: Implementar modal de gerenciamento de membros
}

// ==================== FILTRO DE AGENTES EM CHAMADOS ====================

// Adicionar filtro de agente na seção de gerenciar chamados
function adicionarFiltroAgente() {
    // Verificar se o filtro já existe
    if (document.getElementById('filtroAgente')) return;

    // Encontrar o container de filtros na seção de gerenciar chamados
    const secaoGerenciar = document.getElementById('gerenciar-chamados');
    if (!secaoGerenciar) return;

    // Procurar pelo container de filtros existente
    let filtrosContainer = secaoGerenciar.querySelector('.d-flex.mb-3');

    // Se não existir, criar um
    if (!filtrosContainer) {
        filtrosContainer = document.createElement('div');
        filtrosContainer.className = 'd-flex mb-3 align-items-center flex-wrap gap-2';

        // Inserir antes do grid de chamados
        const chamadosGrid = secaoGerenciar.querySelector('#chamadosGrid');
        if (chamadosGrid) {
            chamadosGrid.parentNode.insertBefore(filtrosContainer, chamadosGrid);
        }
    }

    // Criar label e select para agente
    const labelAgente = document.createElement('label');
    labelAgente.textContent = 'Filtrar por Agente:';
    labelAgente.className = 'me-2';

    const filtroAgente = document.createElement('select');
    filtroAgente.id = 'filtroAgente';
    filtroAgente.className = 'form-control me-3';
    filtroAgente.style.maxWidth = '200px';
    filtroAgente.innerHTML = '<option value="">Todos os agentes</option>';

    // Adicionar event listener
    filtroAgente.addEventListener('change', function() {
        renderChamadosPage(1);
    });

    // Adicionar ao container
    filtrosContainer.appendChild(labelAgente);
    filtrosContainer.appendChild(filtroAgente);

    // Carregar agentes para o filtro
    carregarAgentesParaFiltro();
}

// Carregar agentes para filtro
async function carregarAgentesParaFiltro() {
    try {
        const response = await fetch('/ti/painel/api/agentes');
        if (!response.ok) return;

        const agentes = await response.json();
        const select = document.getElementById('filtroAgente');
        if (!select) return;

        // Limpar e adicionar opções
        select.innerHTML = '<option value="">Todos os agentes</option>';
        agentes.filter(a => a.ativo).forEach(agente => {
            const option = document.createElement('option');
            option.value = agente.id;
            option.textContent = `${agente.nome} ${agente.sobrenome}`;
            select.appendChild(option);
        });

    } catch (error) {
        console.error('Erro ao carregar agentes para filtro:', error);
    }
}

// ==================== FILTRO DE PERMISSÕES ====================

function inicializarFiltroPermissoes() {
    console.log('Tentando inicializar filtro de permissões...');

    const filtroInput = document.getElementById('filtroPermissoes');
    const btnFiltrar = document.getElementById('btnFiltrarPermissoes');

    console.log('Elementos encontrados:', { filtroInput: !!filtroInput, btnFiltrar: !!btnFiltrar });

    if (!filtroInput || !btnFiltrar) {
        console.log('Elementos de filtro não encontrados. Tentando novamente...');
        setTimeout(inicializarFiltroPermissoes, 200);
        return;
    }

    // Função para filtrar usuários
    const filtrarUsuarios = () => {
        const termoBusca = filtroInput.value.toLowerCase().trim();
        console.log('Executando filtro com termo:', termoBusca);
        filtrarListaUsuarios(termoBusca);

        // Feedback visual
        if (termoBusca) {
            filtroInput.style.backgroundColor = '#e8f4fd';
            filtroInput.style.borderColor = '#007bff';
        } else {
            filtroInput.style.backgroundColor = '';
            filtroInput.style.borderColor = '';
        }
    };

    // Event listeners para busca em tempo real
    filtroInput.addEventListener('input', debounce(filtrarUsuarios, 100));
    btnFiltrar.addEventListener('click', filtrarUsuarios);

    // Filtrar ao pressionar Enter
    filtroInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            filtrarUsuarios();
        }
    });

    // Adicionar placeholder mais descritivo
    filtroInput.placeholder = 'Buscar por nome, email ou nível de acesso...';

    // Funcionalidade para limpar filtro com Escape
    filtroInput.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            filtroInput.value = '';
            filtrarUsuarios();
            filtroInput.blur();
        }
    });

    // Mostrar/esconder ícone de limpeza
    filtroInput.addEventListener('input', function() {
        const parentGroup = filtroInput.closest('.input-group');
        if (parentGroup) {
            let clearBtn = parentGroup.querySelector('.btn-clear-filter');
            if (filtroInput.value.trim() && !clearBtn) {
                clearBtn = document.createElement('button');
                clearBtn.className = 'btn btn-outline-secondary btn-clear-filter';
                clearBtn.type = 'button';
                clearBtn.innerHTML = '<i class="fas fa-times"></i>';
                clearBtn.title = 'Limpar filtro';
                clearBtn.onclick = function() {
                    filtroInput.value = '';
                    filtrarUsuarios();
                    filtroInput.focus();
                    clearBtn.remove();
                };
                parentGroup.appendChild(clearBtn);
            } else if (!filtroInput.value.trim() && clearBtn) {
                clearBtn.remove();
            }
        }
    });

    console.log('Filtro de permissões inicializado com sucesso!');
}

function filtrarListaUsuarios(termoBusca) {
    const usuariosGrid = document.getElementById('usuariosGrid');
    if (!usuariosGrid) {
        console.log('usuariosGrid não encontrado');
        return;
    }

    // Buscar por cards específicas de usuários
    const cards = usuariosGrid.querySelectorAll('.usuario-card');
    let usuariosVisiveis = 0;

    console.log(`Filtrando ${cards.length} cards de usuários com termo: "${termoBusca}"`);

    cards.forEach(card => {
        // Buscar elementos específicos baseados na estrutura real
        const nomeElement = card.querySelector('.card-header h3');
        const emailElements = card.querySelectorAll('.info-row span');
        const statusElement = card.querySelector('.status-badge');

        // Extrair textos específicos
        const nomeUsuario = nomeElement ? nomeElement.textContent.toLowerCase() : '';

        // Buscar email nos spans das info-rows
        let emailUsuario = '';
        let usuarioLogin = '';
        let nivelUsuario = '';
        let setoresUsuario = '';

        emailElements.forEach((span, index) => {
            const texto = span.textContent.toLowerCase();
            if (texto.includes('@')) {
                emailUsuario = texto;
            } else {
                // Baseado na ordem das info-rows: Usuário, E-mail, Nível, Setor(es)
                switch(index) {
                    case 0: usuarioLogin = texto; break;
                    case 2: nivelUsuario = texto; break;
                    case 3: setoresUsuario = texto; break;
                }
            }
        });

        const statusUsuario = statusElement ? statusElement.textContent.toLowerCase() : '';

        // Verificar se algum campo contém o termo de busca
        const encontrado = termoBusca === '' ||
                          nomeUsuario.includes(termoBusca) ||
                          emailUsuario.includes(termoBusca) ||
                          usuarioLogin.includes(termoBusca) ||
                          nivelUsuario.includes(termoBusca) ||
                          setoresUsuario.includes(termoBusca) ||
                          statusUsuario.includes(termoBusca);

        if (encontrado) {
            card.style.display = '';
            card.style.transition = 'opacity 0.3s ease';
            card.style.opacity = '1';
            card.style.transform = 'scale(1)';
            usuariosVisiveis++;
        } else {
            card.style.display = 'none';
            card.style.opacity = '0';
            card.style.transform = 'scale(0.95)';
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

    // Mostrar contador de resultados
    if (termoBusca) {
        console.log(`Filtro aplicado: "${termoBusca}" - ${usuariosVisiveis} usuário(s) encontrado(s)`);
    }
}

// ==================== FUNCIONALIDADES DE GRUPOS ====================

function inicializarModalGrupos() {
    const btnCriarGrupo = document.getElementById('btnCriarGrupo');
    const modalCriarGrupo = document.getElementById('modalCriarGrupo');
    const btnCancelarGrupo = document.getElementById('btnCancelarGrupo');
    const btnSalvarGrupo = document.getElementById('btnSalvarGrupo');
    const modalClose = document.getElementById('modalCriarGrupoClose');

    if (!btnCriarGrupo || !modalCriarGrupo) return;

    // Abrir modal
    btnCriarGrupo.addEventListener('click', async () => {
        await carregarUnidadesParaGrupo();
        modalCriarGrupo.classList.add('active');
    });

    // Fechar modal
    [btnCancelarGrupo, modalClose].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                modalCriarGrupo.classList.remove('active');
                limparFormularioGrupo();
            });
        }
    });

    // Salvar grupo
    if (btnSalvarGrupo) {
        btnSalvarGrupo.addEventListener('click', criarGrupo);
    }

    // Adicionar botões de seleção de unidades
    adicionarBotoesSelecaoUnidades();
}

async function carregarUnidadesParaGrupo() {
    try {
        const response = await fetch('/ti/painel/api/unidades');
        if (!response.ok) {
            throw new Error('Erro ao carregar unidades');
        }

        const unidades = await response.json();
        const select = document.getElementById('unidadesGrupo');

        if (!select) return;

        // Limpar e carregar unidades
        select.innerHTML = '';

        unidades.forEach(unidade => {
            const option = document.createElement('option');
            option.value = unidade.id;
            option.textContent = unidade.nome;
            select.appendChild(option);
        });

        console.log(`${unidades.length} unidades carregadas para seleção`);

    } catch (error) {
        console.error('Erro ao carregar unidades:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar lista de unidades');
        }
    }
}

function adicionarBotoesSelecaoUnidades() {
    const unidadesGrupo = document.getElementById('unidadesGrupo');
    if (!unidadesGrupo) return;

    // Verificar se já existem botões
    const containerExistente = unidadesGrupo.parentNode.querySelector('.buttons-container');
    if (containerExistente) {
        containerExistente.remove();
    }

    // Criar container para botões
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'buttons-container mt-2';

    // Botão selecionar todas
    const btnSelecionarTodas = document.createElement('button');
    btnSelecionarTodas.type = 'button';
    btnSelecionarTodas.className = 'btn btn-sm btn-outline-primary me-2';
    btnSelecionarTodas.innerHTML = '<i class="fas fa-check-double"></i> Selecionar Todas';
    btnSelecionarTodas.onclick = () => selecionarTodasUnidades(true);

    // Botão desmarcar todas
    const btnDesmarcarTodas = document.createElement('button');
    btnDesmarcarTodas.type = 'button';
    btnDesmarcarTodas.className = 'btn btn-sm btn-outline-secondary';
    btnDesmarcarTodas.innerHTML = '<i class="fas fa-times"></i> Desmarcar Todas';
    btnDesmarcarTodas.onclick = () => selecionarTodasUnidades(false);

    buttonsContainer.appendChild(btnSelecionarTodas);
    buttonsContainer.appendChild(btnDesmarcarTodas);

    // Inserir após o select
    unidadesGrupo.parentNode.insertBefore(buttonsContainer, unidadesGrupo.nextSibling);
}

function selecionarTodasUnidades(selecionar) {
    const select = document.getElementById('unidadesGrupo');
    if (!select) return;

    for (let option of select.options) {
        option.selected = selecionar;
    }

    // Disparar evento de mudança
    const event = new Event('change', { bubbles: true });
    select.dispatchEvent(event);
}

async function criarGrupo() {
    try {
        const nome = document.getElementById('nomeGrupo').value.trim();
        const descricao = document.getElementById('descricaoGrupo').value.trim();
        const ativo = document.getElementById('ativoGrupo').checked;
        const unidadesSelect = document.getElementById('unidadesGrupo');

        if (!nome) {
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showError('Erro', 'Nome do grupo é obrigatório');
            }
            return;
        }

        // Coletar unidades selecionadas
        const unidadesSelecionadas = Array.from(unidadesSelect.selectedOptions).map(option =>
            parseInt(option.value)
        );

        const dadosGrupo = {
            nome,
            descricao,
            ativo,
            unidades: unidadesSelecionadas
        };

        const response = await fetch('/ti/painel/api/grupos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dadosGrupo)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao criar grupo');
        }

        const resultado = await response.json();

        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Sucesso', resultado.message || 'Grupo criado com sucesso');
        }

        // Fechar modal e recarregar lista
        document.getElementById('modalCriarGrupo').classList.remove('active');
        limparFormularioGrupo();
        await carregarGrupos();

    } catch (error) {
        console.error('Erro ao criar grupo:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

function limparFormularioGrupo() {
    const form = document.getElementById('formCriarGrupo');
    if (form) {
        form.reset();
    }

    // Desmarcar todas as unidades
    const select = document.getElementById('unidadesGrupo');
    if (select) {
        for (let option of select.options) {
            option.selected = false;
        }
    }
}

async function carregarGrupos() {
    try {
        const response = await fetch('/ti/painel/api/grupos');
        if (!response.ok) {
            throw new Error('Erro ao carregar grupos');
        }

        const grupos = await response.json();
        renderizarGrupos(grupos);

    } catch (error) {
        console.error('Erro ao carregar grupos:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar grupos');
        }
    }
}

function renderizarGrupos(grupos) {
    const container = document.getElementById('gruposGrid');
    if (!container) return;

    if (!grupos || grupos.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-users fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">Nenhum grupo encontrado</h5>
                <p class="text-muted">Crie o primeiro grupo para organizar usuários</p>
            </div>
        `;
        return;
    }

    container.innerHTML = grupos.map(grupo => `
        <div class="card group-card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5 class="card-title group-name">${grupo.nome}</h5>
                    <span class="badge ${grupo.ativo ? 'bg-success' : 'bg-secondary'}">
                        ${grupo.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                </div>
                <p class="card-text group-description text-muted">${grupo.descricao || 'Sem descrição'}</p>
                <div class="group-stats mb-3">
                    <small class="text-muted">
                        <i class="fas fa-users"></i> ${grupo.membros_count} membros •
                        <i class="fas fa-building"></i> ${grupo.unidades_count} unidades
                    </small>
                </div>
                <div class="group-info">
                    <small class="text-muted">
                        Criado por: ${grupo.criado_por}<br>
                        Data: ${grupo.data_criacao}
                    </small>
                </div>
                <div class="card-actions mt-3">
                    <button class="btn btn-sm btn-primary" onclick="editarGrupo(${grupo.id})">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-sm btn-info" onclick="gerenciarMembros(${grupo.id})">
                        <i class="fas fa-users"></i> Membros
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="excluirGrupo(${grupo.id})">
                        <i class="fas fa-trash"></i> Excluir
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// ==================== CARREGAR AGENTES ====================

async function carregarEstatisticasAgentes() {
    try {
        const response = await fetch('/ti/painel/api/agentes/estatisticas');
        if (!response.ok) {
            throw new Error('Erro ao carregar estatísticas dos agentes');
        }
        const estatisticas = await response.json();
        atualizarEstatisticasAgentes(estatisticas);
    } catch (error) {
        console.error('Erro ao carregar estatísticas dos agentes:', error);
        // Tentar usar dados locais se disponíveis
        if (agentesData && agentesData.length > 0) {
            atualizarEstatisticasAgentesLocal(agentesData);
        }
    }
}

function atualizarEstatisticasAgentes(estatisticas) {
    const totalAgentes = document.getElementById('totalAgentes');
    const agentesAtivos = document.getElementById('agentesAtivos');
    const chamadosAtribuidos = document.getElementById('chamadosAtribuidos');
    const agentesDisponiveis = document.getElementById('agentesDisponiveis');

    if (totalAgentes) totalAgentes.textContent = estatisticas.total_agentes || 0;
    if (agentesAtivos) agentesAtivos.textContent = estatisticas.agentes_ativos || 0;
    if (chamadosAtribuidos) chamadosAtribuidos.textContent = estatisticas.chamados_atribuidos || 0;
    if (agentesDisponiveis) agentesDisponiveis.textContent = estatisticas.agentes_disponiveis || 0;
}

function atualizarEstatisticasAgentesLocal(agentes) {
    const totalAgentes = document.getElementById('totalAgentes');
    const agentesAtivos = document.getElementById('agentesAtivos');
    const chamadosAtribuidos = document.getElementById('chamadosAtribuidos');
    const agentesDisponiveis = document.getElementById('agentesDisponiveis');

    if (totalAgentes) totalAgentes.textContent = agentes.length;
    if (agentesAtivos) agentesAtivos.textContent = agentes.filter(a => a.ativo).length;
    if (chamadosAtribuidos) chamadosAtribuidos.textContent = agentes.reduce((sum, a) => sum + (a.chamados_ativos || 0), 0);
    if (agentesDisponiveis) agentesDisponiveis.textContent = agentes.filter(a => a.pode_receber_chamado).length;
}

// ==================== CONFIGURAÇÕES AVANÇADAS ====================

async function carregarConfiguracoesAvancadas() {
    try {
        const response = await fetch('/ti/painel/api/configuracoes-avancadas');
        if (!response.ok) {
            throw new Error('Erro ao carregar configurações avançadas');
        }

        const config = await response.json();
        preencherFormularioConfiguracoesAvancadas(config);

    } catch (error) {
        console.error('Erro ao carregar configurações avançadas:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar configurações avançadas');
        }
    }
}

function preencherFormularioConfiguracoesAvancadas(config) {
    // Sistema
    if (config.sistema) {
        const sistema = config.sistema;
        setValueById('debugMode', sistema.debug_mode);
        setValueById('logLevel', sistema.log_level);
        setValueById('maxFileSize', sistema.max_file_size);
        setValueById('sessionTimeout', sistema.session_timeout);
        setValueById('autoLogout', sistema.auto_logout);
    }

    // Segurança
    if (config.seguranca) {
        const seguranca = config.seguranca;
        setValueById('forceHttps', seguranca.force_https);
        setValueById('csrfProtection', seguranca.csrf_protection);
        setValueById('rateLimiting', seguranca.rate_limiting);
        setValueById('passwordComplexity', seguranca.password_complexity);
    }

    // Performance
    if (config.performance) {
        const performance = config.performance;
        setValueById('cacheEnabled', performance.cache_enabled);
        setValueById('compression', performance.compression);
        setValueById('cdnEnabled', performance.cdn_enabled);
        setValueById('databasePoolSize', performance.database_pool_size);
    }

    // Backup
    if (config.backup) {
        const backup = config.backup;
        setValueById('autoBackup', backup.auto_backup);
        setValueById('backupFrequency', backup.backup_frequency);
        setValueById('retentionDays', backup.retention_days);
        setValueById('backupLocation', backup.backup_location);
    }
}

function setValueById(id, value) {
    const element = document.getElementById(id);
    if (element) {
        if (element.type === 'checkbox') {
            element.checked = value;
        } else {
            element.value = value;
        }
    }
}

// ==================== ALERTAS DO SISTEMA ====================

async function carregarAlertasSistema() {
    try {
        const response = await fetch('/ti/painel/api/alertas?page=1&per_page=10');
        if (!response.ok) {
            throw new Error('Erro ao carregar alertas');
        }

        const data = await response.json();
        renderizarAlertasSistema(data.alertas);

    } catch (error) {
        console.error('Erro ao carregar alertas:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar alertas do sistema');
        }
    }
}

function renderizarAlertasSistema(alertas) {
    const container = document.getElementById('alertasGrid');
    if (!container) return;

    if (!alertas || alertas.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-shield-alt fa-3x text-success mb-3"></i>
                <h5 class="text-success">Sistema funcionando normalmente</h5>
                <p class="text-muted">Nenhum alerta ativo no momento</p>
            </div>
        `;
        return;
    }

    container.innerHTML = alertas.map(alerta => `
        <div class="alert alert-${getAlertClass(alerta.tipo)} d-flex align-items-center" role="alert">
            <i class="fas fa-${getAlertIcon(alerta.tipo)} me-2"></i>
            <div class="flex-grow-1">
                <strong>${alerta.titulo}</strong>
                <p class="mb-0">${alerta.mensagem}</p>
                <small class="text-muted">${alerta.data}</small>
            </div>
            <span class="badge bg-${alerta.prioridade === 'crítica' ? 'danger' : alerta.prioridade === 'alta' ? 'warning' : 'info'}">
                ${alerta.prioridade}
            </span>
        </div>
    `).join('');
}

function getAlertClass(tipo) {
    switch(tipo) {
        case 'error': return 'danger';
        case 'warning': return 'warning';
        case 'info': return 'info';
        default: return 'secondary';
    }
}

function getAlertIcon(tipo) {
    switch(tipo) {
        case 'error': return 'exclamation-triangle';
        case 'warning': return 'exclamation-circle';
        case 'info': return 'info-circle';
        default: return 'bell';
    }
}

// ==================== BACKUP E MANUTENÇÃO ====================

async function carregarBackupManutencao() {
    try {
        // Adicionar event listeners para os botões existentes
        const btnCriarBackup = document.getElementById('btnCriarBackup');
        if (btnCriarBackup) {
            btnCriarBackup.addEventListener('click', criarBackup);
        }

        console.log('Seção backup/manutenção carregada');
    } catch (error) {
        console.error('Erro ao carregar backup/manutenção:', error);
    }
}

// ==================== LOGS DE ACESSO ====================

async function carregarLogsAcesso() {
    try {
        const tabela = document.getElementById('tabelaLogsAcesso');
        if (tabela) {
            // Simular logs de acesso
            const logs = [
                { usuario: 'Admin', dataLogin: '31/01/2025 10:30:00', dataLogout: '31/01/2025 12:15:00', duracao: '1h 45m', ip: '192.168.1.100', status: 'Ativo' },
                { usuario: 'João Silva', dataLogin: '31/01/2025 10:25:00', dataLogout: '31/01/2025 11:30:00', duracao: '1h 05m', ip: '192.168.1.101', status: 'Finalizado' },
                { usuario: 'Maria Santos', dataLogin: '31/01/2025 10:20:00', dataLogout: '-', duracao: '-', ip: '192.168.1.102', status: 'Bloqueado' }
            ];

            tabela.innerHTML = logs.map(log => `
                <tr>
                    <td>${log.usuario}</td>
                    <td>${log.dataLogin}</td>
                    <td>${log.dataLogout}</td>
                    <td>${log.duracao}</td>
                    <td>${log.ip}</td>
                    <td>
                        <span class="badge bg-${log.status === 'Ativo' ? 'success' : log.status === 'Finalizado' ? 'info' : 'danger'}">
                            ${log.status}
                        </span>
                    </td>
                </tr>
            `).join('');
        }

        // Atualizar estatísticas
        const acessosHoje = document.getElementById('acessosHoje');
        if (acessosHoje) acessosHoje.textContent = '15';

    } catch (error) {
        console.error('Erro ao carregar logs de acesso:', error);
    }
}

// ==================== LOGS DE AÇÕES ====================

async function carregarLogsAcoes() {
    try {
        const response = await fetch('/ti/painel/api/logs/acoes');
        if (!response.ok) {
            throw new Error('Erro ao carregar logs de aç��es');
        }
        const data = await response.json();

        const tabela = document.getElementById('tabelaLogsAcoes');
        if (tabela) {
            tabela.innerHTML = data.logs.map(log => `
                <tr>
                    <td>${log.id}</td>
                    <td>${log.usuario_nome}</td>
                    <td>${log.acao}</td>
                    <td>
                        <span class="badge bg-${log.categoria === 'sistema' ? 'primary' : log.categoria === 'chamado' ? 'info' : log.categoria === 'usuario' ? 'warning' : 'secondary'}">
                            ${log.categoria || 'N/A'}
                        </span>
                    </td>
                    <td>${log.data_acao}</td>
                    <td>${log.ip_address || 'N/A'}</td>
                    <td>
                        <span class="badge bg-${log.sucesso ? 'success' : 'danger'}">
                            ${log.sucesso ? 'Sucesso' : 'Erro'}
                        </span>
                    </td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary" onclick="verDetalhesLog(${log.id}, '${log.detalhes}', '${log.erro_detalhes}')">
                            <i class="fas fa-eye"></i> Ver
                        </button>
                    </td>
                </tr>
            `).join('');
        }

        // Carregar estatísticas
        await carregarEstatisticasLogsAcoes();

    } catch (error) {
        console.error('Erro ao carregar logs de ações:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar logs de ações');
        }
    }
}

async function carregarEstatisticasLogsAcoes() {
    try {
        const response = await fetch('/ti/painel/api/logs/acoes/estatisticas');
        if (!response.ok) throw new Error('Erro ao carregar estatísticas');

        const stats = await response.json();

        // Atualizar elementos da tela
        const totalAcoes = document.getElementById('totalAcoes');
        if (totalAcoes) totalAcoes.textContent = stats.total_acoes;

        const taxaSucesso = document.getElementById('taxaSucessoAcoes');
        if (taxaSucesso) taxaSucesso.textContent = `${stats.taxa_sucesso}%`;

        const acoesErro = document.getElementById('acoesErro');
        if (acoesErro) acoesErro.textContent = stats.acoes_erro;

    } catch (error) {
        console.error('Erro ao carregar estatísticas de logs:', error);
    }
}

function verDetalhesLog(id, detalhes, erroDetalhes) {
    const modal = document.getElementById('modalDetalhesLog');
    if (modal) {
        const conteudo = document.getElementById('conteudoDetalhesLog');
        if (conteudo) {
            conteudo.innerHTML = `
                <div class="mb-3">
                    <h6>Detalhes da Ação:</h6>
                    <p class="text-muted">${detalhes || 'Sem detalhes disponíveis'}</p>
                </div>
                ${erroDetalhes ? `
                    <div class="mb-3">
                        <h6 class="text-danger">Detalhes do Erro:</h6>
                        <p class="text-danger">${erroDetalhes}</p>
                    </div>
                ` : ''}
            `;
        }
        modal.classList.add('active');
    }
}

// ==================== ANÁLISE DE PROBLEMAS ====================

async function carregarAnaliseProblemas() {
    try {
        const response = await fetch('/ti/painel/api/analise/problemas');
        if (!response.ok) {
            throw new Error('Erro ao carregar análise de problemas');
        }
        const data = await response.json();

        // Carregar problemas mais frequentes
        const tabelaProblemasFrequentes = document.getElementById('tabelaProblemasFrequentes');
        if (tabelaProblemasFrequentes) {
            tabelaProblemasFrequentes.innerHTML = data.problemas_frequentes.map(problema => `
                <tr>
                    <td>${problema.problema}</td>
                    <td>${problema.quantidade}</td>
                    <td>${problema.tempo_medio_resolucao ? problema.tempo_medio_resolucao.toFixed(1) + 'h' : 'N/A'}</td>
                </tr>
            `).join('');
        }

        // Carregar unidades com mais problemas
        const tabelaUnidadesProblemas = document.getElementById('tabelaUnidadesProblemas');
        if (tabelaUnidadesProblemas) {
            tabelaUnidadesProblemas.innerHTML = data.unidades_problemas.map(unidade => `
                <tr>
                    <td>${unidade.unidade}</td>
                    <td>${unidade.total}</td>
                    <td>${unidade.abertos}</td>
                    <td>${unidade.concluidos}</td>
                    <td>
                        <span class="badge bg-${unidade.taxa_resolucao >= 80 ? 'success' : unidade.taxa_resolucao >= 60 ? 'warning' : 'danger'}">
                            ${unidade.taxa_resolucao}%
                        </span>
                    </td>
                </tr>
            `).join('');
        }

        // Gráfico de tendências semanais
        await renderizarGraficoTendencias(data.tendencias_semanais);

        // Análise por prioridade
        await renderizarGraficoPrioridades(data.resolucao_por_prioridade);

    } catch (error) {
        console.error('Erro ao carregar análise de problemas:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar análise de problemas');
        }
    }
}

async function renderizarGraficoTendencias(tendencias) {
    const ctx = document.getElementById('graficoTendenciasSemanais');
    if (!ctx || !tendencias) return;

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: tendencias.map(t => `Sem ${t.semana}/${t.ano}`),
            datasets: [{
                label: 'Chamados por Semana',
                data: tendencias.map(t => t.quantidade),
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Tendência de Chamados por Semana'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function renderizarGraficoPrioridades(prioridades) {
    const ctx = document.getElementById('graficoPrioridades');
    if (!ctx || !prioridades) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: prioridades.map(p => p.prioridade),
            datasets: [{
                data: prioridades.map(p => p.total),
                backgroundColor: [
                    '#FF6384',
                    '#36A2EB',
                    '#FFCE56',
                    '#4BC0C0',
                    '#9966FF'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Distribuição por Prioridade'
                }
            }
        }
    });
}

// ==================== MONITORAMENTO ====================

async function carregarMonitoramentoCatraca() {
    try {
        // Simulação de dados de catraca
        const dados = {
            status: 'online',
            acessos_hoje: 245,
            acessos_semana: 1680,
            alertas: [
                { id: 1, tipo: 'warning', mensagem: 'Catraca 3 com lentidão', timestamp: '10:30' },
                { id: 2, tipo: 'info', mensagem: 'Manutenção programada às 18h', timestamp: '09:15' }
            ]
        };

        const statusCatraca = document.getElementById('statusCatraca');
        if (statusCatraca) {
            statusCatraca.innerHTML = `
                <span class="badge bg-${dados.status === 'online' ? 'success' : 'danger'}">
                    ${dados.status === 'online' ? 'Online' : 'Offline'}
                </span>
            `;
        }

        const acessosHojeCatraca = document.getElementById('acessosHojeCatraca');
        if (acessosHojeCatraca) acessosHojeCatraca.textContent = dados.acessos_hoje;

        const acessosSemanaCatraca = document.getElementById('acessosSemanaCatraca');
        if (acessosSemanaCatraca) acessosSemanaCatraca.textContent = dados.acessos_semana;

    } catch (error) {
        console.error('Erro ao carregar monitoramento de catraca:', error);
    }
}

async function carregarMonitoramentoMikrotiks() {
    try {
        // Simulação de dados de mikrotiks
        const equipamentos = [
            { nome: 'Router Principal', ip: '192.168.1.1', status: 'online', uptime: '15 dias' },
            { nome: 'Switch Core', ip: '192.168.1.2', status: 'online', uptime: '30 dias' },
            { nome: 'AP WiFi Hall', ip: '192.168.1.10', status: 'warning', uptime: '2 dias' }
        ];

        const tabelaEquipamentos = document.getElementById('tabelaEquipamentos');
        if (tabelaEquipamentos) {
            tabelaEquipamentos.innerHTML = equipamentos.map(eq => `
                <tr>
                    <td>${eq.nome}</td>
                    <td>${eq.ip}</td>
                    <td>
                        <span class="badge bg-${eq.status === 'online' ? 'success' : eq.status === 'warning' ? 'warning' : 'danger'}">
                            ${eq.status === 'online' ? 'Online' : eq.status === 'warning' ? 'Atenção' : 'Offline'}
                        </span>
                    </td>
                    <td>${eq.uptime}</td>
                    <td>
                        <button class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-cog"></i> Config
                        </button>
                    </td>
                </tr>
            `).join('');
        }

    } catch (error) {
        console.error('Erro ao carregar monitoramento de mikrotiks:', error);
    }
}

async function carregarMonitoramentoUsuarios() {
    try {
        // Simulação de dados de usuários ativos
        const usuariosOnline = [
            { nome: 'João Silva', setor: 'TI', login: '10:30', atividade: 'Ativo' },
            { nome: 'Maria Santos', setor: 'Financeiro', login: '09:15', atividade: 'Ativo' },
            { nome: 'Pedro Costa', setor: 'Gerencial', login: '08:45', atividade: 'Inativo (5min)' }
        ];

        const tabelaUsuariosOnline = document.getElementById('tabelaUsuariosOnline');
        if (tabelaUsuariosOnline) {
            tabelaUsuariosOnline.innerHTML = usuariosOnline.map(user => `
                <tr>
                    <td>${user.nome}</td>
                    <td>${user.setor}</td>
                    <td>${user.login}</td>
                    <td>
                        <span class="badge bg-${user.atividade === 'Ativo' ? 'success' : 'warning'}">
                            ${user.atividade}
                        </span>
                    </td>
                </tr>
            `).join('');
        }

        const totalUsuariosOnline = document.getElementById('totalUsuariosOnline');
        if (totalUsuariosOnline) totalUsuariosOnline.textContent = usuariosOnline.length;

    } catch (error) {
        console.error('Erro ao carregar monitoramento de usuários:', error);
    }
}

// ==================== ATRIBUIÇÃO DE AGENTES ====================

let agentesDisponiveis = [];

async function carregarAgentesDisponiveis() {
    try {
        const response = await fetch('/ti/painel/api/agentes');
        if (!response.ok) throw new Error('Erro ao carregar agentes');
        agentesDisponiveis = await response.json();
        return agentesDisponiveis.filter(agente => agente.ativo);
    } catch (error) {
        console.error('Erro ao carregar agentes:', error);
        return [];
    }
}

async function atribuirAgente(chamadoId) {
    try {
        const agentes = await carregarAgentesDisponiveis();

        if (agentes.length === 0) {
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showWarning('Aviso', 'Nenhum agente ativo disponível');
            }
            return;
        }

        // Criar modal de seleção de agente
        const modalContent = `
            <div class="modal" id="modalAtribuirAgente" style="display: block;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Atribuir Agente ao Chamado</h3>
                        <button class="close" onclick="fecharModalAgente()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <div class="form-group">
                            <label for="selectAgente">Selecione o agente:</label>
                            <select id="selectAgente" class="form-control">
                                <option value="">Selecione um agente...</option>
                                ${agentes.map(agente => `
                                    <option value="${agente.id}" ${!agente.pode_receber_chamado ? 'disabled' : ''}>
                                        ${agente.nome} - ${agente.nivel_experiencia}
                                        (${agente.chamados_ativos}/${agente.max_chamados_simultaneos} chamados)
                                        ${!agente.pode_receber_chamado ? ' - LIMITE ATINGIDO' : ''}
                                    </option>
                                `).join('')}
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="observacoesAtribuicao">Observações (opcional):</label>
                            <textarea id="observacoesAtribuicao" class="form-control" rows="3" placeholder="Observações sobre a atribuição..."></textarea>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-secondary" onclick="fecharModalAgente()">Cancelar</button>
                        <button class="btn btn-primary" onclick="confirmarAtribuicao(${chamadoId})">Atribuir</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalContent);

    } catch (error) {
        console.error('Erro ao abrir modal de atribuição:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar agentes');
        }
    }
}

async function alterarAgente(chamadoId) {
    // Usar a mesma função de atribuir para alteração
    await atribuirAgente(chamadoId);
}

async function confirmarAtribuicao(chamadoId) {
    try {
        const agenteSelect = document.getElementById('selectAgente');
        const observacoes = document.getElementById('observacoesAtribuicao');

        const agenteId = agenteSelect.value;
        if (!agenteId) {
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showWarning('Aviso', 'Selecione um agente');
            }
            return;
        }

        const response = await fetch(`/ti/painel/api/chamados/${chamadoId}/atribuir`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agente_id: parseInt(agenteId),
                observacoes: observacoes.value
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Erro ao atribuir agente');
        }

        const data = await response.json();

        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Sucesso', data.message);
        }

        fecharModalAgente();

        // Recarregar chamados para mostrar a atribuição
        await loadChamados();

    } catch (error) {
        console.error('Erro ao atribuir agente:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

function fecharModalAgente() {
    const modal = document.getElementById('modalAtribuirAgente');
    if (modal) {
        modal.remove();
    }
}

// ==================== EVENT LISTENERS PARA FILTROS ====================

document.addEventListener('DOMContentLoaded', function() {
    // Botão filtrar chamados
    const btnFiltrarChamados = document.getElementById('btnFiltrarChamados');
    if (btnFiltrarChamados) {
        btnFiltrarChamados.addEventListener('click', function() {
            currentPage = 1;
            renderChamadosPage(currentPage);
        });
    }

    // Botão limpar filtros
    const btnLimparFiltros = document.getElementById('btnLimparFiltros');
    if (btnLimparFiltros) {
        btnLimparFiltros.addEventListener('click', function() {
            // Limpar todos os campos de filtro
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

            // Renderizar novamente
            currentPage = 1;
            renderChamadosPage(currentPage);
        });
    }

    // Filtro em tempo real para solicitante e problema
    const filtroSolicitante = document.getElementById('filtroSolicitante');
    const filtroProblema = document.getElementById('filtroProblema');

    if (filtroSolicitante) {
        filtroSolicitante.addEventListener('input', debounce(function() {
            currentPage = 1;
            renderChamadosPage(currentPage);
        }, 500));
    }

    if (filtroProblema) {
        filtroProblema.addEventListener('input', debounce(function() {
            currentPage = 1;
            renderChamadosPage(currentPage);
        }, 500));
    }

    // Filtros de mudança imediata
    const filtroPrioridade = document.getElementById('filtroPrioridade');
    const filtroAgenteResponsavel = document.getElementById('filtroAgenteResponsavel');
    const filtroUnidade = document.getElementById('filtroUnidade');

    if (filtroPrioridade) {
        filtroPrioridade.addEventListener('change', function() {
            currentPage = 1;
            renderChamadosPage(currentPage);
        });
    }

    if (filtroAgenteResponsavel) {
        filtroAgenteResponsavel.addEventListener('change', function() {
            currentPage = 1;
            renderChamadosPage(currentPage);
        });
    }

    if (filtroUnidade) {
        filtroUnidade.addEventListener('change', function() {
            currentPage = 1;
            renderChamadosPage(currentPage);
        });
    }
});

// Função debounce para evitar muitas chamadas
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
    if (filtroPermissoes) {
        filtroPermissoes.value = '';
        filtrarListaUsuarios('');
    }

    // Recarregar dados de chamados
    if (typeof renderChamadosPage === 'function' && window.chamadosData) {
        currentPage = 1;
        renderChamadosPage(currentPage);
    }

    // Mostrar notificação
    if (window.advancedNotificationSystem) {
        window.advancedNotificationSystem.showInfo('Filtros Limpos', 'Todos os filtros foram removidos');
    }
}

// ==================== DASHBOARD AVANÇADO ====================

async function carregarDashboardAvancado() {
    try {
        // Atualizar dados das métricas existentes
        const dashTotalUsuarios = document.getElementById('dashTotalUsuarios');
        const dashTaxaAtividade = document.getElementById('dashTaxaAtividade');

        if (dashTotalUsuarios) dashTotalUsuarios.textContent = '124';
        if (dashTaxaAtividade) dashTaxaAtividade.textContent = '85% ativos este mês';

        // Adicionar event listener para o botão atualizar
        const btnAtualizar = document.getElementById('btnAtualizarDashboard');
        if (btnAtualizar) {
            btnAtualizar.addEventListener('click', () => {
                if (window.advancedNotificationSystem) {
                    window.advancedNotificationSystem.showInfo('Dashboard', 'Atualizando dados do dashboard...');
                }
                setTimeout(() => {
                    carregarDashboardAvancado();
                }, 1000);
            });
        }

        console.log('Dashboard avançado carregado');
    } catch (error) {
        console.error('Erro ao carregar dashboard avançado:', error);
    }
}

// Funções auxiliares
function criarBackup() {
    if (window.advancedNotificationSystem) {
        window.advancedNotificationSystem.showInfo('Backup', 'Iniciando processo de backup...');
    }
}

function executarManutencao() {
    if (window.advancedNotificationSystem) {
        window.advancedNotificationSystem.showInfo('Manutenção', 'Iniciando processo de manutenção...');
    }
}

// Garantir que as funções estejam disponíveis globalmente
window.inicializarFiltroPermissoes = inicializarFiltroPermissoes;
window.filtrarListaUsuarios = filtrarListaUsuarios;
window.limparTodosFiltros = limparTodosFiltros;
window.atribuirAgente = atribuirAgente;
window.alterarAgente = alterarAgente;
window.confirmarAtribuicao = confirmarAtribuicao;
window.fecharModalAgente = fecharModalAgente;
window.carregarAgentes = carregarAgentes;
window.carregarGrupos = carregarGrupos;
window.renderizarAgentes = renderizarAgentes;
window.renderizarGrupos = renderizarGrupos;
window.excluirAgente = excluirAgente;
window.excluirGrupo = excluirGrupo;
window.toggleAgenteStatus = toggleAgenteStatus;
window.editarAgente = editarAgente;
window.editarGrupo = editarGrupo;
window.gerenciarMembrosGrupo = gerenciarMembrosGrupo;
window.adicionarFiltroAgente = adicionarFiltroAgente;
