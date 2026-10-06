"""Require Google authentication and explicit authorization before reading records."""
import streamlit as st


def is_allowed(user, allowed_emails):
    email = user.get('email', '')
    return (
        user.is_logged_in
        and user.get('email_verified') is True
        and isinstance(email, str)
        and email.casefold() in {value.strip().casefold() for value in allowed_emails}
    )


def require_access():
    try:
        auth = st.secrets.get('auth', {})
        allowed = st.secrets.get('allowed_emails', [])
    except FileNotFoundError:
        auth, allowed = {}, []
    fields = ('redirect_uri', 'cookie_secret', 'client_id', 'client_secret')
    ready = (
        isinstance(allowed, list) and bool(allowed)
        and all(isinstance(email, str) and email.strip() for email in allowed)
        and all(auth.get(field) for field in fields)
        and auth.get('server_metadata_url') == 'https://accounts.google.com/.well-known/openid-configuration'
    )
    if not ready:
        st.title('🏠 RentalOps')
        st.warning('Private access is not configured yet. The owner must complete Google sign-in settings before records can be accessed.')
        st.stop()
    if not st.user.is_logged_in:
        st.title('🏠 RentalOps')
        st.write('Sign in with your approved Google account to manage your properties.')
        if st.button('Sign in with Google', type='primary'):
            st.login()
        st.stop()
    if not is_allowed(st.user, allowed):
        st.error('This Google account is not authorized to access RentalOps.')
        if st.button('Sign out'):
            st.logout()
        st.stop()
    st.sidebar.caption(f"Signed in as {st.user.get('email')}")
    if st.sidebar.button('Sign out'):
        st.logout()
        st.stop()
