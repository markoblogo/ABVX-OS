# Request identifier flow

The service passes an optional request identifier to the transport component. Transport owns the single `build_headers` compatibility point; callers without an identifier retain the original headers.
