import { z } from "zod";

export const StructuredOutputSchema = z
  .object({
    answer: z
      .string()
      .min(1, "answer é obrigatório")
      .max(4000, "answer inválido"),
    source_document: z
      .string()
      .min(1, "source_document é obrigatório")
      .max(100, "source_document inválido"),
    confidence_score: z
      .number()
      .min(0, "confidence_score deve ser >= 0")
      .max(1, "confidence_score deve ser <= 1"),
  })
  .strict();

export type StructuredOutput = z.infer<typeof StructuredOutputSchema>;

type LoggerLike = {
  warn: (message: string, meta?: Record<string, unknown>) => void;
};

const defaultLogger: LoggerLike = {
  warn: (message, meta) => {
    console.warn(message, meta ?? {});
  },
};

const SAFE_RESPONSE: Readonly<StructuredOutput> = Object.freeze({
  answer:
    "Não foi possível validar a resposta com segurança. Por favor, consulte um supervisor.",
  source_document: "SYSTEM-GUARDRAIL",
  confidence_score: 0,
});

const DANGEROUS_CARGO_REGEX =
  /\bcarga(s)?\s+perigosa(s)?\b|\bclasse(s)?\s*[1-6]\b|\bANTT\b/i;

const RETURN_REGEX =
  /\bdevolu[cç][aã]o\b|\bdevolver\b|\bdevolvida(s)?\b|\bdevolvido(s)?\b/i;

const NEGATIVE_REGEX =
  /\bn[aã]o\b|\bn[aã]o\s+é\s+poss[ií]vel\b|\bn[aã]o\s+pode(m)?\b|\bineleg[ií]vel\b/i;

const AFFIRMS_DANGEROUS_RETURN_REGEX =
  /\bé\s+poss[ií]vel\b.*\bdevolu[cç][aã]o\b|\bpode(m)?\s+(ser\s+)?devolvid[ao](s)?\b|\bdevolu[cç][aã]o\s+permitida\b/i;

function normalizeText(value: string): string {
  return value.normalize("NFC").toLowerCase();
}

/**
 * Retorna true se a resposta afirmar (ou não negar claramente) que carga
 * perigosa pode ser devolvida — situação que deve ser bloqueada.
 *
 * Casos esperados:
 *   BLOQUEAR: "a carga perigosa pode ser devolvida"
 *   BLOQUEAR: "cargas perigosas classe 3 podem ser devolvidas" (sem negação)
 *   PERMITIR:  "cargas perigosas não podem ser devolvidas"
 *   PERMITIR:  "a devolução não é possível para cargas da ANTT"
 */
function violatesDangerousReturnGuardrail(answer: string): boolean {
  const text = normalizeText(answer);

  const mentionsDangerousCargo = DANGEROUS_CARGO_REGEX.test(text);
  const mentionsReturn = RETURN_REGEX.test(text);

  if (!mentionsDangerousCargo || !mentionsReturn) {
    return false;
  }

  const affirmsReturn = AFFIRMS_DANGEROUS_RETURN_REGEX.test(text);
  const hasNegation = NEGATIVE_REGEX.test(text);

  if (affirmsReturn) {
    return true;
  }

  return !hasNegation;
}

type ValidationResult = {
  ok: boolean;
  response: StructuredOutput;
  reason?: string;
};

export function validateResponse(
  raw: unknown,
  logger: LoggerLike = defaultLogger
): ValidationResult {
  const parsed = StructuredOutputSchema.safeParse(raw);

  if (!parsed.success) {
    logger.warn("response_rejected_schema_validation", {
      reason: "invalid_schema",
      issues: parsed.error.issues,
    });
    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "invalid_schema",
    };
  }

  const trimmedAnswer = parsed.data.answer.trim();
  const trimmedSourceDocument = parsed.data.source_document.trim();

  if (!trimmedAnswer) {
    logger.warn("response_rejected_empty_answer", {
      reason: "empty_answer_after_trim",
    });
    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "empty_answer_after_trim",
    };
  }

  if (!trimmedSourceDocument) {
    logger.warn("response_rejected_missing_source_document", {
      reason: "missing_source_document",
    });
    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "missing_source_document",
    };
  }

  const structured: StructuredOutput = {
    answer: trimmedAnswer,
    source_document: trimmedSourceDocument,
    confidence_score: parsed.data.confidence_score,
  };

  if (violatesDangerousReturnGuardrail(structured.answer)) {
    logger.warn("response_rejected_dangerous_return_guardrail", {
      reason: "dangerous_return_must_be_negative",
      source_document: structured.source_document,
    });
    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "dangerous_return_must_be_negative",
    };
  }

  return {
    ok: true,
    response: structured,
  };
}