
[group('setup')]
@ollama:
    ollama pull nomic-embed-text

[group('run')]
@run:
    uv run gradio src/GradioUI.py