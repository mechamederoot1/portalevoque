// Sistema de Notificações Melhorado
class ImprovedNotificationSystem {
    constructor() {
        this.notifications = [];
        this.currentFilter = 'all';
        this.socket = null;
        this.settings = {
            novoChamado: true,
            statusAlterado: true,
            novoUsuario: true,
            emailNotifications: true,
            soundEnabled: true,
            autoMarkRead: false,
            maxNotifications: 50
        };
        this.isInitialized = false;
        this.init();
    }

    init() {
        if (this.isInitialized) return;
        
        try {
            this.bindEvents();
            this.initializeSocket();
            this.loadRecentNotifications();
            this.createSampleNotifications(); // Para demonstração
            this.isInitialized = true;
            console.log('Sistema de notificações melhorado inicializado');
        } catch (error) {
            console.error('Erro ao inicializar notificações:', error);
        }
    }

    bindEvents() {
        // Botão de notificações na navbar
        const btnNotificacoes = document.getElementById('btnNotificacoes');
        if (btnNotificacoes) {
            btnNotificacoes.addEventListener('click', (e) => {
                e.preventDefault();
                this.openNotificationModal();
            });
        }

        // Fechar modal
        const closeBtn = document.getElementById('modalNotificacoesClose');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.closeNotificationModal();
            });
        }

        // Fechar modal ao clicar no botão fechar
        const btnFechar = document.getElementById('btnFecharNotificacoes');
        if (btnFechar) {
            btnFechar.addEventListener('click', () => {
                this.closeNotificationModal();
            });
        }

        // Marcar todas como lidas
        const markAllBtn = document.getElementById('btnMarcarTodasLidas');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', () => {
                this.markAllAsRead();
            });
        }

        // Limpar todas
        const clearAllBtn = document.getElementById('btnLimparNotificacoes');
        if (clearAllBtn) {
            clearAllBtn.addEventListener('click', () => {
                this.clearAllNotifications();
            });
        }

        // Filtros
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                const filter = e.target.getAttribute('data-filter');
                this.setFilter(filter);
            }
        });

        // Fechar modal ao clicar fora
        const modal = document.getElementById('modalNotificacoes');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeNotificationModal();
                }
            });
        }

        // Tecla ESC para fechar
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeNotificationModal();
            }
        });
    }

    openNotificationModal() {
        const modal = document.getElementById('modalNotificacoes');
        if (modal) {
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            this.renderNotifications();
            this.updateNotificationCount();
        }
    }

    closeNotificationModal() {
        const modal = document.getElementById('modalNotificacoes');
        if (modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }

    setFilter(filter) {
        this.currentFilter = filter;
        
        // Atualizar botões de filtro
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-filter') === filter) {
                btn.classList.add('active');
            }
        });

        this.renderNotifications();
    }

    getFilteredNotifications() {
        let filtered = [...this.notifications];

        switch (this.currentFilter) {
            case 'unread':
                filtered = filtered.filter(n => !n.read);
                break;
            case 'system':
                filtered = filtered.filter(n => n.type === 'system' || n.type === 'config');
                break;
            case 'tickets':
                filtered = filtered.filter(n => n.type === 'chamado' || n.type === 'sla');
                break;
        }

        return filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    }

    renderNotifications() {
        const container = document.getElementById('listaNotificacoes');
        if (!container) return;

        const filtered = this.getFilteredNotifications();

        if (filtered.length === 0) {
            container.innerHTML = this.getEmptyState();
            return;
        }

        container.innerHTML = filtered.map(notification => 
            this.createNotificationHTML(notification)
        ).join('');

        // Adicionar event listeners para ações
        this.bindNotificationActions();
    }

    createNotificationHTML(notification) {
        const timeAgo = this.getTimeAgo(notification.timestamp);
        const priorityClass = this.getPriorityClass(notification.priority);
        const iconClass = this.getIconClass(notification.type);
        
        return `
            <div class="notification-item ${notification.read ? '' : 'unread'} fade-in" 
                 data-id="${notification.id}" 
                 data-type="${notification.type}">
                ${notification.priority ? `<div class="notification-priority ${priorityClass}"></div>` : ''}
                
                <div class="notification-header">
                    <div class="notification-icon ${iconClass}">
                        <i class="${this.getIconName(notification.type)}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">
                            ${notification.title}
                            ${notification.badge ? `<span class="notification-badge">${notification.badge}</span>` : ''}
                        </div>
                        <div class="notification-message">
                            ${notification.message}
                        </div>
                    </div>
                </div>

                <div class="notification-meta">
                    <div class="notification-time">
                        <i class="fas fa-clock"></i>
                        ${timeAgo}
                    </div>
                    <div class="notification-actions">
                        ${!notification.read ? 
                            `<button class="notification-action primary" onclick="improvedNotifications.markAsRead('${notification.id}')">
                                <i class="fas fa-check"></i> Marcar como lida
                            </button>` : ''
                        }
                        <button class="notification-action" onclick="improvedNotifications.removeNotification('${notification.id}')">
                            <i class="fas fa-times"></i> Remover
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getEmptyState() {
        const messages = {
            all: 'Nenhuma notificação encontrada',
            unread: 'Não há notificações não lidas',
            system: 'Nenhuma notificação do sistema',
            tickets: 'Nenhuma notificação de chamados'
        };

        return `
            <div class="notifications-empty">
                <div class="empty-icon">
                    <i class="fas fa-bell-slash"></i>
                </div>
                <h4>${messages[this.currentFilter]}</h4>
                <p>Quando houver novas notificações, elas aparecerão aqui.</p>
            </div>
        `;
    }

    getIconClass(type) {
        const classes = {
            'system': 'system',
            'config': 'config',
            'chamado': 'info',
            'sla': 'warning',
            'usuario': 'info',
            'success': 'success',
            'error': 'danger',
            'warning': 'warning',
            'info': 'info'
        };
        return classes[type] || 'system';
    }

    getIconName(type) {
        const icons = {
            'system': 'fas fa-cog',
            'config': 'fas fa-tools',
            'chamado': 'fas fa-ticket-alt',
            'sla': 'fas fa-exclamation-triangle',
            'usuario': 'fas fa-user-plus',
            'success': 'fas fa-check-circle',
            'error': 'fas fa-times-circle',
            'warning': 'fas fa-exclamation-triangle',
            'info': 'fas fa-info-circle'
        };
        return icons[type] || 'fas fa-bell';
    }

    getPriorityClass(priority) {
        const classes = {
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        };
        return classes[priority] || '';
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffInMinutes = Math.floor((now - time) / (1000 * 60));

        if (diffInMinutes < 1) return 'Agora mesmo';
        if (diffInMinutes < 60) return `${diffInMinutes}m atrás`;
        
        const diffInHours = Math.floor(diffInMinutes / 60);
        if (diffInHours < 24) return `${diffInHours}h atrás`;
        
        const diffInDays = Math.floor(diffInHours / 24);
        return `${diffInDays}d atrás`;
    }

    addNotification(notification) {
        const newNotification = {
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            read: false,
            ...notification
        };

        this.notifications.unshift(newNotification);

        // Limitar número de notificações
        if (this.notifications.length > this.settings.maxNotifications) {
            this.notifications = this.notifications.slice(0, this.settings.maxNotifications);
        }

        this.updateNotificationCount();
        this.playNotificationSound();

        // Se o modal estiver aberto, re-renderizar
        const modal = document.getElementById('modalNotificacoes');
        if (modal && modal.style.display !== 'none') {
            this.renderNotifications();
        }

        return newNotification.id;
    }

    markAsRead(notificationId) {
        const notification = this.notifications.find(n => n.id === notificationId);
        if (notification) {
            notification.read = true;
            this.updateNotificationCount();
            this.renderNotifications();
        }
    }

    markAllAsRead() {
        this.notifications.forEach(n => n.read = true);
        this.updateNotificationCount();
        this.renderNotifications();
        
        this.showSuccess('Sucesso', 'Todas as notificações foram marcadas como lidas');
    }

    removeNotification(notificationId) {
        this.notifications = this.notifications.filter(n => n.id !== notificationId);
        this.updateNotificationCount();
        this.renderNotifications();
    }

    clearAllNotifications() {
        if (confirm('Tem certeza que deseja limpar todas as notificações?')) {
            this.notifications = [];
            this.updateNotificationCount();
            this.renderNotifications();
            
            this.showSuccess('Sucesso', 'Todas as notificações foram removidas');
        }
    }

    updateNotificationCount() {
        const unreadCount = this.notifications.filter(n => !n.read).length;
        
        // Atualizar badge na navbar
        const badge = document.getElementById('notificationCount');
        if (badge) {
            if (unreadCount > 0) {
                badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }

        // Atualizar texto no modal
        const countText = document.getElementById('notificationsCountText');
        if (countText) {
            if (unreadCount > 0) {
                countText.textContent = `${unreadCount} ${unreadCount === 1 ? 'nova notificação' : 'novas notificações'}`;
            } else {
                countText.textContent = 'Nenhuma notificação nova';
            }
        }
    }

    playNotificationSound() {
        if (!this.settings.soundEnabled) return;
        
        try {
            // Criar um som simples usando Web Audio API
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            console.log('Som de notificação não disponível');
        }
    }

    createSampleNotifications() {
        // Criar algumas notificações de exemplo
        const samples = [
            {
                type: 'config',
                title: 'Configurações SLA',
                message: 'Configurações carregadas com sucesso!',
                priority: 'medium',
                badge: 'Sistema'
            },
            {
                type: 'chamado',
                title: 'Novo Chamado #1234',
                message: 'João Silva reportou problema na impressora da unidade Central',
                priority: 'high',
                badge: 'Urgente'
            },
            {
                type: 'sla',
                title: 'Alerta de SLA',
                message: 'Chamado #1233 está próximo do vencimento (80% do tempo)',
                priority: 'high',
                badge: 'Atenção'
            },
            {
                type: 'usuario',
                title: 'Novo Usuário',
                message: 'Maria Santos foi adicionada ao sistema como Gestora',
                priority: 'low',
                badge: 'Novo'
            },
            {
                type: 'system',
                title: 'Backup Automático',
                message: 'Backup do sistema realizado com sucesso às 03:00',
                priority: 'low',
                badge: 'Sistema'
            }
        ];

        // Adicionar com diferentes timestamps
        samples.forEach((sample, index) => {
            const timestamp = new Date();
            timestamp.setMinutes(timestamp.getMinutes() - (index * 15)); // 15 min de diferença
            
            this.notifications.push({
                id: `sample-${index}`,
                timestamp: timestamp.toISOString(),
                read: index > 2, // Primeiras 3 não lidas
                ...sample
            });
        });

        this.updateNotificationCount();
    }

    // Métodos para mostrar notificações toast (fora do modal)
    showSuccess(title, message) {
        this.addNotification({
            type: 'success',
            title: title,
            message: message,
            priority: 'low'
        });
    }

    showError(title, message) {
        this.addNotification({
            type: 'error',
            title: title,
            message: message,
            priority: 'high'
        });
    }

    showWarning(title, message) {
        this.addNotification({
            type: 'warning',
            title: title,
            message: message,
            priority: 'medium'
        });
    }

    showInfo(title, message) {
        this.addNotification({
            type: 'info',
            title: title,
            message: message,
            priority: 'low'
        });
    }

    bindNotificationActions() {
        // As ações são vinculadas através de onclick nos templates
        // Este método pode ser usado para ações mais complexas
    }

    initializeSocket() {
        try {
            if (typeof io === 'undefined') {
                console.warn('Socket.IO não está disponível');
                return;
            }

            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true,
                timeout: 20000
            });

            this.socket.on('connect', () => {
                console.log('Socket.IO conectado para notificações');
            });

            this.socket.on('disconnect', () => {
                console.log('Socket.IO desconectado');
            });

            // Eventos de notificação via socket
            this.socket.on('novo_chamado', (data) => {
                this.addNotification({
                    type: 'chamado',
                    title: 'Novo Chamado',
                    message: `Chamado ${data.codigo} criado por ${data.solicitante}`,
                    priority: 'medium',
                    badge: 'Novo'
                });
            });

            this.socket.on('status_atualizado', (data) => {
                this.addNotification({
                    type: 'chamado',
                    title: 'Status Atualizado',
                    message: `Chamado ${data.codigo} alterado para ${data.novo_status}`,
                    priority: 'low',
                    badge: 'Atualizado'
                });
            });

        } catch (error) {
            console.error('Erro ao inicializar Socket.IO:', error);
        }
    }

    loadRecentNotifications() {
        // Carregar notificações do servidor se necessário
        // Por enquanto, usando apenas as amostras
    }

    updateSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
    }

    // Método para testar notificações
    testNotifications() {
        const types = ['success', 'error', 'warning', 'info'];
        const type = types[Math.floor(Math.random() * types.length)];
        
        this.addNotification({
            type: type,
            title: `Teste de Notificação ${type.toUpperCase()}`,
            message: `Esta é uma notificação de teste do tipo ${type}`,
            priority: 'medium',
            badge: 'Teste'
        });
    }
}

// Inicializar sistema melhorado
let improvedNotifications;

document.addEventListener('DOMContentLoaded', function() {
    improvedNotifications = new ImprovedNotificationSystem();
    
    // Expor globalmente para debug
    window.improvedNotifications = improvedNotifications;
    
    console.log('Sistema de notificações melhorado carregado');
});

// Compatibilidade com sistema antigo
window.advancedNotificationSystem = {
    showSuccess: (title, message) => improvedNotifications?.showSuccess(title, message),
    showError: (title, message) => improvedNotifications?.showError(title, message),
    showWarning: (title, message) => improvedNotifications?.showWarning(title, message),
    showInfo: (title, message) => improvedNotifications?.showInfo(title, message),
    testNotifications: () => improvedNotifications?.testNotifications(),
    updateSettings: (settings) => improvedNotifications?.updateSettings(settings)
};
