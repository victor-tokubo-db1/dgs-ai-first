import { z } from "zod";

export const StructuredOutputSchema = z
  .object({
    answer: z.string().min(1, "answer é obrigatório").max(4000, "answer inválido"),
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

const SAFE_RESPONSE: StructuredOutput = {
  answer:
    "Não foi possível validar a resposta com segurança. Por favor, consulte um supervisor.",
  source_document: "SYSTEM-GUARDRAIL",
  confidence_score: 0,
};

const DANGEROUS_CARGO_REGEX =
  /\bcarga(s)?\s+perigosa(s)?\b|\bclasse(s)?\s*[1-6]\b|\bANTT\b/i;

const RETURN_REGEX =
  /\bdevolu(c|ç)(a|ã)o\b|\bdevolver\b|\bdevolvida(s)?\b|\bdevolvido(s)?\b/i;

const NEGATIVE_REGEX =
  /\bn(a|ã)o\b|\bnão\b|\bnao\b|\bn(a|ã)o\s+é\s+poss[ií]vel\b|\bn(a|ã)o\s+pode(m)?\b|\bineleg[ií]vel\b/i;

const POSITIVE_RETURN_REGEX =
  /\bé\s+poss[ií]vel\b.*\bdevolu(c|ç)(a|ã)o\b|\bpode(m)?\s+(ser\s+)?devolvid(a|o)(s)?\b|\bdevolu(c|ç)(a|ã)o\s+permitida\b/i;

function normalizeText(value: string): string {
  return value.normalize("NFC").toLowerCase();
}

function violatesDangerousReturnGuardrail(answer: string): boolean {
  const text = normalizeText(answer);
  const mentionsDangerous = DANGEROUS_CARGO_REGEX.test(text);
  const mentionsReturn = RETURN_REGEX.test(text);

  if (!mentionsDangerous || !mentionsReturn) {
    return false;
  }

  const hasNegative = NEGATIVE_REGEX.test(text);
  const hasPositiveReturn = POSITIVE_RETURN_REGEX.test(text);

  if (hasPositiveReturn) {
    return true;
  }

  return !hasNegative;
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

  const structured: StructuredOutput = {
    answer: parsed.data.answer.trim(),
    source_document: parsed.data.source_document.trim(),
    confidence_score: parsed.data.confidence_score,
  };

  if (!structured.source_document) {
    logger.warn("response_rejected_missing_source_document", {
      reason: "missing_source_document",
    });

    return {
      ok: false,
      response: SAFE_RESPONSE,
      reason: "missing_source_document",
    };
  }

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