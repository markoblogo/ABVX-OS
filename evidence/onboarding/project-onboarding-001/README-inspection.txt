CoqPi onboarding source inspection, 2026-08-08

Repository: https://github.com/markoblogo/CoqPi
Commit: 552d9857fce3f9058fe7f7f4e6faa8b247c49523
Runtime: local Electron desktop app, React renderer, TypeScript backend, Vite build
Primary providers: OpenAI Realtime and OpenAI text; optional Ollama fallback
Boundary: secrets stay in Electron main/backend; no autonomous outbound sender
Live call: not run; requires human consent, API key, device permissions, network, and a real microphone

Selected first slice:
  real-mic readiness is now gated by realtimeReady.
