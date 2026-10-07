# Documentation

## Guides

- [Architecture and API](architecture.md): service components, endpoints, request schemas, and streaming format.
- [Usage and configuration](usage.md): local setup, provider configuration, Streamlit, and Docker Compose.
- [Testing](testing.md): test scope, execution, and how to extend the suite.

## Scope

The gateway streams model output but does not include authentication, persistent conversations, request quotas, or provider credential management. Deploy it only behind appropriate access controls, and treat API keys entered in the UI as credentials sent to the gateway process.
