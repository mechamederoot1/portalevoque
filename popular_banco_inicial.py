#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados iniciais
"""
from app import app
from database import db, seed_unidades, Unidade, ProblemaReportado, ItemInternet

def popular_banco():
    with app.app_context():
        try:
            print("🔄 Populando banco de dados com dados iniciais...")
            
            # Verificar se já existem dados
            unidades_count = Unidade.query.count()
            problemas_count = ProblemaReportado.query.count()
            itens_count = ItemInternet.query.count()
            
            print(f"📊 Estado atual:")
            print(f"   - Unidades: {unidades_count}")
            print(f"   - Problemas: {problemas_count}")
            print(f"   - Itens Internet: {itens_count}")
            
            # Executar seed_unidades que já popula tudo
            seed_unidades()
            
            # Verificar após inserção
            unidades_count = Unidade.query.count()
            problemas_count = ProblemaReportado.query.count()
            itens_count = ItemInternet.query.count()
            
            print(f"📊 Estado após inserção:")
            print(f"   - Unidades: {unidades_count}")
            print(f"   - Problemas: {problemas_count}")
            print(f"   - Itens Internet: {itens_count}")
            
            print("✅ Banco de dados populado com sucesso!")
            
            # Listar algumas unidades como exemplo
            print("\n🏢 Primeiras 5 unidades:")
            primeiras_unidades = Unidade.query.limit(5).all()
            for unidade in primeiras_unidades:
                print(f"   - {unidade.nome}")
            
            print("\n🔧 Problemas disponíveis:")
            problemas = ProblemaReportado.query.all()
            for problema in problemas:
                print(f"   - {problema.nome} (Prioridade: {problema.prioridade_padrao})")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    popular_banco()
