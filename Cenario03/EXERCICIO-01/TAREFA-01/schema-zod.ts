import { z } from "zod";

export const StructuredOutputSchema = z
  .object({
    answer: z
      .string()
      .min(1, "answer é obrigatório")
      .max(4000, "answer excede o tamanho máximo"),
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