
from flask import request, jsonify, session, g
from datetime import datetime, timedelta
import json
import logging
from functools import wraps
import ipaddress
import re

logger = logging.getLogger(__name__)

class SecurityMiddleware:
    def __init__(self, app=None):
        self.app = app
        self.blocked_ips = {}
        self.failed_attempts = {}
        self.rate_limits = {}
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializa o middleware com a aplicação Flask"""
        self.app = app
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Configurações padrão
        app.config.setdefault('SECURITY_MAX_FAILED_ATTEMPTS', 5)
        app.config.setdefault('SECURITY_BLOCK_DURATION', 3600)  # 1 hora
        app.config.setdefault('SECURITY_RATE_LIMIT_REQUESTS', 100)
        app.config.setdefault('SECURITY_RATE_LIMIT_WINDOW', 3600)  # 1 hora
        
        logger.info("SecurityMiddleware inicializado")
    
    def get_client_ip(self):
        """Obtém o IP real do cliente, considerando proxies"""
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
        else:
            ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        return ip
    
    def is_valid_ip(self, ip):
        """Valida se o IP é válido"""
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def is_whitelisted_ip(self, ip):
        """Verifica se o IP está na whitelist"""
        whitelist = self.app.config.get('SECURITY_IP_WHITELIST', ['127.0.0.1', 'localhost'])
        return ip in whitelist
    
    def record_failed_attempt(self, ip):
        """Registra uma tentativa de login falhada"""
        current_time = datetime.now()
        
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = {
                'count': 0,
                'first_attempt': current_time,
                'last_attempt': current_time
            }
        
        self.failed_attempts[ip]['count'] += 1
        self.failed_attempts[ip]['last_attempt'] = current_time
        
        # Se excedeu o limite, bloqueia o IP
        max_attempts = self.app.config.get('SECURITY_MAX_FAILED_ATTEMPTS', 5)
        if self.failed_attempts[ip]['count'] >= max_attempts:
            self.block_ip(ip)
            logger.warning(f"IP {ip} bloqueado após {max_attempts} tentativas falhadas")
    
    def block_ip(self, ip, duration=None):
        """Bloqueia um IP por um período determinado"""
        if duration is None:
            duration = self.app.config.get('SECURITY_BLOCK_DURATION', 3600)
        
        expires = datetime.now() + timedelta(seconds=duration)
        self.blocked_ips[ip] = {
            'blocked_at': datetime.now(),
            'expires': expires,
            'reason': 'Múltiplas tentativas falhadas'
        }
        
        logger.warning(f"IP {ip} bloqueado até {expires}")
    
    def is_ip_blocked(self, ip):
        """Verifica se um IP está bloqueado"""
        if ip not in self.blocked_ips:
            return False
        
        block_info = self.blocked_ips[ip]
        
        # Verificar se existe o campo expires e se não é None
        if 'expires' not in block_info or block_info['expires'] is None:
            # Se não há expiração definida, remove o bloqueio
            del self.blocked_ips[ip]
            return False
        
        # Verificar se o bloqueio expirou
        try:
            if datetime.now() >= block_info['expires']:
                # Bloqueio expirou, remover da lista
                del self.blocked_ips[ip]
                logger.info(f"Bloqueio do IP {ip} expirou e foi removido")
                return False
        except (TypeError, AttributeError) as e:
            # Se houver erro na comparação, remover o bloqueio inválido
            logger.error(f"Erro ao verificar expiração do bloqueio para IP {ip}: {e}")
            del self.blocked_ips[ip]
            return False
        
        return True
    
    def unblock_ip(self, ip):
        """Remove o bloqueio de um IP"""
        if ip in self.blocked_ips:
            del self.blocked_ips[ip]
            logger.info(f"IP {ip} desbloqueado manualmente")
    
    def clear_failed_attempts(self, ip):
        """Limpa as tentativas falhadas de um IP"""
        if ip in self.failed_attempts:
            del self.failed_attempts[ip]
    
    def check_rate_limit(self, ip):
        """Verifica o rate limiting para um IP"""
        current_time = datetime.now()
        window = self.app.config.get('SECURITY_RATE_LIMIT_WINDOW', 3600)
        max_requests = self.app.config.get('SECURITY_RATE_LIMIT_REQUESTS', 100)
        
        if ip not in self.rate_limits:
            self.rate_limits[ip] = {
                'requests': [],
                'window_start': current_time
            }
        
        rate_info = self.rate_limits[ip]
        
        # Remove requisições antigas (fora da janela de tempo)
        cutoff_time = current_time - timedelta(seconds=window)
        rate_info['requests'] = [req_time for req_time in rate_info['requests'] if req_time > cutoff_time]
        
        # Adiciona a requisição atual
        rate_info['requests'].append(current_time)
        
        # Verifica se excedeu o limite
        if len(rate_info['requests']) > max_requests:
            logger.warning(f"Rate limit excedido para IP {ip}: {len(rate_info['requests'])} requisições")
            return False
        
        return True
    
    def validate_input(self, data):
        """Valida entrada para prevenir ataques"""
        if isinstance(data, str):
            # Padrões suspeitos
            suspicious_patterns = [
                r'<script[^>]*>.*?</script>',  # XSS
                r'union\s+select',  # SQL Injection
                r'drop\s+table',  # SQL Injection
                r'exec\s*\(',  # Command Injection
                r'javascript:',  # XSS
                r'on\w+\s*=',  # Event handlers
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, data, re.IGNORECASE):
                    logger.warning(f"Entrada suspeita detectada: {pattern}")
                    return False
        
        return True
    
    def sanitize_input(self, data):
        """Sanitiza entrada de dados"""
        if isinstance(data, str):
            # Remove tags HTML perigosas
            data = re.sub(r'<script[^>]*>.*?</script>', '', data, flags=re.IGNORECASE)
            data = re.sub(r'javascript:', '', data, flags=re.IGNORECASE)
            data = re.sub(r'on\w+\s*=', '', data, flags=re.IGNORECASE)
        
        return data
    
    def before_request(self):
        """Middleware executado antes de cada requisição"""
        client_ip = self.get_client_ip()
        
        # Valida se o IP é válido
        if not self.is_valid_ip(client_ip):
            logger.error(f"IP inválido detectado: {client_ip}")
            return jsonify({'error': 'IP inválido'}), 400
        
        # Pula verificações para IPs na whitelist
        if self.is_whitelisted_ip(client_ip):
            return
        
        # Verifica se o IP está bloqueado
        if self.is_ip_blocked(client_ip):
            block_info = self.blocked_ips.get(client_ip, {})
            expires = block_info.get('expires')
            expires_str = expires.strftime('%Y-%m-%d %H:%M:%S') if expires else 'indefinido'
            
            logger.warning(f"Tentativa de acesso bloqueada do IP {client_ip}")
            return jsonify({
                'error': 'IP bloqueado',
                'message': f'Seu IP foi bloqueado até {expires_str}',
                'expires': expires_str
            }), 403
        
        # Verifica rate limiting
        if not self.check_rate_limit(client_ip):
            logger.warning(f"Rate limit excedido para IP {client_ip}")
            return jsonify({
                'error': 'Rate limit excedido',
                'message': 'Muitas requisições. Tente novamente mais tarde.'
            }), 429
        
        # Valida dados de entrada
        if request.is_json:
            try:
                data = request.get_json()
                if data and not self.validate_input(json.dumps(data)):
                    return jsonify({'error': 'Dados inválidos'}), 400
            except Exception as e:
                logger.error(f"Erro ao validar JSON: {e}")
                return jsonify({'error': 'JSON inválido'}), 400
        
        # Valida parâmetros da URL
        for key, value in request.args.items():
            if not self.validate_input(value):
                return jsonify({'error': 'Parâmetros inválidos'}), 400
        
        # Valida dados do formulário
        for key, value in request.form.items():
            if not self.validate_input(value):
                return jsonify({'error': 'Dados do formulário inválidos'}), 400
        
        # Armazena informações no contexto da requisição
        g.client_ip = client_ip
        g.security_validated = True
    
    def after_request(self, response):
        """Middleware executado após cada requisição"""
        # Adiciona headers de segurança
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://cdn.socket.io; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; img-src 'self' data: https://images.totalpass.com; connect-src 'self' wss: ws:;"
        
        return response
    
    def get_security_status(self):
        """Retorna status atual da segurança"""
        return {
            'blocked_ips_count': len(self.blocked_ips),
            'failed_attempts_count': len(self.failed_attempts),
            'rate_limited_ips': len(self.rate_limits),
            'blocked_ips': list(self.blocked_ips.keys()),
            'security_active': True
        }
    
    def cleanup_expired_blocks(self):
        """Remove bloqueios expirados (deve ser chamado periodicamente)"""
        current_time = datetime.now()
        expired_ips = []
        
        for ip, block_info in self.blocked_ips.items():
            if 'expires' in block_info and block_info['expires'] and current_time >= block_info['expires']:
                expired_ips.append(ip)
        
        for ip in expired_ips:
            del self.blocked_ips[ip]
            logger.info(f"Bloqueio expirado removido para IP {ip}")
        
        return len(expired_ips)

# Decorador para endpoints que requerem validação extra
def require_security_validation(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'security_validated') or not g.security_validated:
            return jsonify({'error': 'Validação de segurança necessária'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Decorador para rate limiting específico
def rate_limit(max_requests=10, window=60):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            
            # Implementar rate limiting específico aqui se necessário
            # Por agora, usa o rate limiting global
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator