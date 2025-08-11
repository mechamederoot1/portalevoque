"""
Script simplificado para verificar e criar estrutura do banco de dados
Execute este arquivo diretamente ou importe as funções
"""

def verificar_e_criar_estrutura():
    """Verifica e cria a estrutura do banco de dados"""
    
    try:
        from flask import Flask
        from database import db, init_app, seed_unidades
        from config import get_config
        import os
        
        # Criar app Flask temporário para contexto
        app = Flask(__name__)
        app.config.from_object(get_config())
        
        # Inicializar banco
        db.init_app(app)
        
        with app.app_context():
            print("🔧 Verificando e criando estrutura do banco de dados...")
            
            # Criar todas as tabelas
            print("📋 Criando todas as tabelas...")
            db.create_all()
            print("✅ Estrutura de tabelas criada/verificada")
            
            # Executar função de inicialização
            print("🌱 Inicializando dados...")
            init_app(app)
            print("✅ Dados inicializados")
            
            # Verificar tabelas criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print(f"\n📊 ESTRUTURA DO BANCO CRIADA:")
            print(f"Total de tabelas: {len(tabelas)}")
            
            for tabela in sorted(tabelas):
                colunas = inspector.get_columns(tabela)
                print(f"  • {tabela} ({len(colunas)} colunas)")
            
            print("\n✅ Estrutura do banco de dados criada com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

def verificar_dados_essenciais():
    """Verifica se os dados essenciais estão no banco"""
    
    try:
        from flask import Flask
        from database import db, User, Unidade, ProblemaReportado, ItemInternet, Configuracao
        from config import get_config
        
        app = Flask(__name__)
        app.config.from_object(get_config())
        db.init_app(app)
        
        with app.app_context():
            print("\n🔍 Verificando dados essenciais...")
            
            # Verificar usuários
            total_users = User.query.count()
            admin_exists = User.query.filter_by(usuario='admin').first() is not None
            
            # Verificar unidades
            total_unidades = Unidade.query.count()
            
            # Verificar problemas
            total_problemas = ProblemaReportado.query.count()
            
            # Verificar itens internet
            total_itens = ItemInternet.query.count()
            
            # Verificar configurações
            total_configs = Configuracao.query.count()
            
            print(f"👥 Usuários: {total_users} (Admin existe: {'✅' if admin_exists else '❌'})")
            print(f"🏢 Unidades: {total_unidades}")
            print(f"🔧 Problemas reportados: {total_problemas}")
            print(f"🌐 Itens de internet: {total_itens}")
            print(f"⚙️  Configurações: {total_configs}")
            
            if admin_exists and total_unidades > 0 and total_problemas > 0:
                print("✅ Dados essenciais estão presentes!")
                return True
            else:
                print("⚠️  Alguns dados essenciais estão faltando!")
                return False
                
    except Exception as e:
        print(f"❌ Erro ao verificar dados: {str(e)}")
        return False

def criar_usuario_admin():
    """Cria usuário admin se não existir"""
    
    try:
        from flask import Flask
        from database import db, User, get_brazil_time
        from config import get_config
        
        app = Flask(__name__)
        app.config.from_object(get_config())
        db.init_app(app)
        
        with app.app_context():
            admin_user = User.query.filter_by(usuario='admin').first()
            
            if not admin_user:
                print("🔄 Criando usuário admin...")
                admin_user = User(
                    nome='Administrador',
                    sobrenome='Sistema',
                    usuario='admin',
                    email='admin@evoquefitness.com',
                    nivel_acesso='Administrador',
                    setor='TI',
                    bloqueado=False,
                    data_criacao=get_brazil_time().replace(tzinfo=None)
                )
                admin_user.set_password('admin123')
                admin_user.setores = ['TI']
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuário admin criado: admin/admin123")
                return True
            else:
                print("✅ Usuário admin já existe")
                return True
                
    except Exception as e:
        print(f"❌ Erro ao criar admin: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Executando verificação da estrutura do banco...")
    
    # Executar verificações
    if verificar_e_criar_estrutura():
        verificar_dados_essenciais()
        criar_usuario_admin()
        print("\n🎉 Processo concluído!")
    else:
        print("\n❌ Processo falhou!")
