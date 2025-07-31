// ==================== GERENCIAMENTO DE AGENTES DE SUPORTE ====================

let agentesData = [];
let agentesStatisticsData = {};

// Carregar agentes de suporte
async function carregarAgentes() {
    try {
        console.log('Carregando agentes de suporte...');

        // Carregar usuários com nível "Agente de suporte"
        const response = await fetch('/ti/painel/api/usuarios');
        if (!response.ok) {
            throw new Error('Erro ao carregar usuários');
        }

        const todosUsuarios = await response.json();

        // Filtrar apenas usuários com nível "Agente de suporte"
        agentesData = todosUsuarios.filter(usuario =>
            usuario.nivel_acesso === 'Agente de suporte' && !usuario.bloqueado
        );

        console.log('Agentes carregados:', agentesData);

        // Carregar estatísticas
        await carregarEstatisticasAgentes();

        // Renderizar os dados
        renderizarAgentes();

    } catch (error) {
        console.error('Erro ao carregar agentes:', error);
        const container = document.getElementById('agentesGrid');
        if (container) {
            container.innerHTML = '<p class="text-center py-4">Erro ao carregar agentes. Tente novamente mais tarde.</p>';
        }

        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar agentes de suporte');
        }
    }
}

// Carregar estatísticas dos agentes
async function carregarEstatisticasAgentes() {
    try {
        console.log('Carregando estatísticas dos agentes...');

        // Calcular estatísticas baseado nos dados dos agentes
        const totalAgentes = agentesData.length;
        const agentesAtivos = agentesData.filter(agente => !agente.bloqueado).length;

        // Buscar estatísticas de chamados se o endpoint existir
        let chamadosAtribuidos = 0;
        let agentesDisponiveis = agentesAtivos;

        try {
            const responseEstatisticas = await fetch('/ti/painel/api/agentes/estatisticas');
            if (responseEstatisticas.ok) {
                const estatisticas = await responseEstatisticas.json();
                chamadosAtribuidos = estatisticas.chamados_atribuidos || 0;
                agentesDisponiveis = estatisticas.agentes_disponiveis || agentesAtivos;
            }
        } catch (err) {
            console.log('Endpoint de estatísticas não disponível, usando valores padrão');
        }

        agentesStatisticsData = {
            total_agentes: totalAgentes,
            agentes_ativos: agentesAtivos,
            chamados_atribuidos: chamadosAtribuidos,
            agentes_disponiveis: agentesDisponiveis
        };

        console.log('Estatísticas calculadas:', agentesStatisticsData);

        // Atualizar cards de estatísticas
        atualizarCardsEstatisticas();

    } catch (error) {
        console.error('Erro ao carregar estatísticas dos agentes:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar estatísticas dos agentes');
        }
    }
}

// Atualizar cards de estatísticas
function atualizarCardsEstatisticas() {
    if (!agentesStatisticsData) return;
    
    const totalElement = document.getElementById('totalAgentes');
    const ativosElement = document.getElementById('agentesAtivos');
    const atribuidosElement = document.getElementById('chamadosAtribuidos');
    const disponiveisElement = document.getElementById('agentesDisponiveis');
    
    if (totalElement) totalElement.textContent = agentesStatisticsData.total_agentes || 0;
    if (ativosElement) ativosElement.textContent = agentesStatisticsData.agentes_ativos || 0;
    if (atribuidosElement) atribuidosElement.textContent = agentesStatisticsData.chamados_atribuidos || 0;
    if (disponiveisElement) disponiveisElement.textContent = agentesStatisticsData.agentes_disponiveis || 0;
}

