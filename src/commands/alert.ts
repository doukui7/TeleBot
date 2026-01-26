/**
 * Alert Command
 * 특정 사용자에게 알림 전송
 *
 * Usage: npm run alert
 */

import dotenv from 'dotenv';
dotenv.config();

import { getUserById } from '../config/supabase';
import { sendMessage } from '../services/telegram';

interface AlertOptions {
    userId: string;
    message: string;
}

export async function sendAlert(options: AlertOptions): Promise<boolean> {
    const { userId, message } = options;

    const user = await getUserById(userId);

    if (!user || !user.telegram_id || !user.telegram_token) {
        console.error(`[Alert] User ${userId} not found or missing telegram settings`);
        return false;
    }

    const result = await sendMessage({
        chatId: user.telegram_id,
        token: user.telegram_token,
        message,
        parseMode: 'HTML'
    });

    if (result.success) {
        console.log(`[Alert] Message sent to user ${userId}`);
    } else {
        console.error(`[Alert] Failed to send to user ${userId}: ${result.error}`);
    }

    return result.success;
}

// CLI usage example
async function main() {
    const userId = process.argv[2];
    const message = process.argv[3];

    if (!userId || !message) {
        console.log('Usage: npm run alert <userId> "<message>"');
        console.log('Example: npm run alert abc123 "Price alert: BTC > $100,000"');
        return;
    }

    await sendAlert({ userId, message });
}

main().catch(console.error);
