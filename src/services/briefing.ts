import * as cheerio from 'cheerio';

interface NewsItem {
    title: string;
    link: string;
}

interface Feed {
    title: string;
    url: string;
}

const DEFAULT_FEEDS: Feed[] = [
    { title: '🇺🇸 미국 증시', url: 'https://news.google.com/rss/search?q=US+Stock+Market&hl=en-US&gl=US&ceid=US:en' },
    { title: '🇰🇷 한국 증시', url: 'https://news.google.com/rss/search?q=%EC%A3%BC%EC%8B%9D%EC%8B%9C%EC%9E%A5&hl=ko&gl=KR&ceid=KR:ko' },
    { title: '🪙 비트코인', url: 'https://news.google.com/rss/search?q=Bitcoin&hl=en-US&gl=US&ceid=US:en' }
];

// Jaccard Similarity for deduplication
function getSimilarity(str1: string, str2: string): number {
    const clean = (s: string) => s.replace(/[^\w\s가-힣]/g, '').toLowerCase();
    const s1 = new Set(clean(str1).split(/\s+/));
    const s2 = new Set(clean(str2).split(/\s+/));
    const intersection = new Set([...s1].filter(x => s2.has(x)));
    const union = new Set([...s1, ...s2]);
    return union.size === 0 ? 0 : intersection.size / union.size;
}

async function fetchFeedNews(feed: Feed, maxItems: number = 3): Promise<NewsItem[]> {
    try {
        const response = await fetch(feed.url);
        const xml = await response.text();
        const $ = cheerio.load(xml, { xmlMode: true });

        const items: NewsItem[] = [];

        $('item').each((_, item) => {
            if (items.length >= 10) return; // Initial pool limit

            const title = $(item).find('title').text();
            const link = $(item).find('link').text();

            // Deduplication
            let isDuplicate = false;
            for (const existing of items) {
                const sim = getSimilarity(existing.title, title);
                if (sim > 0.4 || existing.title.includes(title) || title.includes(existing.title)) {
                    isDuplicate = true;
                    break;
                }
            }

            if (!isDuplicate) {
                items.push({ title, link });
            }
        });

        return items.slice(0, maxItems);

    } catch (error) {
        console.error(`RSS Error ${feed.title}:`, error);
        return [];
    }
}

export async function generateBriefing(feeds: Feed[] = DEFAULT_FEEDS): Promise<string> {
    let message = `📢 <b>오늘의 시장 브리핑</b>\n\n`;

    for (const feed of feeds) {
        const items = await fetchFeedNews(feed);

        message += `<b>${feed.title}</b>\n`;

        if (items.length === 0) {
            message += `- 관련 뉴스가 없습니다.\n`;
        } else {
            items.forEach(item => {
                message += `- <a href="${item.link}">${item.title}</a>\n`;
            });
        }

        message += `\n`;
    }

    const now = new Date();
    message += `\n⏰ ${now.toLocaleDateString('ko-KR')} ${now.toLocaleTimeString('ko-KR')}`;

    return message;
}

export async function generateMarkdownBriefing(feeds: Feed[] = DEFAULT_FEEDS): Promise<string> {
    let message = `📢 **오늘의 시장 브리핑**\n\n`;

    for (const feed of feeds) {
        const items = await fetchFeedNews(feed);

        message += `*${feed.title}*\n`;

        if (items.length === 0) {
            message += `- 관련 뉴스가 없습니다.\n`;
        } else {
            items.forEach(item => {
                message += `- [${item.title}](${item.link})\n`;
            });
        }

        message += `\n`;
    }

    return message;
}
