# audioToText

CLI chica para transcribir audio con OpenAI, limpiar el texto y guardar un `.txt` con un comando corto.

## Requisitos

- `uv`
- Python 3.12
- API key de OpenAI

## Instalación

```bash
uv sync
```

Si querés usar el comando sin prefijar `uv run`, podés activar el entorno virtual:

```bash
source .venv/bin/activate
```

## Configuración

Copiá `.env.example` a `.env` y completá al menos la API key:

```bash
cp .env.example .env
```

Variables disponibles:

- `OPENAI_API_KEY`
- `INPUT_DIR`
- `OUTPUT_DIR`
- `TRANSCRIPTION_MODEL`
- `CLEANUP_MODEL`
- `LOG_LEVEL`

Defaults:

- `INPUT_DIR=audio_inputs`
- `OUTPUT_DIR=transcriptions`
- `TRANSCRIPTION_MODEL=gpt-4o-transcribe`
- `CLEANUP_MODEL=gpt-4.1-mini`

El CLI intenta cargar un `.env` del directorio actual si existe. Si corrés `text` desde la raíz del repo, usa ese `.env`. Si no existe, toma variables de entorno normales del sistema.

## Uso rápido

Poné un audio en `audio_inputs/` del directorio desde el que vas a correr el comando, y corré:

```bash
uv run text nota
```

Si existe un único archivo que empiece por ese stem, por ejemplo `audio_inputs/nota.mp3`, el CLI lo resuelve solo y guarda:

```bash
transcriptions/nota.txt
```

También podés usar el nombre completo:

```bash
uv run text nota-reunion.m4a
```

O una ruta explícita:

```bash
uv run text /ruta/completa/audio.wav
```

## Opciones útiles

Guardar salida en otra carpeta:

```bash
uv run text nota --output-dir otro_directorio
```

Guardar en un archivo puntual:

```bash
uv run text nota --output transcriptions/salida-final.txt
```

Guardar la transcripción cruda sin cleanup:

```bash
uv run text nota --skip-cleanup
```

Cambiar modelos en una ejecución:

```bash
uv run text nota \
  --transcription-model gpt-4o-transcribe \
  --cleanup-model gpt-4.1-mini
```

Ver más logs:

```bash
uv run text nota --verbose
```

## Compatibilidad

El archivo `audio_transcriber.py` quedó como wrapper para el CLI nuevo, pero el flujo recomendado es usar `text`.
