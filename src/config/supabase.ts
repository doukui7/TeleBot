import { createClient, SupabaseClient } from '@supabase/supabase-js';
import dotenv from 'dotenv';

dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
    throw new Error('Missing Supabase environment variables');
}

export const supabase: SupabaseClient = createClient(supabaseUrl, supabaseServiceKey);

export interface TelegramUser {
    id: string;
    telegram_id: string;
    telegram_token: string;
}

export async function getTelegramUsers(): Promise<TelegramUser[]> {
    const { data, error } = await supabase
        .from('users')
        .select('id, telegram_id, telegram_token')
        .not('telegram_id', 'is', null)
        .not('telegram_token', 'is', null);

    if (error) {
        console.error('Error fetching telegram users:', error);
        return [];
    }

    return data || [];
}

export async function getUserById(userId: string): Promise<TelegramUser | null> {
    const { data, error } = await supabase
        .from('users')
        .select('id, telegram_id, telegram_token')
        .eq('id', userId)
        .single();

    if (error || !data) {
        return null;
    }

    return data;
}
