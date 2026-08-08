# Architecture-affecting fixture

Add request identifiers across the transport and service components. Keep the existing `build_headers` helper as the single header construction point, preserve callers that do not provide an identifier, update the concise architecture note, and add tests for both components.
