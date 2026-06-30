import { app, HttpRequest, HttpResponseInit } from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';
import { z } from 'zod';
import { logger } from '../../shared/logger';

const FeedbackInputSchema = z.object({
	queryId: z.string().min(1),
	rating: z.number(),
	comment: z.string().optional(),
	attendantEmail: z.string().email(),
});

const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING!);
const database = client.database('novatech');
const container = database.container('feedbacks');

export async function feedbackHandler(
	request: HttpRequest
): Promise<HttpResponseInit> {
	const parsed = FeedbackInputSchema.safeParse(await request.json());

	if (!parsed.success) {
		return {
			status: 400,
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(parsed.error),
		};
	}

	const feedback = {
		...parsed.data,
		timestamp: new Date().toISOString(),
	};

	logger.info('Feedback recebido', {
		queryId: feedback.queryId,
		rating: feedback.rating,
	});

	try {
		await container.items.create(feedback);

		return {
			status: 201,
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ id: feedback.queryId }),
		};
	} catch (err) {
		logger.error('Falha ao persistir feedback', {
			err,
			queryId: feedback.queryId,
		});

		return {
			status: 503,
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ message: 'Serviço indisponível' }),
		};
	}
}

app.http('feedback', {
	methods: ['POST'],
	handler: feedbackHandler,
});
