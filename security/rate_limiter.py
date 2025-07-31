"""
Sistema de Rate Limiting para prevenir ataques de força bruta e DDoS
"""
from datetime import datetime, timedelta
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self):
        # Armazena tentativas por IP
        self.attempts = defaultdict(list)
        
        # Configurações de rate limiting por endpoint
        self.limits = {
            'auth.login': {'requests': 15, 'window': 300},  # 15 tentativas em 5 minutos
            'auth.first_login': {'requests': 10, 'window': 300},
            'ti.abrir_chamado': {'requests': 50, 'window': 60},  # 50 chamados por minuto
            'default': {'requests': 1000, 'window': 60},  # 1000 requests por minuto (padrão)
            'api_endpoints': {'requests': 800, 'window': 60},  # APIs bem liberais
        }
    
    def is_allowed(self, ip, endpoint):
        """Verifica se uma requisição é permitida baseada no rate limiting"""
        current_time = time.time()
        
        # Determina o limite para o endpoint
        limit_config = self.get_limit_config(endpoint)
        max_requests = limit_config['requests']
        window_seconds = limit_config['window']
        
        # Cria chave única para IP + endpoint
        key = f"{ip}:{endpoint or 'unknown'}"
        
        # Remove tentativas antigas
        self.cleanup_old_attempts(key, current_time, window_seconds)
        
        # Verifica se excedeu o limite
        if len(self.attempts[key]) >= max_requests:
            return False
        
        # Adiciona a tentativa atual
        self.attempts[key].append(current_time)
        return True
    
    def get_limit_config(self, endpoint):
        """Obtém configuração de limite para um endpoint específico"""
        if not endpoint:
            return self.limits['default']
        
        # Verifica se é um endpoint de API
        if endpoint.startswith('api') or '/api/' in str(endpoint):
            return self.limits['api_endpoints']
        
        # Verifica endpoints específicos
        if endpoint in self.limits:
            return self.limits[endpoint]
        
        return self.limits['default']
    
    def cleanup_old_attempts(self, key, current_time, window_seconds):
        """Remove tentativas antigas fora da janela de tempo"""
        cutoff_time = current_time - window_seconds
        self.attempts[key] = [
            attempt_time for attempt_time in self.attempts[key]
            if attempt_time > cutoff_time
        ]
    
    def get_remaining_attempts(self, ip, endpoint):
        """Retorna o número de tentativas restantes"""
        current_time = time.time()
        limit_config = self.get_limit_config(endpoint)
        max_requests = limit_config['requests']
        window_seconds = limit_config['window']
        
        key = f"{ip}:{endpoint or 'unknown'}"
        self.cleanup_old_attempts(key, current_time, window_seconds)
        
        return max(0, max_requests - len(self.attempts[key]))
    
    def get_reset_time(self, ip, endpoint):
        """Retorna quando o rate limit será resetado"""
        current_time = time.time()
        limit_config = self.get_limit_config(endpoint)
        window_seconds = limit_config['window']
        
        key = f"{ip}:{endpoint or 'unknown'}"
        
        if not self.attempts[key]:
            return current_time
        
        oldest_attempt = min(self.attempts[key])
        return oldest_attempt + window_seconds
    
    def block_ip_temporarily(self, ip, duration_minutes=15):
        """Bloqueia um IP temporariamente"""
        current_time = time.time()
        block_until = current_time + (duration_minutes * 60)
        
        # Adiciona muitas tentativas falsas para bloquear
        key = f"{ip}:blocked"
        self.attempts[key] = [block_until] * 1000  # Número alto para garantir bloqueio
    
    def is_ip_blocked(self, ip):
        """Verifica se um IP está bloqueado"""
        current_time = time.time()
        key = f"{ip}:blocked"
        
        if key in self.attempts:
            # Se ainda há tentativas "falsas" no futuro, está bloqueado
            future_attempts = [t for t in self.attempts[key] if t > current_time]
            if future_attempts:
                return True
            else:
                # Remove o bloqueio expirado
                del self.attempts[key]
        
        return False
