#!/usr/bin/env python3
"""
Script de Verificação de Correções - Quintou Backend
Verifica se todas as correções da auditoria foram implementadas corretamente.

Uso: python verify_fixes.py
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple

# Cores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text: str):
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def print_info(text: str):
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")

def check_file_exists(filepath: str) -> bool:
    """Verifica se arquivo existe"""
    return Path(filepath).exists()

def check_file_contains(filepath: str, pattern: str, use_regex: bool = False) -> bool:
    """Verifica se arquivo contém determinado padrão"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if use_regex:
                return bool(re.search(pattern, content, re.MULTILINE | re.DOTALL))
            else:
                return pattern in content
    except FileNotFoundError:
        return False
    except Exception as e:
        print_warning(f"Erro ao ler {filepath}: {str(e)}")
        return False

def check_no_mock_data(filepath: str) -> bool:
    """Verifica se arquivo NÃO contém dados mock"""
    mock_patterns = [
        r'pi_mocked',
        r'"pi_mocked"',
        r'client_secret\s*=\s*["\']pi_mocked',
        r'# Mock de resposta',
    ]
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            for pattern in mock_patterns:
                if re.search(pattern, content):
                    return False
        return True
    except:
        return False

def verify_payment_integration() -> bool:
    """Verifica integração real do Stripe PaymentIntent"""
    print_header("1. INTEGRAÇÃO STRIPE PAYMENTINTENT")
    
    filepath = "app/services/payment_service.py"
    checks = []
    
    # Verifica se arquivo existe
    if not check_file_exists(filepath):
        print_error(f"Arquivo {filepath} não encontrado")
        return False
    
    print_info(f"Verificando {filepath}...")
    
    # Verifica se contém integração real
    checks.append((
        "Chamada stripe.PaymentIntent.create()",
        check_file_contains(filepath, "stripe.PaymentIntent.create(")
    ))
    
    checks.append((
        "Parâmetro transfer_data (Destination Charge)",
        check_file_contains(filepath, "transfer_data")
    ))
    
    checks.append((
        "Parâmetro application_fee_amount",
        check_file_contains(filepath, "application_fee_amount")
    ))
    
    checks.append((
        "Metadata com booking_id",
        check_file_contains(filepath, '"booking_id": str(booking.id)')
    ))
    
    checks.append((
        "Verificação de stripe_account_id do host",
        check_file_contains(filepath, "host.stripe_account_id")
    ))
    
    checks.append((
        "Sem dados mock (pi_mocked)",
        check_no_mock_data(filepath)
    ))
    
    checks.append((
        "Tratamento de erros Stripe",
        check_file_contains(filepath, "stripe.error.StripeError")
    ))
    
    # Mostra resultados
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    return all_passed

