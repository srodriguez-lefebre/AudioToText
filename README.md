# audioToText CLI

CLI simple para transcribir un archivo de audio con OpenAI, reestructurar el texto y guardarlo en un `.txt`.

## Requisitos

- Python 3.10+
- API key de OpenAI

## Instalacion

```bash
python3 -m pip install -r requirements.txt
```

## Uso rapido

1. Coloca tu archivo de audio en `audio_inputs/` (o usa cualquier ruta).
2. Exporta tu API key:

```bash
export OPENAI_API_KEY="tu_api_key"
```

3. Ejecuta:

```bash
python3 audio_transcriber.py --input audio_inputs/mi-audio.mp3
```

Resultado por defecto: `transcriptions/mi-audio.txt`.

## Opciones utiles

```bash
python3 audio_transcriber.py \
  --input audio_inputs/mi-audio.mp3 \
  --output transcriptions/salida-final.txt \
  --transcription-model gpt-4o-transcribe \
  --cleanup-model gpt-4.1-mini
```

Para guardar texto crudo sin reestructurar:

```bash
python3 audio_transcriber.py --input audio_inputs/mi-audio.mp3 --skip-cleanup
```
