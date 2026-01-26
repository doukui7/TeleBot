/**
 * Telegram Bot Main Entry
 *
 * 독립 실행 또는 cron 스케줄러로 동작
 */

import dotenv from 'dotenv';
dotenv.config();

import cron from 'node-cron';
import { getTelegramUsers } from './config/supabase';
import { generateBriefing } from './services/briefing';
import { sendToMultipleUsers, sendMessage } from './services/telegram';

// Re-export for external usage
export { sendMessage, sendToMultipleUsers } from './services/telegram';
export { generateBriefing, generateMarkdownBriefing } from './services/briefing';
export { getTelegramUsers, getUserById } from './config/supabase';
export { sendAlert } from './commands/alert';

async function sendDailyBriefing() {
    console.log(`[${new Date().toISOString()}] Running daily briefing...`);

    try {
        const briefing = await generateBriefing();
        const users = await getTelegramUsers();

        if (users.length === 0) {
            console.log('No telegram users to send briefing');
            return;
        }

        const results = await sendToMultipleUsers(users, briefing, 'HTML');
        const success = results.filter(r => r.success).length;
        console.log(`Briefing sent to ${success}/${users.length} users`);

    } catch (error) {
        console.error('Daily briefing error:', error);
    }
}

// Start server mode with cron scheduler
function startServer() {
    console.log('=================================');
    console.log('  Quanters Telegram Bot Started');
    console.log('=================================');
    console.log('');

    // Daily briefing at 8:00 AM KST (23:00 UTC previous day)
    cron.schedule('0 23 * * *', () => {
        sendDailyBriefing();
    }, {
        timezone: 'UTC'
    });

    console.log('Scheduled jobs:');
    console.log('  - Daily Briefing: 08:00 KST');
    console.log('');
    console.log('Press Ctrl+C to stop');
}

// Check if running directly
if (require.main === module) {
    const command = process.argv[2];

    if (command === 'briefing') {
        sendDailyBriefing().then(() => process.exit(0));
    } else if (command === 'server') {
        startServer();
    } else {
        console.log('Usage:');
        console.log('  npm start server   - Start with cron scheduler');
        console.log('  npm start briefing - Send briefing immediately');
        console.log('  npm run briefing   - Send briefing (direct)');
        console.log('  npm run alert      - Send alert to user');
    }
}