def verify_password_reset() -> bool:
    """Verifica sistema de reset de senha"""
    print_header("2. SISTEMA DE RESET DE SENHA")
    
    checks = []
    
    # Verifica modelo
    print_info("Verificando modelo PasswordResetToken...")
    model_file = "app/models/password_reset.py"
    checks.append((
        "Modelo PasswordResetToken criado",
        check_file_exists(model_file)
    ))
    
    if check_file_exists(model_file):
        checks.append((
            "Campo token (String unique)",
            check_file_contains(model_file, "token = Column(String, unique=True")
        ))
        checks.append((
            "Campo expires_at",
            check_file_contains(model_file, "expires_at")
        ))
        checks.append((
            "Campo used_at",
            check_file_contains(model_file, "used_at")
        ))
        checks.append((
            "Método is_expired",
            check_file_contains(model_file, "def is_expired")
        ))
        checks.append((
            "Método is_used",
            check_file_contains(model_file, "def is_used")
        ))
    
    # Verifica serviço de email
    print_info("Verificando EmailService...")
    email_file = "app/services/email_service.py"
    checks.append((
        "EmailService criado",
        check_file_exists(email_file)
    ))
    
    if check_file_exists(email_file):
        checks.append((
            "Suporte a SendGrid",
            check_file_contains(email_file, "sendgrid")
        ))
        checks.append((
            "Suporte a SMTP",
            check_file_contains(email_file, "_send_via_smtp")
        ))
        checks.append((
            "Modo console (desenvolvimento)",
            check_file_contains(email_file, "_send_via_console")
        ))
        checks.append((
            "Método send_password_reset",
            check_file_contains(email_file, "async def send_password_reset")
        ))
    
    # Verifica auth_service
    print_info("Verificando auth_service.py...")
    auth_file = "app/services/auth_service.py"
    checks.append((
        "forgot_password implementado (sem TODO)",
        not check_file_contains(auth_file, "# TODO: Generate reset token")
    ))
    checks.append((
        "reset_password implementado (sem stub)",
        not check_file_contains(auth_file, 'raise HTTPException(status_code=501, detail="Not implemented")')
    ))
    checks.append((
        "Criação de token de reset",
        check_file_contains(auth_file, "PasswordResetToken")
    ))
    checks.append((
        "Envio de email",
        check_file_contains(auth_file, "email_service.send_password_reset")
    ))
    checks.append((
        "Validação de token expirado",
        check_file_contains(auth_file, "is_expired")
    ))
    checks.append((
        "Validação de token usado",
        check_file_contains(auth_file, "is_used")
    ))
    
    # Verifica config
    print_info("Verificando configurações...")
    config_file = "app/config.py"
    checks.append((
        "EMAIL_FROM configurado",
        check_file_contains(config_file, "EMAIL_FROM")
    ))
    checks.append((
        "SENDGRID_API_KEY configurado",
        check_file_contains(config_file, "SENDGRID_API_KEY")
    ))
    checks.append((
        "SMTP_HOST configurado",
        check_file_contains(config_file, "SMTP_HOST")
    ))
    checks.append((
        "FRONTEND_URL configurado",
        check_file_contains(config_file, "FRONTEND_URL")
    ))
    
    # Mostra resultados
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    return all_passed

def verify_cpf_phone_validation() -> bool:
    """Verifica validação de CPF e telefone únicos"""
    print_header("3. VALIDAÇÃO CPF E TELEFONE ÚNICOS")
    
    filepath = "app/services/auth_service.py"
    checks = []
    
    print_info(f"Verificando {filepath}...")
    
    checks.append((
        "Sem TODO de validação",
        not check_file_contains(filepath, "# TODO: Adicionar verificação de CPF")
    ))
    
    checks.append((
        "Verifica CPF único",
        check_file_contains(filepath, "select(User).where(User.cpf == user_in.cpf)")
    ))
    
    checks.append((
        "Verifica telefone único",
        check_file_contains(filepath, "select(User).where(User.phone == user_in.phone)")
    ))
    
    checks.append((
        "Erro para CPF duplicado",
        check_file_contains(filepath, "CPF já cadastrado")
    ))
    
    checks.append((
        "Erro para telefone duplicado",
        check_file_contains(filepath, "Telefone já cadastrado")
    ))
    
    # Mostra resultados
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    return all_passed

def verify_rating_calculation() -> bool:
    """Verifica cálculo automático de rating"""
    print_header("4. CÁLCULO AUTOMÁTICO DE RATING")
    
    filepath = "app/services/review_service.py"
    checks = []
    
    print_info(f"Verificando {filepath}...")
    
    checks.append((
        "Sem TODO de rating",
        not check_file_contains(filepath, "# TODO: Atualizar average_rating")
    ))
    
    checks.append((
        "Uso de func.avg() do SQLAlchemy",
        check_file_contains(filepath, "func.avg(Review.rating)")
    ))
    
    checks.append((
        "Uso de func.count() do SQLAlchemy",
        check_file_contains(filepath, "func.count(Review.id)")
    ))
    
    checks.append((
        "Atualiza host.average_rating",
        check_file_contains(filepath, "host.average_rating")
    ))
    
    checks.append((
        "Atualiza guest.average_rating",
        check_file_contains(filepath, "guest.average_rating")
    ))
    
    checks.append((
        "Atualiza space.average_rating",
        check_file_contains(filepath, "space.average_rating")
    ))
    
    checks.append((
        "Atualiza total_reviews",
        check_file_contains(filepath, "total_reviews")
    ))
    
    # Mostra resultados
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    return all_passed

