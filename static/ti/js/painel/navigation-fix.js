// Navigation Fix Script
// Este script corrige problemas de navegação entre seções do painel

console.log('🔧 NAVIGATION FIX: Carregando correção de navegação...');

// Função simples e direta para navegação
function forceNavigateToSection(sectionId) {
    console.log('🔧 NAVIGATION FIX: Forçando navegação para:', sectionId);
    
    // Remover active de todas as seções
    const allSections = document.querySelectorAll('section.content-section');
    allSections.forEach(section => {
        section.classList.remove('active');
        section.style.display = 'none';
    });
    
    // Ativar a seção alvo
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.add('active');
        targetSection.style.display = 'block';
        console.log('✅ NAVIGATION FIX: Seção ativada:', sectionId);
        
        // Atualizar URL hash
        if (window.location.hash !== '#' + sectionId) {
            window.location.hash = sectionId;
        }
        
        // Atualizar links ativos
        document.querySelectorAll('.sidebar nav ul li a').forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + sectionId) {
                link.classList.add('active');
            }
        });
        
        // Carregar conteúdo da seção se necessário
        if (typeof loadSectionContent === 'function') {
            setTimeout(() => {
                loadSectionContent(sectionId);
            }, 100);
        }
    } else {
        console.error('❌ NAVIGATION FIX: Seção não encontrada:', sectionId);
    }
}

// Aguardar DOM carregado
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 NAVIGATION FIX: DOM carregado, aplicando correções...');
    
    // Aguardar um pouco para todos os scripts carregarem
    setTimeout(() => {
        console.log('🔧 NAVIGATION FIX: Aplicando correções de navegação...');
        
        // Interceptar todos os cliques nos links da sidebar
        document.querySelectorAll('.sidebar nav ul li a').forEach(link => {
            const href = link.getAttribute('href');
            if (href && href.startsWith('#') && href !== '#') {
                // Remover event listeners existentes (se possível)
                const newLink = link.cloneNode(true);
                link.parentNode.replaceChild(newLink, link);
                
                // Adicionar novo event listener
                newLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const sectionId = href.substring(1);
                    console.log('🔗 NAVIGATION FIX: Click interceptado para:', sectionId);
                    
                    forceNavigateToSection(sectionId);
                });
            }
        });
        
        // Configurar navegação por hash
        window.addEventListener('hashchange', function() {
            const hash = window.location.hash.substring(1);
            if (hash) {
                console.log('🔗 NAVIGATION FIX: Hash change detectado:', hash);
                forceNavigateToSection(hash);
            }
        });
        
        // Navegar para seção inicial
        const hash = window.location.hash.substring(1);
        if (hash && document.getElementById(hash)) {
            console.log('🔧 NAVIGATION FIX: Navegando para hash inicial:', hash);
            forceNavigateToSection(hash);
        } else {
            console.log('🔧 NAVIGATION FIX: Navegando para seção padrão: visao-geral');
            forceNavigateToSection('visao-geral');
        }
        
        console.log('✅ NAVIGATION FIX: Correções aplicadas com sucesso!');
        
    }, 500); // Aguardar 500ms para outros scripts carregarem
});

// Disponibilizar função globalmente para debug
window.forceNavigateToSection = forceNavigateToSection;

console.log('🔧 NAVIGATION FIX: Script de correção carregado');
