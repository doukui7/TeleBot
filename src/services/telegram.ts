export interface SendMessageOptions {
    chatId: string;
    token: string;
    message: string;
    parseMode?: 'HTML' | 'Markdown' | 'MarkdownV2';
}

export interface SendResult {
    success: boolean;
    chatId: string;
    error?: string;
}

export async function sendMessage(options: SendMessageOptions): Promise<SendResult> {
    const { chatId, token, message, parseMode = 'HTML' } = options;

    try {
        const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: chatId,
                text: message,
                parse_mode: parseMode
            })
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            return {
                success: false,
                chatId,
                error: result.description || 'Unknown error'
            };
        }

        return { success: true, chatId };

    } catch (error) {
        return {
            success: false,
            chatId,
            error: error instanceof Error ? error.message : 'Network error'
        };
    }
}

export async function sendToMultipleUsers(
    users: Array<{ telegram_id: string; telegram_token: string }>,
    message: string,
    parseMode: 'HTML' | 'Markdown' | 'MarkdownV2' = 'HTML'
): Promise<SendResult[]> {
    const results = await Promise.all(
        users.map(user =>
            sendMessage({
                chatId: user.telegram_id,
                token: user.telegram_token,
                message,
                parseMode
            })
        )
    );

    return results;
}