def verify_stripe_webhook() -> bool:
    """Verifica implementação do webhook Stripe"""
    print_header("5. WEBHOOK STRIPE")
    
    filepath = "app/routers/payments.py"
    checks = []
    
    print_info(f"Verificando {filepath}...")
    
    checks.append((
        "Sem comentário 'pass' no webhook",
        not check_file_contains(filepath, "# booking.status = 'CONFIRMED'\n    # db.commit()\n    pass")
    ))
    
    checks.append((
        "Processa checkout.session.completed",
        check_file_contains(filepath, "checkout.session.completed")
    ))
    
    checks.append((
        "Processa payment_intent.succeeded",
        check_file_contains(filepath, "payment_intent.succeeded")
    ))
    
    checks.append((
        "Atualiza booking.status para CONFIRMED",
        check_file_contains(filepath, "booking.status = BookingStatus.CONFIRMED")
    ))
    
    checks.append((
        "Atualiza payment.status para COMPLETED",
        check_file_contains(filepath, "payment.status = PaymentStatus.COMPLETED")
    ))
    
    checks.append((
        "Cria notificação para guest",
        check_file_contains(filepath, 'type="BOOKING_CONFIRMED"')
    ))
    
    checks.append((
        "Cria notificação para host",
        check_file_contains(filepath, 'type="PAYMENT_RECEIVED"')
    ))
    
    checks.append((
        "Tratamento de exceções",
        check_file_contains(filepath, "except Exception as e:")
    ))
    
    # Mostra resultados
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    return all_passed

def verify_fee_consistency() -> bool:
    """Verifica consistência das taxas da plataforma"""
    print_header("6. CONSISTÊNCIA DAS TAXAS")
    
    checks = []
    
    # Verifica arquivo de constantes
    print_info("Verificando app/constants.py...")
    constants_file = "app/constants.py"
    checks.append((
        "Arquivo constants.py criado",
        check_file_exists(constants_file)
    ))
    
    if check_file_exists(constants_file):
        checks.append((
            "PLATFORM_GUEST_FEE_PERCENTAGE definido",
            check_file_contains(constants_file, "PLATFORM_GUEST_FEE_PERCENTAGE")
        ))
        checks.append((
            "PLATFORM_HOST_FEE_PERCENTAGE definido",
            check_file_contains(constants_file, "PLATFORM_HOST_FEE_PERCENTAGE")
        ))
        checks.append((
            "Taxa guest é 10% (0.10)",
            check_file_contains(constants_file, "Decimal('0.10')")
        ))
        checks.append((
            "Taxa host é 15% (0.15)",
            check_file_contains(constants_file, "Decimal('0.15')")
        ))
    
    # Verifica uso em booking_service
    print_info("Verificando booking_service.py...")
    booking_file = "app/services/booking_service.py"
    checks.append((
        "Importa constantes",
        check_file_contains(booking_file, "from app.constants import")
    ))
    checks.append((
        "Usa PLATFORM_GUEST_FEE_PERCENTAGE",
        check_file_contains(booking_file, "PLATFORM_GUEST_FEE_PERCENTAGE")
    ))
    checks.append((
        "Usa PLATFORM_HOST_FEE_PERCENTAGE",
        check_file_contains(booking_file, "PLATFORM_HOST_FEE_PERCENTAGE")
    ))
    checks.append((
        "Sem valores hardcoded (0.15/0.10)",
        not check_file_contains(booking_file, "Decimal('0.15') # 15% taxa do guest")
    ))
    
    # Verifica uso em stripe_service
    print_info("Verificando stripe_service.py...")
    stripe_file = "app/services/stripe_service.py"
    checks.append((
        "Importa constantes",
        check_file_contains(stripe_file, "from app.constants import")
    ))
    checks.append((
        "Sem constantes antigas (HOST_FEE_PERCENTAGE)",
        not check_file_contains(stripe_file, "HOST_FEE_PERCENTAGE = 0.15")
    ))
    
    # Mostra resultados
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    return all_passed

