import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import { verifyToken, getAuthToken } from "@/lib/auth";

export const maxDuration = 300;

const openai = new OpenAI();

export async function POST(request: NextRequest) {
  // Auth check
  const token = await getAuthToken();
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const payload = await verifyToken(token);
  if (!payload) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const formData = await request.formData();
    const audio = formData.get("audio") as File | null;
    const skipCleanup = formData.get("skipCleanup") === "true";
    const transcriptionModel =
      (formData.get("transcriptionModel") as string) ||
      process.env.TRANSCRIPTION_MODEL ||
      "gpt-4o-transcribe";
    const cleanupModel =
      (formData.get("cleanupModel") as string) ||
      process.env.CLEANUP_MODEL ||
      "gpt-4.1-mini";

    if (!audio) {
      return NextResponse.json(
        { error: "No audio file provided" },
        { status: 400 }
      );
    }

    // Transcribe
    const transcription = await openai.audio.transcriptions.create({
      file: audio,
      model: transcriptionModel,
      response_format: "json",
    });

    let text = transcription.text;

    // Cleanup pass
    if (!skipCleanup) {
      const cleanup = await openai.chat.completions.create({
        model: cleanupModel,
        messages: [
          {
            role: "system",
            content:
              "Restructura esta transcripcion a texto claro y legible en español. Corrige errores de puntuación y gramática. Mantén el contenido original.",
          },
          { role: "user", content: text },
        ],
      });

      text = cleanup.choices[0]?.message?.content || text;
    }

    return NextResponse.json({ text });
  } catch (error) {
    console.error("Transcription error:", error);
    const message =
      error instanceof Error ? error.message : "Transcription failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
