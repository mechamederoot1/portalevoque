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
        const targetId = link.getAttribute('href').substring(1);
        activateSection(targetId);
        navLinks.forEach(l => l.classList.remove('active'));
        navLinks.forEach(l => {
            if (l.getAttribute('href').substring(1) === targetId) l.classList.add('active');
        });
    });
});

function activateSection(id) {
    sections.forEach(section => {
        if (section.id === id) {
            section.classList.add('active');
            section.setAttribute('tabindex', '0');
            section.focus();
            
            // Carregar conteúdo específico da seção
            loadSectionContent(id);
        } else {
            section.classList.remove('active');
            section.removeAttribute('tabindex');
        }
    });
}

// Theme toggle
const themeToggleBtn = document.getElementById('themeToggle');
themeToggleBtn.addEventListener('click', () => {
    if (document.body.getAttribute('data-theme') === 'dark') {
        document.body.setAttribute('data-theme', 'light');
        themeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
    } else {
        document.body.setAttribute('data-theme', 'dark');
        themeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
    }
});

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
    } catch (error) {
        console.error('Erro ao carregar chamados:', error);
        chamadosGrid.innerHTML = '<p class="text-center py-4">Erro ao carregar chamados. Tente novamente mais tarde.</p>';
        // Usar sistema de notificações avançado
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar chamados');
        }
    }
}

