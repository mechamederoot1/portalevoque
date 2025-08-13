# 🏗️ Setup Tabelas SLA - MySQL Azure

Este conjunto de scripts configura as tabelas de SLA (Service Level Agreement) no banco MySQL Azure da Evoque Fitness.

## 📋 Arquivos Incluídos

- `setup_sla_azure.py` - Script principal de setup
- `validate_sla_setup.py` - Script de validação
- `requirements_sla_setup.txt` - Dependências Python
- `run_sla_setup.sh` - Script bash facilitador
- `README_SLA_SETUP.md` - Este arquivo

## 🎯 O que o Setup Faz

### Tabelas Criadas:
1. **`configuracoes_sla`** - Configurações de SLA por prioridade
2. **`horario_comercial`** - Configurações de horário comercial
3. **`historico_sla`** - Histórico de cálculos SLA

### Dados Padrão Inseridos:
- **SLAs por Prioridade:**
  - Crítica: 2h resolução, 1h primeira resposta
  - Urgente: 2h resolução, 1h primeira resposta
  - Alta: 8h resolução, 2h primeira resposta
  - Normal: 24h resolução, 4h primeira resposta
  - Baixa: 72h resolução, 8h primeira resposta

- **Horário Comercial:**
  - 08:00 às 18:00
  - Segunda a sexta-feira
  - Sem intervalo de almoço
  - Timezone: America/Sao_Paulo

## 🚀 Como Executar

### Opção 1: Script Interativo (Recomendado)
```bash
chmod +x run_sla_setup.sh
./run_sla_setup.sh
```

### Opção 2: Execução Direta

#### 1. Instalar dependências:
```bash
pip3 install -r requirements_sla_setup.txt
```

#### 2. Testar conexão:
```bash
python3 setup_sla_azure.py test
```

#### 3. Executar setup completo:
```bash
python3 setup_sla_azure.py
```

#### 4. Validar configurações:
```bash
python3 validate_sla_setup.py
```

## 🔧 Configurações do Banco

O script usa as seguintes configurações (já incluídas):

```python
DB_CONFIG = {
    'host': 'evoque-database.mysql.database.azure.com',
    'user': 'infra',
    'password': 'Evoque12@',
    'database': 'infra',
    'port': 3306
}
```

## ✅ Verificações de Segurança

- ✅ Usa prepared statements (PyMySQL)
- ✅ Verifica se tabelas já existem antes de criar
- ✅ Não duplica dados se já existirem
- ✅ Usa transações para operações seguras
- ✅ Valida estrutura antes de inserir dados

## 📊 Estrutura das Tabelas

### configuracoes_sla
```sql
CREATE TABLE configuracoes_sla (
    id INT AUTO_INCREMENT PRIMARY KEY,
    prioridade VARCHAR(50) NOT NULL,
    tempo_primeira_resposta DECIMAL(5,2) DEFAULT 4.0,
    tempo_resolucao DECIMAL(5,2) NOT NULL,
    considera_horario_comercial BOOLEAN DEFAULT TRUE,
    considera_feriados BOOLEAN DEFAULT TRUE,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    usuario_atualizacao INT NULL,
    UNIQUE KEY unique_prioridade (prioridade)
);
```

### horario_comercial
```sql
CREATE TABLE horario_comercial (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL DEFAULT 'Padrão',
    descricao VARCHAR(255) NULL,
    hora_inicio TIME NOT NULL DEFAULT '08:00:00',
    hora_fim TIME NOT NULL DEFAULT '18:00:00',
    segunda BOOLEAN DEFAULT TRUE,
    terca BOOLEAN DEFAULT TRUE,
    quarta BOOLEAN DEFAULT TRUE,
    quinta BOOLEAN DEFAULT TRUE,
    sexta BOOLEAN DEFAULT TRUE,
    sabado BOOLEAN DEFAULT FALSE,
    domingo BOOLEAN DEFAULT FALSE,
    considera_almoco BOOLEAN DEFAULT FALSE,
    ativo BOOLEAN DEFAULT TRUE,
    padrao BOOLEAN DEFAULT FALSE,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_padrao (padrao)
);
```

## 🔍 Validações Executadas

O script de validação verifica:
- ✅ Estrutura das tabelas
- ✅ Dados padrão inseridos corretamente
- ✅ Queries funcionais
- ✅ Integridade referencial
- ✅ Configurações de timezone

## 🐛 Solução de Problemas

### Erro de Conexão
```
❌ Erro ao conectar: (2003, "Can't connect to MySQL server")
```
**Solução:** Verificar se as credenciais estão corretas e se o firewall permite conexão.

### Erro de Permissão
```
❌ Erro: (1142, "CREATE command denied to user")
```
**Solução:** Usuário precisa de permissões CREATE e INSERT no banco.

### Dependências Faltando
```
❌ ModuleNotFoundError: No module named 'pymysql'
```
**Solução:** 
```bash
pip3 install -r requirements_sla_setup.txt
```

## 📈 Após o Setup

1. **Execute a aplicação Flask:**
   ```bash
   python app.py
   ```

2. **Acesse o painel administrativo:**
   - URL: `/ti/painel`
   - Vá em "SLA & Métricas"

3. **Verifique as configurações:**
   - Cards de SLA devem mostrar dados
   - Tabela de chamados deve considerar horário comercial

4. **Teste as funcionalidades:**
   - Crie chamados de teste
   - Verifique cálculo de SLA
   - Teste botão "Corrigir Dados"

## 🔄 Atualizações Futuras

Para atualizar configurações:

1. **Via Interface Web:**
   - Painel > SLA & Métricas > Configurações

2. **Via Banco Direto:**
   ```sql
   UPDATE configuracoes_sla 
   SET tempo_resolucao = 4.0 
   WHERE prioridade = 'Crítica';
   ```

3. **Via Script Python:**
   ```python
   from database import atualizar_sla_prioridade
   atualizar_sla_prioridade('Crítica', 4.0, 1.0, usuario_id=1)
   ```

## 🎉 Sucesso!

Se tudo correr bem, você verá:
```
🎉 SETUP CONCLUÍDO COM SUCESSO!
✅ Tabelas SLA criadas e configuradas
✅ Dados padrão inseridos
✅ Sistema pronto para uso
```

O sistema agora está pronto para calcular SLA considerando:
- ✅ Horário comercial (08:00-18:00)
- ✅ Dias úteis (Segunda a Sexta)
- ✅ Pausas automáticas nos fins de semana
- ✅ Configurações específicas por prioridade
- ✅ Auditoria completa de alterações

## 📞 Suporte

Em caso de problemas:
1. Execute `python3 validate_sla_setup.py` para diagnóstico
2. Verifique logs da aplicação Flask
3. Consulte as configurações no painel administrativo
