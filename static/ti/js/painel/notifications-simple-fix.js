// Fix simples para as notificações melhoradas
(function() {
    'use strict';

    // Aguardar DOM carregar
    function initNotificationFix() {
        console.log('🔧 Aplicando correções nas notificações...');

        // Adicionar exemplos de notificações melhoradas quando modal abrir
        const btnNotificacoes = document.getElementById('btnNotificacoes');
        const modalNotificacoes = document.getElementById('modalNotificacoes');
        const listaNotificacoes = document.getElementById('listaNotificacoes');

        if (btnNotificacoes && modalNotificacoes && listaNotificacoes) {
            btnNotificacoes.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Mostrar modal
                modalNotificacoes.style.display = 'flex';
                document.body.style.overflow = 'hidden';

                // Adicionar notificações exemplo se estiver vazio
                if (listaNotificacoes.children.length === 0 || listaNotificacoes.textContent.trim() === '') {
                    createSampleNotifications();
                }
            });

            // Fechar modal
            const closeButtons = [
                document.getElementById('modalNotificacoesClose'),
                document.getElementById('btnFecharNotificacoes')
            ];

            closeButtons.forEach(btn => {
                if (btn) {
                    btn.addEventListener('click', function() {
                        modalNotificacoes.style.display = 'none';
                        document.body.style.overflow = '';
                    });
                }
            });

            // Fechar ao clicar fora
            modalNotificacoes.addEventListener('click', function(e) {
                if (e.target === modalNotificacoes) {
                    modalNotificacoes.style.display = 'none';
                    document.body.style.overflow = '';
                }
            });

            // Filtros
            document.addEventListener('click', function(e) {
                if (e.target.classList.contains('filter-btn')) {
                    // Remover active de todos
                    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
                    // Adicionar active no clicado
                    e.target.classList.add('active');
                    
                    // Simular filtro
                    const filter = e.target.getAttribute('data-filter');
                    filterNotifications(filter);
                }
            });

            // Marcar todas como lidas
            const btnMarcarTodas = document.getElementById('btnMarcarTodasLidas');
            if (btnMarcarTodas) {
                btnMarcarTodas.addEventListener('click', function() {
                    markAllAsRead();
                });
            }

            // Limpar todas
            const btnLimparTodas = document.getElementById('btnLimparNotificacoes');
            if (btnLimparTodas) {
                btnLimparTodas.addEventListener('click', function() {
                    if (confirm('Tem certeza que deseja limpar todas as notificações?')) {
                        clearAllNotifications();
                    }
                });
            }
        }

        // Atualizar contador inicial
        updateNotificationCount(3); // Mostrar 3 não lidas

        console.log('✅ Correções de notificações aplicadas');
    }

    function createSampleNotifications() {
        const listaNotificacoes = document.getElementById('listaNotificacoes');
        if (!listaNotificacoes) return;

        const notifications = [
            {
                id: 'notif-1',
                type: 'config',
                icon: 'fas fa-tools',
                iconClass: 'config',
                title: 'Configurações SLA',
                message: 'Configurações carregadas com sucesso!',
                time: 'há 3 minutos',
                priority: 'medium',
                badge: 'Sistema',
                unread: true
            },
            {
                id: 'notif-2',
                type: 'chamado',
                icon: 'fas fa-ticket-alt',
                iconClass: 'info',
                title: 'Novo Chamado #1234',
                message: 'João Silva reportou problema na impressora da unidade Central',
                time: 'há 15 minutos',
                priority: 'high',
                badge: 'Urgente',
                unread: true
            },
            {
                id: 'notif-3',
                type: 'sla',
                icon: 'fas fa-exclamation-triangle',
                iconClass: 'warning',
                title: 'Alerta de SLA',
                message: 'Chamado #1233 está próximo do vencimento (80% do tempo)',
                time: 'há 30 minutos',
                priority: 'high',
                badge: 'Atenção',
                unread: true
            },
            {
                id: 'notif-4',
                type: 'usuario',
                icon: 'fas fa-user-plus',
                iconClass: 'info',
                title: 'Novo Usuário',
                message: 'Maria Santos foi adicionada ao sistema como Gestora',
                time: 'há 1 hora',
                priority: 'low',
                badge: 'Novo',
                unread: false
            },
            {
                id: 'notif-5',
                type: 'system',
                icon: 'fas fa-cog',
                iconClass: 'system',
                title: 'Backup Automático',
                message: 'Backup do sistema realizado com sucesso às 03:00',
                time: 'há 2 horas',
                priority: 'low',
                badge: 'Sistema',
                unread: false
            }
        ];

        const html = notifications.map(notif => createNotificationHTML(notif)).join('');
        listaNotificacoes.innerHTML = html;

        // Adicionar event listeners para ações
        addNotificationEventListeners();
    }

    function createNotificationHTML(notif) {
        return `
            <div class="notification-item ${notif.unread ? 'unread' : ''} fade-in" 
                 data-id="${notif.id}" 
                 data-type="${notif.type}">
                ${notif.priority ? `<div class="notification-priority ${notif.priority}"></div>` : ''}
                
                <div class="notification-header">
                    <div class="notification-icon ${notif.iconClass}">
                        <i class="${notif.icon}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">
                            ${notif.title}
                            ${notif.badge ? `<span class="notification-badge">${notif.badge}</span>` : ''}
                        </div>
                        <div class="notification-message">
                            ${notif.message}
                        </div>
                    </div>
                </div>

                <div class="notification-meta">
                    <div class="notification-time">
                        <i class="fas fa-clock"></i>
                        ${notif.time}
                    </div>
                    <div class="notification-actions">
                        ${notif.unread ? 
                            `<button class="notification-action primary" onclick="markAsRead('${notif.id}')">
                                <i class="fas fa-check"></i> Marcar como lida
                            </button>` : ''
                        }
                        <button class="notification-action" onclick="removeNotification('${notif.id}')">
                            <i class="fas fa-times"></i> Remover
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function addNotificationEventListeners() {
        // Event listeners já são adicionados via onclick nos templates
    }

    function filterNotifications(filter) {
        const items = document.querySelectorAll('.notification-item');
        
        items.forEach(item => {
            const type = item.getAttribute('data-type');
            const isUnread = item.classList.contains('unread');
            
            let show = false;
            
            switch (filter) {
                case 'all':
                    show = true;
                    break;
                case 'unread':
                    show = isUnread;
                    break;
                case 'system':
                    show = type === 'system' || type === 'config';
                    break;
                case 'tickets':
                    show = type === 'chamado' || type === 'sla';
                    break;
            }
            
            item.style.display = show ? 'block' : 'none';
        });
    }

    function markAllAsRead() {
        const items = document.querySelectorAll('.notification-item.unread');
        items.forEach(item => {
            item.classList.remove('unread');
            const actions = item.querySelector('.notification-actions');
            if (actions) {
                const markButton = actions.querySelector('.notification-action.primary');
                if (markButton) {
                    markButton.remove();
                }
            }
        });
        updateNotificationCount(0);
        
        // Mostrar feedback
        if (window.advancedNotificationSystem && window.advancedNotificationSystem.showSuccess) {
            window.advancedNotificationSystem.showSuccess('Sucesso', 'Todas as notificações foram marcadas como lidas');
        }
    }

    function clearAllNotifications() {
        const listaNotificacoes = document.getElementById('listaNotificacoes');
        if (listaNotificacoes) {
            listaNotificacoes.innerHTML = `
                <div class="notifications-empty">
                    <div class="empty-icon">
                        <i class="fas fa-bell-slash"></i>
                    </div>
                    <h4>Nenhuma notificação</h4>
                    <p>Quando houver novas notificações, elas aparecerão aqui.</p>
                </div>
            `;
        }
        updateNotificationCount(0);
    }

    function updateNotificationCount(count) {
        const badge = document.getElementById('notificationCount');
        const countText = document.getElementById('notificationsCountText');
        
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }

        if (countText) {
            if (count > 0) {
                countText.textContent = `${count} ${count === 1 ? 'nova notificação' : 'novas notificações'}`;
            } else {
                countText.textContent = 'Nenhuma notificação nova';
            }
        }
    }

    // Funções globais para onclick
    window.markAsRead = function(id) {
        const item = document.querySelector(`[data-id="${id}"]`);
        if (item) {
            item.classList.remove('unread');
            const markButton = item.querySelector('.notification-action.primary');
            if (markButton) {
                markButton.remove();
            }
            
            // Recalcular count
            const unreadItems = document.querySelectorAll('.notification-item.unread');
            updateNotificationCount(unreadItems.length);
        }
    };

    window.removeNotification = function(id) {
        const item = document.querySelector(`[data-id="${id}"]`);
        if (item) {
            item.style.transition = 'all 0.3s ease';
            item.style.opacity = '0';
            item.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                item.remove();
                
                // Recalcular count
                const unreadItems = document.querySelectorAll('.notification-item.unread');
                updateNotificationCount(unreadItems.length);
                
                // Verificar se não há mais notificações
                const remainingItems = document.querySelectorAll('.notification-item');
                if (remainingItems.length === 0) {
                    const listaNotificacoes = document.getElementById('listaNotificacoes');
                    if (listaNotificacoes) {
                        listaNotificacoes.innerHTML = `
                            <div class="notifications-empty">
                                <div class="empty-icon">
                                    <i class="fas fa-bell-slash"></i>
                                </div>
                                <h4>Nenhuma notificação</h4>
                                <p>Quando houver novas notificações, elas aparecerão aqui.</p>
                            </div>
                        `;
                    }
                }
            }, 300);
        }
    };

    // Inicializar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNotificationFix);
    } else {
        initNotificationFix();
    }

    // Backup - inicializar após delay
    setTimeout(initNotificationFix, 500);

})();