// Função para atualizar contadores da visão geral
async function atualizarContadoresVisaoGeral() {
    try {
        const response = await fetch('/ti/painel/api/chamados/estatisticas');
        if (!response.ok) {
            throw new Error('Erro ao carregar estatísticas');
        }
        const stats = await response.json();
        
        document.getElementById('countAbertos').textContent = stats.Aberto || 0;
        document.getElementById('countAguardando').textContent = stats.Aguardando || 0;
        document.getElementById('countConcluidos').textContent = stats.Concluido || 0;
        document.getElementById('countCancelados').textContent = stats.Cancelado || 0;
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar estatísticas');
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

    // Filtrar por agente se o filtro existir
    const filtroAgente = document.getElementById('filtroAgente');
    if (filtroAgente && filtroAgente.value) {
        const agenteId = filtroAgente.value;
        filtrados = filtrados.filter(chamado =>
            chamado.agente_id && chamado.agente_id.toString() === agenteId
        );
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
        ${chamado.agente ? `
        <div class="info-row">
            <strong>Agente:</strong>
            <span class="badge bg-info">${chamado.agente.nome}</span>
        </div>` : ''}
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

// Função para renderizar a paginação
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
    // Listener para mudança no select
    document.querySelectorAll('.card select').forEach(select => {
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

// Prevenir comportamento padrão dos selects
document.getElementById('nivelAcesso')?.addEventListener('click', function(e) {
    e.stopPropagation();
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
    
    if (!dados.nome) erros.push('Nome é obrigatório');
    if (!dados.sobrenome) erros.push('Sobrenome é obrigatório');
    if (!dados.email) erros.push('E-mail é obrigatório');
    if (!dados.usuario) erros.push('Nome de usuário é obrigatório');
    if (!dados.senha) erros.push('Senha é obrigatória. Clique em "Gerar Senha"');
    if (!dados.nivel_acesso) erros.push('Nível de acesso é obrigatório');
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

        // Validação
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

        // Usar sistema de notificações avançado
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Usuário Criado', `Usuário ${data.nome} criado com sucesso!`);
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
        console.error('Erro ao atualizar usuário:', error);
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
    switch(sectionId) {
        case 'listar-unidades':
            renderListarUnidades();
            break;
        case 'gerenciar-chamados':
            loadChamados();
            // Adicionar filtro de agente após carregar chamados
            setTimeout(() => {
                adicionarFiltroAgente();
            }, 500);
            break;
        case 'permissoes':
            loadUsuarios();
            // Inicializar filtro de permissões
            inicializarFiltroPermissoes();
            break;
        case 'bloqueios':
            loadUsuariosBloqueados();
            break;
        case 'sla-dashboard':
            // Carregar dados SLA se a função existir
            if (typeof carregarSLA === 'function') {
                carregarSLA();
            }
            break;
        case 'configuracoes':
            // Carregar configurações de prioridades
            if (window.prioridadesManager) {
                window.prioridadesManager.carregarProblemas();
            }
            atualizarContadoresVisaoGeral();
            break;
        case 'visao-geral':
            atualizarContadoresVisaoGeral();
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

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    // Carregar chamados
    loadChamados();
    
    // Se estiver na seção de listar unidades, carrega elas
    if (window.location.hash === '#listar-unidades') {
        renderListarUnidades();
    }
    
    // Ativa a seção baseada no hash da URL
    const hash = window.location.hash.substring(1);
    if (hash) {
        activateSection(hash);
    } else {
        activateSection('visao-geral');
    }
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
                    `Chamado ${data.codigo} foi excluído`
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

        // Recarregar lista de agentes se estiver na seção
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
        const response = await fetch('/ti/painel/api/agentes');
        if (!response.ok) {
            throw new Error('Erro ao carregar agentes');
        }
        agentesData = await response.json();
        renderizarAgentes();
    } catch (error) {
        console.error('Erro ao carregar agentes:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar agentes');
        }
    }
}

// Renderizar lista de agentes
function renderizarAgentes() {
    const container = document.querySelector('#agentes-suporte .cards-grid');
    if (!container) return;

    container.innerHTML = '';

    if (agentesData.length === 0) {
        container.innerHTML = '<p class="text-center py-4">Nenhum agente cadastrado.</p>';
        return;
    }

    agentesData.forEach(agente => {
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
        case 'grupos-usuarios':
            setTimeout(() => {
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
    const filtroInput = document.getElementById('filtroPermissoes');
    const btnFiltrar = document.getElementById('btnFiltrarPermissoes');

    if (!filtroInput || !btnFiltrar) return;

    // Função para filtrar usuários
    const filtrarUsuarios = () => {
        const termoBusca = filtroInput.value.toLowerCase().trim();
        filtrarListaUsuarios(termoBusca);
    };

    // Event listeners
    filtroInput.addEventListener('input', filtrarUsuarios);
    btnFiltrar.addEventListener('click', filtrarUsuarios);

    // Filtrar ao pressionar Enter
    filtroInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            filtrarUsuarios();
        }
    });
}

function filtrarListaUsuarios(termoBusca) {
    const usuariosGrid = document.getElementById('usuariosGrid');
    if (!usuariosGrid) return;

    const cards = usuariosGrid.querySelectorAll('.user-card');
    let usuariosVisiveis = 0;

    cards.forEach(card => {
        const nome = card.querySelector('.user-name')?.textContent.toLowerCase() || '';
        const email = card.querySelector('.user-email')?.textContent.toLowerCase() || '';
        const usuario = card.querySelector('.user-username')?.textContent.toLowerCase() || '';
        const unidade = card.querySelector('.user-unidade')?.textContent.toLowerCase() || '';

        const textoCompleto = `${nome} ${email} ${usuario} ${unidade}`;

        if (termoBusca === '' || textoCompleto.includes(termoBusca)) {
            card.style.display = '';
            usuariosVisiveis++;
        } else {
            card.style.display = 'none';
        }
    });

    // Mostrar mensagem se nenhum usuário for encontrado
    const mensagemVazia = document.getElementById('mensagemUsuariosVazia');
    if (usuariosVisiveis === 0 && termoBusca !== '') {
        if (!mensagemVazia) {
            const mensagem = document.createElement('div');
            mensagem.id = 'mensagemUsuariosVazia';
            mensagem.className = 'text-center py-4';
            mensagem.innerHTML = `
                <i class="fas fa-search fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">Nenhum usuário encontrado</h5>
                <p class="text-muted">Tente usar termos de busca diferentes</p>
            `;
            usuariosGrid.appendChild(mensagem);
        }
    } else if (mensagemVazia) {
        mensagemVazia.remove();
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

async function carregarAgentes() {
    try {
        const response = await fetch('/ti/painel/api/agentes');
        if (!response.ok) {
            throw new Error('Erro ao carregar agentes');
        }

        const agentes = await response.json();
        renderizarAgentes(agentes);
        atualizarEstatisticasAgentes(agentes);

    } catch (error) {
        console.error('Erro ao carregar agentes:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar agentes de suporte');
        }
    }
}

function renderizarAgentes(agentes) {
    const container = document.getElementById('agentesGrid');
    if (!container) return;

    if (!agentes || agentes.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-headset fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">Nenhum agente encontrado</h5>
                <p class="text-muted">Crie o primeiro agente de suporte</p>
            </div>
        `;
        return;
    }

    container.innerHTML = agentes.map(agente => `
        <div class="card agent-card">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h5 class="card-title agent-name">${agente.nome}</h5>
                    <span class="badge ${agente.ativo ? 'bg-success' : 'bg-secondary'}">
                        ${agente.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                </div>
                <p class="card-text agent-email text-muted">${agente.email}</p>
                <div class="agent-stats mb-3">
                    <small class="text-muted">
                        <i class="fas fa-star"></i> ${agente.nivel_experiencia} •
                        <i class="fas fa-tasks"></i> ${agente.chamados_ativos}/${agente.max_chamados_simultaneos} chamados
                    </small>
                </div>
                <div class="agent-specialties mb-2">
                    ${agente.especialidades && agente.especialidades.map ?
                        agente.especialidades.map(esp =>
                            `<span class="badge bg-primary me-1">${esp}</span>`
                        ).join('') : ''
                    }
                </div>
                <div class="agent-info">
                    <small class="text-muted">
                        Criado: ${agente.data_criacao}
                    </small>
                </div>
                <div class="card-actions mt-3">
                    <button class="btn btn-sm btn-primary" onclick="editarAgente(${agente.id})">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-sm btn-info" onclick="verChamadosAgente(${agente.id})">
                        <i class="fas fa-tasks"></i> Chamados
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="excluirAgente(${agente.id})">
                        <i class="fas fa-trash"></i> Excluir
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

function atualizarEstatisticasAgentes(agentes) {
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
    const container = document.getElementById('alertasContainer');
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
        const container = document.getElementById('backupContainer');
        if (container) {
            container.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-database me-2"></i>Backup do Sistema</h5>
                            </div>
                            <div class="card-body">
                                <p>Último backup: <strong>31/01/2025 06:00:00</strong></p>
                                <p>Status: <span class="badge bg-success">Sucesso</span></p>
                                <button class="btn btn-primary" onclick="criarBackup()">
                                    <i class="fas fa-download"></i> Criar Backup
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-tools me-2"></i>Manutenção</h5>
                            </div>
                            <div class="card-body">
                                <p>Limpeza automática: <strong>Ativada</strong></p>
                                <p>Próxima manutenção: <strong>01/02/2025 02:00:00</strong></p>
                                <button class="btn btn-warning" onclick="executarManutencao()">
                                    <i class="fas fa-wrench"></i> Executar Manutenção
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao carregar backup/manutenção:', error);
    }
}

// ==================== LOGS DE ACESSO ====================

async function carregarLogsAcesso() {
    try {
        const container = document.getElementById('logsAcessoContainer');
        if (container) {
            // Simular logs de acesso
            const logs = [
                { usuario: 'Admin', ip: '192.168.1.100', data: '31/01/2025 10:30:00', acao: 'Login' },
                { usuario: 'João Silva', ip: '192.168.1.101', data: '31/01/2025 10:25:00', acao: 'Logout' },
                { usuario: 'Maria Santos', ip: '192.168.1.102', data: '31/01/2025 10:20:00', acao: 'Acesso Negado' }
            ];

            container.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Usuário</th>
                                <th>IP</th>
                                <th>Data/Hora</th>
                                <th>Ação</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${logs.map(log => `
                                <tr>
                                    <td>${log.usuario}</td>
                                    <td>${log.ip}</td>
                                    <td>${log.data}</td>
                                    <td>
                                        <span class="badge bg-${log.acao === 'Login' ? 'success' : log.acao === 'Logout' ? 'info' : 'danger'}">
                                            ${log.acao}
                                        </span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;
        }
    } catch (error) {
        console.error('Erro ao carregar logs de acesso:', error);
    }
}

// ==================== DASHBOARD AVANÇADO ====================

async function carregarDashboardAvancado() {
    try {
        const container = document.getElementById('dashboardAvancadoContainer');
        if (container) {
            container.innerHTML = `
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <h6>CPU</h6>
                                <h3>45%</h3>
                                <small>Normal</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-success text-white">
                            <div class="card-body">
                                <h6>Memória</h6>
                                <h3>62%</h3>
                                <small>Normal</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-warning text-white">
                            <div class="card-body">
                                <h6>Disco</h6>
                                <h3>78%</h3>
                                <small>Atenção</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-info text-white">
                            <div class="card-body">
                                <h6>Rede</h6>
                                <h3>23%</h3>
                                <small>Baixo</small>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-header">
                        <h5>Monitoramento em Tempo Real</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="chartMonitoramento" width="400" height="200"></canvas>
                    </div>
                </div>
            `;
        }
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