// Renderizar lista de agentes
function renderizarAgentes() {
    const container = document.getElementById('agentesGrid');
    if (!container) {
        console.error('Container agentesGrid não encontrado');
        return;
    }
    
    if (!agentesData || agentesData.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <i class="fas fa-headset fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">Nenhum agente encontrado</h5>
                <p class="text-muted">Crie o primeiro agente de suporte</p>
            </div>
        `;
        return;
    }
    
    const html = agentesData.map(agente => {
        const statusClass = agente.ativo ? 'status-concluido' : 'status-cancelado';
        const statusText = agente.ativo ? 'Ativo' : 'Inativo';
        const statusIcon = agente.ativo ? 'fa-check-circle' : 'fa-times-circle';
        
        const nivelBadgeClass = {
            'junior': 'bg-info',
            'pleno': 'bg-warning',
            'senior': 'bg-success'
        }[agente.nivel_experiencia] || 'bg-secondary';
        
        return `
            <div class="card agente-card mb-3">
                <div class="card-header">
                    <h3>${agente.nome}</h3>
                    <div class="status-badge ${statusClass}">
                        <i class="fas ${statusIcon}"></i>
                        ${statusText}
                    </div>
                </div>
                <div class="card-body">
                    <div class="info-row">
                        <strong>Usuário:</strong>
                        <span>${agente.email || 'undefined'}</span>
                    </div>
                    <div class="info-row">
                        <strong>Nível:</strong>
                        <span class="badge ${nivelBadgeClass}">${agente.nivel_experiencia}</span>
                    </div>
                    <div class="info-row">
                        <strong>Máx. Chamados:</strong>
                        <span>${agente.max_chamados_simultaneos}</span>
                    </div>
                    <div class="info-row">
                        <strong>Chamados Ativos:</strong>
                        <span class="badge ${agente.chamados_ativos > 0 ? 'bg-warning' : 'bg-secondary'}">${agente.chamados_ativos}</span>
                    </div>
                    <div class="info-row">
                        <strong>Especialidades:</strong>
                        <span>${agente.especialidades && agente.especialidades.length > 0 ? agente.especialidades.join(', ') : 'Não informado'}</span>
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn btn-primary btn-sm" onclick="editarAgente(${agente.id})" title="Editar agente">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-info btn-sm" onclick="verChamadosAgente(${agente.id})" title="Ver chamados">
                        <i class="fas fa-ticket-alt"></i> Chamados
                    </button>
                    <button class="btn ${agente.ativo ? 'btn-warning' : 'btn-success'} btn-sm" 
                            onclick="toggleStatusAgente(${agente.id})" 
                            title="${agente.ativo ? 'Desativar' : 'Ativar'} agente">
                        <i class="fas ${agente.ativo ? 'fa-pause' : 'fa-play'}"></i>
                        ${agente.ativo ? 'Desativar' : 'Ativar'}
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="excluirAgente(${agente.id})" title="Excluir agente">
                        <i class="fas fa-trash"></i> Excluir
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// Criar novo agente
async function criarAgente() {
    try {
        // Carregar usuários disponíveis
        const response = await fetch('/ti/painel/api/usuarios-disponiveis');
        if (!response.ok) {
            throw new Error('Erro ao carregar usuários disponíveis');
        }
        
        const usuariosDisponiveis = await response.json();
        
        if (usuariosDisponiveis.length === 0) {
            if (window.advancedNotificationSystem) {
                window.advancedNotificationSystem.showWarning('Aviso', 'Não há usuários disponíveis para se tornarem agentes');
            }
            return;
        }
        
        // Criar modal de seleção
        const modalHtml = `
            <div class="modal active" id="modalCriarAgente">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3>Criar Novo Agente</h3>
                        <button class="modal-close" onclick="fecharModalCriarAgente()">&times;</button>
                    </div>
                    <div class="modal-body">
                        <form id="formCriarAgente">
                            <div class="form-group mb-3">
                                <label for="usuarioAgente">Selecionar Usuário</label>
                                <select class="form-control" id="usuarioAgente" required>
                                    <option value="">Selecione um usuário</option>
                                    ${usuariosDisponiveis.map(u => `
                                        <option value="${u.id}">${u.nome} (${u.email})</option>
                                    `).join('')}
                                </select>
                            </div>
                            <div class="form-group mb-3">
                                <label for="nivelExperiencia">Nível de Experiência</label>
                                <select class="form-control" id="nivelExperiencia" required>
                                    <option value="junior">Júnior</option>
                                    <option value="pleno">Pleno</option>
                                    <option value="senior">Sênior</option>
                                </select>
                            </div>
                            <div class="form-group mb-3">
                                <label for="maxChamados">Máximo de Chamados Simultâneos</label>
                                <input type="number" class="form-control" id="maxChamados" value="10" min="1" max="50" required>
                            </div>
                            <div class="form-group mb-3">
                                <label for="especialidadesAgente">Especialidades</label>
                                <div class="checkbox-group">
                                    <label><input type="checkbox" value="Hardware"> Hardware</label>
                                    <label><input type="checkbox" value="Software"> Software</label>
                                    <label><input type="checkbox" value="Redes"> Redes</label>
                                    <label><input type="checkbox" value="Sistemas"> Sistemas</label>
                                    <label><input type="checkbox" value="Notebook/Desktop"> Notebook/Desktop</label>
                                    <label><input type="checkbox" value="Internet"> Internet</label>
                                    <label><input type="checkbox" value="Sistema EVO"> Sistema EVO</label>
                                    <label><input type="checkbox" value="Outros"> Outros</label>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary" onclick="salvarNovoAgente()">
                            <i class="fas fa-save"></i> Criar Agente
                        </button>
                        <button class="btn btn-secondary" onclick="fecharModalCriarAgente()">
                            <i class="fas fa-times"></i> Cancelar
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Remover modal existente se houver
        const modalExistente = document.getElementById('modalCriarAgente');
        if (modalExistente) {
            modalExistente.remove();
        }
        
        // Adicionar modal ao body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
    } catch (error) {
        console.error('Erro ao criar modal de agente:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', 'Erro ao carregar usuários disponíveis');
        }
    }
}

// Fechar modal de criar agente
function fecharModalCriarAgente() {
    const modal = document.getElementById('modalCriarAgente');
    if (modal) {
        modal.remove();
    }
}

// Salvar novo agente
async function salvarNovoAgente() {
    try {
        const usuarioId = document.getElementById('usuarioAgente').value;
        const nivelExperiencia = document.getElementById('nivelExperiencia').value;
        const maxChamados = parseInt(document.getElementById('maxChamados').value);
        
        // Coletar especialidades selecionadas
        const especialidades = Array.from(document.querySelectorAll('#modalCriarAgente input[type="checkbox"]:checked'))
            .map(checkbox => checkbox.value);
        
        if (!usuarioId) {
            throw new Error('Selecione um usuário');
        }
        
        const dados = {
            usuario_id: parseInt(usuarioId),
            ativo: true,
            nivel_experiencia: nivelExperiencia,
            max_chamados_simultaneos: maxChamados,
            especialidades: especialidades
        };
        
        const response = await fetch('/ti/painel/api/agentes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(dados)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Erro ao criar agente');
        }
        
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Sucesso', result.message || 'Agente criado com sucesso');
        }
        
        fecharModalCriarAgente();
        carregarAgentes();
        
    } catch (error) {
        console.error('Erro ao salvar agente:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

// Editar agente
async function editarAgente(agenteId) {
    // TODO: Implementar edição de agente
    if (window.advancedNotificationSystem) {
        window.advancedNotificationSystem.showInfo('Info', 'Funcionalidade de edição em desenvolvimento');
    }
}

// Ver chamados do agente
async function verChamadosAgente(agenteId) {
    // TODO: Implementar visualização de chamados do agente
    if (window.advancedNotificationSystem) {
        window.advancedNotificationSystem.showInfo('Info', 'Funcionalidade de visualização de chamados em desenvolvimento');
    }
}

// Toggle status do agente
async function toggleStatusAgente(agenteId) {
    try {
        const agente = agentesData.find(a => a.id === agenteId);
        if (!agente) {
            throw new Error('Agente não encontrado');
        }
        
        const novoStatus = !agente.ativo;
        const action = novoStatus ? 'ativar' : 'desativar';
        
        if (!confirm(`Tem certeza que deseja ${action} este agente?`)) {
            return;
        }
        
        const response = await fetch(`/ti/painel/api/agentes/${agenteId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ativo: novoStatus })
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || `Erro ao ${action} agente`);
        }
        
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Sucesso', result.message || `Agente ${novoStatus ? 'ativado' : 'desativado'} com sucesso`);
        }
        
        carregarAgentes();
        
    } catch (error) {
        console.error('Erro ao alterar status do agente:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

// Excluir agente
async function excluirAgente(agenteId) {
    try {
        const agente = agentesData.find(a => a.id === agenteId);
        if (!agente) {
            throw new Error('Agente não encontrado');
        }
        
        if (!confirm(`Tem certeza que deseja excluir o agente "${agente.nome}"? Esta ação não pode ser desfeita.`)) {
            return;
        }
        
        const response = await fetch(`/ti/painel/api/agentes/${agenteId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Erro ao excluir agente');
        }
        
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showSuccess('Sucesso', result.message || 'Agente excluído com sucesso');
        }
        
        carregarAgentes();
        
    } catch (error) {
        console.error('Erro ao excluir agente:', error);
        if (window.advancedNotificationSystem) {
            window.advancedNotificationSystem.showError('Erro', error.message);
        }
    }
}

// Configurar event listeners
function configurarEventListenersAgentes() {
    // Botão criar agente
    const btnCriarAgente = document.getElementById('btnCriarAgente');
    if (btnCriarAgente) {
        btnCriarAgente.addEventListener('click', criarAgente);
    }
}

// Inicializar a seção de agentes
function inicializarAgentes() {
    console.log('Inicializando seção de agentes...');
    configurarEventListenersAgentes();
    carregarAgentes();
}

// Exportar funções para uso global
window.carregarAgentes = carregarAgentes;
window.carregarEstatisticasAgentes = carregarEstatisticasAgentes;
window.inicializarAgentes = inicializarAgentes;
window.criarAgente = criarAgente;
window.editarAgente = editarAgente;
window.verChamadosAgente = verChamadosAgente;
window.toggleStatusAgente = toggleStatusAgente;
window.excluirAgente = excluirAgente;
window.fecharModalCriarAgente = fecharModalCriarAgente;
window.salvarNovoAgente = salvarNovoAgente;
