#!/usr/bin/env python3
"""
Test script to verify that the session security fixes are working correctly.
This script creates two test users and verifies that their portfolio selections
are stored per-user in the database, not in shared sessions.
"""

import os
import sys
import django

# Setup Django environment FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_tracker.settings')
django.setup()

# Now import Django modules
from django.test import Client
from django.contrib.auth.models import User
from django.urls import reverse

from stocks.models import UserProfile, Portfolio, Stock
from stocks.views import get_user_current_portfolio, set_user_current_portfolio


def test_user_specific_portfolio_storage():
    """Test that portfolio selections are stored per-user, not in sessions"""
    print("🧪 Testing User-Specific Portfolio Storage...")
    
    # Clean up any existing test users
    User.objects.filter(username__in=['test_user_1', 'test_user_2']).delete()
    
    # Create two test users
    user1 = User.objects.create_user('test_user_1', 'user1@test.com', 'testpass123')
    user2 = User.objects.create_user('test_user_2', 'user2@test.com', 'testpass123')
    
    print(f"✅ Created test users: {user1.username}, {user2.username}")
    
    # Test 1: Default portfolio behavior
    portfolio1_default = get_user_current_portfolio(user1)
    portfolio2_default = get_user_current_portfolio(user2)
    
    print(f"📊 User1 default portfolio: '{portfolio1_default}'")
    print(f"📊 User2 default portfolio: '{portfolio2_default}'")
    
    assert portfolio1_default == 'My Investment Portfolio', "User1 should have default portfolio"
    assert portfolio2_default == 'My Investment Portfolio', "User2 should have default portfolio"
    
    # Test 2: Set different portfolios for each user
    success1 = set_user_current_portfolio(user1, 'User1 Tech Portfolio')
    success2 = set_user_current_portfolio(user2, 'User2 Value Portfolio')
    
    assert success1, "Setting portfolio for user1 should succeed"
    assert success2, "Setting portfolio for user2 should succeed"
    
    print("✅ Set different portfolios for each user")
    
    # Test 3: Verify portfolios are stored separately
    portfolio1_after = get_user_current_portfolio(user1)
    portfolio2_after = get_user_current_portfolio(user2)
    
    print(f"📊 User1 portfolio after change: '{portfolio1_after}'")
    print(f"📊 User2 portfolio after change: '{portfolio2_after}'")
    
    assert portfolio1_after == 'User1 Tech Portfolio', "User1 portfolio should be correctly saved"
    assert portfolio2_after == 'User2 Value Portfolio', "User2 portfolio should be correctly saved"
    assert portfolio1_after != portfolio2_after, "Users should have different portfolios"
    
    # Test 4: Change one user's portfolio, verify other user is unaffected
    success1_change = set_user_current_portfolio(user1, 'User1 Growth Portfolio')
    assert success1_change, "Changing user1 portfolio should succeed"
    
    portfolio1_final = get_user_current_portfolio(user1)
    portfolio2_final = get_user_current_portfolio(user2)
    
    print(f"📊 User1 portfolio after second change: '{portfolio1_final}'")
    print(f"📊 User2 portfolio (should be unchanged): '{portfolio2_final}'")
    
    assert portfolio1_final == 'User1 Growth Portfolio', "User1 portfolio should be updated"
    assert portfolio2_final == 'User2 Value Portfolio', "User2 portfolio should remain unchanged"
    
    print("✅ Portfolio isolation test PASSED - Users have independent portfolio selections")
    
    # Clean up
    user1.delete()
    user2.delete()
    print("🧹 Cleaned up test users")


def test_session_security_settings():
    """Test that Django session security settings are properly configured"""
    print("\n🔒 Testing Session Security Settings...")
    
    from django.conf import settings
    
    # Check that session settings are configured
    assert hasattr(settings, 'SESSION_COOKIE_NAME'), "SESSION_COOKIE_NAME should be set"
    assert settings.SESSION_COOKIE_NAME == 'portfolio_sessionid', "Should have unique session cookie name"
    
    assert hasattr(settings, 'SESSION_COOKIE_HTTPONLY'), "SESSION_COOKIE_HTTPONLY should be set"
    assert settings.SESSION_COOKIE_HTTPONLY is True, "Session cookies should be HTTP-only"
    
    assert hasattr(settings, 'SESSION_COOKIE_SAMESITE'), "SESSION_COOKIE_SAMESITE should be set"
    assert settings.SESSION_COOKIE_SAMESITE in ['Lax', 'Strict'], "SameSite should be set for CSRF protection"
    
    assert hasattr(settings, 'SESSION_COOKIE_AGE'), "SESSION_COOKIE_AGE should be set"
    assert settings.SESSION_COOKIE_AGE == 86400, "Session should expire in 24 hours"
    
    assert hasattr(settings, 'SESSION_SAVE_EVERY_REQUEST'), "SESSION_SAVE_EVERY_REQUEST should be set"
    assert settings.SESSION_SAVE_EVERY_REQUEST is True, "Should refresh session on every request"
    
    print("✅ Session security settings are properly configured")


def test_web_session_isolation():
    """Test session isolation through web requests"""
    print("\n🌐 Testing Web Session Isolation...")
    
    # Clean up any existing test users
    User.objects.filter(username__in=['web_user_1', 'web_user_2']).delete()
    
    # Create two test users
    user1 = User.objects.create_user('web_user_1', 'web1@test.com', 'testpass123')
    user2 = User.objects.create_user('web_user_2', 'web2@test.com', 'testpass123')
    
    # Create two separate client sessions
    client1 = Client()
    client2 = Client()
    
    # Log in each user with their respective client
    login1 = client1.login(username='web_user_1', password='testpass123')
    login2 = client2.login(username='web_user_2', password='testpass123')
    
    assert login1, "User1 login should succeed"
    assert login2, "User2 login should succeed"
    
    print("✅ Both users logged in with separate sessions")
    
    # Each client should have a different session
    session1_key = client1.session.session_key
    session2_key = client2.session.session_key
    
    assert session1_key != session2_key, "Users should have different session keys"
    print(f"📊 User1 session key: {session1_key[:10]}...")
    print(f"📊 User2 session key: {session2_key[:10]}...")
    
    # Clean up
    user1.delete()
    user2.delete()
    print("🧹 Cleaned up test users")
    print("✅ Web session isolation test PASSED")


def main():
    """Run all security tests"""
    print("🚀 Starting Session Security Tests\n")
    
    try:
        test_user_specific_portfolio_storage()
        test_session_security_settings()
        test_web_session_isolation()
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Session security issue has been successfully fixed!")
        print("\n📋 Summary of fixes:")
        print("  • Portfolio selection now stored in database per-user (not in sessions)")
        print("  • Session cookies have unique name and security settings")
        print("  • HTTP-only and SameSite protection enabled")
        print("  • Session timeout and refresh settings configured")
        print("  • Users can no longer access other users' portfolio selections")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        print(f"🔍 Error details: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
