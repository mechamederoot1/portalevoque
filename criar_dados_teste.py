#!/usr/bin/env python3
"""
Script para criar dados de teste de chamados no banco
"""
from app import app
from database import db, Chamado, User, get_brazil_time
import random

def criar_dados_teste():
    with app.app_context():
        print("=== CRIANDO DADOS DE TESTE ===")
        
        # Verificar se já existem chamados
        total_chamados = Chamado.query.count()
        print(f"Total atual de chamados: {total_chamados}")
        
        if total_chamados > 0:
            print("⚠️  J�� existem chamados no banco. Deseja continuar? (y/N)")
            resposta = input().lower()
            if resposta != 'y':
                print("Operação cancelada.")
                return
        
        # Dados de exemplo
        unidades = [
            "Academia Evoque Alphaville",
            "Academia Evoque Moema", 
            "Academia Evoque Vila Olímpia",
            "Academia Evoque Pinheiros",
            "Academia Evoque Brooklin"
        ]
        
        problemas = [
            "Computador não liga",
            "Internet lenta",
            "Impressora não funciona", 
            "Sistema travando",
            "Erro no sistema de vendas",
            "Problema no ar condicionado",
            "Equipamento de som com defeito",
            "TV não funciona",
            "Sistema de som ambiente parado",
            "Problema na rede wifi"
        ]
        
        status_opcoes = ["Aberto", "Aguardando", "Concluido", "Cancelado"]
        prioridades = ["Baixa", "Normal", "Alta", "Crítica"]
        
        # Criar chamados de teste
        for i in range(1, 16):  # Criar 15 chamados
            codigo = f"TI{i:04d}"
            protocolo = f"P{i:06d}"
            
            chamado = Chamado(
                codigo=codigo,
                protocolo=protocolo,
                solicitante=f"Usuário Teste {i}",
                cargo="Funcionário" if i % 3 != 0 else "Gerente",
                email=f"usuario{i}@academiaevoque.com.br",
                telefone=f"(11) 9999-{i:04d}",
                unidade=random.choice(unidades),
                problema=random.choice(problemas),
                descricao=f"Descrição detalhada do problema {i}. Lorem ipsum dolor sit amet.",
                status=random.choice(status_opcoes),
                prioridade=random.choice(prioridades),
                data_abertura=get_brazil_time().replace(tzinfo=None)
            )
            
            # Se for concluído, adicionar data de conclusão
            if chamado.status == "Concluido":
                chamado.data_conclusao = get_brazil_time().replace(tzinfo=None)
            
            db.session.add(chamado)
            print(f"✅ Criado chamado {codigo} - Status: {chamado.status}")
        
        try:
            db.session.commit()
            print(f"\n🎉 {15} chamados de teste criados com sucesso!")
            
            # Verificar contagem final
            total_final = Chamado.query.count()
            print(f"Total de chamados no banco: {total_final}")
            
            # Mostrar contagem por status
            print("\n=== CONTAGEM POR STATUS ===")
            for status in status_opcoes:
                count = Chamado.query.filter_by(status=status).count()
                print(f"{status}: {count}")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar dados: {e}")

if __name__ == "__main__":
    criar_dados_teste()
