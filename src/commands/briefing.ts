/**
 * Briefing Command
 * 시장 브리핑 생성 및 전송
 *
 * Usage: npm run briefing
 */

import dotenv from 'dotenv';
dotenv.config();

import { getTelegramUsers } from '../config/supabase';
import { generateBriefing } from '../services/briefing';
import { sendToMultipleUsers } from '../services/telegram';

async function main() {
    console.log('[Briefing] Starting market briefing...');

    // 1. Generate briefing content
    console.log('[Briefing] Generating content...');
    const briefingMessage = await generateBriefing();
    console.log('[Briefing] Content generated successfully');

    // 2. Get telegram users
    console.log('[Briefing] Fetching telegram users...');
    const users = await getTelegramUsers();

    if (users.length === 0) {
        console.log('[Briefing] No telegram users found');
        return;
    }

    console.log(`[Briefing] Found ${users.length} users`);

    // 3. Send to all users
    console.log('[Briefing] Sending messages...');
    const results = await sendToMultipleUsers(users, briefingMessage, 'HTML');

    // 4. Report results
    const success = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;

    console.log(`[Briefing] Complete! Success: ${success}, Failed: ${failed}`);

    if (failed > 0) {
        console.log('[Briefing] Failed users:');
        results
            .filter(r => !r.success)
            .forEach(r => console.log(`  - ${r.chatId}: ${r.error}`));
    }
}

main().catch(console.error);