def verify_documentation() -> bool:
    """Verifica documentação criada"""
    print_header("7. DOCUMENTAÇÃO")
    
    checks = []
    
    docs = [
        ("AUDITORIA_BUGS_E_FIXES.md", "Relatório de auditoria"),
        ("CORREÇÕES_IMPLEMENTADAS.md", "Resumo das correções"),
        ("GUIA_DEPLOY.md", "Guia de deployment"),
        (".env.example", "Exemplo de configurações"),
    ]
    
    for filename, description in docs:
        checks.append((
            f"{description} ({filename})",
            check_file_exists(filename)
        ))
    
    # Verifica conteúdo do .env.example
    if check_file_exists(".env.example"):
        checks.append((
            ".env.example contém SENDGRID_API_KEY",
            check_file_contains(".env.example", "SENDGRID_API_KEY")
        ))
        checks.append((
            ".env.example contém EMAIL_FROM",
            check_file_contains(".env.example", "EMAIL_FROM")
        ))
        checks.append((
            ".env.example contém FRONTEND_URL",
            check_file_contains(".env.example", "FRONTEND_URL")
        ))
    
    # Mostra resultados
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    return all_passed

def verify_migration() -> bool:
    """Verifica migração do Alembic"""
    print_header("8. MIGRAÇÃO ALEMBIC")
    
    checks = []
    
    migration_file = "alembic/versions/add_password_reset_tokens.py"
    
    checks.append((
        "Arquivo de migração criado",
        check_file_exists(migration_file)
    ))
    
    if check_file_exists(migration_file):
        checks.append((
            "Cria tabela password_reset_tokens",
            check_file_contains(migration_file, "create_table('password_reset_tokens'")
        ))
        checks.append((
            "Adiciona índice no token",
            check_file_contains(migration_file, "ix_password_reset_tokens_token")
        ))
        checks.append((
            "Define função upgrade()",
            check_file_contains(migration_file, "def upgrade()")
        ))
        checks.append((
            "Define função downgrade()",
            check_file_contains(migration_file, "def downgrade()")
        ))
    
    # Mostra resultados
    all_passed = True
    for check_name, passed in checks:
        if passed:
            print_success(check_name)
        else:
            print_error(check_name)
            all_passed = False
    
    return all_passed

def main():
    """Função principal"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║     VERIFICAÇÃO DE CORREÇÕES - QUINTOU BACKEND                     ║")
    print("║     Versão 2.0 - Pós-Auditoria                                     ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}")
    
    # Verifica se está no diretório correto
    if not os.path.exists("app"):
        print_error("Erro: Execute este script na raiz do projeto backend")
        sys.exit(1)
    
    # Lista de verificações
    verifications = [
        ("Integração Stripe PaymentIntent", verify_payment_integration),
        ("Sistema de Reset de Senha", verify_password_reset),
        ("Validação CPF e Telefone", verify_cpf_phone_validation),
        ("Cálculo Automático de Rating", verify_rating_calculation),
        ("Webhook Stripe", verify_stripe_webhook),
        ("Consistência das Taxas", verify_fee_consistency),
        ("Documentação", verify_documentation),
        ("Migração Alembic", verify_migration),
    ]
    
    results = []
    
    for name, func in verifications:
        try:
            passed = func()
            results.append((name, passed))
        except Exception as e:
            print_error(f"Erro ao verificar {name}: {str(e)}")
            results.append((name, False))
    
    # Resumo final
    print_header("RESUMO FINAL")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    failed = total - passed
    
    for name, status in results:
        if status:
            print_success(f"{name}")
        else:
            print_error(f"{name}")
    
    print(f"\n{Colors.BOLD}Resultado:{Colors.END}")
    print(f"  Total: {total}")
    print(f"  {Colors.GREEN}Passou: {passed}{Colors.END}")
    print(f"  {Colors.RED}Falhou: {failed}{Colors.END}")
    print(f"  Taxa de sucesso: {(passed/total)*100:.1f}%\n")
    
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ TODAS AS CORREÇÕES FORAM IMPLEMENTADAS COM SUCESSO!{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ ALGUMAS CORREÇÕES AINDA PRECISAM SER IMPLEMENTADAS{Colors.END}\n")
        print_info("Revise os itens marcados com ✗ acima")
        return 1

if __name__ == "__main__":
    sys.exit(main())
