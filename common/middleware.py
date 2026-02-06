import time
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils.cache import patch_vary_headers

class HostIsolatedSessionMiddleware(SessionMiddleware):
    """
    Extends SessionMiddleware to use different cookie names based on the Host header.
    This allows concurrent logins on 'localhost' and '127.0.0.1' without conflict.
    """
    
    def _get_cookie_name(self, request):
        default_name = settings.SESSION_COOKIE_NAME
        host = request.get_host().split(':')[0]
        
        # Create a unique suffix safe for cookie names
        suffix = host.replace('.', '_').replace(':', '')
        
        # Only modify for local dev environments to avoid production weirdness
        if host in ['localhost', '127.0.0.1', 'testserver']:
            return f"{default_name}_{suffix}"
            
        return default_name

    def process_request(self, request):
        # Override to use dynamic cookie name
        cookie_name = self._get_cookie_name(request)
        session_key = request.COOKIES.get(cookie_name)
        request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        """
        Copy of SessionMiddleware.process_response but using dynamic cookie name.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response

        # First check if we need to delete cookie (if empty)
        if settings.SESSION_COOKIE_NAME in request.COOKIES and empty:
            response.delete_cookie(
                settings.SESSION_COOKIE_NAME,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )
            return response
            
        if settings.SESSION_EXPIRE_AT_BROWSER_CLOSE:
            max_age = None
            expires = None
        else:
            max_age = request.session.get_expiry_age()
            expires_time = time.time() + max_age
            expires = time.strftime(
                "%a, %d-%b-%Y %H:%M:%S GMT", time.gmtime(expires_time)
            )

        # Helper to set the dynamic cookie
        def set_dynamic_cookie(response, key):
            response.set_cookie(
                key,
                request.session.session_key,
                max_age=max_age,
                expires=expires,
                domain=settings.SESSION_COOKIE_DOMAIN,
                path=settings.SESSION_COOKIE_PATH,
                secure=settings.SESSION_COOKIE_SECURE or None,
                httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                samesite=settings.SESSION_COOKIE_SAMESITE,
            )

        # Standard logic
        if accessed:
            patch_vary_headers(response, ("Cookie",))
            
        if (modified or settings.SESSION_SAVE_EVERY_REQUEST) and not empty:
            if request.session.get_expire_at_browser_close():
                max_age = None
                expires = None
            
            if response.status_code != 500:
                try:
                    request.session.save()
                except UpdateError:
                    return response
                
                # KEY CHANGE: Use dynamic name
                cookie_name = self._get_cookie_name(request)
                set_dynamic_cookie(response, cookie_name)
                
        return response
